"""
Tests for t-test based inference methods.

These tests verify that the Python t-test methods produce correct results
and match the expected behavior from the R implementation.
"""

import pytest
import numpy as np
from scinference import sc_cf, did_cf


class TestSCCF:
    """Tests for synthetic control with cross-fitting t-test."""

    def test_sc_cf_basic(self, large_t1_data):
        """Test SC cross-fitting on basic data."""
        result = sc_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        assert "t_hat" in result
        assert "tau_hat" in result
        assert "se_hat" in result

        assert isinstance(result["t_hat"], float)
        assert isinstance(result["tau_hat"], float)
        assert isinstance(result["se_hat"], float)

    def test_sc_cf_positive_se(self, large_t1_data):
        """Test that standard error is positive."""
        result = sc_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        assert result["se_hat"] > 0

    def test_sc_cf_different_k(self, large_t1_data):
        """Test SC cross-fitting with different K values."""
        for K in [2, 3, 5]:
            result = sc_cf(
                Y1=large_t1_data["Y1"],
                Y0=large_t1_data["Y0"],
                T1=large_t1_data["T1"],
                T0=large_t1_data["T0"],
                K=K,
            )

            assert result["se_hat"] > 0
            # t_hat should be tau_hat / se_hat
            np.testing.assert_almost_equal(
                result["t_hat"], result["tau_hat"] / result["se_hat"], decimal=10
            )

    def test_sc_cf_t_statistic_formula(self, large_t1_data):
        """Test that t-statistic is correctly computed."""
        result = sc_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        expected_t = result["tau_hat"] / result["se_hat"]
        np.testing.assert_almost_equal(result["t_hat"], expected_t, decimal=10)


class TestDIDCF:
    """Tests for difference-in-differences with cross-fitting t-test."""

    def test_did_cf_basic(self, large_t1_data):
        """Test DID cross-fitting on basic data."""
        result = did_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        assert "t_hat" in result
        assert "tau_hat" in result
        assert "se_hat" in result

    def test_did_cf_positive_se(self, large_t1_data):
        """Test that standard error is positive."""
        result = did_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        assert result["se_hat"] > 0

    def test_did_cf_different_k(self, large_t1_data):
        """Test DID cross-fitting with different K values."""
        for K in [2, 3, 5]:
            result = did_cf(
                Y1=large_t1_data["Y1"],
                Y0=large_t1_data["Y0"],
                T1=large_t1_data["T1"],
                T0=large_t1_data["T0"],
                K=K,
            )

            assert result["se_hat"] > 0

    def test_did_cf_vs_sc_cf(self, large_t1_data):
        """Test that DID and SC cross-fitting give different results."""
        result_did = did_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        result_sc = sc_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        # Results should generally be different
        # (unless data happens to be such that SC weights equal DID weights)
        assert result_did["tau_hat"] != result_sc["tau_hat"] or result_did[
            "se_hat"
        ] != result_sc["se_hat"]


class TestCrossFittingProperties:
    """Tests for properties of cross-fitting methods."""

    def test_r_calculation(self, large_t1_data):
        """Test that r = min(floor(T0/K), T1) is correctly applied."""
        T0 = large_t1_data["T0"]
        T1 = large_t1_data["T1"]
        K = 2

        r = min(int(np.floor(T0 / K)), T1)
        expected_r = min(15, 30)  # T0=30, K=2, T1=30

        assert r == expected_r

    def test_folds_cover_data(self, large_t1_data):
        """Test that cross-fitting folds properly partition the holdout data."""
        T0 = large_t1_data["T0"]
        K = 3
        T1 = large_t1_data["T1"]

        r = min(int(np.floor(T0 / K)), T1)
        base = T0 - (r * K)

        # Collect all holdout indices
        all_holdout = []
        for k in range(K):
            start_idx = base + k * r
            end_idx = base + (k + 1) * r
            Hk = list(range(start_idx, end_idx))
            all_holdout.extend(Hk)

        # No duplicates
        assert len(all_holdout) == len(set(all_holdout))

        # All indices should be valid
        assert all(0 <= idx < T0 for idx in all_holdout)

    def test_consistent_results_same_seed(self, large_t1_data):
        """Test that results are deterministic (no randomness in t-test)."""
        result1 = sc_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        result2 = sc_cf(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            K=2,
        )

        np.testing.assert_almost_equal(result1["tau_hat"], result2["tau_hat"])
        np.testing.assert_almost_equal(result1["se_hat"], result2["se_hat"])


class TestEdgeCases:
    """Edge case tests for t-test methods."""

    def test_minimum_k(self):
        """Test with K=2 (minimum allowed)."""
        np.random.seed(42)
        T0, T1, J = 20, 20, 10
        Y0 = np.random.randn(T0 + T1, J)
        Y1 = Y0.mean(axis=1) + np.random.randn(T0 + T1)

        result = sc_cf(Y1, Y0, T1, T0, K=2)
        assert result["se_hat"] > 0

    def test_large_k(self):
        """Test with larger K value."""
        np.random.seed(42)
        T0, T1, J = 50, 20, 10
        Y0 = np.random.randn(T0 + T1, J)
        Y1 = Y0.mean(axis=1) + np.random.randn(T0 + T1)

        result = sc_cf(Y1, Y0, T1, T0, K=10)
        assert result["se_hat"] > 0

    def test_t1_larger_than_t0_divided_by_k(self):
        """Test when T1 > floor(T0/K), so r = floor(T0/K)."""
        np.random.seed(42)
        T0, T1, J = 20, 50, 10  # T1 > T0
        K = 2
        Y0 = np.random.randn(T0 + T1, J)
        Y1 = Y0.mean(axis=1) + np.random.randn(T0 + T1)

        result = sc_cf(Y1, Y0, T1, T0, K=K)

        # r should be floor(20/2) = 10, not 50
        assert result["se_hat"] > 0
