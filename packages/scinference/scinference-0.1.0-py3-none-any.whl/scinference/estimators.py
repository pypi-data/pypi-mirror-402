"""
Estimators for synthetic control methods.

This module implements three estimation methods:
- did: Difference-in-differences
- sc: Synthetic control (Abadie et al.)
- classo: Constrained lasso
"""

import numpy as np
import cvxpy as cp
from typing import Dict


def did(Y1: np.ndarray, Y0: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Difference-in-differences estimator.

    Computes residuals as:
        u_hat = Y1 - mean(Y1 - rowMeans(Y0)) - rowMeans(Y0)

    Parameters
    ----------
    Y1 : array-like
        Treated unit outcomes (T x 1 vector)
    Y0 : array-like
        Control units outcomes (T x J matrix)

    Returns
    -------
    dict
        Dictionary containing:
        - u_hat: residuals (T x 1 vector)
    """
    Y1 = np.asarray(Y1, dtype=np.float64).flatten()
    Y0 = np.asarray(Y0, dtype=np.float64)

    Y0_row_means = Y0.mean(axis=1)
    u_hat = Y1 - np.mean(Y1 - Y0_row_means) - Y0_row_means

    return {"u_hat": u_hat}


def sc(Y1: np.ndarray, Y0: np.ndarray, lsei_type: int = 1) -> Dict[str, np.ndarray]:
    """
    Synthetic control estimator.

    Solves the constrained least squares problem:
        min ||Y0 @ w - Y1||^2
        subject to: sum(w) = 1, w >= 0

    This is equivalent to R's limSolve::lsei function.

    Parameters
    ----------
    Y1 : array-like
        Treated unit outcomes (T x 1 vector)
    Y0 : array-like
        Control units outcomes (T x J matrix)
    lsei_type : int, optional
        Type parameter (kept for R compatibility, default=1)

    Returns
    -------
    dict
        Dictionary containing:
        - u_hat: residuals (T x 1 vector)
        - w_hat: weights (J x 1 vector)
    """
    Y1 = np.asarray(Y1, dtype=np.float64).flatten()
    Y0 = np.asarray(Y0, dtype=np.float64)

    J = Y0.shape[1]

    # Solve constrained least squares with cvxpy
    # min ||Y0 @ w - Y1||^2  s.t. sum(w) = 1, w >= 0
    w = cp.Variable(J)
    objective = cp.Minimize(cp.sum_squares(Y0 @ w - Y1))
    constraints = [cp.sum(w) == 1, w >= 0]

    problem = cp.Problem(objective, constraints)

    # Try OSQP first (fast quadratic solver)
    try:
        problem.solve(solver=cp.OSQP, verbose=False)
    except Exception:
        pass

    if w.value is None:
        # Fallback to ECOS if OSQP fails
        try:
            problem.solve(solver=cp.ECOS, verbose=False)
        except Exception:
            pass

    if w.value is None:
        # Final fallback to SCS
        problem.solve(solver=cp.SCS, verbose=False)

    w_hat = w.value
    u_hat = Y1 - Y0 @ w_hat

    return {"u_hat": u_hat, "w_hat": w_hat}


def classo(Y1: np.ndarray, Y0: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Constrained lasso estimator.

    Solves the optimization problem:
        min (1/T) * ||Y1 - [1, Y0] @ w||^2
        subject to: sum(|w[1:]|) <= 1

    This is equivalent to R's CVXR implementation.

    Parameters
    ----------
    Y1 : array-like
        Treated unit outcomes (T x 1 vector)
    Y0 : array-like
        Control units outcomes (T x J matrix)

    Returns
    -------
    dict
        Dictionary containing:
        - u_hat: residuals (T x 1 vector)
        - w_hat: weights ((J+1) x 1 vector, including intercept)
    """
    Y1 = np.asarray(Y1, dtype=np.float64).flatten()
    Y0 = np.asarray(Y0, dtype=np.float64)

    T, J = Y0.shape

    # Add intercept column: X = [1, Y0]
    X = np.column_stack([np.ones(T), Y0])

    # min (1/T) * ||Y1 - X @ w||^2  s.t. sum(|w[1:]|) <= 1
    w = cp.Variable(J + 1)
    objective = cp.Minimize(cp.sum_squares(Y1 - X @ w) / T)
    constraints = [cp.norm1(w[1:]) <= 1]

    problem = cp.Problem(objective, constraints)

    # Try OSQP first
    try:
        problem.solve(solver=cp.OSQP, verbose=False)
    except Exception:
        pass

    if w.value is None:
        # Fallback to ECOS
        try:
            problem.solve(solver=cp.ECOS, verbose=False)
        except Exception:
            pass

    if w.value is None:
        # Final fallback to SCS
        problem.solve(solver=cp.SCS, verbose=False)

    w_hat = w.value
    u_hat = Y1 - X @ w_hat

    return {"u_hat": u_hat, "w_hat": w_hat}
