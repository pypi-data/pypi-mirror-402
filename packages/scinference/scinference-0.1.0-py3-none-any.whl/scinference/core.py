"""
Main inference function for synthetic control methods.

This module provides the main `scinference` function that serves as the
primary entry point for all inference methods in this package.
"""

import numpy as np
from scipy.stats import t as t_dist
from typing import Dict, Union, Optional
from .conformal import movingblock, iid, confidence_interval
from .ttest import sc_cf, did_cf


def scinference(
    Y1: np.ndarray,
    Y0: np.ndarray,
    T1: int,
    T0: int,
    inference_method: str = "conformal",
    alpha: float = 0.1,
    ci: bool = False,
    theta0: Union[float, np.ndarray] = 0,
    estimation_method: str = "sc",
    permutation_method: str = "mb",
    ci_grid: Optional[np.ndarray] = None,
    n_perm: int = 5000,
    lsei_type: int = 1,
    K: int = 2,
) -> Dict:
    """
    Inference methods for synthetic control.

    This function implements inference methods for synthetic controls and
    related methods based on Chernozhukov et al. (2020). It applies to
    settings with one treated unit and J control units where the treated
    unit is untreated for the first T0 periods and treated for the
    remaining T1 periods.

    Parameters
    ----------
    Y1 : array-like
        Outcome data for treated unit (T x 1 vector where T = T0 + T1)
    Y0 : array-like
        Outcome data for control units (T x J matrix)
    T1 : int
        Number of post-treatment periods
    T0 : int
        Number of pre-treatment periods
    inference_method : str, optional
        Inference method: "conformal" (default) or "ttest"
    alpha : float, optional
        Significance level for confidence intervals (default=0.1)
    ci : bool, optional
        Whether to compute pointwise confidence intervals (default=False)
    theta0 : float or array-like, optional
        Null hypothesis for treatment effect trajectory. Can be a scalar
        (same effect for all periods) or a vector of length T1 (default=0)
    estimation_method : str, optional
        Counterfactual estimation method:
        - "did": Difference-in-differences
        - "sc": Synthetic control (default)
        - "classo": Constrained lasso (only for conformal)
    permutation_method : str, optional
        Permutation method for conformal inference:
        - "mb": Moving block (default)
        - "iid": IID permutations
    ci_grid : array-like, optional
        Grid of values for confidence interval computation (required if ci=True)
    n_perm : int, optional
        Number of permutations for iid method (default=5000)
    lsei_type : int, optional
        Option for lsei solver in sc method (default=1)
    K : int, optional
        Number of cross-fits for t-test (must be > 1, default=2)

    Returns
    -------
    dict
        For conformal inference:
            - p_val: p-value for the null hypothesis test
            - lb: lower bounds of pointwise CIs (if ci=True, otherwise NaN)
            - ub: upper bounds of pointwise CIs (if ci=True, otherwise NaN)

        For t-test:
            - att: Average Treatment Effect on the Treated
            - se: Standard error
            - lb: Lower bound of confidence interval
            - ub: Upper bound of confidence interval

    Examples
    --------
    Conformal inference with synthetic control:

    >>> import numpy as np
    >>> from scinference import scinference
    >>> np.random.seed(12345)
    >>> J, T0, T1 = 50, 50, 5
    >>> Y0 = np.random.randn(T0 + T1, J)
    >>> w = np.zeros(J); w[:3] = 1/3
    >>> Y1 = Y0 @ w + np.random.randn(T0 + T1)
    >>> Y1[T0:] += 2
    >>> result = scinference(Y1, Y0, T1=T1, T0=T0, theta0=4)
    >>> print(f"p-value: {result['p_val']:.4f}")

    T-test with cross-fitting:

    >>> result = scinference(Y1, Y0, T1=T1, T0=T0, inference_method="ttest", K=2)
    >>> print(f"ATT: {result['att']:.4f}, SE: {result['se']:.4f}")

    References
    ----------
    Chernozhukov, V., Wuthrich, K., & Zhu, Y. (2020). An Exact and Robust
    Conformal Inference Method for Counterfactual and Synthetic Controls.

    See Also
    --------
    did : Difference-in-differences estimator
    sc : Synthetic control estimator
    classo : Constrained lasso estimator
    """
    # Convert inputs to numpy arrays
    Y1 = np.asarray(Y1, dtype=np.float64).flatten()
    Y0 = np.asarray(Y0, dtype=np.float64)

    # Input validation
    if len(Y1) != (T0 + T1):
        raise ValueError(
            f"length of Y1 ({len(Y1)}) needs to be equal to T0 + T1 ({T0 + T1})"
        )
    if Y0.shape[0] != (T0 + T1):
        raise ValueError(
            f"number of rows in Y0 ({Y0.shape[0]}) needs to be equal to T0 + T1 ({T0 + T1})"
        )
    if inference_method not in ["conformal", "ttest"]:
        raise ValueError(
            f"The selected inference method '{inference_method}' is not available. "
            "Choose 'conformal' or 'ttest'."
        )

    # Conformal inference
    if inference_method == "conformal":
        if estimation_method not in ["did", "sc", "classo"]:
            raise ValueError(
                f"The selected estimation method '{estimation_method}' is not "
                "implemented for conformal inference. Choose 'did', 'sc', or 'classo'."
            )
        if permutation_method not in ["iid", "mb"]:
            raise ValueError(
                f"The selected permutation method '{permutation_method}' is not "
                "available. Choose 'mb' (moving block) or 'iid'."
            )

        # Validate theta0
        theta0 = np.asarray(theta0, dtype=np.float64).flatten()
        if len(theta0) != 1 and len(theta0) != T1:
            raise ValueError(
                f"length of theta0 ({len(theta0)}) should be 1 or T1 ({T1})"
            )

        # Compute p-value
        if permutation_method == "mb":
            p_val = movingblock(
                Y1=Y1,
                Y0=Y0,
                T1=T1,
                T0=T0,
                theta0=theta0,
                estimation_method=estimation_method,
                lsei_type=lsei_type,
            )
        else:
            p_val = iid(
                Y1=Y1,
                Y0=Y0,
                T1=T1,
                T0=T0,
                theta0=theta0,
                estimation_method=estimation_method,
                n_perm=n_perm,
                lsei_type=lsei_type,
            )

        # Compute confidence intervals if requested
        if ci:
            if ci_grid is None:
                raise ValueError(
                    "ci_grid must be specified when ci=True. "
                    "Provide a grid of values for the confidence interval."
                )

            ci_grid = np.asarray(ci_grid, dtype=np.float64)
            obj = confidence_interval(
                Y1=Y1,
                Y0=Y0,
                T1=T1,
                T0=T0,
                estimation_method=estimation_method,
                alpha=alpha,
                ci_grid=ci_grid,
                lsei_type=lsei_type,
            )
            lb = obj["lb"]
            ub = obj["ub"]
        else:
            lb = np.nan
            ub = np.nan

        return {"p_val": p_val, "lb": lb, "ub": ub}

    # T-test
    elif inference_method == "ttest":
        if estimation_method not in ["did", "sc"]:
            raise ValueError(
                f"The selected estimation method '{estimation_method}' is not "
                "implemented for the t-test. Choose 'did' or 'sc'."
            )
        if K <= 1:
            raise ValueError(f"K ({K}) must be strictly greater than 1")

        # Compute ATT and standard error using cross-fitting
        if estimation_method == "did":
            obj = did_cf(Y1, Y0, T1, T0, K)
        else:
            obj = sc_cf(Y1, Y0, T1, T0, K, lsei_type)

        att = obj["tau_hat"]
        se = obj["se_hat"]

        # Compute confidence interval using t-distribution
        t_critical = t_dist.ppf(1 - alpha / 2, df=K - 1)
        lb = att - t_critical * se
        ub = att + t_critical * se

        return {"att": att, "se": se, "lb": lb, "ub": ub}
