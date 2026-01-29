"""
Bandwidth Selection for Kernel Density Estimation.

This module implements the kdbwselect function for data-driven bandwidth
selection for kernel density estimation.
"""

import numpy as np
from scipy import stats
from .npfunctions import kd_K_fun, kd_bw_fun, kd_cer_fun


class KdbwselectResult:
    """Result class for kdbwselect bandwidth selection."""

    def __init__(self, bws, bws_imse, opt):
        self.bws = bws
        self.bws_imse = bws_imse
        self.opt = opt

    def __repr__(self):
        return f"kdbwselect Result (n={self.opt['n']}, bwselect={self.opt['bwselect']})"

    def summary(self, sep=5):
        """Print summary of bandwidth selection results."""
        print("Call: kdbwselect\n")
        print(f"Sample size (n)                             =    {self.opt['n']}")
        print(f"Kernel function                             =    {self.opt['kernel']}")
        print(f"Bandwidth selection method                  =    {self.opt['bwselect']}")
        print()

        if self.opt['bwselect'] in ["imse-dpi", "imse-rot"]:
            print("=" * 23)
            print(f"{'h':>8}{'b':>8}")
            print("=" * 23)
            print(f"{self.bws[0, 1]:8.3f}{self.bws[0, 2]:8.3f}")
            print("=" * 23)
        else:
            ncols = self.bws.shape[1]
            print("=" * (15 + 8 * ncols))
            print(f"{'eval':>10}{'h':>8}{'b':>8}")
            print("=" * (15 + 8 * ncols))

            for j in range(self.bws.shape[0]):
                print(f"{j+1:4}{self.bws[j, 0]:8.3f}{self.bws[j, 1]:8.3f}{self.bws[j, 2]:8.3f}")
                if sep > 0 and (j + 1) % sep == 0:
                    print("-" * (15 + 8 * ncols))

            print("=" * (15 + 8 * ncols))


def kdbwselect(x, eval=None, neval=None, kernel="epa", bwselect="mse-dpi",
               bwcheck=21, imsegrid=30, subset=None):
    """
    Bandwidth selection for kernel density estimation.

    Parameters
    ----------
    x : array-like
        Data vector.
    eval : array-like or None
        Evaluation points.
    neval : int or None
        Number of evaluation points.
    kernel : str
        Kernel function: 'epa', 'uni', 'gau'. Default is 'epa'.
    bwselect : str
        Bandwidth selection method. Default is 'mse-dpi'.
    bwcheck : int
        Minimum effective sample size. Default is 21.
    imsegrid : int
        IMSE grid points. Default is 30.
    subset : array-like or None
        Subset indices.

    Returns
    -------
    KdbwselectResult
        Object containing bandwidth selection results.
    """
    p = 2
    deriv = 0

    # Normalize inputs
    kernel = kernel.lower()
    bwselect = bwselect.lower()

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

    # Kernel type name and constants
    kernel_type = "Gaussian"
    C_h = 1.06
    C_b = 1
    if kernel == "epa":
        kernel_type = "Epanechnikov"
        C_h = 2.34
        C_b = 3.49
    elif kernel == "uni":
        kernel_type = "Uniform"
        C_h = 1.06
        C_b = 1

    # Initialize bandwidth matrix
    bws = np.zeros((neval, 3))  # eval, h, b
    bws_imse = None

    # IMSE-ROT bandwidths
    h_imse_rot = np.std(x, ddof=1) * C_h * N**(-1 / (1 + 2*p))
    b_imse_rot = np.std(x, ddof=1) * C_b * N**(-1 / (1 + 2*(p+2) + 2*p))

    if bwselect == "imse-rot":
        bws[:, 0] = eval
        bws[:, 1] = h_imse_rot
        bws[:, 2] = b_imse_rot

    # IMSE-DPI
    if bwselect == "imse-dpi":
        B_h = np.zeros(imsegrid)
        V_h = np.zeros(imsegrid)

        qseq_imse = np.linspace(0.1, 0.9, imsegrid)
        eval_imse = np.percentile(x, qseq_imse * 100)

        for i in range(imsegrid):
            K_b = kd_K_fun((x - eval_imse[i]) / b_imse_rot, v=p+2, r=p, kernel=kernel)
            K_h = kd_K_fun((x - eval_imse[i]) / h_imse_rot, v=p, r=deriv, kernel=kernel)
            f_b = np.mean(K_b['Kx']) / b_imse_rot**(1+p)
            f_h_rot = np.mean(K_h['Kx']) / h_imse_rot
            B_h[i] = f_b * K_h['k_v']
            V_h[i] = f_h_rot * K_h['R_v']

        h_imse_dpi = kd_bw_fun(np.mean(V_h), np.mean(B_h), N, v=p, r=deriv)

        bws[:, 0] = eval
        bws[:, 1] = h_imse_dpi
        bws[:, 2] = b_imse_rot

    # MSE-DPI and coverage error methods
    if bwselect in ["mse-dpi", "ce-dpi", "ce-rot"]:
        B_h = np.zeros(neval)
        V_h = np.zeros(neval)

        for i in range(neval):
            bw_min = 0
            if bwcheck is not None:
                bw_min = np.sort(np.abs(x - eval[i]))[min(bwcheck - 1, N - 1)]

            K_b = kd_K_fun((x - eval[i]) / b_imse_rot, v=p+2, r=p, kernel=kernel)
            K_h = kd_K_fun((x - eval[i]) / h_imse_rot, v=p, r=deriv, kernel=kernel)
            f_b = np.mean(K_b['Kx']) / b_imse_rot**(1+p)
            f_h_rot = np.mean(K_h['Kx']) / h_imse_rot
            B_h[i] = f_b * K_h['k_v']
            V_h[i] = f_h_rot * K_h['R_v']

            h_mse_dpi = kd_bw_fun(V_h[i], B_h[i], N, v=p, r=deriv)
            b_mse_dpi = b_imse_rot

            if bwcheck is not None:
                h_mse_dpi = max(h_mse_dpi, bw_min)
                b_mse_dpi = max(b_mse_dpi, bw_min)

            bws[i, 0] = eval[i]
            bws[i, 1] = h_mse_dpi
            bws[i, 2] = b_mse_dpi

            # Coverage error adjustments
            if bwselect == "ce-rot":
                h_ce_rot = h_mse_dpi * N**(-((p-2) / ((1+2*p) * (1+p+2))))
                b_ce_rot = b_mse_dpi * N**(-((p-2) / ((1+2*p) * (1+p+2))))

                if bwcheck is not None:
                    h_ce_rot = max(h_ce_rot, bw_min)
                    b_ce_rot = max(b_ce_rot, bw_min)

                bws[i, 1] = h_ce_rot
                bws[i, 2] = b_ce_rot

            elif bwselect == "ce-dpi":
                try:
                    h_ce_dpi = kd_cer_fun(x, eval[i], h_mse_dpi, h_mse_dpi, p, kernel)
                except:
                    h_ce_dpi = h_mse_dpi * N**(-((p-2) / ((1+2*p) * (1+p+2))))
                b_ce_dpi = b_mse_dpi

                if bwcheck is not None:
                    h_ce_dpi = max(h_ce_dpi, bw_min)
                    b_ce_dpi = max(b_ce_dpi, bw_min)

                bws[i, 1] = h_ce_dpi
                bws[i, 2] = b_ce_dpi

    opt = {
        'p': p,
        'n': N,
        'neval': neval,
        'kernel': kernel_type,
        'bwselect': bwselect
    }

    return KdbwselectResult(bws, bws_imse, opt)
