"""
DID-HAD: Difference-in-Differences with Heterogeneous Adoption Design

A Python implementation of the Heterogeneous Adoption Design (HAD) estimator
from de Chaisemartin et al. (2025) for difference-in-differences analysis
when all groups receive treatment but with varying intensities.

This package uses nprobust for local polynomial regression with automatic
bandwidth selection, matching the Stata did_had implementation.

Example
-------
>>> import pandas as pd
>>> from did_had import DidHad
>>>
>>> df = pd.read_stata("tutorial_data.dta")
>>> # Default options match Stata: kernel="epa", bw_method="mse-dpi"
>>> model = DidHad(kernel="epa", bw_method="mse-dpi")
>>> results = model.fit(df, outcome="y", group="g", time="t", treatment="d", effects=5, placebo=4)
>>> print(results)
"""

from .core import DidHad, DidHadResults
from .utils import (
    kernel_weights,
    silverman_bandwidth,
    lprobust_rbc_mu_se,
    quasi_untreated_group_test,
    KernelType,
    BwMethodType,
    NPROBUST_AVAILABLE,
)

__version__ = "0.2.0"
__author__ = "Anzony Quispe"
__email__ = "anzonyquispe@example.com"

__all__ = [
    "DidHad",
    "DidHadResults",
    "kernel_weights",
    "silverman_bandwidth",
    "lprobust_rbc_mu_se",
    "quasi_untreated_group_test",
    "KernelType",
    "BwMethodType",
    "NPROBUST_AVAILABLE",
]
