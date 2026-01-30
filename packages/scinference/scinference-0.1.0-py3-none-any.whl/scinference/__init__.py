"""
scinference: Inference methods for synthetic control and related methods.

This package implements inference methods for synthetic controls and related
methods based on Chernozhukov et al. (2020). It applies to settings with one
treated unit and J control units where the treated unit is untreated for the
first T0 periods and treated for the remaining T1 periods.

Main function:
    scinference: Perform inference for synthetic control methods

Example:
    >>> import numpy as np
    >>> from scinference import scinference
    >>>
    >>> # Generate example data
    >>> np.random.seed(12345)
    >>> J, T0, T1 = 50, 50, 5
    >>> Y0 = np.random.randn(T0 + T1, J)
    >>> w = np.zeros(J)
    >>> w[:3] = 1/3
    >>> Y1 = Y0 @ w + np.random.randn(T0 + T1)
    >>> Y1[T0:] += 2  # Add treatment effect
    >>>
    >>> # Test null hypothesis theta0=4
    >>> result = scinference(Y1, Y0, T1=T1, T0=T0, theta0=4)
    >>> print(f"p-value: {result['p_val']:.4f}")
"""

from .core import scinference
from .estimators import did, sc, classo
from .conformal import movingblock, iid, confidence_interval
from .ttest import sc_cf, did_cf

__version__ = "0.1.0"
__author__ = "Kaspar Wuthrich"
__email__ = "kwuthrich@ucsd.edu"

__all__ = [
    "scinference",
    "did",
    "sc",
    "classo",
    "movingblock",
    "iid",
    "confidence_interval",
    "sc_cf",
    "did_cf",
]
