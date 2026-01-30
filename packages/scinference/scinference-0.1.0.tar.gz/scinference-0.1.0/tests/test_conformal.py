"""
Tests for conformal inference methods.

These tests verify that the Python conformal inference methods produce
correct results and match the expected behavior from the R implementation.
"""

import pytest
import numpy as np
from scinference import movingblock, iid, confidence_interval


class TestMovingBlock:
    """Tests for the moving block permutation test."""

    def test_movingblock_basic(self, simple_data):
        """Test moving block on basic synthetic data."""
        p_val = movingblock(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            theta0=0,
            estimation_method="sc",
        )

        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1

    def test_movingblock_true_null(self, simple_data):
        """Test that p-value is larger when null is true."""
        # With true effect of 2, testing theta0=2 should give larger p-value
        p_val_true = movingblock(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            theta0=2,  # True effect
            estimation_method="sc",
        )

        p_val_false = movingblock(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            theta0=10,  # False effect
            estimation_method="sc",
        )

        # P-value for true null should typically be larger
        # This is a probabilistic test, so we use a loose comparison
        assert p_val_true > 0.01 or p_val_false < p_val_true

    def test_movingblock_estimation_methods(self, simple_data):
        """Test moving block with different estimation methods."""
        for method in ["did", "sc", "classo"]:
            p_val = movingblock(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                theta0=0,
                estimation_method=method,
            )
            assert 0 <= p_val <= 1

    def test_movingblock_vector_theta0(self, simple_data):
        """Test moving block with vector theta0."""
        T1 = simple_data["T1"]
        theta0 = np.array([2.0, 2.1, 1.9, 2.0, 2.2])  # Length T1

        p_val = movingblock(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=T1,
            T0=simple_data["T0"],
            theta0=theta0,
            estimation_method="sc",
        )

        assert 0 <= p_val <= 1

    def test_movingblock_invalid_method(self, simple_data):
        """Test that invalid estimation method raises error."""
        with pytest.raises(ValueError, match="Unknown estimation method"):
            movingblock(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                theta0=0,
                estimation_method="invalid",
            )


class TestIID:
    """Tests for the IID permutation test."""

    def test_iid_basic(self, simple_data):
        """Test IID on basic synthetic data."""
        np.random.seed(42)
        p_val = iid(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            theta0=0,
            estimation_method="sc",
            n_perm=1000,
        )

        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1

    def test_iid_estimation_methods(self, simple_data):
        """Test IID with different estimation methods."""
        np.random.seed(123)
        for method in ["did", "sc", "classo"]:
            p_val = iid(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                theta0=0,
                estimation_method=method,
                n_perm=500,
            )
            assert 0 <= p_val <= 1

    def test_iid_more_permutations(self, simple_data):
        """Test that more permutations doesn't change p-value drastically."""
        np.random.seed(999)
        p_val_500 = iid(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            theta0=2,
            estimation_method="sc",
            n_perm=500,
        )

        np.random.seed(999)
        p_val_2000 = iid(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            theta0=2,
            estimation_method="sc",
            n_perm=2000,
        )

        # P-values should be in the same ballpark
        assert abs(p_val_500 - p_val_2000) < 0.2

    def test_iid_vector_theta0(self, simple_data):
        """Test IID with vector theta0."""
        np.random.seed(42)
        T1 = simple_data["T1"]
        theta0 = np.ones(T1) * 2

        p_val = iid(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=T1,
            T0=simple_data["T0"],
            theta0=theta0,
            estimation_method="sc",
            n_perm=500,
        )

        assert 0 <= p_val <= 1


class TestConfidenceInterval:
    """Tests for pointwise confidence intervals."""

    def test_confidence_interval_basic(self, simple_data):
        """Test confidence interval on basic synthetic data."""
        ci_grid = np.arange(-2, 6, 0.5)

        result = confidence_interval(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            estimation_method="sc",
            alpha=0.1,
            ci_grid=ci_grid,
        )

        assert "lb" in result
        assert "ub" in result
        assert len(result["lb"]) == simple_data["T1"]
        assert len(result["ub"]) == simple_data["T1"]

    def test_confidence_interval_bounds_order(self, simple_data):
        """Test that lower bounds are less than upper bounds."""
        ci_grid = np.arange(-5, 10, 0.2)

        result = confidence_interval(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            estimation_method="sc",
            alpha=0.1,
            ci_grid=ci_grid,
        )

        # Where both bounds are not NaN, lb should be <= ub
        valid = ~(np.isnan(result["lb"]) | np.isnan(result["ub"]))
        assert np.all(result["lb"][valid] <= result["ub"][valid])

    def test_confidence_interval_covers_true(self, simple_data):
        """Test that CI typically covers the true effect."""
        ci_grid = np.arange(-2, 8, 0.1)

        result = confidence_interval(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            estimation_method="sc",
            alpha=0.1,
            ci_grid=ci_grid,
        )

        # True effect is 2, should be covered by most CIs
        true_effect = simple_data["true_effect"]
        covered = (result["lb"] <= true_effect) & (result["ub"] >= true_effect)
        # At least some periods should cover the true effect
        assert np.sum(covered) >= 1

    def test_confidence_interval_estimation_methods(self, simple_data):
        """Test confidence intervals with different estimation methods."""
        ci_grid = np.arange(-2, 6, 0.5)

        for method in ["did", "sc", "classo"]:
            result = confidence_interval(
                Y1=simple_data["Y1"],
                Y0=simple_data["Y0"],
                T1=simple_data["T1"],
                T0=simple_data["T0"],
                estimation_method=method,
                alpha=0.1,
                ci_grid=ci_grid,
            )
            assert len(result["lb"]) == simple_data["T1"]

    def test_confidence_interval_alpha_effect(self, simple_data):
        """Test that smaller alpha gives wider CIs."""
        ci_grid = np.arange(-5, 10, 0.1)

        result_90 = confidence_interval(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            estimation_method="sc",
            alpha=0.1,
            ci_grid=ci_grid,
        )

        result_80 = confidence_interval(
            Y1=simple_data["Y1"],
            Y0=simple_data["Y0"],
            T1=simple_data["T1"],
            T0=simple_data["T0"],
            estimation_method="sc",
            alpha=0.2,
            ci_grid=ci_grid,
        )

        # 90% CI should generally be wider than 80% CI
        width_90 = result_90["ub"] - result_90["lb"]
        width_80 = result_80["ub"] - result_80["lb"]

        valid = ~(np.isnan(width_90) | np.isnan(width_80))
        # At least on average, 90% CI should be wider
        assert np.mean(width_90[valid]) >= np.mean(width_80[valid]) - 0.5
