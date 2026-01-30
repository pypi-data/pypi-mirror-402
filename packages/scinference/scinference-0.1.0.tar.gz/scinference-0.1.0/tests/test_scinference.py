"""
Integration tests for the main scinference function.

These tests verify that the Python implementation produces results that
match the R package output.
"""

import pytest
import numpy as np
from scinference import scinference


class TestScinferenceConformal:
    """Tests for conformal inference through the main function."""

    def test_conformal_basic(self, simple_data):
        """Test basic conformal inference."""
        result = scinference(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            inference_method="conformal",
            theta0=0,
        )

        assert "p_val" in result
        assert "lb" in result
        assert "ub" in result
        assert 0 <= result["p_val"] <= 1

    def test_conformal_with_ci(self, simple_data):
        """Test conformal inference with confidence intervals."""
        result = scinference(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            inference_method="conformal",
            ci=True,
            ci_grid=np.arange(-2, 8, 0.2),
        )

        assert isinstance(result["lb"], np.ndarray)
        assert isinstance(result["ub"], np.ndarray)
        assert len(result["lb"]) == simple_data["T1"]

    def test_conformal_iid_permutation(self, simple_data):
        """Test conformal inference with IID permutations."""
        np.random.seed(42)
        result = scinference(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            inference_method="conformal",
            permutation_method="iid",
            n_perm=500,
            theta0=2,
        )

        assert 0 <= result["p_val"] <= 1


class TestScinferenceTtest:
    """Tests for t-test inference through the main function."""

    def test_ttest_basic(self, large_t1_data):
        """Test basic t-test inference."""
        result = scinference(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            inference_method="ttest",
            K=2,
        )

        assert "att" in result
        assert "se" in result
        assert "lb" in result
        assert "ub" in result
        assert result["se"] > 0
        assert result["lb"] < result["ub"]

    def test_ttest_did_method(self, large_t1_data):
        """Test t-test with DID estimation method."""
        result = scinference(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            inference_method="ttest",
            estimation_method="did",
            K=2,
        )

        assert result["se"] > 0

    def test_ttest_confidence_interval(self, large_t1_data):
        """Test that t-test CI is correctly computed."""
        from scipy.stats import t as t_dist

        alpha = 0.1
        K = 2
        result = scinference(
            Y1=large_t1_data["Y1"],
            Y0=large_t1_data["Y0"],
            T1=large_t1_data["T1"],
            T0=large_t1_data["T0"],
            inference_method="ttest",
            alpha=alpha,
            K=K,
        )

        # Verify CI formula
        t_critical = t_dist.ppf(1 - alpha / 2, df=K - 1)
        expected_lb = result["att"] - t_critical * result["se"]
        expected_ub = result["att"] + t_critical * result["se"]

        np.testing.assert_almost_equal(result["lb"], expected_lb, decimal=10)
        np.testing.assert_almost_equal(result["ub"], expected_ub, decimal=10)


class TestRComparison:
    """Tests comparing Python results to R package output."""

    def test_conformal_matches_r(self, conformal_test_data):
        """Test that conformal inference matches R results."""
        result = scinference(
            Y1=conformal_test_data["Y1"],
            Y0=conformal_test_data["Y0"],
            T1=conformal_test_data["T1"],
            T0=conformal_test_data["T0"],
            theta0=4,
            estimation_method="sc",
            permutation_method="mb",
        )

        # R result: p_val = 0.01818182
        # Allow some tolerance for numerical differences
        expected_p_val = 0.01818182
        np.testing.assert_almost_equal(result["p_val"], expected_p_val, decimal=6)

    def test_conformal_ci_matches_r(self, conformal_test_data):
        """Test that conformal confidence intervals match R results."""
        result = scinference(
            Y1=conformal_test_data["Y1"],
            Y0=conformal_test_data["Y0"],
            T1=conformal_test_data["T1"],
            T0=conformal_test_data["T0"],
            estimation_method="sc",
            ci=True,
            ci_grid=np.arange(-2, 8.1, 0.1),
        )

        # R results:
        # LB: [0.8, 1.5, 0.4, 1.8, -0.5]
        # UB: [4.1, 4.6, 4.0, 5.2, 2.6]
        expected_lb = np.array([0.8, 1.5, 0.4, 1.8, -0.5])
        expected_ub = np.array([4.1, 4.6, 4.0, 5.2, 2.6])

        np.testing.assert_array_almost_equal(
            np.round(result["lb"], 1), expected_lb, decimal=1
        )
        np.testing.assert_array_almost_equal(
            np.round(result["ub"], 1), expected_ub, decimal=1
        )

    def test_ttest_matches_r(self, ttest_test_data):
        """Test that t-test results match R results."""
        result = scinference(
            Y1=ttest_test_data["Y1"],
            Y0=ttest_test_data["Y0"],
            T1=ttest_test_data["T1"],
            T0=ttest_test_data["T0"],
            inference_method="ttest",
            K=2,
        )

        # R results:
        # ATT: 1.488715
        # SE: 0.2922196
        # LB: -0.356287
        # UB: 3.333716
        np.testing.assert_almost_equal(result["att"], 1.488715, decimal=5)
        np.testing.assert_almost_equal(result["se"], 0.2922196, decimal=5)
        np.testing.assert_almost_equal(result["lb"], -0.356287, decimal=4)
        np.testing.assert_almost_equal(result["ub"], 3.333716, decimal=4)


class TestInputValidation:
    """Tests for input validation."""

    def test_invalid_y1_length(self, simple_data):
        """Test error when Y1 length doesn't match T0+T1."""
        with pytest.raises(ValueError, match="length of Y1"):
            scinference(
                Y1=simple_data["Y1"][:10],  # Wrong length
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
            )

    def test_invalid_y0_rows(self, simple_data):
        """Test error when Y0 rows don't match T0+T1."""
        with pytest.raises(ValueError, match="number of rows in Y0"):
            scinference(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"][:10, :],  # Wrong number of rows
                T1=simple_data["T1"],
                T0=simple_data["T0"],
            )

    def test_invalid_inference_method(self, simple_data):
        """Test error for invalid inference method."""
        with pytest.raises(ValueError, match="inference method"):
            scinference(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                inference_method="invalid",
            )

    def test_invalid_estimation_method_conformal(self, simple_data):
        """Test error for invalid estimation method in conformal."""
        with pytest.raises(ValueError, match="estimation method"):
            scinference(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                inference_method="conformal",
                estimation_method="invalid",
            )

    def test_invalid_estimation_method_ttest(self, large_t1_data):
        """Test error for classo in t-test (not supported)."""
        with pytest.raises(ValueError, match="estimation method"):
            scinference(
                Y1=large_t1_data["Y1"],
                Y0=large_t1_data["Y0"],
                T1=large_t1_data["T1"],
                T0=large_t1_data["T0"],
                inference_method="ttest",
                estimation_method="classo",
            )

    def test_invalid_permutation_method(self, simple_data):
        """Test error for invalid permutation method."""
        with pytest.raises(ValueError, match="permutation method"):
            scinference(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                inference_method="conformal",
                permutation_method="invalid",
            )

    def test_invalid_theta0_length(self, simple_data):
        """Test error when theta0 has wrong length."""
        with pytest.raises(ValueError, match="theta0"):
            scinference(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                theta0=np.array([1, 2, 3]),  # Wrong length (not 1 or T1)
            )

    def test_ci_without_grid(self, simple_data):
        """Test error when ci=True but no grid provided."""
        with pytest.raises(ValueError, match="ci_grid"):
            scinference(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                ci=True,
                ci_grid=None,
            )

    def test_invalid_k(self, large_t1_data):
        """Test error when K <= 1."""
        with pytest.raises(ValueError, match="K"):
            scinference(
                Y1=large_t1_data["Y1"],
                Y0=large_t1_data["Y0"],
                T1=large_t1_data["T1"],
                T0=large_t1_data["T0"],
                inference_method="ttest",
                K=1,
            )


class TestDefaultParameters:
    """Tests for default parameter values."""

    def test_default_inference_method(self, simple_data):
        """Test that default inference method is conformal."""
        result = scinference(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
        )

        # Conformal returns p_val
        assert "p_val" in result

    def test_default_estimation_method(self, simple_data):
        """Test that default estimation method is sc."""
        # This should work without specifying estimation_method
        result = scinference(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
        )

        assert "p_val" in result

    def test_default_permutation_method(self, simple_data):
        """Test that default permutation method is mb (moving block)."""
        result = scinference(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
        )

        # Should produce consistent results with mb
        assert "p_val" in result
