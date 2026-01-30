"""
Conformal inference methods for synthetic control.

This module implements:
- movingblock: Moving block permutation test
- iid: IID permutation test
- confidence_interval: Pointwise confidence intervals via test inversion
"""

import numpy as np
from typing import Dict, Union
from .estimators import did, sc, classo


def movingblock(
    Y1: np.ndarray,
    Y0: np.ndarray,
    T1: int,
    T0: int,
    theta0: Union[float, np.ndarray],
    estimation_method: str,
    lsei_type: int = 1,
) -> float:
    """
    Moving block permutation test for conformal inference.

    Computes a p-value for testing the null hypothesis that the treatment
    effect equals theta0 using moving block permutations.

    Parameters
    ----------
    Y1 : array-like
        Treated unit outcomes (T x 1 vector)
    Y0 : array-like
        Control units outcomes (T x J matrix)
    T1 : int
        Number of post-treatment periods
    T0 : int
        Number of pre-treatment periods
    theta0 : float or array-like
        Null hypothesis for treatment effect (scalar or T1-length vector)
    estimation_method : str
        Estimation method: "did", "sc", or "classo"
    lsei_type : int, optional
        Type parameter for sc method (default=1)

    Returns
    -------
    float
        p-value for the null hypothesis test
    """
    T01 = T0 + T1

    # Handle theta0 (scalar or vector)
    theta0 = np.asarray(theta0, dtype=np.float64).flatten()
    if len(theta0) == 1:
        theta0 = np.repeat(theta0, T1)

    # Adjust Y1 under the null: Y1_0 = Y1 - theta0 in post-treatment
    Y1_0 = Y1.copy()
    Y1_0[T0:T01] = Y1[T0:T01] - theta0

    # Get residuals using the specified estimation method
    if estimation_method == "classo":
        u_hat = classo(Y1_0, Y0)["u_hat"]
    elif estimation_method == "sc":
        u_hat = sc(Y1_0, Y0, lsei_type)["u_hat"]
    elif estimation_method == "did":
        u_hat = did(Y1_0, Y0)["u_hat"]
    else:
        raise ValueError(f"Unknown estimation method: {estimation_method}")

    # Moving block test statistic
    # Create circular sequence by concatenating u_hat with itself
    sub_size = T1
    u_hat_c = np.concatenate([u_hat, u_hat])

    # Compute test statistic for each block position
    S_vec = np.zeros(T01)
    for s in range(T01):
        S_vec[s] = np.sum(np.abs(u_hat_c[s : s + sub_size]))

    # p-value: proportion of blocks with test statistic >= observed
    # The observed test statistic is at position T0 (0-indexed)
    p = np.mean(S_vec >= S_vec[T0])

    return float(p)


def iid(
    Y1: np.ndarray,
    Y0: np.ndarray,
    T1: int,
    T0: int,
    theta0: Union[float, np.ndarray],
    estimation_method: str,
    n_perm: int,
    lsei_type: int = 1,
) -> float:
    """
    IID permutation test for conformal inference.

    Computes a p-value for testing the null hypothesis that the treatment
    effect equals theta0 using random IID permutations.

    Parameters
    ----------
    Y1 : array-like
        Treated unit outcomes (T x 1 vector)
    Y0 : array-like
        Control units outcomes (T x J matrix)
    T1 : int
        Number of post-treatment periods
    T0 : int
        Number of pre-treatment periods
    theta0 : float or array-like
        Null hypothesis for treatment effect (scalar or T1-length vector)
    estimation_method : str
        Estimation method: "did", "sc", or "classo"
    n_perm : int
        Number of random permutations
    lsei_type : int, optional
        Type parameter for sc method (default=1)

    Returns
    -------
    float
        p-value for the null hypothesis test
    """
    T01 = T0 + T1

    # Handle theta0 (scalar or vector)
    theta0 = np.asarray(theta0, dtype=np.float64).flatten()
    if len(theta0) == 1:
        theta0 = np.repeat(theta0, T1)

    # Adjust Y1 under the null
    Y1_0 = Y1.copy()
    Y1_0[T0:T01] = Y1[T0:T01] - theta0

    # Get residuals using the specified estimation method
    if estimation_method == "classo":
        u_hat = classo(Y1_0, Y0)["u_hat"]
    elif estimation_method == "sc":
        u_hat = sc(Y1_0, Y0, lsei_type)["u_hat"]
    elif estimation_method == "did":
        u_hat = did(Y1_0, Y0)["u_hat"]
    else:
        raise ValueError(f"Unknown estimation method: {estimation_method}")

    # Post-treatment indices (0-indexed)
    post_ind = np.arange(T0, T01)

    # Observed test statistic
    Sq = np.sum(np.abs(u_hat[post_ind]))

    # Permutation distribution
    S_vec = np.zeros(n_perm)
    for r in range(n_perm):
        u_hat_p = np.random.permutation(u_hat)
        S_vec[r] = np.sum(np.abs(u_hat_p[post_ind]))

    # p-value with continuity correction
    p = (1 + np.sum(S_vec >= Sq)) / (n_perm + 1)

    return float(p)


def confidence_interval(
    Y1: np.ndarray,
    Y0: np.ndarray,
    T1: int,
    T0: int,
    estimation_method: str,
    alpha: float,
    ci_grid: np.ndarray,
    lsei_type: int = 1,
) -> Dict[str, np.ndarray]:
    """
    Pointwise confidence intervals via test inversion.

    Computes pointwise (1-alpha) confidence intervals for each post-treatment
    period by inverting a conformal test.

    Parameters
    ----------
    Y1 : array-like
        Treated unit outcomes (T x 1 vector)
    Y0 : array-like
        Control units outcomes (T x J matrix)
    T1 : int
        Number of post-treatment periods
    T0 : int
        Number of pre-treatment periods
    estimation_method : str
        Estimation method: "did", "sc", or "classo"
    alpha : float
        Significance level (e.g., 0.1 for 90% CI)
    ci_grid : array-like
        Grid of values to test for inclusion in the CI
    lsei_type : int, optional
        Type parameter for sc method (default=1)

    Returns
    -------
    dict
        Dictionary containing:
        - lb: lower bounds (T1 x 1 vector)
        - ub: upper bounds (T1 x 1 vector)
    """
    ci_grid = np.asarray(ci_grid, dtype=np.float64)
    lb = np.full(T1, np.nan)
    ub = np.full(T1, np.nan)

    for t in range(T1):
        # Extract pre-treatment data and single post-treatment period
        # R: indices <- c(1:T0, T0+t) with 1-indexing
        # Python: indices 0 to T0-1 and T0+t with 0-indexing
        indices = list(range(T0)) + [T0 + t]
        Y1_temp = Y1[indices]
        Y0_temp = Y0[indices, :]

        ps_temp = np.zeros(len(ci_grid))

        for ind, theta in enumerate(ci_grid):
            # Adjust the post-treatment observation
            Y1_0_temp = Y1_temp.copy()
            Y1_0_temp[T0] = Y1_temp[T0] - theta

            # Get residuals
            if estimation_method == "classo":
                u_hat = classo(Y1_0_temp, Y0_temp)["u_hat"]
            elif estimation_method == "sc":
                u_hat = sc(Y1_0_temp, Y0_temp, lsei_type)["u_hat"]
            elif estimation_method == "did":
                u_hat = did(Y1_0_temp, Y0_temp)["u_hat"]
            else:
                raise ValueError(f"Unknown estimation method: {estimation_method}")

            # p-value: proportion of residuals with |u| >= |u[T0]|
            ps_temp[ind] = np.mean(np.abs(u_hat) >= np.abs(u_hat[T0]))

        # Include grid values where p-value > alpha
        ci_temp = ci_grid[ps_temp > alpha]
        if len(ci_temp) > 0:
            lb[t] = np.min(ci_temp)
            ub[t] = np.max(ci_temp)

    return {"lb": lb, "ub": ub}
