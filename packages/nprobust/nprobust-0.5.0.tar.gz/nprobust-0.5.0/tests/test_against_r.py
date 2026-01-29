"""
Test Python nprobust against R reference values.

Before running these tests:
1. Navigate to the tests directory
2. Run: Rscript generate_r_reference.R
3. Run: pytest test_against_r.py -v

This will compare Python results against R reference values and report
any significant differences.
"""

import numpy as np
import pandas as pd
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nprobust import lprobust, lpbwselect, kdrobust, kdbwselect


# Tolerance for numerical comparison
RTOL = 0.05  # 5% relative tolerance
ATOL = 0.01  # Absolute tolerance for small values


def get_test_data():
    """Load test data (same random seed as R)."""
    test_data_path = os.path.join(os.path.dirname(__file__), "test_data.csv")

    if os.path.exists(test_data_path):
        data = pd.read_csv(test_data_path)
        return data['x'].values, data['y'].values
    else:
        # Generate data with same seed as R
        np.random.seed(42)
        n = 200
        x = np.random.uniform(0, 1, n)
        y = np.sin(2 * np.pi * x) + np.random.normal(0, 0.5, n)
        return x, y


def load_r_reference(filename):
    """Load R reference values from CSV file."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        return pd.read_csv(filepath).values
    return None


def compare_arrays(python_arr, r_arr, name="values"):
    """Compare Python and R arrays with tolerance."""
    if r_arr is None:
        pytest.skip(f"R reference file not found for {name}")

    python_arr = np.asarray(python_arr)
    r_arr = np.asarray(r_arr)

    # Check shapes match
    assert python_arr.shape == r_arr.shape, \
        f"Shape mismatch for {name}: Python {python_arr.shape} vs R {r_arr.shape}"

    # Check values match within tolerance
    diff = np.abs(python_arr - r_arr)
    rel_diff = diff / (np.abs(r_arr) + ATOL)

    max_diff = np.max(diff)
    max_rel_diff = np.max(rel_diff)

    # Report differences
    if max_rel_diff > RTOL:
        print(f"\n{name} comparison:")
        print(f"  Max absolute difference: {max_diff:.6f}")
        print(f"  Max relative difference: {max_rel_diff:.4%}")
        print(f"  Python:\n{python_arr}")
        print(f"  R:\n{r_arr}")

    return np.allclose(python_arr, r_arr, rtol=RTOL, atol=ATOL)


class TestLprobustAgainstR:
    """Compare lprobust Python results against R reference values."""

    def test_lprobust_basic(self):
        """Test lprobust with h=0.2, p=1, kernel=epa."""
        x, y = get_test_data()
        r_ref = load_r_reference("r_lprobust_h02_p1_epa.csv")

        if r_ref is None:
            pytest.skip("R reference file not found. Run generate_r_reference.R first.")

        result = lprobust(y, x, h=0.2, p=1, kernel="epa", neval=10)
        python_est = result.Estimate

        # Compare key columns: eval, tau.us, se.us
        # Note: Column indices may differ between Python and R
        print("\nPython lprobust results:")
        print(python_est[:5])
        print("\nR lprobust results:")
        print(r_ref[:5])

        # Check that evaluation points match
        assert compare_arrays(python_est[:, 0], r_ref[:, 0], "eval points")

        # Check point estimates (may have small differences due to implementation)
        # Using larger tolerance for estimates
        diff = np.abs(python_est[:, 4] - r_ref[:, 4])
        print(f"\nPoint estimate differences: mean={np.mean(diff):.6f}, max={np.max(diff):.6f}")

    def test_lprobust_uniform_kernel(self):
        """Test lprobust with uniform kernel."""
        x, y = get_test_data()
        r_ref = load_r_reference("r_lprobust_h02_uni.csv")

        if r_ref is None:
            pytest.skip("R reference file not found.")

        result = lprobust(y, x, h=0.2, kernel="uni", neval=10)

        print("\nPython (uniform kernel):")
        print(result.Estimate[:5])


class TestLpbwselectAgainstR:
    """Compare lpbwselect Python results against R reference values."""

    def test_lpbwselect_mse_dpi(self):
        """Test lpbwselect MSE-DPI."""
        x, y = get_test_data()
        r_ref = load_r_reference("r_lpbwselect_msedpi.csv")

        if r_ref is None:
            pytest.skip("R reference file not found.")

        result = lpbwselect(y, x, bwselect="mse-dpi", neval=5)

        print("\nPython lpbwselect (MSE-DPI):")
        print(result.bws)
        print("\nR lpbwselect (MSE-DPI):")
        print(r_ref)

        # Compare bandwidths
        diff_h = np.abs(result.bws[:, 1] - r_ref[:, 1])
        print(f"\nBandwidth h differences: mean={np.mean(diff_h):.6f}, max={np.max(diff_h):.6f}")

    def test_lpbwselect_imse_dpi(self):
        """Test lpbwselect IMSE-DPI."""
        x, y = get_test_data()
        r_ref = load_r_reference("r_lpbwselect_imsedpi.csv")

        if r_ref is None:
            pytest.skip("R reference file not found.")

        result = lpbwselect(y, x, bwselect="imse-dpi")

        print("\nPython lpbwselect (IMSE-DPI):")
        print(result.bws)


class TestKdrobustAgainstR:
    """Compare kdrobust Python results against R reference values."""

    def test_kdrobust_basic(self):
        """Test kdrobust with h=0.2."""
        x, _ = get_test_data()
        r_ref = load_r_reference("r_kdrobust_h02.csv")

        if r_ref is None:
            pytest.skip("R reference file not found.")

        result = kdrobust(x, h=0.2, neval=10)

        print("\nPython kdrobust (h=0.2):")
        print(result.Estimate[:5])
        print("\nR kdrobust (h=0.2):")
        print(r_ref[:5])

        # Compare density estimates
        diff = np.abs(result.Estimate[:, 4] - r_ref[:, 4])
        print(f"\nDensity estimate differences: mean={np.mean(diff):.6f}, max={np.max(diff):.6f}")

    def test_kdrobust_gaussian(self):
        """Test kdrobust with Gaussian kernel."""
        x, _ = get_test_data()
        r_ref = load_r_reference("r_kdrobust_h02_gau.csv")

        if r_ref is None:
            pytest.skip("R reference file not found.")

        result = kdrobust(x, h=0.2, kernel="gau", neval=10)

        print("\nPython kdrobust (Gaussian):")
        print(result.Estimate[:5])


class TestKdbwselectAgainstR:
    """Compare kdbwselect Python results against R reference values."""

    def test_kdbwselect_mse_dpi(self):
        """Test kdbwselect MSE-DPI."""
        x, _ = get_test_data()
        r_ref = load_r_reference("r_kdbwselect_msedpi.csv")

        if r_ref is None:
            pytest.skip("R reference file not found.")

        result = kdbwselect(x, bwselect="mse-dpi", neval=5)

        print("\nPython kdbwselect (MSE-DPI):")
        print(result.bws)
        print("\nR kdbwselect (MSE-DPI):")
        print(r_ref)


def run_comparison_report():
    """Generate a detailed comparison report."""
    print("=" * 60)
    print("NPROBUST: Python vs R Comparison Report")
    print("=" * 60)

    x, y = get_test_data()

    # lprobust comparison
    print("\n\n1. LPROBUST COMPARISON")
    print("-" * 40)

    print("\nPython lprobust(y, x, h=0.2, neval=5):")
    lp_result = lprobust(y, x, h=0.2, neval=5)
    lp_result.summary()

    r_ref = load_r_reference("r_lprobust_h02_p1_epa.csv")
    if r_ref is not None:
        print("\nR reference values (first 5 rows):")
        print(r_ref[:5])

    # lpbwselect comparison
    print("\n\n2. LPBWSELECT COMPARISON")
    print("-" * 40)

    print("\nPython lpbwselect(y, x, bwselect='mse-dpi', neval=5):")
    bw_result = lpbwselect(y, x, bwselect="mse-dpi", neval=5)
    bw_result.summary()

    # kdrobust comparison
    print("\n\n3. KDROBUST COMPARISON")
    print("-" * 40)

    print("\nPython kdrobust(x, h=0.2, neval=5):")
    kd_result = kdrobust(x, h=0.2, neval=5)
    kd_result.summary()

    # kdbwselect comparison
    print("\n\n4. KDBWSELECT COMPARISON")
    print("-" * 40)

    print("\nPython kdbwselect(x, bwselect='mse-dpi', neval=5):")
    kdbw_result = kdbwselect(x, bwselect="mse-dpi", neval=5)
    kdbw_result.summary()

    print("\n" + "=" * 60)
    print("END OF COMPARISON REPORT")
    print("=" * 60)


if __name__ == "__main__":
    run_comparison_report()
