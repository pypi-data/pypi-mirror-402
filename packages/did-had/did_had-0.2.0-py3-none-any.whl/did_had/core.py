"""
Core DID-HAD estimator implementation.

This module implements the Heterogeneous Adoption Design (HAD) estimator
following de Chaisemartin et al. (2025).
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Literal

from .utils import (
    silverman_bandwidth,
    lprobust_rbc_mu_se,
    quasi_untreated_group_test,
    KernelType,
    BwMethodType,
)


@dataclass
class DidHadResults:
    """
    Container for DID-HAD estimation results.

    Attributes
    ----------
    estimates : pd.DataFrame
        DataFrame with all estimates (effects and placebos)
    effects : pd.DataFrame
        DataFrame with effect estimates only
    placebos : pd.DataFrame
        DataFrame with placebo estimates only
    n_groups : int
        Number of groups in the analysis
    n_periods : int
        Number of time periods
    adoption_period : int
        Period F when treatment adoption occurs
    kernel : str
        Kernel used for estimation
    alpha : float
        Significance level
    """
    estimates: pd.DataFrame
    effects: pd.DataFrame
    placebos: pd.DataFrame
    n_groups: int
    n_periods: int
    adoption_period: int
    kernel: str
    alpha: float
    dynamic: bool = False
    bw_method: str = "mse-dpi"

    def summary(self) -> str:
        """Return a formatted summary string."""
        lines = []
        lines.append("=" * 75)
        lines.append("DID-HAD Estimation Results")
        lines.append("=" * 75)
        lines.append(f"Number of groups: {self.n_groups:,}")
        lines.append(f"Number of periods: {self.n_periods}")
        lines.append(f"Adoption period (F): {self.adoption_period}")
        lines.append(f"Kernel: {self.kernel}")
        lines.append(f"Bandwidth selection: {self.bw_method}")
        lines.append(f"Confidence level: {(1 - self.alpha) * 100:.0f}%")
        lines.append(f"Dynamic effects: {self.dynamic}")
        lines.append("")

        # Effects section
        if len(self.effects) > 0:
            lines.append("-" * 75)
            lines.append("                          Effect Estimates                      QUG* Test")
            lines.append("         " + "-" * 51 + " " + "-" * 15)
            lines.append("          Estimate       SE     LB.CI     UB.CI     N      BW    N.BW        T    p.val")

            for _, row in self.effects.iterrows():
                name = str(row["name"])
                est = row["estimate"]
                se = row["se"]
                lb = row["ci_lower"]
                ub = row["ci_upper"]
                n = int(row["n_groups"])
                bw = row["bandwidth"]
                nbw = int(row["n_in_bw"])
                T_qg = row["qg_T"]
                p_qg = row["qg_pval"]

                n_str = f"{n:,}"

                if np.isfinite(T_qg):
                    T_str = f"{T_qg:8.5f}"
                    p_str = f"{p_qg:8.5f}"
                    T_part = f"{T_str} {p_str}"
                else:
                    T_part = " " * 17

                lines.append(
                    f"{name:<9}"
                    f"{est:9.5f} "
                    f"{se:8.5f} "
                    f"{lb:9.5f} "
                    f"{ub:9.5f} "
                    f"{n_str:>5} "
                    f"{bw:7.5f} "
                    f"{nbw:6d} "
                    f"{T_part}"
                )
            lines.append("*Quasi-Untreated Group")
            lines.append("")

        # Placebos section
        if len(self.placebos) > 0:
            lines.append("-" * 62)
            lines.append("                           Placebo Estimates")
            lines.append("          " + "-" * 52)
            lines.append("           Estimate       SE     LB.CI     UB.CI     N      BW    N.BW")

            for _, row in self.placebos.iterrows():
                name = str(row["name"])
                est = row["estimate"]
                se = row["se"]
                lb = row["ci_lower"]
                ub = row["ci_upper"]
                n = int(row["n_groups"])
                bw = row["bandwidth"]
                nbw = int(row["n_in_bw"])
                n_str = f"{n:,}"

                lines.append(
                    f"{name:<9}"
                    f"{est:9.5f} "
                    f"{se:8.5f} "
                    f"{lb:9.5f} "
                    f"{ub:9.5f} "
                    f"{n_str:>5} "
                    f"{bw:7.5f} "
                    f"{nbw:6d}"
                )
            lines.append("")

        lines.append("=" * 75)
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.summary()

    def to_dataframe(self) -> pd.DataFrame:
        """Return all estimates as a DataFrame."""
        return self.estimates.copy()

    def att(self) -> float:
        """Return the average treatment effect on the treated (mean of effects)."""
        if len(self.effects) == 0:
            return np.nan
        return self.effects["estimate"].mean()


class DidHad:
    """
    Heterogeneous Adoption Design (HAD) Estimator.

    This class implements the HAD estimator from de Chaisemartin et al. (2025)
    for settings where all groups receive treatment but with different intensities.

    Uses nprobust package for local polynomial regression with automatic
    bandwidth selection, matching the Stata did_had implementation.

    Parameters
    ----------
    kernel : str, default="epa"
        Kernel function for local polynomial regression.
        Options: 'epa'/'epanechnikov', 'tri'/'triangular',
        'uni'/'uniform', 'gau'/'gaussian'
    bw_method : str, default="mse-dpi"
        Bandwidth selection method.
        Options: 'mse-dpi', 'mse-rot', 'imse-dpi', 'imse-rot', 'ce-dpi', 'ce-rot'
    alpha : float, default=0.05
        Significance level for confidence intervals
    nnmatch : int, default=3
        Number of nearest neighbors for variance estimation
    vce : str, default="nn"
        Variance-covariance estimator: 'nn', 'hc0', 'hc1', 'hc2', 'hc3'

    Examples
    --------
    >>> import pandas as pd
    >>> from did_had import DidHad
    >>>
    >>> # Load data
    >>> df = pd.read_stata("tutorial_data.dta")
    >>>
    >>> # Fit the model with default options (matching Stata defaults)
    >>> model = DidHad(kernel="epa", bw_method="mse-dpi")
    >>> results = model.fit(
    ...     df=df,
    ...     outcome="y",
    ...     group="g",
    ...     time="t",
    ...     treatment="d",
    ...     effects=5,
    ...     placebo=4
    ... )
    >>>
    >>> # View results
    >>> print(results)
    >>> print(f"ATT: {results.att():.4f}")
    """

    def __init__(
        self,
        kernel: KernelType = "epa",
        bw_method: BwMethodType = "mse-dpi",
        alpha: float = 0.05,
        nnmatch: int = 3,
        vce: str = "nn",
    ):
        self.kernel = kernel
        self.bw_method = bw_method
        self.alpha = alpha
        self.nnmatch = nnmatch
        self.vce = vce
        self._results: Optional[DidHadResults] = None
        # Normal critical value for default 95% CI
        self._z_crit = 1.959963984540054

    @property
    def results(self) -> Optional[DidHadResults]:
        """Return fitted results or None if not fitted."""
        return self._results

    def fit(
        self,
        df: pd.DataFrame,
        outcome: str,
        group: str,
        time: str,
        treatment: str,
        effects: int = 1,
        placebo: int = 0,
        dynamic: bool = False,
        bandwidth: Optional[float] = None,
        bandwidth_effect: Optional[Union[float, Dict[int, float]]] = None,
        bandwidth_placebo: Optional[Union[float, Dict[int, float]]] = None,
    ) -> DidHadResults:
        """
        Fit the DID-HAD model.

        Parameters
        ----------
        df : pd.DataFrame
            Panel data with columns for outcome, group, time, and treatment
        outcome : str
            Name of the outcome variable column
        group : str
            Name of the group identifier column
        time : str
            Name of the time period column
        treatment : str
            Name of the treatment variable column
        effects : int, default=1
            Number of post-treatment effect periods to estimate
        placebo : int, default=0
            Number of pre-treatment placebo periods to estimate
        dynamic : bool, default=False
            If True, scale effects by cumulative treatment dose
        bandwidth : float, optional
            Global bandwidth (used if bandwidth_effect/bandwidth_placebo not set)
        bandwidth_effect : float or dict, optional
            Bandwidth(s) for effect estimates. Can be a scalar or dict mapping
            horizon to bandwidth
        bandwidth_placebo : float or dict, optional
            Bandwidth(s) for placebo estimates. Can be a scalar or dict mapping
            horizon to bandwidth

        Returns
        -------
        DidHadResults
            Object containing estimation results with summary() method
        """
        df = df.copy()
        cols = [group, time, outcome, treatment]
        df = df[cols].dropna()

        # Ensure numeric types
        for c in cols:
            df[c] = pd.to_numeric(df[c])

        # Wide panel: rows = groups, columns = time periods
        y_pivot = df.pivot(index=group, columns=time, values=outcome)
        d_pivot = df.pivot(index=group, columns=time, values=treatment)
        groups = y_pivot.index.to_numpy()
        times = np.sort(y_pivot.columns.to_numpy())

        n_groups = len(groups)
        n_periods = len(times)

        # First period with positive treatment (F)
        F = None
        for t_val in times:
            if (d_pivot[t_val] > 0).any():
                F = t_val
                break
        if F is None:
            raise ValueError("Could not find adoption period F (no positive treatment).")

        Fm1 = F - 1
        t_min = times.min()
        t_max = times.max()

        # Check: treatment must be zero before F
        for t_val in times[times < F]:
            if (d_pivot[t_val] != 0).any():
                raise ValueError(f"Treatment is nonzero before F at t={t_val}.")

        # Max feasible effect horizon
        max_effect = int(effects)
        while max_effect > 0 and (Fm1 + max_effect > t_max):
            max_effect -= 1

        # Max feasible placebo horizon
        max_placebo = int(placebo)
        while max_placebo > 0 and (Fm1 - max_placebo < t_min):
            max_placebo -= 1

        if max_effect == 0 and max_placebo == 0:
            raise ValueError("No feasible effect or placebo horizons given the time range.")

        # Helper: bandwidth by horizon for effects
        def _get_bw_effect(ell):
            if bandwidth_effect is None:
                return bandwidth
            if np.isscalar(bandwidth_effect):
                return float(bandwidth_effect)
            if isinstance(bandwidth_effect, dict):
                return float(bandwidth_effect.get(ell, bandwidth))
            raise ValueError("bandwidth_effect must be None, scalar, or dict")

        # Helper: bandwidth by horizon for placebos
        def _get_bw_placebo(ell):
            if bandwidth_placebo is None:
                return bandwidth
            if np.isscalar(bandwidth_placebo):
                return float(bandwidth_placebo)
            if isinstance(bandwidth_placebo, dict):
                return float(bandwidth_placebo.get(ell, bandwidth))
            raise ValueError("bandwidth_placebo must be None, scalar, or dict")

        results_rows = []

        # Post-treatment effects
        for ell in range(1, max_effect + 1):
            t_post = Fm1 + ell
            if t_post not in y_pivot.columns:
                continue

            y_post = y_pivot[t_post]
            y_base = y_pivot[Fm1]
            delta_y = (y_post - y_base).to_numpy()

            dose_current = d_pivot[t_post].to_numpy()

            if dynamic:
                dose_norm = (
                    d_pivot.loc[:, (times >= F) & (times <= t_post)]
                    .sum(axis=1)
                    .to_numpy()
                )
            else:
                dose_norm = dose_current.copy()

            bw_use = _get_bw_effect(ell)

            est, se_est, low, up, bw_eff, n_in_bw, dy_arr, du_arr, dn_arr = self._compute_effect(
                delta_y,
                dose_current,
                dose_norm,
                bw_use,
            )

            T_qg, p_qg = quasi_untreated_group_test(du_arr)

            results_rows.append({
                "type": "effect",
                "horizon": ell,
                "estimate": est,
                "se": se_est,
                "ci_lower": low,
                "ci_upper": up,
                "bandwidth": bw_eff,
                "n_in_bw": n_in_bw,
                "n_groups": dy_arr.size,
                "qg_T": T_qg,
                "qg_pval": p_qg,
            })

        # Pre-treatment placebos
        for ell in range(1, max_placebo + 1):
            t_pre = Fm1 - ell
            t_future = Fm1 + ell
            if t_pre not in y_pivot.columns or t_future not in y_pivot.columns:
                continue

            y_pre = y_pivot[t_pre]
            y_base = y_pivot[Fm1]
            delta_y_pre = (y_pre - y_base).to_numpy()

            dose_future = d_pivot[t_future].to_numpy()

            if dynamic:
                dose_norm = (
                    d_pivot.loc[:, (times >= F) & (times <= t_future)]
                    .sum(axis=1)
                    .to_numpy()
                )
            else:
                dose_norm = dose_future.copy()

            bw_use = _get_bw_placebo(ell)

            est, se_est, low, up, bw_eff, n_in_bw, dy_arr, du_arr, dn_arr = self._compute_effect(
                delta_y_pre,
                dose_future,
                dose_norm,
                bw_use,
            )

            results_rows.append({
                "type": "placebo",
                "horizon": ell,
                "estimate": est,
                "se": se_est,
                "ci_lower": low,
                "ci_upper": up,
                "bandwidth": bw_eff,
                "n_in_bw": n_in_bw,
                "n_groups": dy_arr.size,
                "qg_T": np.nan,
                "qg_pval": np.nan,
            })

        estimates = pd.DataFrame(results_rows)
        estimates["name"] = np.where(
            estimates["type"] == "effect",
            "Effect_" + estimates["horizon"].astype(int).astype(str),
            "Placebo_" + estimates["horizon"].astype(int).astype(str),
        )

        effects_df = estimates[estimates["type"] == "effect"].sort_values("horizon").reset_index(drop=True)
        placebos_df = estimates[estimates["type"] == "placebo"].sort_values("horizon").reset_index(drop=True)

        self._results = DidHadResults(
            estimates=estimates,
            effects=effects_df,
            placebos=placebos_df,
            n_groups=n_groups,
            n_periods=n_periods,
            adoption_period=F,
            kernel=self.kernel,
            alpha=self.alpha,
            dynamic=dynamic,
            bw_method=self.bw_method,
        )

        return self._results

    def _compute_effect(
        self,
        delta_y: np.ndarray,
        dose_use: np.ndarray,
        dose_norm: np.ndarray,
        bw_override: Optional[float],
    ) -> tuple:
        """
        Compute effect estimate using kernel regression with nprobust.lprobust.

        This method implements the estimation procedure from Stata's did_had command:
        - Runs lprobust with eval=0 to estimate mu_hat at zero treatment
        - Uses automatic bandwidth selection (MSE-DPI by default) or fixed bandwidth
        - Computes bias-corrected estimates and robust standard errors

        Parameters
        ----------
        delta_y : np.ndarray
            Outcome differences (Y_t - Y_{F-1})
        dose_use : np.ndarray
            Dose used as running variable in lprobust
        dose_norm : np.ndarray
            Dose used for normalization (denominator in ß_qs)
        bw_override : float, optional
            Bandwidth override. If None, uses automatic bandwidth selection.

        Returns
        -------
        tuple
            (estimate, se, ci_lower, ci_upper, bandwidth, n_in_bw,
             delta_y_clean, dose_use_clean, dose_norm_clean)
        """
        delta_y = np.asarray(delta_y, dtype=float)
        dose_use = np.asarray(dose_use, dtype=float)
        dose_norm = np.asarray(dose_norm, dtype=float)

        mask = ~(np.isnan(delta_y) | np.isnan(dose_use) | np.isnan(dose_norm))
        delta_y = delta_y[mask]
        dose_use = dose_use[mask]
        dose_norm = dose_norm[mask]

        if delta_y.size == 0:
            raise ValueError("No valid observations at this horizon.")

        delta_mean = delta_y.mean()
        dose_norm_mean = dose_norm.mean()
        if dose_norm_mean == 0:
            raise ValueError("Average normalization dose is zero; cannot scale effect.")

        # Call lprobust with automatic bandwidth selection or fixed bandwidth
        # Matching Stata: lprobust y_diff_XX treatment_1_XX, eval(grid_XX) kernel(`kernel') bwselect(`bw_method')
        tau_cl, tau_bc, se_mu, h_opt, n_in_bw = lprobust_rbc_mu_se(
            x=dose_use,
            y=delta_y,
            h=bw_override,  # None = automatic bandwidth selection
            kernel=self.kernel,
            matches=self.nnmatch,
            b=None,
            bwselect=self.bw_method,
            vce=self.vce,
        )

        # Use the selected/provided bandwidth
        bw_eff = h_opt

        # ß_qs = (mean(Δy) - tau.us) / mean(d_norm)
        # Stata: scalar ß_qs_XX=(mean_y_diff_XX-mu_hat_XX_alt)/mean_treatment_XX
        est_qs = (delta_mean - tau_cl) / dose_norm_mean

        # M_hat_hG = tau.us - tau.bc (bias)
        # Stata: scalar M_hat_hG_XX=e(Result)[1,5]-e(Result)[1,6]
        M_hat_hG = tau_cl - tau_bc

        # B_hat_Hg = - M_hat_hG / mean(d_norm)
        # Stata: scalar B_hat_Hg_XX=-M_hat_hG_XX/mean_treatment_XX
        B_hat_Hg = -M_hat_hG / dose_norm_mean

        # se_est = se_mu / mean(d_norm)
        # Stata: scalar se_naive_XX=se_mu_XX/mean_treatment_XX
        se_est = se_mu / dose_norm_mean

        # CI with bias correction (matches Stata's did_had)
        # Stata: scalar low_XX=ß_qs_XX-B_hat_Hg_XX-invnormal(1-(`alpha'/2))*scalar(se_naive_XX)
        low = est_qs - B_hat_Hg - self._z_crit * se_est
        up = est_qs - B_hat_Hg + self._z_crit * se_est

        return est_qs, se_est, low, up, bw_eff, n_in_bw, delta_y, dose_use, dose_norm

    def summary(self) -> str:
        """Return summary of fitted results."""
        if self._results is None:
            raise ValueError("Model not fitted. Call fit() first.")
        return self._results.summary()

    def save_results(
        self,
        filepath: str,
        format: Literal["csv", "stata", "excel", "pickle"] = "csv"
    ) -> None:
        """
        Save results to file.

        Parameters
        ----------
        filepath : str
            Path to save file
        format : str
            Output format: 'csv', 'stata', 'excel', or 'pickle'
        """
        if self._results is None:
            raise ValueError("Model not fitted. Call fit() first.")

        df = self._results.estimates

        if format == "csv":
            df.to_csv(filepath, index=False)
        elif format == "stata":
            df.to_stata(filepath)
        elif format == "excel":
            df.to_excel(filepath, index=False)
        elif format == "pickle":
            df.to_pickle(filepath)
        else:
            raise ValueError(f"Unknown format: {format}")

    def plot(
        self,
        figsize: tuple = (6.5, 4.5),
        title: str = None,
        x_label: str = "Time from Treatment",
        y_label: str = "Estimate",
        note: str = None,
    ):
        """
        Create event-study plot.

        Parameters
        ----------
        figsize : tuple
            Figure size (default: (6.5, 4.5))
        title : str, optional
            Plot title
        x_label : str
            X-axis label (default: "Time from Treatment")
        y_label : str
            Y-axis label (default: "Estimate")
        note : str, optional
            Text note at the bottom of the figure

        Returns
        -------
        tuple
            (fig, ax) matplotlib Figure and Axes
        """
        if self._results is None:
            raise ValueError("Model not fitted. Call fit() first.")

        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
        except ImportError:
            raise ImportError("matplotlib and seaborn are required for plotting")

        # Extract data
        effects = self._results.effects.copy()
        placebos = self._results.placebos.copy()

        # Construct time column based on horizon
        # Placebo_1 (horizon=1) -> time=-1, Placebo_2 -> time=-2, etc.
        # Effect_1 (horizon=1) -> time=1, Effect_2 -> time=2, etc.
        n_pl = placebos.shape[0]
        if n_pl > 0:
            placebos["time"] = -placebos["horizon"].astype(int)

        n_eff = effects.shape[0]
        if n_eff > 0:
            effects["time"] = effects["horizon"].astype(int)

        # Sort by time
        placebos = placebos.sort_values("time")
        effects = effects.sort_values("time")

        # Style (similar to journal/event-study figure)
        sns.set_theme(style="white", context="paper")
        plt.rcParams["font.family"] = "serif"
        plt.rcParams["font.size"] = 12

        fig, ax = plt.subplots(figsize=figsize)

        # Pre-treatment (placebos): vertical CI + dots
        if n_pl > 0:
            ax.vlines(
                x=placebos["time"],
                ymin=placebos["ci_lower"],
                ymax=placebos["ci_upper"],
                color="black",
                linewidth=2,
            )
            ax.scatter(
                placebos["time"],
                placebos["estimate"],
                color="black",
                s=35,
                zorder=3,
            )

        # Post-treatment (effects): vertical CI + dots
        if n_eff > 0:
            ax.vlines(
                x=effects["time"],
                ymin=effects["ci_lower"],
                ymax=effects["ci_upper"],
                color="black",
                linewidth=2,
            )
            ax.scatter(
                effects["time"],
                effects["estimate"],
                color="black",
                s=35,
                zorder=3,
            )

        # Omitted period at 0 with CI [0, 0]
        ax.vlines(0, 0, 0, color="black", linewidth=2)
        ax.scatter(0, 0, color="black", s=35, zorder=4)

        # Zero lines (axes)
        ax.axhline(0, color="black", linewidth=1)
        ax.axvline(0, color="black", linewidth=1)

        # Ticks
        x_min = int(placebos["time"].min()) if n_pl > 0 else 0
        x_max = int(effects["time"].max()) if n_eff > 0 else 0
        xticks = list(range(x_min, x_max + 1))
        ax.set_xticks(xticks)
        ax.set_xticklabels([str(x) for x in xticks])

        # Only horizontal dashed grid
        ax.yaxis.grid(True, linestyle="--", linewidth=0.7, color="0.8")
        ax.xaxis.grid(False)

        # Remove top and right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.tick_params(axis="both", direction="out", length=4)

        # Labels
        ax.set_xlabel(x_label, labelpad=10)
        ax.set_ylabel(y_label)

        # Title
        if title is not None:
            ax.set_title(title, loc="center", pad=15)

        # Note at bottom
        if note is not None:
            fig.text(0.5, 0.02, note, ha="center", va="bottom", fontsize=9)
            fig.subplots_adjust(top=0.92, bottom=0.18, left=0.12, right=0.97)
        else:
            fig.tight_layout()

        return fig, ax
