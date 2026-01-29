"""
Local Polynomial Regression Estimation with Robust Bias-Corrected Inference.

This module implements the lprobust function for nonparametric local polynomial
point estimation and robust bias-corrected inference.
"""

import numpy as np
from scipy import stats
from math import factorial
from .npfunctions import W_fun, qrXXinv, lprobust_res, lprobust_vce


class LprobustResult:
    """Result class for lprobust estimation."""

    def __init__(self, Estimate, opt, cov_us=None, cov_rb=None):
        self.Estimate = Estimate
        self.opt = opt
        self.cov_us = cov_us
        self.cov_rb = cov_rb

    def __repr__(self):
        return f"lprobust Result (n={self.opt['n']}, p={self.opt['p']}, deriv={self.opt['deriv']})"

    def summary(self, alpha=0.05, sep=5):
        """Print summary of results."""
        print("Call: lprobust\n")
        print(f"Sample size (n)                              =    {self.opt['n']}")
        print(f"Polynomial order for point estimation (p)    =    {self.opt['p']}")
        print(f"Order of derivative estimated (deriv)        =    {self.opt['deriv']}")
        print(f"Polynomial order for confidence interval (q) =    {self.opt['q']}")
        print(f"Kernel function                              =    {self.opt['kernel']}")
        print(f"Bandwidth method                             =    {self.opt['bwselect']}")
        print()

        z = stats.norm.ppf(1 - alpha / 2)
        CI_l = self.Estimate[:, 5] - self.Estimate[:, 7] * z
        CI_r = self.Estimate[:, 5] + self.Estimate[:, 7] * z

        print("=" * 77)
        print(f"{'':14}{'':10}{'':8}{'Point':>10}{'Std.':>10}{'Robust B.C.':^25}")
        print(f"{'eval':>14}{'h':>10}{'Eff.n':>8}{'Est.':>10}{'Error':>10}"
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


def lprobust(y, x, eval=None, neval=None, p=None, deriv=None, h=None, b=None, rho=1,
             kernel="epa", bwselect=None, bwcheck=21, bwregul=1, imsegrid=30, vce="nn",
             covgrid=False, cluster=None, nnmatch=3, level=95, interior=False, subset=None):
    """
    Local polynomial point estimation with robust bias-corrected inference.

    Parameters
    ----------
    y : array-like
        Response variable.
    x : array-like
        Independent variable.
    eval : array-like or None
        Evaluation points. If None, generated automatically.
    neval : int or None
        Number of evaluation points.
    p : int or None
        Polynomial order for point estimation. Default is 1.
    deriv : int or None
        Order of derivative. Default is 0.
    h : float or array-like or None
        Bandwidth for main estimation.
    b : float or array-like or None
        Bandwidth for bias correction.
    rho : float
        Ratio h/b. Default is 1.
    kernel : str
        Kernel function: 'epa' (Epanechnikov), 'uni' (uniform),
        'tri' (triangular), 'gau' (Gaussian). Default is 'epa'.
    bwselect : str or None
        Bandwidth selection method: 'mse-dpi', 'mse-rot', 'imse-dpi',
        'imse-rot', 'ce-dpi', 'ce-rot'.
    bwcheck : int
        Minimum effective sample size. Default is 21.
    bwregul : float
        Bandwidth regularization. Default is 1.
    imsegrid : int
        Number of grid points for IMSE bandwidth. Default is 30.
    vce : str
        Variance-covariance estimator: 'nn', 'hc0', 'hc1', 'hc2', 'hc3'.
        Default is 'nn'.
    covgrid : bool
        If True, compute covariance across evaluation points.
    cluster : array-like or None
        Cluster variable for cluster-robust inference.
    nnmatch : int
        Number of matches for NN variance estimator. Default is 3.
    level : float
        Confidence level. Default is 95.
    interior : bool
        If True, use interior bandwidth selection. Default is False.
    subset : array-like or None
        Subset indices.

    Returns
    -------
    LprobustResult
        Object containing estimation results.
    """
    # Import lpbwselect here to avoid circular import
    from .lpbwselect import lpbwselect

    # Convert to numpy arrays
    y = np.asarray(y).flatten()
    x = np.asarray(x).flatten()

    # Apply subset
    if subset is not None:
        subset = np.asarray(subset)
        x = x[subset]
        y = y[subset]
        if cluster is not None:
            cluster = np.asarray(cluster)[subset]

    # Handle missing values
    na_ok = ~np.isnan(x) & ~np.isnan(y)
    if cluster is not None:
        cluster = np.asarray(cluster)
        na_ok = na_ok & ~np.isnan(cluster)
        cluster = cluster[na_ok]

    x = x[na_ok]
    y = y[na_ok]

    # Set default p and deriv
    if deriv is not None and p is None:
        p = deriv + 1
    if p is None:
        p = 1
    if deriv is None:
        deriv = 0
    q = p + 1

    x_max = np.max(x)
    x_min = np.min(x)
    N = len(x)

    # Generate evaluation points
    if eval is None:
        if neval is None:
            eval = np.linspace(x_min, x_max, 30)
        else:
            eval = np.linspace(x_min, x_max, neval)
    else:
        eval = np.asarray(eval).flatten()
    neval = len(eval)

    # Default bandwidth selection
    if h is None and bwselect is None:
        if neval == 1:
            bwselect = "mse-dpi"
        else:
            bwselect = "imse-dpi"

    # Sort for NN variance estimator
    if vce == "nn":
        order_x = np.argsort(x)
        x = x[order_x]
        y = y[order_x]
        if cluster is not None:
            cluster = cluster[order_x]

    # Normalize inputs
    kernel = kernel.lower()
    if bwselect is not None:
        bwselect = bwselect.lower()
    vce = vce.lower()

    # Kernel type name
    kernel_type = "Epanechnikov"
    if kernel in ["triangular", "tri"]:
        kernel_type = "Triangular"
    elif kernel in ["uniform", "uni"]:
        kernel_type = "Uniform"
    elif kernel in ["gaussian", "gau"]:
        kernel_type = "Gaussian"

    # Validate inputs
    if kernel not in ["gau", "gaussian", "uni", "uniform", "tri", "triangular", "epa", "epanechnikov", ""]:
        raise ValueError("kernel incorrectly specified")

    if vce not in ["nn", "", "hc1", "hc2", "hc3", "hc0"]:
        raise ValueError("vce incorrectly specified")

    if p < 0 or deriv < 0 or nnmatch <= 0:
        raise ValueError("p, deriv and matches should be positive integers")

    if deriv > p:
        raise ValueError("deriv can only be equal or lower than p")

    if level > 100 or level <= 0:
        raise ValueError("level should be set between 0 and 100")

    if rho < 0:
        raise ValueError("rho should be greater than 0")

    # Bandwidth selection
    if h is not None:
        bwselect = "Manual"

    if h is not None and rho > 0 and b is None:
        b = h / rho

    if h is None:
        lpbws = lpbwselect(y=y, x=x, eval=eval, deriv=deriv, p=p, vce=vce,
                          cluster=cluster, bwselect=bwselect, interior=interior,
                          kernel=kernel, bwcheck=bwcheck, bwregul=bwregul,
                          imsegrid=imsegrid, subset=None)
        h = lpbws.bws[:, 1]
        b = lpbws.bws[:, 2]
        if rho > 0:
            b = h / rho
        rho_vec = h / b

    if np.isscalar(h) and neval > 1:
        h = np.repeat(h, neval)
        b = np.repeat(b, neval)
        rho_vec = h / b
    elif np.isscalar(h):
        h = np.array([h])
        b = np.array([b])
        rho_vec = h / b
    else:
        rho_vec = h / b

    # Compute duplicates for NN
    dups = np.zeros(N, dtype=int)
    dupsid = np.zeros(N, dtype=int)
    if vce == "nn":
        for j in range(N):
            dups[j] = np.sum(x == x[j])
        j = 0
        while j < N:
            dupsid[j:j + dups[j]] = np.arange(1, dups[j] + 1)
            j += dups[j]

    # Initialize results
    Estimate = np.zeros((neval, 8))

    for i in range(neval):
        # Adjust bandwidth for minimum observations
        if bwcheck is not None:
            bw_min = np.sort(np.abs(x - eval[i]))[min(bwcheck - 1, N - 1)]
            h[i] = max(h[i], bw_min)
            b[i] = max(b[i], bw_min)

        # Compute kernel weights
        w_h = W_fun((x - eval[i]) / h[i], kernel) / h[i]
        w_b = W_fun((x - eval[i]) / b[i], kernel) / b[i]
        ind_h = w_h > 0
        ind_b = w_b > 0
        N_h = np.sum(ind_h)
        N_b = np.sum(ind_b)

        if h[i] > b[i]:
            ind = ind_h
        else:
            ind = ind_b

        eN = np.sum(ind)
        eY = y[ind]
        eX = x[ind]
        W_h = w_h[ind]
        W_b = w_b[ind]

        eC = None
        if cluster is not None:
            eC = cluster[ind]

        edups = np.zeros(eN, dtype=int)
        edupsid = np.zeros(eN, dtype=int)
        if vce == "nn":
            edups = dups[ind]
            edupsid = dupsid[ind]

        # Build design matrices
        u = (eX - eval[i]) / h[i]
        R_q = np.zeros((eN, q + 1))
        for j in range(q + 1):
            R_q[:, j] = (eX - eval[i])**j
        R_p = R_q[:, :p + 1]

        # Compute estimators
        L = (R_p * W_h[:, None]).T @ (u**(p + 1))
        invG_q = qrXXinv(np.sqrt(W_b)[:, None] * R_q)
        invG_p = qrXXinv(np.sqrt(W_h)[:, None] * R_p)

        e_p1 = np.zeros((q + 1, 1))
        e_p1[p + 1] = 1
        e_v = np.zeros((p + 1, 1))
        e_v[deriv] = 1

        Q_q = (R_p * W_h[:, None]).T - h[i]**(p + 1) * (L.reshape(-1, 1) @ e_p1.T) @ (invG_q @ R_q.T * W_b)
        Q_q = Q_q.T

        beta_p = invG_p @ (R_p * W_h[:, None]).T @ eY
        beta_q = invG_q @ (R_q * W_b[:, None]).T @ eY
        beta_bc = invG_p @ Q_q.T @ eY

        tau_cl = factorial(deriv) * beta_p[deriv]
        tau_bc = factorial(deriv) * beta_bc[deriv]

        # Compute variance
        hii = None
        predicts_p = np.zeros((eN, 1))
        predicts_q = np.zeros((eN, 1))

        if vce in ["hc0", "hc1", "hc2", "hc3"]:
            predicts_p = (R_p @ beta_p).reshape(-1, 1)
            predicts_q = (R_q @ beta_q).reshape(-1, 1)
            if vce in ["hc2", "hc3"]:
                hii = np.zeros((eN, 1))
                for j in range(eN):
                    hii[j, 0] = R_p[j, :] @ invG_p @ (R_p * W_h[:, None])[j, :]

        res_h = lprobust_res(eX, eY, predicts_p, hii, vce, nnmatch, edups, edupsid, p + 1)
        if vce == "nn":
            res_b = res_h
        else:
            res_b = lprobust_res(eX, eY, predicts_q, hii, vce, nnmatch, edups, edupsid, q + 1)

        V_Y_cl = invG_p @ lprobust_vce(R_p * W_h[:, None], res_h, eC) @ invG_p
        V_Y_bc = invG_p @ lprobust_vce(Q_q, res_b, eC) @ invG_p

        se_cl = np.sqrt(factorial(deriv)**2 * V_Y_cl[deriv, deriv])
        se_rb = np.sqrt(factorial(deriv)**2 * V_Y_bc[deriv, deriv])

        Estimate[i, :] = [eval[i], h[i], b[i], eN, tau_cl, tau_bc, se_cl, se_rb]

    # Covariance computation (if requested)
    cov_us = np.full((neval, neval), np.nan)
    cov_rb = np.full((neval, neval), np.nan)

    if covgrid:
        # Implementation of covariance grid would go here
        # This is a complex computation; simplified for now
        pass

    opt = {
        'p': p,
        'q': q,
        'deriv': deriv,
        'kernel': kernel_type,
        'n': N,
        'neval': neval,
        'bwselect': bwselect
    }

    return LprobustResult(Estimate, opt, cov_us, cov_rb)
