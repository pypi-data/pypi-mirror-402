"""
Utility functions for DID-HAD estimator.

This module contains kernel functions, bandwidth selection,
and nearest-neighbor residuals computation.

Uses nprobust package for local polynomial regression (lprobust).
"""

import numpy as np
from typing import Literal, Optional

# Import lprobust from nprobust package
try:
    from nprobust import lprobust
    NPROBUST_AVAILABLE = True
except ImportError:
    NPROBUST_AVAILABLE = False

KernelType = Literal["epa", "epanechnikov", "tri", "triangular", "uni", "uniform", "gau", "gaussian"]
BwMethodType = Literal["mse-dpi", "mse-rot", "imse-dpi", "imse-rot", "ce-dpi", "ce-rot"]


def kernel_weights(u: np.ndarray, kernel: KernelType = "epa") -> np.ndarray:
    """
    Compute kernel weights K(u).

    Note: Does NOT include the 1/h factor - that is applied externally.

    Parameters
    ----------
    u : np.ndarray
        Standardized distance array (x - eval) / h
    kernel : str
        Kernel type: 'epa'/'epanechnikov', 'tri'/'triangular',
        'uni'/'uniform', 'gau'/'gaussian'

    Returns
    -------
    np.ndarray
        Kernel weights
    """
    u = np.asarray(u, dtype=float)
    k = kernel.lower()

    if k in ("epa", "epanechnikov"):
        w = 0.75 * (1.0 - u**2)
        w[np.abs(u) > 1] = 0.0
        return w
    elif k in ("tri", "triangular"):
        w = 1.0 - np.abs(u)
        w[np.abs(u) > 1] = 0.0
        return w
    elif k in ("uni", "uniform"):
        return (np.abs(u) <= 1).astype(float)
    elif k in ("gau", "gaussian"):
        return np.exp(-0.5 * u**2) / np.sqrt(2 * np.pi)
    else:
        raise ValueError(f"Unknown kernel '{kernel}'")


def silverman_bandwidth(x: np.ndarray) -> float:
    """
    Silverman's rule of thumb bandwidth: h = 1.06 * sd * n^(-1/5).

    Parameters
    ----------
    x : np.ndarray
        Data array

    Returns
    -------
    float
        Optimal bandwidth
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = x.size
    if n < 2:
        raise ValueError("Not enough data to compute bandwidth")
    std = x.std(ddof=1)
    if std == 0:
        return 1e-8
    return 1.06 * std * n ** (-1 / 5)


def nn_residuals_lprobust_style(x_sorted: np.ndarray, y_sorted: np.ndarray,
                                 matches: int = 3) -> np.ndarray:
    """
    Nearest-neighbor residuals computation (lprobust-style).

    This is a close translation of lprobust.res for vce="nn".
    Assumes x_sorted is sorted in increasing order.

    Parameters
    ----------
    x_sorted : np.ndarray
        Sorted x values
    y_sorted : np.ndarray
        y values sorted by x
    matches : int
        Number of nearest neighbors to match

    Returns
    -------
    np.ndarray
        NN residuals
    """
    x_sorted = np.asarray(x_sorted, dtype=float)
    y_sorted = np.asarray(y_sorted, dtype=float)
    n = len(y_sorted)
    if n <= 1:
        return np.zeros_like(y_sorted)

    # Emulate 1-based indexing as in R
    xR = np.empty(n + 1, dtype=float)
    yR = np.empty(n + 1, dtype=float)
    xR[0] = np.nan
    yR[0] = np.nan
    xR[1:] = x_sorted
    yR[1:] = y_sorted

    dupsR = np.zeros(n + 1, dtype=int)
    dupsidR = np.zeros(n + 1, dtype=int)

    # dups[j] = how many times x[j] appears among all x's
    for jR in range(1, n + 1):
        dupsR[jR] = np.sum(xR[1:] == xR[jR])

    # dupsid: 1,...,k inside each block of duplicates
    jR = 1
    while jR <= n:
        k = dupsR[jR]
        if k <= 0:
            k = 1
        dupsidR[jR:jR + k] = np.arange(1, k + 1, dtype=int)
        jR += k

    resR = np.zeros(n + 1, dtype=float)
    max_m = min(matches, n - 1)

    for posR in range(1, n + 1):
        rpos = int(dupsR[posR] - dupsidR[posR])
        lpos = int(dupsidR[posR] - 1)

        while lpos + rpos < max_m:
            if posR - lpos - 1 <= 0:
                idxR = posR + rpos + 1
                if idxR > n:
                    break
                rpos += int(dupsR[idxR])
            elif posR + rpos + 1 > n:
                idxL = posR - lpos - 1
                if idxL < 1:
                    break
                lpos += int(dupsR[idxL])
            elif (xR[posR] - xR[posR - lpos - 1]) > (xR[posR + rpos + 1] - xR[posR]):
                rpos += int(dupsR[posR + rpos + 1])
            elif (xR[posR] - xR[posR - lpos - 1]) < (xR[posR + rpos + 1] - xR[posR]):
                lpos += int(dupsR[posR - lpos - 1])
            else:
                rpos += int(dupsR[posR + rpos + 1])
                lpos += int(dupsR[posR - lpos - 1])

        indJ_start = posR - lpos
        indJ_end = min(n, posR + rpos)
        idxs = np.arange(indJ_start, indJ_end + 1, dtype=int)
        Ji = idxs.size - 1

        if Ji <= 0:
            resR[posR] = 0.0
            continue

        yJ = np.sum(yR[idxs]) - yR[posR]
        resR[posR] = np.sqrt(Ji / (Ji + 1.0)) * (yR[posR] - yJ / Ji)

    # Back to 0-based indexing
    return resR[1:]


def lprobust_rbc_mu_se(
    x: np.ndarray,
    y: np.ndarray,
    h: Optional[float] = None,
    kernel: KernelType = "epa",
    matches: int = 3,
    b: Optional[float] = None,
    bwselect: Optional[BwMethodType] = "mse-dpi",
    vce: str = "nn",
) -> tuple:
    """
    Robust bias-corrected local polynomial regression using nprobust.lprobust.

    This function wraps the nprobust.lprobust function to match the interface
    used in the Stata did_had command.

    Parameters
    ----------
    x : np.ndarray
        Running variable (treatment)
    y : np.ndarray
        Outcome variable (first-differenced outcome)
    h : float, optional
        Main bandwidth. If None, automatic bandwidth selection is used.
    kernel : str
        Kernel type: 'epa', 'tri', 'uni', 'gau'
    matches : int
        Number of NN matches for variance estimation (default: 3)
    b : float, optional
        Bias bandwidth (defaults to automatic selection)
    bwselect : str, optional
        Bandwidth selection method: 'mse-dpi', 'mse-rot', 'imse-dpi',
        'imse-rot', 'ce-dpi', 'ce-rot'. Default is 'mse-dpi'.
    vce : str
        Variance-covariance estimator: 'nn' (default), 'hc0', 'hc1', 'hc2', 'hc3'

    Returns
    -------
    tuple
        (tau_cl, tau_bc, se_rb, h_opt, n_in_bw)
        - tau_cl: conventional local linear estimate (tau.us)
        - tau_bc: bias-corrected estimate (tau.bc)
        - se_rb: robust bias-corrected standard error (se.rb)
        - h_opt: selected/used bandwidth
        - n_in_bw: effective number of observations in bandwidth
    """
    if not NPROBUST_AVAILABLE:
        raise ImportError(
            "nprobust package is required. Install it with: pip install nprobust"
        )

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x = x[mask]
    y = y[mask]

    if x.size == 0:
        raise ValueError("No data after removing NaN values")

    # Evaluation point = 0 (as in Stata: gen grid_XX=0 if _n==1)
    eval_point = np.array([0.0])

    # Call lprobust with automatic bandwidth selection or fixed bandwidth
    # Matching Stata: lprobust y_diff_XX treatment_1_XX, eval(grid_XX) kernel(`kernel') bwselect(`bw_method')
    result = lprobust(
        y=y,
        x=x,
        eval=eval_point,
        p=1,           # Local linear (p=1)
        deriv=0,       # Estimate the function itself
        kernel=kernel,
        h=h,           # Main bandwidth (None = automatic)
        b=b,           # Bias bandwidth (None = automatic)
        bwselect=bwselect if h is None else None,  # Only use bwselect if h not provided
        vce=vce,
        nnmatch=matches,
    )

    # Extract results from Estimate matrix
    # Columns: [0]=eval, [1]=h, [2]=b, [3]=N.h, [4]=tau.us, [5]=tau.bc, [6]=se.us, [7]=se.rb, ...
    est = result.Estimate[0]  # First (and only) evaluation point

    h_opt = est[1]      # Bandwidth h
    n_in_bw = int(est[3])  # N.h (observations within bandwidth)
    tau_cl = est[4]     # tau.us (conventional estimate)
    tau_bc = est[5]     # tau.bc (bias-corrected estimate)
    se_rb = est[7]      # se.rb (robust bias-corrected SE)

    return float(tau_cl), float(tau_bc), float(se_rb), float(h_opt), int(n_in_bw)


def _lprobust_rbc_mu_se_fallback(
    x: np.ndarray,
    y: np.ndarray,
    h: float,
    kernel: KernelType = "tri",
    matches: int = 3,
    b: float = None,
) -> tuple:
    """
    Fallback implementation of lprobust when nprobust is not available.

    This is the original manual implementation with p=1, q=2, deriv=0, eval=0, vce="nn".
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x = x[mask]
    y = y[mask]

    if x.size == 0:
        raise ValueError("No data")

    # Sort as in vce = "nn"
    order = np.argsort(x)
    x = x[order]
    y = y[order]

    if b is None:
        b = h  # rho = 1 default in lprobust

    # Weights W.fun((x - eval)/h) / h with eval = 0
    u_h = x / h
    u_b = x / b
    W_h = kernel_weights(u_h, kernel=kernel) / h
    W_b = kernel_weights(u_b, kernel=kernel) / b

    ind_h = W_h > 0
    ind_b = W_b > 0
    ind = ind_b.copy()
    if h > b:
        ind = ind_h

    eX = x[ind]
    eY = y[ind]
    Wh = W_h[ind]
    Wb = W_b[ind]

    n = eX.size
    if n == 0:
        raise ValueError("No obs in kernel support.")

    # R.q = [1, x, x^2], R.p = [1, x]
    R_q = np.vstack([np.ones(n), eX, eX**2]).T
    R_p = R_q[:, :2]

    # u = (x - eval) / h = x/h
    u = eX / h

    # L = crossprod(R.p * W.h, u^(p+1)), with p = 1 => u^2
    L = (R_p * Wh[:, None]).T @ (u**2)
    L = L.reshape(2, 1)

    # invG.q = qrXXinv((sqrt(W.b) * R.q))
    Xq = np.sqrt(Wb)[:, None] * R_q
    Gq = Xq.T @ Xq
    invG_q = np.linalg.inv(Gq)

    # invG.p = qrXXinv((sqrt(W.h) * R.p))
    Xp = np.sqrt(Wh)[:, None] * R_p
    Gp = Xp.T @ Xp
    invG_p = np.linalg.inv(Gp)

    # e.p1 has 1 in position (p+2) = 3 => index 2 in 0-based
    e_p1 = np.array([[0.0], [0.0], [1.0]])  # (3 x 1)

    # A = L %*% t(e.p1) => 2 x 3
    A = L @ e_p1.T

    # t(t(invG.q %*% t(R.q)) * W.b)
    M = invG_q @ R_q.T        # 3 x n
    C = (M.T * Wb[:, None]).T # 3 x n

    # Term = h^(p+1) * (A %*% C), p=1 => h^2
    Term = (h**2) * (A @ C)   # 2 x n

    # t(R.p * W.h)
    Term1 = (R_p * Wh[:, None]).T  # 2 x n

    # Q.q = t(Term1 - Term) => n x 2
    Q_q = (Term1 - Term).T

    # Conventional beta.p and tau_cl
    beta_p = invG_p @ ((R_p * Wh[:, None]).T @ eY)
    tau_cl = beta_p[0]

    # Bias-corrected beta.bc and tau_bc
    beta_bc = invG_p @ (Q_q.T @ eY)
    tau_bc = beta_bc[0]

    # NN residuals (as in lprobust.res with vce = "nn")
    res_nn = nn_residuals_lprobust_style(eX, eY, matches=matches)

    # lprobust.vce(Q.q, res, C=NULL) = crossprod(c(res) * Q.q)
    RX = Q_q
    B = res_nn[:, None] * RX
    M_bc = B.T @ B  # 2 x 2

    # V_beta_bc = invG.p %*% M_bc %*% invG.p
    V_beta_bc = invG_p @ M_bc @ invG_p
    se_rb = np.sqrt(max(V_beta_bc[0, 0], 0.0))

    return float(tau_cl), float(tau_bc), float(se_rb), float(h), int(n)


def quasi_untreated_group_test(dose_array: np.ndarray) -> tuple:
    """
    Quasi-untreated group test.

    Tests whether valid quasi-untreated groups exist by comparing
    the two smallest positive treatment doses.

    T = D1 / (D2 - D1)
    p = 1 / (1 + T)

    Parameters
    ----------
    dose_array : np.ndarray
        Array of treatment doses

    Returns
    -------
    tuple
        (T_statistic, p_value)
    """
    x = np.asarray(dose_array, dtype=float)
    pos = x[x > 0]
    pos = np.sort(pos)
    if pos.size < 2:
        return np.nan, np.nan
    d1, d2 = pos[0], pos[1]
    if d2 <= d1:
        return np.nan, np.nan
    T = d1 / (d2 - d1)
    if T <= 0:
        return T, np.nan
    p_val = 1.0 / (1.0 + T)
    return T, p_val
