"""
Internal helper functions for nprobust package.

These functions implement kernel weighting, bandwidth selection,
residual computation, and variance-covariance estimation.
"""

import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar
from math import factorial


def W_fun(u, kernel):
    """
    Compute kernel weights.

    Parameters
    ----------
    u : array-like
        Scaled distances.
    kernel : str
        Kernel type: 'epa' (Epanechnikov), 'uni' (uniform),
        'tri' (triangular), or 'gau' (Gaussian).

    Returns
    -------
    w : ndarray
        Kernel weights.
    """
    u = np.asarray(u)
    if kernel == "epa":
        w = 0.75 * (1 - u**2) * (np.abs(u) <= 1)
    elif kernel == "uni":
        w = 0.5 * (np.abs(u) <= 1)
    elif kernel == "tri":
        w = (1 - np.abs(u)) * (np.abs(u) <= 1)
    elif kernel == "gau":
        w = stats.norm.pdf(u)
    else:
        raise ValueError(f"Unknown kernel: {kernel}")
    return w


def kd_bw_fun(V, B, N, v, r):
    """
    Bandwidth function for kernel density estimation.

    Parameters
    ----------
    V : float
        Variance component.
    B : float
        Bias component.
    N : int
        Sample size.
    v : int
        Kernel order.
    r : int
        Derivative order.

    Returns
    -------
    float
        Optimal bandwidth.
    """
    return ((1 + 2*r) * V / (2 * v * N * B**2))**(1 / (1 + 2*v + 2*r))


def kd_K_fun(x, v, r, kernel):
    """
    Compute kernel function values and constants for density estimation.

    Parameters
    ----------
    x : array-like
        Input values.
    v : int
        Kernel order (2, 4, or 6).
    r : int
        Derivative order (0, 2, or 4).
    kernel : str
        Kernel type: 'epa', 'uni', or 'gau'.

    Returns
    -------
    dict
        Dictionary with 'Kx' (kernel values), 'k_v' (integral constant),
        'R_v' (roughness constant).
    """
    x = np.asarray(x)

    # Define kernel function based on v and r
    if v == 2:
        if kernel == "gau":
            if r == 0:
                k = lambda u: stats.norm.pdf(u)
            elif r == 2:
                k = lambda u: (u**2 - 1) * stats.norm.pdf(u)
            elif r == 4:
                k = lambda u: (u**4 - 6*u**2 + 3) * stats.norm.pdf(u)
        elif kernel == "uni":
            if r == 0:
                k = lambda u: 0.5 * (np.abs(u) <= 1)
        elif kernel == "epa":
            if r == 0:
                k = lambda u: 0.75 * (1 - u**2) * (np.abs(u) <= 1)
    elif v == 4:
        if kernel == "uni":
            if r == 0:
                k = lambda u: (np.abs(u) <= 1) * 3 * (-5*u**2 + 3) / 8
            elif r == 2:
                k = lambda u: (np.abs(u) <= 1) * 15 * (3*u**2 - 1) / 4
        elif kernel == "epa":
            if r == 0:
                k = lambda u: (np.abs(u) <= 1) * (15/32) * (7*u**4 - 10*u**2 + 3)
            elif r == 2:
                k = lambda u: (np.abs(u) <= 1) * (105/16) * (6*u**2 - 5*u**4 - 1)
    elif v == 6:
        if kernel == "uni":
            if r == 0:
                k = lambda u: (np.abs(u) <= 1) * 15 * (63*u**4 - 70*u**2 + 15) / 128
            elif r == 2:
                k = lambda u: (np.abs(u) <= 1) * 105 * (-45*u**4 + 42*u**2 - 5) / 32
        elif kernel == "epa":
            if r == 0:
                k = lambda u: (np.abs(u) <= 1) * (35/256) * (-99*u**6 + 189*u**4 - 105*u**2 + 15)
            elif r == 2:
                k = lambda u: (np.abs(u) <= 1) * (315/64) * (77*u**6 - 135*u**4 + 63*u**2 - 5)

    Kx = k(x)

    # Compute integrals numerically
    from scipy.integrate import quad

    # k_v integral
    def integrand_kv(u):
        return ((-1)**v * u**v * k(u)) / factorial(v)

    if kernel == "gau":
        k_v, _ = quad(integrand_kv, -np.inf, np.inf)
    else:
        k_v, _ = quad(integrand_kv, -1, 1)

    # R_v integral (roughness)
    def integrand_Rv(u):
        return k(u)**2

    if kernel == "gau":
        R_v, _ = quad(integrand_Rv, -np.inf, np.inf)
    else:
        R_v, _ = quad(integrand_Rv, -1, 1)

    return {'Kx': Kx, 'k_v': k_v, 'R_v': R_v}


def kd_cer_fun(x, x0, h, b, v, kernel):
    """
    Coverage error rate bandwidth function for kernel density estimation.

    Parameters
    ----------
    x : array-like
        Data vector.
    x0 : float
        Evaluation point.
    h : float
        Main bandwidth.
    b : float
        Pilot bandwidth.
    v : int
        Kernel order.
    kernel : str
        Kernel type.

    Returns
    -------
    float
        Coverage error rate optimal bandwidth.
    """
    from scipy.integrate import quad
    from scipy.optimize import minimize_scalar

    x = np.asarray(x)
    n = len(x)
    rho = h / b
    data_range = np.max(x) - np.min(x)

    # Rule of thumb pilot bandwidth
    q_rot = np.std(x, ddof=1) * n**(-1 / (1 + 2*v + 2*(v+2)))
    K_q = kd_K_fun((x - x0) / q_rot, v=2, r=v+2, kernel="gau")
    f_r_2 = np.mean(K_q['Kx']) / q_rot**(1 + 2*v)

    v_K = kd_K_fun(np.array([1.0]), v=v, r=0, kernel=kernel)['k_v']

    def M_fun(u):
        Kx = kd_K_fun(np.array([u]), v=v, r=0, kernel=kernel)['Kx'][0]
        Lx = kd_K_fun(np.array([rho*u]), v=v+2, r=v, kernel=kernel)['Kx'][0]
        return Kx - rho**(1+v) * Lx * v_K

    def K_fun(u):
        return kd_K_fun(np.array([u]), v=v, r=0, kernel=kernel)['Kx'][0]

    def L_fun(u):
        return kd_K_fun(np.array([u]), v=v+2, r=v, kernel=kernel)['Kx'][0]

    # Integrate to get constants
    limit = 5 if kernel == "gau" else 1

    v_M_2, _ = quad(lambda u: M_fun(u)**2, -limit, limit)
    v_M_3, _ = quad(lambda u: M_fun(u)**3, -limit, limit)
    v_M_4, _ = quad(lambda u: M_fun(u)**4, -limit, limit)
    m_M_4, _ = quad(lambda u: u**4 * M_fun(u), -limit, limit)
    m_K_4, _ = quad(lambda u: u**4 * K_fun(u), -limit, limit)
    m_K_2, _ = quad(lambda u: u**2 * K_fun(u), -limit, limit)
    m_L_2, _ = quad(lambda u: u**2 * L_fun(u), -limit, limit)

    z = stats.norm.ppf(0.975)
    q1 = v_M_4 * (z**2 - 3) / 6 - v_M_3**2 * (z**4 - 4*z**2 + 15) / 9
    q2 = f_r_2**2 * (m_K_4 - rho**(-2) * m_K_2 * m_L_2 / 12)**2 * v_M_2
    q3 = f_r_2 * (m_K_4 - rho**(-2) * m_K_2 * m_L_2 / 12) * v_M_3 * (2*z**2) / 3

    def objective(H):
        return (H**(-1) * q1 - H**(1 + 2*(v+2)) * q2 + H**(v+2) * q3)**2

    result = minimize_scalar(objective, bounds=(np.finfo(float).eps, data_range), method='bounded')
    h_opt = result.x * n**(-1 / (v + 3))

    return h_opt


def qrXXinv(x):
    """
    Compute (X'X)^(-1) using Cholesky decomposition.

    Parameters
    ----------
    x : ndarray
        Design matrix.

    Returns
    -------
    ndarray
        Inverse of X'X.
    """
    XtX = x.T @ x
    try:
        L = np.linalg.cholesky(XtX)
        Linv = np.linalg.solve(L, np.eye(L.shape[0]))
        return Linv.T @ Linv
    except np.linalg.LinAlgError:
        # Fall back to pseudo-inverse if Cholesky fails
        return np.linalg.pinv(XtX)


def lp_bw_fun(V, Bsq, p, v, N, kernel):
    """
    Bandwidth function for local polynomial regression.

    Parameters
    ----------
    V : float
        Variance component.
    Bsq : float
        Squared bias component.
    p : int
        Polynomial order.
    v : int
        Derivative order.
    N : int
        Sample size.
    kernel : str
        Kernel type.

    Returns
    -------
    dict
        Dictionary with 'bw' (bandwidth), 'C1', 'C2' constants.
    """
    from scipy.integrate import quad

    def k_fun(u):
        if kernel == "epa":
            return 0.75 * (1 - u**2) * (np.abs(u) <= 1)
        elif kernel == "uni":
            return 0.5 * (np.abs(u) <= 1)
        elif kernel == "tri":
            return (1 - np.abs(u)) * (np.abs(u) <= 1)
        elif kernel == "gau":
            return stats.norm.pdf(u)
        return 0

    def m1(i, j, k_func):
        result, _ = quad(lambda x: x**i * x**j * k_func(x), 0, np.inf if kernel == "gau" else 1)
        return result

    def m2(i, j, k_func):
        result, _ = quad(lambda x: x**i * x**j * k_func(x)**2, 0, np.inf if kernel == "gau" else 1)
        return result

    def GAMMA(p, k_func):
        out = np.zeros((p+1, p+1))
        for i in range(p+1):
            for j in range(p+1):
                out[i, j] = m1(i, j, k_func)
        return out

    def NU(p, k_func):
        out = np.zeros((p+1, 1))
        for i in range(p+1):
            out[i, 0] = m1(i, p+1, k_func)
        return out

    def PSI(p, k_func):
        out = np.zeros((p+1, p+1))
        for i in range(p+1):
            for j in range(p+1):
                out[i, j] = m2(i, j, k_func)
        return out

    def C1_fun(p0, v, K):
        S_inv = np.linalg.inv(GAMMA(p0, K))
        C1 = (S_inv @ NU(p0, K))[v, 0]
        return C1

    def C2_fun(p0, v, K):
        S_inv = np.linalg.inv(GAMMA(p0, K))
        C2 = (S_inv @ PSI(p0, K) @ S_inv)[v, v]
        return C2

    C1_h = C1_fun(p, v, k_fun)
    C2_h = C2_fun(p, v, k_fun)
    bw = ((2*v + 1) * C2_h * V / (2 * (p + 1 - v) * C1_h**2 * Bsq * N))**(1 / (2*p + 3))

    return {'bw': bw, 'C1': C1_h, 'C2': C2_h}


def lprobust_res(X, y, m, hii, vce, matches, dups, dupsid, d):
    """
    Compute residuals for local polynomial regression.

    Parameters
    ----------
    X : ndarray
        Covariate vector.
    y : ndarray
        Response vector.
    m : ndarray
        Fitted values (predictions).
    hii : ndarray
        Hat matrix diagonal (leverage values).
    vce : str
        Variance-covariance estimator type.
    matches : int
        Number of matches for NN.
    dups : ndarray
        Duplicates count.
    dupsid : ndarray
        Duplicate IDs.
    d : int
        Number of parameters.

    Returns
    -------
    ndarray
        Residuals.
    """
    n = len(y)
    res = np.zeros((n, 1))

    if vce == "nn":
        X = np.asarray(X).flatten()
        y = np.asarray(y).flatten()
        dups = np.asarray(dups).flatten()
        dupsid = np.asarray(dupsid).flatten()

        for pos in range(n):
            rpos = int(dups[pos] - dupsid[pos])
            lpos = int(dupsid[pos] - 1)

            while lpos + rpos < min(matches, n - 1):
                if pos - lpos - 1 < 0:
                    if pos + rpos + 1 < n:
                        rpos = rpos + int(dups[pos + rpos + 1])
                elif pos + rpos + 1 >= n:
                    lpos = lpos + int(dups[pos - lpos - 1])
                elif (X[pos] - X[pos - lpos - 1]) > (X[pos + rpos + 1] - X[pos]):
                    if pos + rpos + 1 < n:
                        rpos = rpos + int(dups[pos + rpos + 1])
                elif (X[pos] - X[pos - lpos - 1]) < (X[pos + rpos + 1] - X[pos]):
                    lpos = lpos + int(dups[pos - lpos - 1])
                else:
                    if pos + rpos + 1 < n:
                        rpos = rpos + int(dups[pos + rpos + 1])
                    lpos = lpos + int(dups[pos - lpos - 1])

            start_idx = max(0, pos - lpos)
            end_idx = min(n, pos + rpos + 1)
            ind_J = list(range(start_idx, end_idx))

            y_J = sum(y[j] for j in ind_J) - y[pos]
            Ji = len(ind_J) - 1
            if Ji > 0:
                res[pos, 0] = np.sqrt(Ji / (Ji + 1)) * (y[pos] - y_J / Ji)
    else:
        y = np.asarray(y).reshape(-1, 1)
        if hii is None or (isinstance(hii, (int, float)) and hii == 0):
            hii = np.zeros((n, 1))
        else:
            hii = np.asarray(hii).reshape(-1, 1)

        if vce == "hc0":
            w = 1.0
        elif vce == "hc1":
            w = np.sqrt(n / (n - d))
        elif vce == "hc2":
            w = np.sqrt(1.0 / (1.0 - hii))
        else:  # hc3
            w = 1.0 / (1.0 - hii)

        res = w * (y - m)

    return res


def lprobust_vce(RX, res, C):
    """
    Compute variance-covariance matrix.

    Parameters
    ----------
    RX : ndarray
        Design matrix times weights.
    res : ndarray
        Residuals.
    C : ndarray or None
        Cluster variable.

    Returns
    -------
    ndarray
        Variance-covariance matrix.
    """
    n = RX.shape[0]
    k = RX.shape[1]
    M = np.zeros((k, k))

    if C is None:
        # No clustering
        M = (res.flatten()[:, None] * RX).T @ (res.flatten()[:, None] * RX)
    else:
        # Cluster robust
        C = np.asarray(C).flatten()
        clusters = np.unique(C)
        g = len(clusters)
        w = ((n - 1) / (n - k)) * (g / (g - 1))

        for cluster in clusters:
            ind = C == cluster
            Xi = RX[ind, :]
            ri = res[ind].flatten()
            temp = Xi.T @ ri
            M = M + np.outer(temp, temp)

        M = w * M

    return M


def lprobust_bw(Y, X, cluster, c, o, nu, o_B, h_V, h_B1, h_B2, scale, vce, nnmatch, kernel, dups, dupsid):
    """
    Bandwidth selection helper for local polynomial regression.

    Parameters
    ----------
    Y : ndarray
        Response vector.
    X : ndarray
        Covariate vector.
    cluster : ndarray or None
        Cluster variable.
    c : float
        Evaluation point.
    o : int
        Polynomial order.
    nu : int
        Derivative order.
    o_B : int
        Bias polynomial order.
    h_V : float
        Variance bandwidth.
    h_B1 : float
        Bias bandwidth 1.
    h_B2 : float
        Bias bandwidth 2.
    scale : float
        Regularization scale.
    vce : str
        Variance-covariance estimator.
    nnmatch : int
        Number of NN matches.
    kernel : str
        Kernel type.
    dups : ndarray
        Duplicates.
    dupsid : ndarray
        Duplicate IDs.

    Returns
    -------
    dict
        Dictionary with V, B1, B2, R, r, rB, rV, bw.
    """
    X = np.asarray(X).flatten()
    Y = np.asarray(Y).flatten()

    # Variance estimation
    w = W_fun((X - c) / h_V, kernel) / h_V
    ind_V = w > 0
    eY = Y[ind_V]
    eX = X[ind_V]
    eW = w[ind_V]
    n_V = np.sum(ind_V)

    R_V = np.zeros((n_V, o + 1))
    for j in range(o + 1):
        R_V[:, j] = (eX - c)**j

    invG_V = qrXXinv(R_V * np.sqrt(eW)[:, None])
    beta_V = invG_V @ (R_V * eW[:, None]).T @ eY

    eC = None
    if cluster is not None:
        eC = cluster[ind_V]

    dups_V = dupsid_V = None
    predicts_V = np.zeros((n_V, 1))
    hii = None

    if vce == "nn":
        dups_V = dups[ind_V]
        dupsid_V = dupsid[ind_V]

    if vce in ["hc0", "hc1", "hc2", "hc3"]:
        predicts_V = (R_V @ beta_V).reshape(-1, 1)
        if vce in ["hc2", "hc3"]:
            hii = np.zeros((n_V, 1))
            for i in range(n_V):
                hii[i, 0] = R_V[i, :] @ invG_V @ (R_V * eW[:, None])[i, :]

    res_V = lprobust_res(eX, eY, predicts_V, hii, vce, nnmatch, dups_V, dupsid_V, o + 1)
    V_V = (invG_V @ lprobust_vce(R_V * eW[:, None], res_V, eC) @ invG_V)[nu, nu]

    # Bias estimation
    Hp = np.array([h_V**j for j in range(o + 1)])
    v1 = (R_V * eW[:, None]).T @ ((eX - c) / h_V)**(o + 1)
    v2 = (R_V * eW[:, None]).T @ ((eX - c) / h_V)**(o + 2)
    BConst1 = (Hp * (invG_V @ v1).flatten())[nu]
    BConst2 = (Hp * (invG_V @ v2).flatten())[nu]

    # Bias bandwidth 1
    w = W_fun((X - c) / h_B1, kernel)
    ind = w > 0
    n_B = np.sum(ind)
    eY = Y[ind]
    eX = X[ind]
    eW = w[ind]

    if cluster is not None:
        eC = cluster[ind]

    R_B1 = np.zeros((n_B, o_B + 1))
    for j in range(o_B + 1):
        R_B1[:, j] = (eX - c)**j

    invG_B1 = qrXXinv(R_B1 * np.sqrt(eW)[:, None])
    beta_B1 = invG_B1 @ (R_B1 * eW[:, None]).T @ eY

    BWreg = 0
    if scale > 0:
        dups_B = dupsid_B = None
        hii = None
        predicts_B = np.zeros((n_B, 1))

        if vce == "nn":
            dups_B = dups[ind]
            dupsid_B = dupsid[ind]

        if vce in ["hc0", "hc1", "hc2", "hc3"]:
            predicts_B = (R_B1 @ beta_B1).reshape(-1, 1)
            if vce in ["hc2", "hc3"]:
                hii = np.zeros((n_B, 1))
                for i in range(n_B):
                    hii[i, 0] = R_B1[i, :] @ invG_B1 @ (R_B1 * eW[:, None])[i, :]

        res_B = lprobust_res(eX, eY, predicts_B, hii, vce, nnmatch, dups_B, dupsid_B, o_B + 1)
        V_B = (invG_B1 @ lprobust_vce(R_B1 * eW[:, None], res_B, eC) @ invG_B1)[o + 1, o + 1]
        BWreg = 3 * BConst1**2 * V_B

    # Bias bandwidth 2
    w = W_fun((X - c) / h_B2, kernel)
    ind = w > 0
    n_B = np.sum(ind)
    eY = Y[ind]
    eX = X[ind]
    eW = w[ind]

    R_B2 = np.zeros((n_B, o_B + 2))
    for j in range(o_B + 2):
        R_B2[:, j] = (eX - c)**j

    invG_B2 = qrXXinv(R_B2 * np.sqrt(eW)[:, None])
    beta_B2 = invG_B2 @ (R_B2 * eW[:, None]).T @ eY

    N = len(X)
    B1 = BConst1 * beta_B1[o + 1]
    B2 = BConst2 * beta_B2[o + 2]
    V = N * h_V**(2*nu + 1) * V_V
    R = BWreg
    r = 1 / (2*o + 3)
    rB = 2 * (o + 1 - nu)
    rV = 2*nu + 1
    bw = ((rV * V) / (N * rB * (B1**2 + scale * R)))**r

    return {'V': V, 'B1': B1, 'B2': B2, 'R': R, 'r': r, 'rB': rB, 'rV': rV, 'bw': bw}


def lpbwce(y, x, K, L, res, c, p, q, h, b, deriv, fact):
    """
    Coverage error bandwidth selection (Python implementation of C++ function).

    Parameters
    ----------
    y : ndarray
        Response vector.
    x : ndarray
        Covariate vector.
    K : ndarray
        Kernel weights for h.
    L : ndarray
        Kernel weights for b.
    res : ndarray
        Residuals.
    c : float
        Evaluation point.
    p : int
        Polynomial order.
    q : int
        Bias polynomial order.
    h : float
        Main bandwidth.
    b : float
        Bias bandwidth.
    deriv : int
        Derivative order.
    fact : int
        Factorial of deriv.

    Returns
    -------
    dict
        Dictionary with q1rbc, q2rbc, q3rbc.
    """
    y = np.asarray(y).flatten()
    x = np.asarray(x).flatten()
    K = np.asarray(K).flatten()
    L = np.asarray(L).flatten()
    res = np.asarray(res).flatten()

    N = len(y)
    rho = h / b

    Wp = K / h
    Wq = L / b
    Xh = (x - c) / h
    Xb = (x - c) / b

    Rq = np.zeros((N, q + 1))
    Rp = np.zeros((N, p + 1))
    for i in range(q + 1):
        Rq[:, i] = Xb**i
    for i in range(p + 1):
        Rp[:, i] = Xh**i

    dWp = np.diag(Wp)
    dWq = np.diag(Wq)
    dK = np.diag(K)
    dL = np.diag(L)

    Lp1 = Rp.T @ dWp @ (Xh**(p+1)) / N
    Gp = Rp.T @ dWp @ Rp / N
    Gq = Rq.T @ dWq @ Rq / N

    iGp = np.linalg.inv(Gp)
    iGq = np.linalg.inv(Gq)

    ep1 = np.zeros((q + 1, 1))
    ep1[p + 1] = 1
    e0 = np.zeros((p + 1, 1))
    e0[deriv] = fact

    lus0 = e0.T @ iGp @ (dK @ Rp).T
    lbc0 = lus0 - rho**(p+1) * (e0.T @ iGp) @ Lp1.reshape(-1, 1) @ ep1.T @ iGq @ (dL @ Rq).T
    lbc0 = lbc0.flatten()

    vx = res**2

    sums2 = np.sum(lbc0**2 * vx)
    s2 = sums2 / (N * h)

    # Compute EK and EL matrices
    Krrp = np.zeros((p+1, p+1))
    Krxip = np.zeros((1, p+1))
    Krxp = np.zeros((1, p+1))
    Lrrq = np.zeros((q+1, q+1))

    for i in range(N):
        Rpi = Rp[i:i+1, :]
        Rqi = Rq[i:i+1, :]
        Krrp += K[i] * Rpi.T @ Rpi
        Lrrq += L[i] * Rqi.T @ Rqi
        Krxip += K[i] * Rpi * Xh[i]**(p+1)
        for j in range(N):
            if j != i:
                Krxp += K[i] * Rpi * Xh[j]**(p+1)

    EKrrp = Krrp / N
    EKrxp = Krxp / (N * (N - 1))
    EKrxip = Krxip / N
    ELrrq = Lrrq / N

    # Compute q terms
    q1 = q2 = q3 = q4 = q6 = q8 = q9 = q10 = q11 = q12 = q3a = 0
    q5a = np.zeros((1, q+1))
    q5b = np.zeros((q+1, 1))
    q7a = np.zeros((1, q+1))
    q7b = np.zeros((q+1, q+1))
    q7c = np.zeros((q+1, 1))

    for i in range(N):
        Rpi = Rp[i:i+1, :]
        Rqi = Rq[i:i+1, :]

        q1 += (lbc0[i] * res[i])**3

        lus1 = fact * iGp[deriv:deriv+1, :] @ (EKrrp - K[i] * Rpi.T @ Rpi) @ iGp @ (K[i] * Rpi.T)
        T1 = fact * iGp[deriv:deriv+1, :] @ ((EKrrp - K[i] * Rpi.T @ Rpi) @ iGp @ Lp1.reshape(-1, 1) @ ep1.T) @ (iGq @ (L[i] * Rqi.T))
        T2 = fact * iGp[deriv:deriv+1, :] @ ((K[i] * Rpi * Xh[i]**(p+1) - EKrxip).T) @ ep1.T @ (iGq @ (L[i] * Rqi.T))
        T3 = fact * iGp[deriv:deriv+1, :] @ ((Lp1.reshape(-1, 1) @ ep1.T @ iGq) @ (ELrrq - L[i] * Rqi.T @ Rqi)) @ (iGq @ (L[i] * Rqi.T))
        lbc1 = lus1 - rho**(p+1) * (T1 + T2 + T3)

        q2 += lbc1.flatten()[0] * lbc0[i] * res[i]**2
        q3 += lbc0[i]**4 * (res[i]**4 - vx[i]**2)
        q4 += lbc0[i]**2 * (Rqi @ iGq @ (L[i] * Rqi.T)).flatten()[0] * res[i]**2
        q5a += lbc0[i]**3 * (Rqi @ iGq) * res[i]**2
        q5b += L[i] * Rqi.T * lbc0[i] * res[i]**2
        q7a += lbc0[i] * res[i]**2 * L[i] * Rqi @ iGq
        q7b += lbc0[i]**2 * Rqi.T @ Rqi @ iGq
        q7c += lbc0[i] * res[i]**2 * L[i] * Rqi.T
        q8 += (lbc0[i] * res[i])**4
        q9 += (lbc0[i]**2 * vx[i] - h * s2) * (lbc0[i] * res[i])**2
        q12 += (lbc0[i]**2 * vx[i] - h * s2)**2
        q3a += (lbc0[i] * res[i])**3

        for j in range(N):
            if j != i:
                Rpj = Rp[j:j+1, :]
                Rqj = Rq[j:j+1, :]

                lus1 = fact * iGp[deriv:deriv+1, :] @ (EKrrp - K[j] * Rpj.T @ Rpj) @ iGp @ (K[i] * Rpi.T)
                T1 = fact * iGp[deriv:deriv+1, :] @ ((EKrrp - K[j] * Rpj.T @ Rpj) @ iGp @ Lp1.reshape(-1, 1) @ ep1.T) @ (iGq @ (L[i] * Rqi.T))
                T2 = fact * iGp[deriv:deriv+1, :] @ ((K[j] * Rpj * Xh[i]**(p+1) - EKrxp).T) @ ep1.T @ (iGq @ (L[i] * Rqi.T))
                T3 = fact * iGp[deriv:deriv+1, :] @ ((Lp1.reshape(-1, 1) @ ep1.T @ iGq) @ (ELrrq - L[j] * Rqj.T @ Rqj)) @ (iGq @ (L[i] * Rqi.T))
                lbc1 = lus1 - rho**(p+1) * (T1 + T2 + T3)

                q10 += lbc1.flatten()[0] * lbc0[i] * (lbc0[j] * res[j])**2 * vx[i]
                q11 += lbc1.flatten()[0] * lbc0[i] * (lbc0[j]**2 * vx[j] - h * s2) * res[i]**2
                q6 += lbc0[i]**2 * (Rqi @ iGq @ (L[j] * Rqj.T)).flatten()[0]**2 * res[j]**2

    Eq1 = (q1 / (N * h))**2
    Eq2 = q2 / (N * h)
    Eq3 = q3 / (N * h)
    Eq4 = q4 / (N * h)
    Eq5 = (q5a / (N * h)) @ (q5b / (N * h))
    Eq6 = q6 / (N * (N - 1) * h**2)
    Eq7 = (q7a / (N * h)) @ (q7b / (N * h)) @ (q7c / (N * h))
    Eq8 = q8 / (N * h)
    Eq9 = q9 / (N * h)
    Eq10 = q10 / (N * (N - 1) * h**2)
    Eq11 = q11 / (N * (N - 1) * h**2)
    Eq12 = q12 / (N * h)

    z = 1.959964
    pz = 0.05844507

    Eq5 = Eq5.flatten()[0] if hasattr(Eq5, 'flatten') else Eq5
    Eq7 = Eq7.flatten()[0] if hasattr(Eq7, 'flatten') else Eq7

    q1bc = pz * (
        Eq1 * (z**3/3 + 7*z/4 + s2*z*(z**2 - 3)/4) / s2**3
        + Eq2 * (-z*(z**2 - 3)/2) / s2
        + Eq3 * (z*(z**2 - 3)/8) / s2**2
        - Eq4 * (z*(z**2 - 1)/2) / s2
        - Eq5 * (z*(z**2 - 1)) / s2**2
        + Eq6 * (z*(z**2 - 1)/4) / s2
        + Eq7 * (z*(z**2 - 1)/2) / s2**2
        + Eq8 * (-z*(z**2 - 3)/24) / s2**2
        + Eq9 * (z*(z**2 - 1)/4) / s2**2
        + Eq10 * (z*(z**2 - 3)) / s2**2
        + Eq11 * (-z) / s2**2
        + Eq12 * (-z*(z**2 + 1)/8) / s2**2
    )

    q2bc = -pz * z / (2 * s2)

    Eq3a = q3a / (N * h)
    q3bc = pz * Eq3a / (s2**2) * (z**3 / 3)

    q1rbc = 2 * q1bc / pz
    q2rbc = 2 * q2bc / pz
    q3rbc = 2 * q3bc / pz

    return {'q1rbc': q1rbc, 'q2rbc': q2rbc, 'q3rbc': q3rbc}
