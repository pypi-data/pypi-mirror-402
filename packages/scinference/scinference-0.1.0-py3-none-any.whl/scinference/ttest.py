"""
T-test based inference methods for synthetic control.

This module implements cross-fitting t-test procedures:
- sc_cf: Synthetic control with cross-fitting
- did_cf: Difference-in-differences with cross-fitting
"""

import numpy as np
from typing import Dict
from .estimators import sc


def sc_cf(
    Y1: np.ndarray,
    Y0: np.ndarray,
    T1: int,
    T0: int,
    K: int,
    lsei_type: int = 1,
) -> Dict[str, float]:
    """
    Synthetic control with cross-fitting t-test.

    Estimates the average treatment effect on the treated (ATT) using
    K-fold cross-fitting with synthetic control weights.

    Parameters
    ----------
    Y1 : array-like
        Treated unit outcomes (T01 x 1 vector)
    Y0 : array-like
        Control units outcomes (T01 x J matrix)
    T1 : int
        Number of post-treatment periods
    T0 : int
        Number of pre-treatment periods
    K : int
        Number of folds for cross-fitting (must be > 1)
    lsei_type : int, optional
        Type parameter for sc method (default=1)

    Returns
    -------
    dict
        Dictionary containing:
        - t_hat: t-statistic (follows t_{K-1} distribution)
        - tau_hat: estimated treatment effect (ATT)
        - se_hat: standard error
    """
    T01 = T0 + T1

    # r = min(floor(T0/K), T1)
    r = min(int(np.floor(T0 / K)), T1)

    # Split data into pre and post treatment periods
    Y1_pre = Y1[:T0]
    Y0_pre = Y0[:T0, :]
    Y1_post = Y1[T0:T01]
    Y0_post = Y0[T0:T01, :]

    tau_mat = np.zeros(K)

    for k in range(K):
        # Holdout indices (Hk)
        # R formula: Hk <- (T0-(r*K)) + seq((k-1)*r+1, k*r, 1)
        # This gives indices from (T0-r*K+(k-1)*r+1) to (T0-r*K+k*r) in 1-indexed R
        # In Python (0-indexed):
        base = T0 - (r * K)
        start_idx = base + k * r
        end_idx = base + (k + 1) * r
        Hk = np.arange(start_idx, end_idx)

        # Training indices (exclude Hk)
        train_idx = np.setdiff1d(np.arange(T0), Hk)

        # Estimate weights on training set
        w_Hk = sc(Y1_pre[train_idx], Y0_pre[train_idx, :], lsei_type)["w_hat"]

        # Compute treatment effect estimate for this fold
        # R: tau.mat[k,1] <- mean(Y1.post - Y0.post %*% w.Hk) -
        #                    mean(Y1.pre[Hk] - Y0.pre[Hk,] %*% w.Hk)
        tau_mat[k] = np.mean(Y1_post - Y0_post @ w_Hk) - np.mean(
            Y1_pre[Hk] - Y0_pre[Hk, :] @ w_Hk
        )

    # Average treatment effect
    tau_hat = np.mean(tau_mat)

    # Standard error with adjustment for cross-fitting
    # R: se.hat <- sqrt(1 + ((K*r)/T1)) * sd(tau.mat) / sqrt(K)
    # Note: R's sd() uses n-1 denominator (ddof=1)
    se_hat = np.sqrt(1 + ((K * r) / T1)) * np.std(tau_mat, ddof=1) / np.sqrt(K)

    # t-statistic (follows t_{K-1} distribution)
    t_hat = tau_hat / se_hat

    return {"t_hat": float(t_hat), "tau_hat": float(tau_hat), "se_hat": float(se_hat)}


def did_cf(
    Y1: np.ndarray,
    Y0: np.ndarray,
    T1: int,
    T0: int,
    K: int,
) -> Dict[str, float]:
    """
    Difference-in-differences with cross-fitting t-test.

    Estimates the average treatment effect on the treated (ATT) using
    K-fold cross-fitting with difference-in-differences.

    Parameters
    ----------
    Y1 : array-like
        Treated unit outcomes (T01 x 1 vector)
    Y0 : array-like
        Control units outcomes (T01 x J matrix)
    T1 : int
        Number of post-treatment periods
    T0 : int
        Number of pre-treatment periods
    K : int
        Number of folds for cross-fitting (must be > 1)

    Returns
    -------
    dict
        Dictionary containing:
        - t_hat: t-statistic (follows t_{K-1} distribution)
        - tau_hat: estimated treatment effect (ATT)
        - se_hat: standard error
    """
    T01 = T0 + T1
    r = min(int(np.floor(T0 / K)), T1)

    # Split data into pre and post treatment periods
    Y1_pre = Y1[:T0]
    Y0_pre = Y0[:T0, :]
    Y1_post = Y1[T0:T01]
    Y0_post = Y0[T0:T01, :]

    tau_mat = np.zeros(K)

    for k in range(K):
        # Holdout indices
        base = T0 - (r * K)
        start_idx = base + k * r
        end_idx = base + (k + 1) * r
        Hk = np.arange(start_idx, end_idx)

        # R: tau.mat[k,1] <- mean(Y1.post - rowMeans(Y0.post)) -
        #                    mean(Y1.pre[Hk] - rowMeans(Y0.pre[Hk,]))
        tau_mat[k] = np.mean(Y1_post - Y0_post.mean(axis=1)) - np.mean(
            Y1_pre[Hk] - Y0_pre[Hk, :].mean(axis=1)
        )

    # Average treatment effect
    tau_hat = np.mean(tau_mat)

    # Standard error with adjustment
    se_hat = np.sqrt(1 + ((K * r) / T1)) * np.std(tau_mat, ddof=1) / np.sqrt(K)

    # t-statistic
    t_hat = tau_hat / se_hat

    return {"t_hat": float(t_hat), "tau_hat": float(tau_hat), "se_hat": float(se_hat)}
