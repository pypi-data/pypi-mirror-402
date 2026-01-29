# nprobust

Python implementation of the R package `nprobust`: Nonparametric Robust Estimation and Inference Methods using Local Polynomial Regression and Kernel Density Estimation.

## Description

This package provides tools for data-driven statistical analysis using local polynomial regression and kernel density estimation methods as described in:

- Calonico, Cattaneo and Farrell (2018): "On the Effect of Bias Estimation on Coverage Accuracy in Nonparametric Inference", *Journal of the American Statistical Association*.
- Calonico, Cattaneo and Farrell (2019): "nprobust: Nonparametric Kernel-Based Estimation and Robust Bias-Corrected Inference", *Journal of Statistical Software*.

## Installation

```bash
pip install nprobust .
```

Or with plotting support:


## Main Functions

- **lprobust**: Local polynomial point estimation and robust bias-corrected inference
- **lpbwselect**: Bandwidth selection for local polynomial regression
- **kdrobust**: Kernel density point estimation and robust bias-corrected inference
- **kdbwselect**: Bandwidth selection for kernel density estimation
- **nprobust_plot**: Plotting function for estimation results

## Basic Usage

```python
import numpy as np
from nprobust import lprobust, lpbwselect, kdrobust, kdbwselect, nprobust_plot

# Generate sample data
np.random.seed(42)
n = 500
x = np.random.uniform(0, 1, n)
y = np.sin(2 * np.pi * x) + np.random.normal(0, 0.5, n)

# Local polynomial regression
result = lprobust(y, x)
result.summary()

# Bandwidth selection
bw = lpbwselect(y, x, bwselect="mse-dpi")
bw.summary()

# Kernel density estimation
kd_result = kdrobust(x)
kd_result.summary()

# Plotting
fig = nprobust_plot(result, title="Local Polynomial Regression")
```

## Parameters

### lprobust

- `y`: Response variable
- `x`: Independent variable
- `eval`: Evaluation points (default: 30 equally spaced points)
- `p`: Polynomial order (default: 1)
- `deriv`: Order of derivative (default: 0)
- `h`: Bandwidth (default: data-driven selection)
- `kernel`: Kernel function ('epa', 'uni', 'tri', 'gau')
- `bwselect`: Bandwidth selection method ('mse-dpi', 'imse-dpi', etc.)
- `vce`: Variance estimator ('nn', 'hc0', 'hc1', 'hc2', 'hc3')

### kdrobust

- `x`: Data vector
- `eval`: Evaluation points
- `h`: Bandwidth
- `kernel`: Kernel function ('epa', 'uni', 'gau')
- `bwselect`: Bandwidth selection method

## References

- Calonico, S., M. D. Cattaneo, and M. H. Farrell (2018). "On the Effect of Bias Estimation on Coverage Accuracy in Nonparametric Inference." *Journal of the American Statistical Association* 113(522): 767-779.
- Calonico, S., M. D. Cattaneo, and M. H. Farrell (2019). "nprobust: Nonparametric Kernel-Based Estimation and Robust Bias-Corrected Inference." *Journal of Statistical Software* 91(8): 1-33.

## License

GPL-2

## Original R Package

https://github.com/nppackages/nprobust
