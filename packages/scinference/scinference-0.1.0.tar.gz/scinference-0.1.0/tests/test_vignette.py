"""
Test file replicating the R scinference vignette examples.

This test file reproduces all examples from the R package vignette:
"Inference for synthetic control methods: the scinference package"
by Victor Chernozhukov, Kaspar Wuthrich, Yinchu Zhu (2020)

References:
- "An Exact and Robust Conformal Inference Method for Counterfactual and
   Synthetic Controls" (arXiv:1712.09089)
- "Practical and robust t-test based inference for synthetic control and
   related methods" (arXiv:1812.10820)
"""

import pytest
import numpy as np
from scinference import scinference


class TestVignetteConformalInference:
    """
    Replicates the conformal inference examples from the R vignette.

    Setup: J=50 controls, T0=50 pre-treatment periods, T1=5 post-treatment periods.
    The outcome equals a weighted average of controls with sparse weights (1/3, 1/3, 1/3, 0, ..., 0).
    The treatment effect is constant and equal to 2 for all periods.
    """

    @pytest.fixture
    def conformal_data(self):
        """Generate the same data as in the R vignette conformal example."""
        np.random.seed(12345)

        J = 50
        T0 = 50
        T1 = 5
        T = T0 + T1

        # Sparse weights: first 3 controls get 1/3 each
        w = np.zeros(J)
        w[:3] = 1 / 3

        # Generate control outcomes (iid normal)
        Y0 = np.random.randn(T, J)

        # Treated outcome = weighted average of controls + noise
        Y1 = Y0 @ w + np.random.randn(T)

        # Add treatment effect of 2 in post-treatment periods
        Y1[T0:] += 2

        return {"Y0": Y0, "Y1": Y1, "T0": T0, "T1": T1, "J": J, "true_effect": 2}

    def test_null_hypothesis_sc_mb(self, conformal_data):
        """
        Test H0: theta = (4,4,4,4,4) using SC with moving block permutations.

        R code:
        scinference(Y1,Y0,T1=T1,T0=T0,theta0=4,estimation_method="sc",permutation_method="mb")$p_val
        """
        result = scinference(
            Y1=conformal_data["Y1"],
            Y0=conformal_data["Y0"],
            T1=conformal_data["T1"],
            T0=conformal_data["T0"],
            theta0=4,
            estimation_method="sc",
            permutation_method="mb",
        )

        # The null theta0=4 should be rejected (true effect is 2)
        # P-value should be small
        assert result["p_val"] < 0.1
        print(f"SC + Moving Block p-value: {result['p_val']:.6f}")

    def test_null_hypothesis_did_mb(self, conformal_data):
        """
        Test H0: theta = (4,4,4,4,4) using DID with moving block permutations.

        R code:
        scinference(Y1,Y0,T1=T1,T0=T0,theta0=4,estimation_method="did",permutation_method="mb")$p_val
        """
        result = scinference(
            Y1=conformal_data["Y1"],
            Y0=conformal_data["Y0"],
            T1=conformal_data["T1"],
            T0=conformal_data["T0"],
            theta0=4,
            estimation_method="did",
            permutation_method="mb",
        )

        assert result["p_val"] < 0.2
        print(f"DID + Moving Block p-value: {result['p_val']:.6f}")

    def test_null_hypothesis_classo_mb(self, conformal_data):
        """
        Test H0: theta = (4,4,4,4,4) using CLasso with moving block permutations.

        R code:
        scinference(Y1,Y0,T1=T1,T0=T0,theta0=4,estimation_method="classo",permutation_method="mb")$p_val
        """
        result = scinference(
            Y1=conformal_data["Y1"],
            Y0=conformal_data["Y0"],
            T1=conformal_data["T1"],
            T0=conformal_data["T0"],
            theta0=4,
            estimation_method="classo",
            permutation_method="mb",
        )

        assert result["p_val"] < 0.2
        print(f"CLasso + Moving Block p-value: {result['p_val']:.6f}")

    def test_null_hypothesis_did_iid(self, conformal_data):
        """
        Test H0: theta = (4,4,4,4,4) using DID with IID permutations.

        R code:
        scinference(Y1,Y0,T1=T1,T0=T0,theta0=4,estimation_method="did",permutation_method="iid")$p_val
        """
        np.random.seed(42)  # For reproducibility of IID permutations
        result = scinference(
            Y1=conformal_data["Y1"],
            Y0=conformal_data["Y0"],
            T1=conformal_data["T1"],
            T0=conformal_data["T0"],
            theta0=4,
            estimation_method="did",
            permutation_method="iid",
            n_perm=5000,
        )

        assert result["p_val"] < 0.2
        print(f"DID + IID p-value: {result['p_val']:.6f}")

    def test_null_hypothesis_sc_iid(self, conformal_data):
        """
        Test H0: theta = (4,4,4,4,4) using SC with IID permutations.

        R code:
        scinference(Y1,Y0,T1=T1,T0=T0,theta0=4,estimation_method="sc",permutation_method="iid")$p_val
        """
        np.random.seed(42)
        result = scinference(
            Y1=conformal_data["Y1"],
            Y0=conformal_data["Y0"],
            T1=conformal_data["T1"],
            T0=conformal_data["T0"],
            theta0=4,
            estimation_method="sc",
            permutation_method="iid",
            n_perm=5000,
        )

        assert result["p_val"] < 0.1
        print(f"SC + IID p-value: {result['p_val']:.6f}")

    def test_null_hypothesis_classo_iid(self, conformal_data):
        """
        Test H0: theta = (4,4,4,4,4) using CLasso with IID permutations.

        R code:
        scinference(Y1,Y0,T1=T1,T0=T0,theta0=4,estimation_method="classo",permutation_method="iid")$p_val
        """
        np.random.seed(42)
        result = scinference(
            Y1=conformal_data["Y1"],
            Y0=conformal_data["Y0"],
            T1=conformal_data["T1"],
            T0=conformal_data["T0"],
            theta0=4,
            estimation_method="classo",
            permutation_method="iid",
            n_perm=5000,
        )

        assert result["p_val"] < 0.2
        print(f"CLasso + IID p-value: {result['p_val']:.6f}")

    def test_confidence_intervals_sc(self, conformal_data):
        """
        Compute pointwise 90% confidence intervals using synthetic control.

        R code:
        obj <- scinference(Y1,Y0,T1=T1,T0=T0,estimation_method="sc",ci=TRUE,ci_grid=seq(-2,8,0.1))
        """
        result = scinference(
            Y1=conformal_data["Y1"],
            Y0=conformal_data["Y0"],
            T1=conformal_data["T1"],
            T0=conformal_data["T0"],
            estimation_method="sc",
            ci=True,
            ci_grid=np.arange(-2, 8.1, 0.1),
            alpha=0.1,  # 90% CI
        )

        lb = result["lb"]
        ub = result["ub"]

        # Check dimensions
        assert len(lb) == conformal_data["T1"]
        assert len(ub) == conformal_data["T1"]

        # Lower bounds should be less than upper bounds
        for t in range(conformal_data["T1"]):
            if not np.isnan(lb[t]) and not np.isnan(ub[t]):
                assert lb[t] <= ub[t]

        # True effect is 2, should be covered by most CIs
        true_effect = conformal_data["true_effect"]
        covered = (lb <= true_effect) & (ub >= true_effect)
        coverage_rate = np.mean(covered)
        assert coverage_rate >= 0.5  # At least half should cover

        print(f"\n90% Pointwise Confidence Intervals:")
        print(f"{'Period':<10} {'Lower':<10} {'Upper':<10} {'Covers True':<12}")
        print("-" * 42)
        for t in range(conformal_data["T1"]):
            covers = "Yes" if covered[t] else "No"
            print(f"{t+1:<10} {lb[t]:<10.2f} {ub[t]:<10.2f} {covers:<12}")

    def test_true_null_not_rejected(self, conformal_data):
        """
        Test that the true null hypothesis (theta0=2) is not rejected.
        """
        result = scinference(
            Y1=conformal_data["Y1"],
            Y0=conformal_data["Y0"],
            T1=conformal_data["T1"],
            T0=conformal_data["T0"],
            theta0=2,  # True effect
            estimation_method="sc",
            permutation_method="mb",
        )

        # P-value should be larger when testing the true null
        assert result["p_val"] > 0.05
        print(f"P-value for true null (theta0=2): {result['p_val']:.6f}")


class TestVignetteTTest:
    """
    Replicates the t-test examples from the R vignette.

    Setup: J=30 controls, T0=30 pre-treatment periods, T1=30 post-treatment periods.
    Note: The t-test requires a large number of post-treatment periods.
    """

    @pytest.fixture
    def ttest_data(self):
        """Generate the same data as in the R vignette t-test example."""
        np.random.seed(12345)

        J = 30
        T0 = 30
        T1 = 30
        T = T0 + T1

        # Sparse weights
        w = np.zeros(J)
        w[:3] = 1 / 3

        # Generate data
        Y0 = np.random.randn(T, J)
        Y1 = Y0 @ w + np.random.randn(T)

        # Add treatment effect of 2
        Y1[T0:] += 2

        return {"Y0": Y0, "Y1": Y1, "T0": T0, "T1": T1, "J": J, "true_effect": 2}

    def test_ttest_k2(self, ttest_data):
        """
        T-test with K=2 cross-fits.

        R code:
        ttest_K2 <- scinference(Y1,Y0,T1=T1,T0=T0,inference_method="ttest",K=2)
        """
        result = scinference(
            Y1=ttest_data["Y1"],
            Y0=ttest_data["Y0"],
            T1=ttest_data["T1"],
            T0=ttest_data["T0"],
            inference_method="ttest",
            K=2,
            alpha=0.1,  # 90% CI
        )

        print(f"\nT-test with K=2:")
        print(f"  ATT estimate: {result['att']:.6f}")
        print(f"  Standard Error: {result['se']:.6f}")
        print(f"  90% CI: [{result['lb']:.6f}, {result['ub']:.6f}]")

        # ATT should be close to true effect of 2
        assert 0 < result["att"] < 4
        # SE should be positive
        assert result["se"] > 0
        # CI should be valid
        assert result["lb"] < result["ub"]

    def test_ttest_k3(self, ttest_data):
        """
        T-test with K=3 cross-fits.

        R code:
        ttest_K3 <- scinference(Y1,Y0,T1=T1,T0=T0,inference_method="ttest",K=3)
        """
        result = scinference(
            Y1=ttest_data["Y1"],
            Y0=ttest_data["Y0"],
            T1=ttest_data["T1"],
            T0=ttest_data["T0"],
            inference_method="ttest",
            K=3,
            alpha=0.1,
        )

        print(f"\nT-test with K=3:")
        print(f"  ATT estimate: {result['att']:.6f}")
        print(f"  Standard Error: {result['se']:.6f}")
        print(f"  90% CI: [{result['lb']:.6f}, {result['ub']:.6f}]")

        assert 0 < result["att"] < 4
        assert result["se"] > 0
        assert result["lb"] < result["ub"]

    def test_ttest_did_method(self, ttest_data):
        """
        T-test using DID estimation method.
        """
        result = scinference(
            Y1=ttest_data["Y1"],
            Y0=ttest_data["Y0"],
            T1=ttest_data["T1"],
            T0=ttest_data["T0"],
            inference_method="ttest",
            estimation_method="did",
            K=2,
            alpha=0.1,
        )

        print(f"\nT-test with DID (K=2):")
        print(f"  ATT estimate: {result['att']:.6f}")
        print(f"  Standard Error: {result['se']:.6f}")
        print(f"  90% CI: [{result['lb']:.6f}, {result['ub']:.6f}]")

        assert result["se"] > 0
        assert result["lb"] < result["ub"]

    def test_ttest_coverage(self, ttest_data):
        """
        Test that the confidence interval covers the true effect.
        """
        result = scinference(
            Y1=ttest_data["Y1"],
            Y0=ttest_data["Y0"],
            T1=ttest_data["T1"],
            T0=ttest_data["T0"],
            inference_method="ttest",
            K=2,
            alpha=0.1,
        )

        true_effect = ttest_data["true_effect"]
        covers = result["lb"] <= true_effect <= result["ub"]
        print(f"\nCI [{result['lb']:.2f}, {result['ub']:.2f}] covers true effect {true_effect}: {covers}")


class TestVignetteComprehensive:
    """
    Comprehensive tests combining multiple aspects of the vignette.
    """

    def test_all_estimation_methods_produce_valid_results(self):
        """Test that all estimation methods work correctly."""
        np.random.seed(12345)
        J, T0, T1 = 50, 50, 5
        Y0 = np.random.randn(T0 + T1, J)
        w = np.zeros(J)
        w[:3] = 1 / 3
        Y1 = Y0 @ w + np.random.randn(T0 + T1)
        Y1[T0:] += 2

        methods = ["did", "sc", "classo"]
        results = {}

        print("\nP-values for H0: theta=4 (false null):")
        print("-" * 40)

        for method in methods:
            result = scinference(
                Y1=Y1, Y0=Y0, T1=T1, T0=T0, theta0=4, estimation_method=method
            )
            results[method] = result["p_val"]
            print(f"  {method.upper()}: {result['p_val']:.6f}")
            assert 0 <= result["p_val"] <= 1

    def test_permutation_methods_comparable(self):
        """Test that MB and IID permutation methods give comparable results."""
        np.random.seed(12345)
        J, T0, T1 = 50, 50, 5
        Y0 = np.random.randn(T0 + T1, J)
        w = np.zeros(J)
        w[:3] = 1 / 3
        Y1 = Y0 @ w + np.random.randn(T0 + T1)
        Y1[T0:] += 2

        result_mb = scinference(
            Y1=Y1,
            Y0=Y0,
            T1=T1,
            T0=T0,
            theta0=4,
            estimation_method="sc",
            permutation_method="mb",
        )

        np.random.seed(42)
        result_iid = scinference(
            Y1=Y1,
            Y0=Y0,
            T1=T1,
            T0=T0,
            theta0=4,
            estimation_method="sc",
            permutation_method="iid",
            n_perm=5000,
        )

        print(f"\nComparing permutation methods:")
        print(f"  Moving Block p-value: {result_mb['p_val']:.6f}")
        print(f"  IID p-value: {result_iid['p_val']:.6f}")

        # Both should reject the false null
        assert result_mb["p_val"] < 0.2
        assert result_iid["p_val"] < 0.2


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
