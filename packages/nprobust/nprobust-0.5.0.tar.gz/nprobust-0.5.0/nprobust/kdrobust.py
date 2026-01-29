"""
Kernel Density Estimation with Robust Bias-Corrected Inference.

This module implements the kdrobust function for nonparametric kernel density
point estimation and robust bias-corrected inference.
"""

import numpy as np
from scipy import stats
from .npfunctions import kd_K_fun


class KdrobustResult:
    """Result class for kdrobust estimation."""

    def __init__(self, Estimate, opt):
        self.Estimate = Estimate
        self.opt = opt

    def __repr__(self):
        return f"kdrobust Result (n={self.opt['n']}, p={self.opt['p']})"

    def summary(self, alpha=0.05, sep=5):
        """Print summary of results."""
        print("Call: kdrobust\n")
        print(f"Sample size (n)                            =     {self.opt['n']}")
        print(f"Kernel order for point estimation (p)      =     {self.opt['p']}")
        print(f"Kernel function                            =     {self.opt['kernel']}")
        print(f"Bandwidth method                           =     {self.opt['bwselect']}")
        print()

        z = stats.norm.ppf(1 - alpha / 2)
        CI_l = self.Estimate[:, 5] - self.Estimate[:, 7] * z
        CI_r = self.Estimate[:, 5] + self.Estimate[:, 7] * z

        print("=" * 77)
        print(f"{'':14}{'':10}{'':8}{'Point':>10}{'Std.':>10}{'Robust B.C.':^25}")
        print(f"{'eval':>14}{'bw':>10}{'Eff.n':>8}{'Est.':>10}{'Error':>10}"
              f"{f'[ {int((1-alpha)*100)}% C.I. ]':^25}")
        print("=" * 77)

        for j in range(self.Estimate.shape[0]):
            eval_val = self.Estimate[j, 0]
            h_val = self.Estimate[j, 1]
            n_val = int(self.Estimate[j, 3])
            tau_us = self.Estimate[j, 4]
            se_us = self.Estimate[j, 6]

            print(f"{j+1:4}{eval_val:10.3f}{h_val:10.3f}{n_val:8}{tau_us:10.3f}"
                  f"{se_us:10.3f}[{CI_l[j]:7.3f} , {CI_r[j]:7.3f}]")

            if sep > 0 and (j + 1) % sep == 0:
                print("-" * 77)

        print("=" * 77)


def kdrobust(x, eval=None, neval=None, h=None, b=None, rho=1, kernel="epa",
             bwselect=None, bwcheck=21, imsegrid=30, level=95, subset=None):
    """
    Kernel density point estimation with robust bias-corrected inference.

    Parameters
    ----------
    x : array-like
        Data vector.
    eval : array-like or None
        Evaluation points. If None, generated automatically.
    neval : int or None
        Number of evaluation points.
    h : float or array-like or None
        Bandwidth for main estimation.
    b : float or array-like or None
        Bandwidth for bias correction.
    rho : float
        Ratio h/b. Default is 1.
    kernel : str
        Kernel function: 'epa' (Epanechnikov), 'uni' (uniform),
        'gau' (Gaussian). Default is 'epa'.
    bwselect : str or None
        Bandwidth selection method: 'mse-dpi', 'imse-dpi', 'imse-rot',
        'ce-dpi', 'ce-rot'.
    bwcheck : int
        Minimum effective sample size. Default is 21.
    imsegrid : int
        Number of grid points for IMSE bandwidth. Default is 30.
    level : float
        Confidence level. Default is 95.
    subset : array-like or None
        Subset indices.

    Returns
    -------
    KdrobustResult
        Object containing estimation results.
    """
    # Import here to avoid circular import
    from .kdbwselect import kdbwselect

    p = 2
    deriv = 0

    # Convert to numpy array
    x = np.asarray(x).flatten()

    # Apply subset
    if subset is not None:
        subset = np.asarray(subset)
        x = x[subset]

    # Handle missing values
    na_ok = ~np.isnan(x)
    x = x[na_ok]

    x_min = np.min(x)
    x_max = np.max(x)
    N = len(x)

    # Generate evaluation points
    if eval is None:
        if neval is None:
            qseq = np.linspace(0.1, 0.9, 30)
            eval = np.percentile(x, qseq * 100)
        else:
            qseq = np.linspace(0.1, 0.9, neval)
            eval = np.percentile(x, qseq * 100)
    else:
        eval = np.asarray(eval).flatten()
    neval = len(eval)

    # Default bandwidth selection
    if h is None and bwselect is None:
        if neval == 1:
            bwselect = "mse-dpi"
        else:
            bwselect = "imse-dpi"

    # Normalize inputs
    kernel = kernel.lower()
    if bwselect is not None:
        bwselect = bwselect.lower()

    # Validate inputs
    if p < 0 or deriv < 0:
        raise ValueError("p should be positive integer")

    if level > 100 or level <= 0:
        raise ValueError("level should be set between 0 and 100")

    if rho < 0:
        raise ValueError("rho should be greater than 0")

    if h is not None:
        bwselect = "Manual"

    # Kernel type name
    kernel_type = "Gaussian"
    if kernel == "epa":
        kernel_type = "Epanechnikov"
    elif kernel == "uni":
        kernel_type = "Uniform"

    # Bandwidth selection
    if h is not None and rho > 0 and b is None:
        b = h / rho

    if h is None:
        kdbws = kdbwselect(x=x, eval=eval, bwselect=bwselect, bwcheck=bwcheck,
                          imsegrid=imsegrid, kernel=kernel)
        h = kdbws.bws[:, 1]
        b = kdbws.bws[:, 2]
        if rho > 0:
            b = h / rho
        rho_vec = h / b
    else:
        if np.isscalar(h):
            h = np.repeat(h, neval)
            b = np.repeat(b, neval)
        rho_vec = h / b

    # Initialize results
    Estimate = np.zeros((neval, 8))

    for i in range(neval):
        # Adjust bandwidth for minimum observations
        if bwcheck is not None:
            bw_min = np.sort(np.abs(x - eval[i]))[min(bwcheck - 1, N - 1)]
            h[i] = max(h[i], bw_min)
            b[i] = max(b[i], bw_min)
            rho_vec[i] = h[i] / b[i]

        # Compute kernel values
        u = (x - eval[i]) / h[i]
        K_d = kd_K_fun(u, v=p, r=deriv, kernel=kernel)
        L_r = kd_K_fun(rho_vec[i] * u, v=p+2, r=p, kernel=kernel)

        K = K_d['Kx']
        M = K - rho_vec[i]**(1+p) * L_r['Kx'] * L_r['k_v']

        f_us = np.mean(K) / h[i]
        f_bc = np.mean(M) / h[i]
        se_us = np.sqrt((np.mean(K**2) - np.mean(K)**2) / (N * h[i]**2))
        se_rb = np.sqrt((np.mean(M**2) - np.mean(M)**2) / (N * h[i]**2))

        eN = np.sum(M > 0)

        Estimate[i, :] = [eval[i], h[i], b[i], eN, f_us, f_bc, se_us, se_rb]

    opt = {
        'p': p,
        'kernel': kernel_type,
        'n': N,
        'neval': neval,
        'bwselect': bwselect
    }

    return KdrobustResult(Estimate, opt)
