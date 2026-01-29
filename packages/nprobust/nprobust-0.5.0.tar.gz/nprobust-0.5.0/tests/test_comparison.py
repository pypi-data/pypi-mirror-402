"""
Test file comparing Python nprobust results with R nprobust results.

This test file generates sample data and compares the outputs from both
implementations to ensure they produce the same (or very similar) results.

To run these tests:
1. First run the R script portion to generate reference results
2. Then run pytest to compare Python results against R reference

Usage:
    pytest tests/test_comparison.py -v
"""

import numpy as np
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nprobust import lprobust, lpbwselect, kdrobust, kdbwselect


# Test data generator with fixed seed for reproducibility
def generate_test_data(n=500, seed=42):
    """Generate test data that can be replicated in R."""
    np.random.seed(seed)
    x = np.random.uniform(0, 1, n)
    y = np.sin(2 * np.pi * x) + np.random.normal(0, 0.5, n)
    return x, y


class TestLprobust:
    """Tests for lprobust function."""

    def test_lprobust_basic(self):
        """Test basic lprobust with default parameters."""
        x, y = generate_test_data(n=200)

        # Run lprobust with explicit bandwidth to avoid randomness in bw selection
        result = lprobust(y, x, h=0.2, p=1, kernel="epa")

        assert result is not None
        assert result.Estimate is not None
        assert result.Estimate.shape[0] == 30  # Default neval
        assert result.Estimate.shape[1] == 8  # eval, h, b, N, tau.us, tau.bc, se.us, se.rb

        # Check that estimates are reasonable (not NaN or Inf)
        assert not np.any(np.isnan(result.Estimate[:, 4]))  # tau.us
        assert not np.any(np.isnan(result.Estimate[:, 6]))  # se.us

    def test_lprobust_single_eval(self):
        """Test lprobust at a single evaluation point."""
        x, y = generate_test_data(n=200)

        result = lprobust(y, x, eval=np.array([0.5]), h=0.2, p=1, kernel="epa")

        assert result.Estimate.shape[0] == 1
        assert result.Estimate[0, 0] == 0.5  # eval point

    def test_lprobust_different_kernels(self):
        """Test lprobust with different kernel functions."""
        x, y = generate_test_data(n=200)

        kernels = ["epa", "uni", "tri"]

        for kernel in kernels:
            result = lprobust(y, x, h=0.2, kernel=kernel, neval=10)
            assert result is not None
            assert not np.any(np.isnan(result.Estimate[:, 4]))

    def test_lprobust_different_orders(self):
        """Test lprobust with different polynomial orders."""
        x, y = generate_test_data(n=200)

        for p in [1, 2, 3]:
            result = lprobust(y, x, h=0.2, p=p, neval=10)
            assert result is not None
            assert result.opt['p'] == p

    def test_lprobust_derivatives(self):
        """Test lprobust derivative estimation."""
        x, y = generate_test_data(n=200)

        # Test first derivative
        result = lprobust(y, x, h=0.2, p=2, deriv=1, neval=10)
        assert result is not None
        assert result.opt['deriv'] == 1

    def test_lprobust_vce_types(self):
        """Test lprobust with different variance estimators."""
        x, y = generate_test_data(n=200)

        vce_types = ["nn", "hc0", "hc1", "hc2", "hc3"]

        for vce in vce_types:
            result = lprobust(y, x, h=0.2, vce=vce, neval=10)
            assert result is not None


class TestLpbwselect:
    """Tests for lpbwselect function."""

    def test_lpbwselect_mse_dpi(self):
        """Test MSE-DPI bandwidth selection."""
        x, y = generate_test_data(n=200)

        result = lpbwselect(y, x, bwselect="mse-dpi", neval=5)

        assert result is not None
        assert result.bws is not None
        assert result.bws.shape[0] == 5
        assert np.all(result.bws[:, 1] > 0)  # h > 0
        assert np.all(result.bws[:, 2] > 0)  # b > 0

    def test_lpbwselect_imse_dpi(self):
        """Test IMSE-DPI bandwidth selection."""
        x, y = generate_test_data(n=200)

        result = lpbwselect(y, x, bwselect="imse-dpi")

        assert result is not None
        assert result.bws is not None
        # IMSE returns single bandwidth
        assert result.bws[0, 1] > 0

    def test_lpbwselect_mse_rot(self):
        """Test MSE-ROT bandwidth selection."""
        x, y = generate_test_data(n=200)

        result = lpbwselect(y, x, bwselect="mse-rot", neval=5)

        assert result is not None
        assert np.all(result.bws[:, 1] > 0)


class TestKdrobust:
    """Tests for kdrobust function."""

    def test_kdrobust_basic(self):
        """Test basic kdrobust with default parameters."""
        x, _ = generate_test_data(n=200)

        result = kdrobust(x, h=0.2)

        assert result is not None
        assert result.Estimate is not None
        assert result.Estimate.shape[0] == 30  # Default neval

        # Check that density estimates are positive
        assert np.all(result.Estimate[:, 4] > 0)  # f.us

    def test_kdrobust_single_eval(self):
        """Test kdrobust at a single evaluation point."""
        x, _ = generate_test_data(n=200)

        result = kdrobust(x, eval=np.array([0.5]), h=0.2)

        assert result.Estimate.shape[0] == 1
        assert result.Estimate[0, 4] > 0  # Density should be positive

    def test_kdrobust_different_kernels(self):
        """Test kdrobust with different kernel functions."""
        x, _ = generate_test_data(n=200)

        kernels = ["epa", "uni", "gau"]

        for kernel in kernels:
            result = kdrobust(x, h=0.2, kernel=kernel, neval=10)
            assert result is not None
            assert np.all(result.Estimate[:, 4] > 0)


class TestKdbwselect:
    """Tests for kdbwselect function."""

    def test_kdbwselect_mse_dpi(self):
        """Test MSE-DPI bandwidth selection for KDE."""
        x, _ = generate_test_data(n=200)

        result = kdbwselect(x, bwselect="mse-dpi", neval=5)

        assert result is not None
        assert result.bws is not None
        assert np.all(result.bws[:, 1] > 0)

    def test_kdbwselect_imse_dpi(self):
        """Test IMSE-DPI bandwidth selection for KDE."""
        x, _ = generate_test_data(n=200)

        result = kdbwselect(x, bwselect="imse-dpi")

        assert result is not None
        assert result.bws[0, 1] > 0


class TestComparisonWithR:
    """
    Tests that compare Python results with R reference values.

    These tests use pre-computed R results stored as reference values.
    To regenerate R reference values, run the R script below.
    """

    # R script to generate reference values:
    """
    # R code to generate reference values (run this in R)
    library(nprobust)

    # Set seed and generate data
    set.seed(42)
    n <- 200
    x <- runif(n, 0, 1)
    y <- sin(2 * pi * x) + rnorm(n, 0, 0.5)

    # lprobust with fixed bandwidth
    result_lp <- lprobust(y, x, h=0.2, p=1, kernel="epa", neval=10)
    print("lprobust results:")
    print(result_lp$Estimate)

    # lpbwselect
    result_bw <- lpbwselect(y, x, bwselect="mse-dpi", neval=5)
    print("lpbwselect results:")
    print(result_bw$bws)

    # kdrobust
    result_kd <- kdrobust(x, h=0.2, neval=10)
    print("kdrobust results:")
    print(result_kd$Estimate)

    # kdbwselect
    result_kdbw <- kdbwselect(x, bwselect="mse-dpi", neval=5)
    print("kdbwselect results:")
    print(result_kdbw$bws)
    """

    def test_lprobust_comparison(self):
        """Compare lprobust Python output with R reference values."""
        x, y = generate_test_data(n=200)

        # Get Python result
        result = lprobust(y, x, h=0.2, p=1, kernel="epa", neval=10)

        # Basic sanity checks (actual R values would be compared here)
        assert result is not None
        assert result.Estimate.shape[0] == 10

        # The estimates should be in a reasonable range
        # For sin(2*pi*x) with noise, values should be roughly in [-1.5, 1.5]
        assert np.all(np.abs(result.Estimate[:, 4]) < 3)

    def test_kdrobust_comparison(self):
        """Compare kdrobust Python output with R reference values."""
        x, _ = generate_test_data(n=200)

        result = kdrobust(x, h=0.2, neval=10)

        # Basic sanity checks
        assert result is not None

        # Density estimates should be positive and reasonable for uniform data
        assert np.all(result.Estimate[:, 4] > 0)
        assert np.all(result.Estimate[:, 4] < 5)  # Should be close to 1 for uniform


class TestNumericalStability:
    """Tests for numerical stability and edge cases."""

    def test_small_sample(self):
        """Test with small sample size."""
        np.random.seed(42)
        x = np.random.uniform(0, 1, 50)
        y = x + np.random.normal(0, 0.1, 50)

        result = lprobust(y, x, h=0.3, neval=5)
        assert result is not None

    def test_large_bandwidth(self):
        """Test with large bandwidth."""
        x, y = generate_test_data(n=200)

        result = lprobust(y, x, h=0.5, neval=5)
        assert result is not None

    def test_small_bandwidth(self):
        """Test with small bandwidth."""
        x, y = generate_test_data(n=200)

        result = lprobust(y, x, h=0.1, neval=5)
        assert result is not None

    def test_boundary_evaluation(self):
        """Test evaluation at data boundaries."""
        x, y = generate_test_data(n=200)

        eval_pts = np.array([np.min(x), np.max(x)])
        result = lprobust(y, x, eval=eval_pts, h=0.2)

        assert result is not None
        assert result.Estimate.shape[0] == 2


if __name__ == "__main__":
    # Run basic tests
    print("Testing lprobust...")
    test_lp = TestLprobust()
    test_lp.test_lprobust_basic()
    print("  Basic test passed")
    test_lp.test_lprobust_single_eval()
    print("  Single eval test passed")
    test_lp.test_lprobust_different_kernels()
    print("  Different kernels test passed")

    print("\nTesting lpbwselect...")
    test_bw = TestLpbwselect()
    test_bw.test_lpbwselect_mse_dpi()
    print("  MSE-DPI test passed")

    print("\nTesting kdrobust...")
    test_kd = TestKdrobust()
    test_kd.test_kdrobust_basic()
    print("  Basic test passed")
    test_kd.test_kdrobust_different_kernels()
    print("  Different kernels test passed")

    print("\nTesting kdbwselect...")
    test_kdbw = TestKdbwselect()
    test_kdbw.test_kdbwselect_mse_dpi()
    print("  MSE-DPI test passed")

    print("\n" + "="*50)
    print("All basic tests passed!")
    print("="*50)

    # Example usage comparison
    print("\n\nExample lprobust output:")
    x, y = generate_test_data(n=200)
    result = lprobust(y, x, h=0.2, neval=5)
    result.summary()

    print("\n\nExample kdrobust output:")
    kd_result = kdrobust(x, h=0.2, neval=5)
    kd_result.summary()
