"""
Tests for estimator functions.

These tests verify that the Python estimators produce correct results
and match the expected behavior from the R implementation.
"""

import pytest
import numpy as np
from scinference import did, sc, classo


class TestDID:
    """Tests for the difference-in-differences estimator."""

    def test_did_basic(self, simple_data):
        """Test DID on basic synthetic data."""
        Y0 = simple_data["Y0"]
        Y1 = simple_data["Y1"]

        result = did(Y1, Y0)

        assert "u_hat" in result
        assert len(result["u_hat"]) == len(Y1)

    def test_did_residuals_mean(self, simple_data):
        """Test that DID residuals have approximately zero mean under no treatment."""
        np.random.seed(999)
        J, T = 50, 55
        Y0 = np.random.randn(T, J)
        # No treatment effect
        Y1 = Y0.mean(axis=1) + np.random.randn(T) * 0.1

        result = did(Y1, Y0)

        # Residuals should have mean close to zero
        assert np.abs(np.mean(result["u_hat"])) < 0.5

    def test_did_output_type(self, simple_data):
        """Test DID output types."""
        result = did(simple_data["Y1"], simple_data["Y0"])

        assert isinstance(result, dict)
        assert isinstance(result["u_hat"], np.ndarray)
        assert result["u_hat"].dtype == np.float64


class TestSC:
    """Tests for the synthetic control estimator."""

    def test_sc_basic(self, simple_data):
        """Test SC on basic synthetic data."""
        Y0 = simple_data["Y0"]
        Y1 = simple_data["Y1"]

        result = sc(Y1, Y0)

        assert "u_hat" in result
        assert "w_hat" in result
        assert len(result["u_hat"]) == len(Y1)
        assert len(result["w_hat"]) == Y0.shape[1]

    def test_sc_weights_sum_to_one(self, simple_data):
        """Test that SC weights sum to 1."""
        result = sc(simple_data["Y1"], simple_data["Y0"])

        np.testing.assert_almost_equal(np.sum(result["w_hat"]), 1.0, decimal=5)

    def test_sc_weights_nonnegative(self, simple_data):
        """Test that SC weights are non-negative."""
        result = sc(simple_data["Y1"], simple_data["Y0"])

        # Allow small numerical tolerance
        assert np.all(result["w_hat"] >= -1e-6)

    def test_sc_perfect_fit(self):
        """Test SC when treated is exactly a weighted average of controls."""
        np.random.seed(123)
        J, T = 10, 20
        Y0 = np.random.randn(T, J)

        # Create perfect synthetic control
        true_w = np.array([0.3, 0.3, 0.4] + [0] * (J - 3))
        Y1 = Y0 @ true_w

        result = sc(Y1, Y0)

        # Residuals should be nearly zero
        np.testing.assert_array_almost_equal(result["u_hat"], np.zeros(T), decimal=4)

    def test_sc_lsei_type_parameter(self, simple_data):
        """Test that lsei_type parameter is accepted."""
        # Should not raise an error
        result = sc(simple_data["Y1"], simple_data["Y0"], lsei_type=1)
        assert "w_hat" in result


class TestCLasso:
    """Tests for the constrained lasso estimator."""

    def test_classo_basic(self, simple_data):
        """Test CLasso on basic synthetic data."""
        Y0 = simple_data["Y0"]
        Y1 = simple_data["Y1"]

        result = classo(Y1, Y0)

        assert "u_hat" in result
        assert "w_hat" in result
        assert len(result["u_hat"]) == len(Y1)
        # w_hat includes intercept, so length is J+1
        assert len(result["w_hat"]) == Y0.shape[1] + 1

    def test_classo_l1_constraint(self, simple_data):
        """Test that CLasso satisfies the L1 constraint."""
        result = classo(simple_data["Y1"], simple_data["Y0"])

        # L1 norm of coefficients (excluding intercept) should be <= 1
        l1_norm = np.sum(np.abs(result["w_hat"][1:]))
        assert l1_norm <= 1.0 + 1e-5

    def test_classo_with_intercept(self):
        """Test CLasso includes an intercept."""
        np.random.seed(456)
        J, T = 10, 30
        Y0 = np.random.randn(T, J)
        Y1 = 5.0 + Y0[:, 0] * 0.5  # Clear intercept of 5

        result = classo(Y1, Y0)

        # Intercept (first element) should be substantial
        assert np.abs(result["w_hat"][0]) > 1.0


class TestEstimatorsEdgeCases:
    """Edge case tests for all estimators."""

    def test_single_control_unit(self):
        """Test estimators with a single control unit."""
        np.random.seed(789)
        T = 20
        Y0 = np.random.randn(T, 1)
        Y1 = Y0.flatten() + np.random.randn(T) * 0.1

        # DID should work
        result_did = did(Y1, Y0)
        assert len(result_did["u_hat"]) == T

        # SC with single unit should give weight of 1
        result_sc = sc(Y1, Y0)
        np.testing.assert_almost_equal(result_sc["w_hat"][0], 1.0, decimal=4)

    def test_list_input(self, simple_data):
        """Test that estimators accept list inputs."""
        Y1_list = simple_data["Y1"].tolist()
        Y0_list = simple_data["Y0"].tolist()

        # Should not raise errors
        did(Y1_list, Y0_list)
        sc(Y1_list, Y0_list)
        classo(Y1_list, Y0_list)

    def test_2d_Y1_input(self, simple_data):
        """Test that Y1 is properly flattened if 2D."""
        Y1_2d = simple_data["Y1"].reshape(-1, 1)

        result = did(Y1_2d, simple_data["Y0"])
        assert result["u_hat"].ndim == 1
