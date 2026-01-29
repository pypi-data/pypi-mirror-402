"""
Bandwidth Selection for Local Polynomial Regression.

This module implements the lpbwselect function for data-driven bandwidth
selection using MSE-optimal, IMSE-optimal, and coverage error optimal criteria.
"""

import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar
from math import factorial
from .npfunctions import (W_fun, qrXXinv, lprobust_res, lprobust_vce,
                          lprobust_bw, lp_bw_fun, lpbwce)


class LpbwselectResult:
    """Result class for lpbwselect bandwidth selection."""

    def __init__(self, bws, bws_imse, opt):
        self.bws = bws
        self.bws_imse = bws_imse
        self.opt = opt

    def __repr__(self):
        return f"lpbwselect Result (n={self.opt['n']}, p={self.opt['p']}, bwselect={self.opt['bwselect']})"

    def summary(self, sep=5):
        """Print summary of bandwidth selection results."""
        print("Call: lpbwselect\n")
        print(f"Sample size (n)                              =    {self.opt['n']}")
        print(f"Polynomial order for point estimation (p)    =    {self.opt['p']}")
        print(f"Order of derivative estimated (deriv)        =    {self.opt['deriv']}")
        print(f"Polynomial order for confidence interval (q) =    {self.opt['q']}")
        print(f"Kernel function                              =    {self.opt['kernel']}")
        print(f"Bandwidth method                             =    {self.opt['bwselect']}")
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


def lpbwselect_mse_rot(y, x, eval_pt, p, deriv, kernel):
    """
    MSE-optimal bandwidth using rule-of-thumb.

    Parameters
    ----------
    y : ndarray
        Response vector.
    x : ndarray
        Covariate vector.
    eval_pt : float
        Evaluation point.
    p : int
        Polynomial order.
    deriv : int
        Derivative order.
    kernel : str
        Kernel type.

    Returns
    -------
    dict
        Dictionary with h, V, B.
    """
    # Import here to avoid circular import
    from .lprobust import lprobust

    even = (p - deriv) % 2 == 0

    C_c = 2.34
    if kernel == "uni":
        C_c = 1.843
    elif kernel == "tri":
        C_c = 2.576

    x_iq = np.percentile(x, 75) - np.percentile(x, 25)
    x_max = np.max(x)
    x_min = np.min(x)
    data_range = x_max - x_min
    N = len(x)

    c_bw = C_c * min(np.std(x, ddof=1), x_iq / 1.349) * N**(-1/5)
    n_h1 = np.sum(np.abs(x - eval_pt) <= c_bw)
    f_hat = n_h1 / (2 * N * c_bw)

    # Fit global polynomial
    k = p + 3
    r_k = np.zeros((N, k + 1))
    for j in range(k + 1):
        r_k[:, j] = x**j

    try:
        gamma_p = np.linalg.lstsq(r_k, y, rcond=None)[0]
        s2_hat = np.sum((y - r_k @ gamma_p)**2) / (N - k - 1)
    except:
        s2_hat = np.var(y, ddof=1)

    # Estimate derivatives
    try:
        result = lprobust(y=y, x=x, h=data_range, eval=np.array([eval_pt]),
                         p=p+3, deriv=p+1, kernel=kernel, vce="nn")
        m_p_1 = result.Estimate[0, 4]

        result = lprobust(y=y, x=x, h=data_range, eval=np.array([eval_pt]),
                         p=p+3, deriv=p+2, kernel=kernel, vce="nn")
        m_p_2 = result.Estimate[0, 4]
    except:
        m_p_1 = 0
        m_p_2 = 0

    bw = lp_bw_fun(s2_hat / max(f_hat, 1e-10),
                   (m_p_1 / factorial(p + 1))**2,
                   p, deriv, N, kernel)

    B1 = bw['C1'] * m_p_1 / factorial(p + 1)
    B2 = bw['C1'] * m_p_2 / factorial(p + 2)
    V = bw['C2'] * s2_hat / max(f_hat, 1e-10)

    if not even:
        h_mse_rot = bw['bw']
        B = B1
    else:
        def h_bw_fun(H):
            return abs(H**(2*p + 2 - 2*deriv) * (B1 + H * B2)**2 + V / (N * H**(1 + 2*deriv)))

        result = minimize_scalar(h_bw_fun, bounds=(np.finfo(float).eps, data_range), method='bounded')
        h_mse_rot = result.x
        B = B1 + h_mse_rot * B2

    return {'h': h_mse_rot, 'V': V, 'B': B}


def lpbwselect_mse_dpi(y, x, cluster, eval_pt, p, q, deriv, kernel,
                       bwcheck, bwregul, vce, nnmatch, interior):
    """
    MSE-optimal bandwidth using direct plug-in.

    Parameters
    ----------
    y : ndarray
        Response vector.
    x : ndarray
        Covariate vector.
    cluster : ndarray or None
        Cluster variable.
    eval_pt : float
        Evaluation point.
    p : int
        Polynomial order.
    q : int
        Bias polynomial order.
    deriv : int
        Derivative order.
    kernel : str
        Kernel type.
    bwcheck : int
        Minimum observations check.
    bwregul : float
        Regularization parameter.
    vce : str
        Variance estimator type.
    nnmatch : int
        NN matches.
    interior : bool
        Interior bandwidth flag.

    Returns
    -------
    dict
        Dictionary with h, b, V_h, B_h, V_b, B_b.
    """
    even = (p - deriv) % 2 == 0

    C_c = 2.34
    if kernel == "uni":
        C_c = 1.843
    elif kernel == "tri":
        C_c = 2.576
    elif kernel == "gau":
        C_c = 1.06

    x_iq = np.percentile(x, 75) - np.percentile(x, 25)
    x_max = np.max(x)
    x_min = np.min(x)
    data_range = x_max - x_min
    N = len(x)

    bw_max = max(abs(eval_pt - x_min), abs(eval_pt - x_max))

    c_bw = C_c * min(np.std(x, ddof=1), x_iq / 1.349) * N**(-1/5)
    c_bw = min(c_bw, bw_max)

    # Handle duplicates for NN
    dups = None
    dupsid = None
    if vce == "nn":
        order_x = np.argsort(x)
        x = x[order_x]
        y = y[order_x]
        if cluster is not None:
            cluster = cluster[order_x]

        dups = np.zeros(N, dtype=int)
        dupsid = np.zeros(N, dtype=int)
        for j in range(N):
            dups[j] = np.sum(x == x[j])
        j = 0
        while j < N:
            dupsid[j:j + dups[j]] = np.arange(1, dups[j] + 1)
            j += dups[j]

    # Bandwidth check
    bw_min = 0
    if bwcheck is not None:
        bw_min = np.sort(np.abs(x - eval_pt))[min(bwcheck - 1, N - 1)]
        c_bw = max(c_bw, bw_min)

    # Compute pilot bandwidths
    C_d1 = lprobust_bw(y, x, cluster, c=eval_pt, o=q+1, nu=q+1, o_B=q+2,
                       h_V=c_bw, h_B1=data_range, h_B2=data_range,
                       scale=0, vce=vce, nnmatch=nnmatch, kernel=kernel,
                       dups=dups, dupsid=dupsid)

    if not even or interior:
        bw_mp2 = C_d1['bw']
    else:
        def bw_fun(H):
            return abs(H**(2*(q+1) + 2 - 2*(q+1)) * (C_d1['B1'] + H * C_d1['B2'])**2 +
                      C_d1['V'] / (N * H**(1 + 2*(q+1))))
        result = minimize_scalar(bw_fun, bounds=(np.finfo(float).eps, data_range), method='bounded')
        bw_mp2 = result.x

    C_d2 = lprobust_bw(y, x, cluster, c=eval_pt, o=q+2, nu=q+2, o_B=q+3,
                       h_V=c_bw, h_B1=data_range, h_B2=data_range,
                       scale=0, vce=vce, nnmatch=nnmatch, kernel=kernel,
                       dups=dups, dupsid=dupsid)

    if not even or interior:
        bw_mp3 = C_d2['bw']
    else:
        def bw_fun(H):
            return abs(H**(2*(q+2) + 2 - 2*(q+2)) * (C_d2['B1'] + H * C_d2['B2'])**2 +
                      C_d2['V'] / (N * H**(1 + 2*(q+2))))
        result = minimize_scalar(bw_fun, bounds=(np.finfo(float).eps, data_range), method='bounded')
        bw_mp3 = result.x

    # Adjust bandwidths
    bw_mp2 = min(bw_mp2, bw_max)
    bw_mp3 = min(bw_mp3, bw_max)

    if bwcheck is not None:
        bw_mp2 = max(bw_mp2, bw_min)
        bw_mp3 = max(bw_mp3, bw_min)

    # Select preliminary bw b
    C_b = lprobust_bw(y, x, cluster, c=eval_pt, o=q, nu=p+1, o_B=q+1,
                      h_V=c_bw, h_B1=bw_mp2, h_B2=bw_mp3,
                      scale=bwregul, vce=vce, nnmatch=nnmatch, kernel=kernel,
                      dups=dups, dupsid=dupsid)

    if not even or interior:
        b_mse_dpi = C_b['bw']
    else:
        def b_bw_fun(H):
            return abs(H**(2*q + 2 - 2*(p+1)) * (C_b['B1'] + H * C_b['B2'] + bwregul * C_b['R'])**2 +
                      C_b['V'] / (N * H**(1 + 2*(p+1))))
        result = minimize_scalar(b_bw_fun, bounds=(np.finfo(float).eps, data_range), method='bounded')
        b_mse_dpi = result.x

    b_mse_dpi = min(b_mse_dpi, bw_max)
    if bwcheck is not None:
        b_mse_dpi = max(b_mse_dpi, bw_min)

    bw_mp1 = b_mse_dpi

    # Select final bw h
    C_h = lprobust_bw(y, x, cluster, c=eval_pt, o=p, nu=deriv, o_B=q,
                      h_V=c_bw, h_B1=bw_mp1, h_B2=bw_mp2,
                      scale=bwregul, vce=vce, nnmatch=nnmatch, kernel=kernel,
                      dups=dups, dupsid=dupsid)

    if not even or interior:
        h_mse_dpi = C_h['bw']
    else:
        def h_bw_fun(H):
            return abs(H**(2*p + 2 - 2*deriv) * (C_h['B1'] + H * C_h['B2'] + bwregul * C_h['R'])**2 +
                      C_h['V'] / (N * H**(1 + 2*deriv)))
        result = minimize_scalar(h_bw_fun, bounds=(np.finfo(float).eps, data_range), method='bounded')
        h_mse_dpi = result.x

    h_mse_dpi = min(h_mse_dpi, bw_max)
    if bwcheck is not None:
        h_mse_dpi = max(h_mse_dpi, bw_min)

    if not even or interior:
        V_h = C_h['rV'] * C_h['V']
        B_h = C_h['rB'] * C_h['B1']**2
        V_b = C_b['rV'] * C_b['V']
        B_b = C_b['rB'] * C_b['B1']**2
    else:
        V_h = C_h['V']
        B_h = (C_h['B1'] + h_mse_dpi * C_h['B2'])**2
        V_b = C_b['V']
        B_b = (C_b['B1'] + b_mse_dpi * C_b['B2'])**2

    return {'h': h_mse_dpi, 'b': b_mse_dpi, 'V_h': V_h, 'B_h': B_h, 'V_b': V_b, 'B_b': B_b}


def lpbwselect_imse_rot(y, x, p, deriv, kernel, imsegrid):
    """
    IMSE-optimal bandwidth using rule-of-thumb.

    Parameters
    ----------
    y : ndarray
        Response vector.
    x : ndarray
        Covariate vector.
    p : int
        Polynomial order.
    deriv : int
        Derivative order.
    kernel : str
        Kernel type.
    imsegrid : int
        Number of grid points.

    Returns
    -------
    dict
        Dictionary with h.
    """
    even = (p - deriv) % 2 == 0
    eval_pts = np.percentile(x, np.linspace(5, 95, 37))
    neval = len(eval_pts)
    x_max = np.max(x)
    x_min = np.min(x)
    data_range = x_max - x_min
    N = len(x)

    V = np.zeros(neval)
    B = np.zeros(neval)

    for i in range(neval):
        est = lpbwselect_mse_rot(y=y, x=x, eval_pt=eval_pts[i], p=p, deriv=deriv, kernel=kernel)
        V[i] = est['V']
        B[i] = est['B']

    if not even:
        h_imse_rot = (np.mean((1 + 2*deriv) * V) / (N * np.mean(2 * (p + 1 - deriv) * B**2)))**(1 / (2*p + 3))
    else:
        def h_bw_fun(H):
            return abs(H**(2*p + 2 - 2*deriv) * np.mean(B**2) + np.mean(V) / (N * H**(1 + 2*deriv)))
        result = minimize_scalar(h_bw_fun, bounds=(np.finfo(float).eps, data_range), method='bounded')
        h_imse_rot = result.x

    return {'h': h_imse_rot}


def lpbwselect_imse_dpi(y, x, cluster, p, q, deriv, kernel, bwcheck, bwregul,
                        imsegrid, vce, nnmatch, interior):
    """
    IMSE-optimal bandwidth using direct plug-in.

    Parameters
    ----------
    y : ndarray
        Response vector.
    x : ndarray
        Covariate vector.
    cluster : ndarray or None
        Cluster variable.
    p : int
        Polynomial order.
    q : int
        Bias polynomial order.
    deriv : int
        Derivative order.
    kernel : str
        Kernel type.
    bwcheck : int
        Minimum observations check.
    bwregul : float
        Regularization parameter.
    imsegrid : int
        Number of grid points.
    vce : str
        Variance estimator type.
    nnmatch : int
        NN matches.
    interior : bool
        Interior bandwidth flag.

    Returns
    -------
    dict
        Dictionary with h, b.
    """
    N = len(x)
    x_max = np.max(x)
    x_min = np.min(x)
    data_range = x_max - x_min
    eval_pts = np.linspace(x_min, x_max, imsegrid)
    neval = len(eval_pts)
    even = (p - deriv) % 2 == 0

    V_h = np.zeros(neval)
    B_h = np.zeros(neval)
    V_b = np.zeros(neval)
    B_b = np.zeros(neval)

    for i in range(neval):
        est = lpbwselect_mse_dpi(y=y, x=x, cluster=cluster, eval_pt=eval_pts[i],
                                  p=p, q=q, deriv=deriv, kernel=kernel,
                                  bwcheck=bwcheck, bwregul=bwregul, vce=vce,
                                  nnmatch=nnmatch, interior=interior)
        V_h[i] = est['V_h']
        B_h[i] = est['B_h']
        V_b[i] = est['V_b']
        B_b[i] = est['B_b']

    if not even or interior:
        b_imse_dpi = (np.mean(V_b) / (N * np.mean(B_b)))**(1 / (2*q + 3))
        h_imse_dpi = (np.mean(V_h) / (N * np.mean(B_h)))**(1 / (2*p + 3))
    else:
        def b_bw_fun(H):
            return abs(H**(2*q + 2 - 2*(p+1)) * np.mean(B_b) + np.mean(V_b) / (N * H**(1 + 2*(p+1))))
        result = minimize_scalar(b_bw_fun, bounds=(np.finfo(float).eps, data_range), method='bounded')
        b_imse_dpi = result.x

        def h_bw_fun(H):
            return abs(H**(2*p + 2 - 2*deriv) * np.mean(B_h) + np.mean(V_h) / (N * H**(1 + 2*deriv)))
        result = minimize_scalar(h_bw_fun, bounds=(np.finfo(float).eps, data_range), method='bounded')
        h_imse_dpi = result.x

    return {'h': h_imse_dpi, 'b': b_imse_dpi}


def lpbwselect(y, x, eval=None, neval=None, p=None, deriv=None, kernel="epa",
               bwselect="mse-dpi", bwcheck=21, bwregul=1, imsegrid=30, vce="nn",
               cluster=None, nnmatch=3, interior=False, subset=None):
    """
    Bandwidth selection for local polynomial regression.

    Parameters
    ----------
    y : array-like
        Response variable.
    x : array-like
        Independent variable.
    eval : array-like or None
        Evaluation points.
    neval : int or None
        Number of evaluation points.
    p : int or None
        Polynomial order. Default is 1.
    deriv : int or None
        Derivative order. Default is 0.
    kernel : str
        Kernel function. Default is 'epa'.
    bwselect : str
        Bandwidth selection method. Default is 'mse-dpi'.
    bwcheck : int
        Minimum effective sample size. Default is 21.
    bwregul : float
        Bandwidth regularization. Default is 1.
    imsegrid : int
        IMSE grid points. Default is 30.
    vce : str
        Variance estimator. Default is 'nn'.
    cluster : array-like or None
        Cluster variable.
    nnmatch : int
        NN matches. Default is 3.
    interior : bool
        Interior bandwidth. Default is False.
    subset : array-like or None
        Subset indices.

    Returns
    -------
    LpbwselectResult
        Object containing bandwidth selection results.
    """
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

    x_max = np.max(x)
    x_min = np.min(x)
    N = len(x)

    # Set defaults
    if deriv is not None and p is None:
        p = deriv + 1
    if p is None:
        p = 1
    if deriv is None:
        deriv = 0
    q = p + 1

    # Generate evaluation points
    if eval is None:
        if neval is None:
            eval = np.linspace(x_min, x_max, 30)
        else:
            eval = np.linspace(x_min, x_max, neval)
    else:
        eval = np.asarray(eval).flatten()
    neval = len(eval)

    # Normalize inputs
    kernel = kernel.lower()
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

    # For IMSE methods, use single evaluation
    if bwselect in ["imse-dpi", "imse-rot"]:
        neval = 1
        eval = np.array([1.0])

    # Initialize bandwidth matrix
    bws = np.zeros((neval, 3))  # eval, h, b
    bws_imse = None

    # IMSE-DPI
    if bwselect == "imse-dpi":
        est = lpbwselect_imse_dpi(y=y, x=x, cluster=cluster, p=p, q=q, deriv=deriv,
                                   kernel=kernel, bwcheck=bwcheck, bwregul=bwregul,
                                   imsegrid=imsegrid, vce=vce, nnmatch=nnmatch,
                                   interior=interior)
        bws[0, 0] = eval[0]
        bws[0, 1] = est['h']
        bws[0, 2] = est['b']

    # IMSE-ROT
    elif bwselect == "imse-rot":
        est_h = lpbwselect_imse_rot(y=y, x=x, p=p, deriv=deriv, kernel=kernel,
                                     imsegrid=imsegrid)
        est_b = lpbwselect_imse_rot(y=y, x=x, p=q, deriv=p+1, kernel=kernel,
                                     imsegrid=imsegrid)
        bws[0, 0] = eval[0]
        bws[0, 1] = est_h['h']
        bws[0, 2] = est_b['h']

    # MSE-DPI or other point-specific methods
    elif bwselect in ["mse-dpi", "mse-rot", "ce-dpi", "ce-rot"]:
        for i in range(neval):
            if bwselect in ["mse-dpi", "ce-dpi", "ce-rot"]:
                est = lpbwselect_mse_dpi(y=y, x=x, cluster=cluster, eval_pt=eval[i],
                                          p=p, q=q, deriv=deriv, kernel=kernel,
                                          bwcheck=bwcheck, bwregul=bwregul, vce=vce,
                                          nnmatch=nnmatch, interior=interior)
                h_mse_dpi = est['h']
                b_mse_dpi = est['b']
                bws[i, 0] = eval[i]
                bws[i, 1] = h_mse_dpi
                bws[i, 2] = b_mse_dpi

            elif bwselect == "mse-rot":
                est_h = lpbwselect_mse_rot(y=y, x=x, eval_pt=eval[i], p=p, deriv=deriv,
                                            kernel=kernel)
                est_b = lpbwselect_mse_rot(y=y, x=x, eval_pt=eval[i], p=q, deriv=p+1,
                                            kernel=kernel)
                bws[i, 0] = eval[i]
                bws[i, 1] = est_h['h']
                bws[i, 2] = est_b['h']

            # Coverage error adjustments
            if bwselect == "ce-dpi":
                even = (p - deriv) % 2 == 0
                if even:
                    h_ce_dpi = h_mse_dpi * N**(-((p+2) / ((2*p+5) * (p+3))))
                    b_ce_dpi = b_mse_dpi * N**(-((q) / ((2*q+3) * (q+3))))
                else:
                    h_ce_dpi = h_mse_dpi * N**(-((p) / ((2*p+3) * (p+3))))
                    b_ce_dpi = b_mse_dpi * N**(-((q+2) / ((2*q+5) * (q+3))))
                bws[i, 1] = h_ce_dpi
                bws[i, 2] = b_ce_dpi

            elif bwselect == "ce-rot":
                even = (p - deriv) % 2 == 0
                if even:
                    h_ce_rot = bws[i, 1] * N**(-((p+2) / ((2*p+5) * (p+3))))
                    b_ce_rot = bws[i, 2] * N**(-((q) / ((2*q+3) * (q+3))))
                else:
                    h_ce_rot = bws[i, 1] * N**(-((p) / ((2*p+3) * (p+3))))
                    b_ce_rot = bws[i, 2] * N**(-((q+2) / ((2*q+5) * (q+3))))
                bws[i, 1] = h_ce_rot
                bws[i, 2] = b_ce_rot

    opt = {
        'n': N,
        'neval': neval,
        'p': p,
        'q': q,
        'deriv': deriv,
        'kernel': kernel_type,
        'bwselect': bwselect
    }

    return LpbwselectResult(bws, bws_imse, opt)
