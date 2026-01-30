
import numpy as np
from scipy import stats
from .location import winvar, winvarN, trim_mean, winval
from .correlation import wincor, winall
from .utils import elimna

def t1way(groups, tr=0.2, alpha=0.05, nboot=100):
    """
    Heteroscedastic one-way ANOVA for trimmed means.
    groups: list of arrays/lists, each representing a group.
    """
    J = len(groups)
    groups = [elimna(g) for g in groups]
    nv = [len(g) for g in groups]
    
    h = []
    w = []
    xbar = []
    pts = []
    
    for g in groups:
        n = len(g)
        hi = n - 2 * int(np.floor(tr * n))
        wi = hi * (hi - 1) / ((n - 1) * winvar(g, tr))
        xbari = trim_mean(g, tr)
        
        h.append(hi)
        w.append(wi)
        xbar.append(xbari)
        pts.extend(g)
        
    h = np.array(h)
    w = np.array(w)
    xbar = np.array(xbar)
    pts = np.array(pts)
    
    u = np.sum(w)
    xtil = np.sum(w * xbar) / u
    A = np.sum(w * (xbar - xtil)**2) / (J - 1)
    B = 2 * (J - 2) * np.sum((1 - w / u)**2 / (h - 1)) / (J**2 - 1)
    
    test_stat = A / (B + 1)
    nu1 = J - 1
    nu2 = 1.0 / (3 * np.sum((1 - w / u)**2 / (h - 1)) / (J**2 - 1))
    p_value = 1.0 - stats.f.cdf(test_stat, nu1, nu2)
    
    # Effect size
    chkn = np.var(nv)
    if chkn == 0:
        top = np.var(xbar, ddof=1)
        bot = winvarN(pts, tr=tr)
        e_pow = top / bot
    else:
        # Bootstrapped for unequal n
        nn = min(nv)
        vals = []
        for _ in range(nboot):
            xdat = [np.random.choice(g, nn, replace=True) for g in groups]
            # Simple version of effect size for bootstrap
            xbars_boot = [trim_mean(g_boot, tr) for g_boot in xdat]
            top_boot = np.var(xbars_boot, ddof=1)
            pts_boot = np.concatenate(xdat)
            bot_boot = winvarN(pts_boot, tr=tr)
            vals.append(top_boot / bot_boot)
        e_pow = np.median(vals)
        
    return {
        "test": test_stat,
        "df1": nu1,
        "df2": nu2,
        "p_value": p_value,
        "effsize": np.sqrt(e_pow)
    }

def johan(cmat, vmean, vsqse, h, alpha=0.05):
    """
    Johansen's test of C mu = 0.
    """
    yvec = np.array(vmean).reshape(-1, 1)
    if vsqse.ndim == 1:
        vsqse = np.diag(vsqse)
    
    test_mat = cmat @ vsqse @ cmat.T
    invc = np.linalg.solve(test_mat, np.eye(test_mat.shape[0]))
    
    test_stat = (yvec.T @ cmat.T @ invc @ cmat @ yvec)[0, 0]
    
    R = vsqse @ cmat.T @ invc @ cmat
    A = np.sum(np.diag(R)**2 / (h - 1))
    
    df = cmat.shape[0]
    crit = stats.chi2.ppf(1 - alpha, df)
    crit = crit + (crit / (2 * df)) * A * (1 + 3 * crit / (df + 2))
    
    return {"teststat": test_stat, "crit": crit}

def t2way(groups, J, K, tr=0.2):
    """
    Two-way ANOVA for trimmed means.
    groups: list of J*K groups.
    J: number of levels for first factor.
    K: number of levels for second factor.
    """
    p = J * K
    tmeans = []
    h = []
    v = []
    
    for g in groups:
        g = elimna(g)
        n = len(g)
        tm = trim_mean(g, tr)
        hi = n - 2 * int(np.floor(tr * n))
        vi = (n - 1) * winvar(g, tr) / (hi * (hi - 1))
        
        tmeans.append(tm)
        h.append(hi)
        v.append(vi)
        
    tmeans = np.array(tmeans)
    h = np.array(h)
    v_diag = np.diag(v)
    
    ij = np.ones((1, J))
    ik = np.ones((1, K))
    
    # Contrast matrix for Factor A
    cj = np.eye(J - 1, J)
    for i in range(J - 1):
        cj[i, i+1] = -1
    cmat_a = np.kron(cj, ik)
    
    # Contrast matrix for Factor B
    ck = np.eye(K - 1, K)
    for i in range(K - 1):
        ck[i, i+1] = -1
    cmat_b = np.kron(ij, ck)
    
    # Contrast matrix for Interaction
    cmat_ab = np.kron(cj, ck)
    
    def get_p_value(cmat, tmeans, v_diag, h):
        alval = np.arange(1, 1000) / 1000.0
        for i, alpha in enumerate(alval):
            res = johan(cmat, tmeans, v_diag, h, alpha=alpha)
            if res["teststat"] > res["crit"]:
                return (i + 1) / 1000.0
        return 1.0

    qa_res = johan(cmat_a, tmeans, v_diag, h, 0.05) # dummy alpha for teststat
    pa = get_p_value(cmat_a, tmeans, v_diag, h)
    
    qb_res = johan(cmat_b, tmeans, v_diag, h, 0.05)
    pb = get_p_value(cmat_b, tmeans, v_diag, h)
    
    qab_res = johan(cmat_ab, tmeans, v_diag, h, 0.05)
    pab = get_p_value(cmat_ab, tmeans, v_diag, h)
    
    return {
        "Qa": qa_res["teststat"],
        "A_p_value": pa,
        "Qb": qb_res["teststat"],
        "B_p_value": pb,
        "Qab": qab_res["teststat"],
        "AB_p_value": pab
    }

def covmtrim(groups, tr=0.2):
    """
    Estimate the covariance matrix for the sample trimmed means.
    groups: list of arrays, all of same length.
    """
    p = len(groups)
    n = len(groups[0])
    h = n - 2 * int(np.floor(tr * n))
    covest = np.zeros((p, p))
    
    for j in range(p):
        covest[j, j] = (n - 1) * winvar(groups[j], tr) / (h * (h - 1))
        for k in range(j):
            res = wincor(groups[j], groups[k], tr=tr)
            covest[j, k] = (n - 1) * res["cov"] / (h * (h - 1))
            covest[k, j] = covest[j, k]
            
    return covest

def johansp(cmat, vmean, vsqse, h, J, K):
    """
    Johansen's test for split-plot design.
    """
    p = J * K
    yvec = np.array(vmean).reshape(-1, 1)
    test_mat = cmat @ vsqse @ cmat.T
    invc = np.linalg.solve(test_mat, np.eye(test_mat.shape[0]))
    
    test_stat = (yvec.T @ cmat.T @ invc @ cmat @ yvec)[0, 0]
    
    temp = np.zeros(J)
    for j in range(J):
        klow = j * K
        kup = (j + 1) * K
        Q = np.zeros((p, p))
        for k in range(klow, kup):
            Q[k, k] = 1
        mtem = vsqse @ cmat.T @ invc @ cmat @ Q
        temp[j] = (np.trace(mtem @ mtem) + np.trace(mtem)**2) / (h[j] - 1)
        
    A = 0.5 * np.sum(temp)
    df1 = cmat.shape[0]
    df2 = df1 * (df1 + 2) / (3 * A)
    cval = df1 + 2 * A - 6 * A / (df1 + 2)
    test_stat = test_stat / cval
    p_value = 1.0 - stats.f.cdf(test_stat, df1, df2)
    
    return {"teststat": test_stat, "p_value": p_value, "df1": df1, "df2": df2}

def bwtrim(groups, tr=0.2):
    """
    Between-within subjects ANOVA (split-plot) on trimmed means.
    groups: list of J groups, where each group is a list of K repeated measurements (arrays/matrices).
    Actually, WRS2 bwtrim takes data in a specific format. 
    In our case, let's assume 'groups' is a list of J groups, where each element is an (n_j, K) array.
    """
    J = len(groups)
    K = groups[0].shape[1]
    p = J * K
    
    tmeans = []
    h = []
    v = np.zeros((p, p))
    
    for j in range(J):
        group_data = groups[j] # (n_j, K)
        # remove rows with ANY NaN
        group_data = group_data[~np.any(np.isnan(group_data), axis=1)]
        n_j = len(group_data)
        hj = n_j - 2 * int(np.floor(tr * n_j))
        h.append(hj)
        
        # for each repeated measure
        tm_j = []
        g_list = []
        for k in range(K):
            tm = trim_mean(group_data[:, k], tr)
            tm_j.append(tm)
            g_list.append(group_data[:, k])
        
        tmeans.extend(tm_j)
        
        # block covariance
        klow = j * K
        kup = (j + 1) * K
        v[klow:kup, klow:kup] = covmtrim(g_list, tr=tr)
        
    tmeans = np.array(tmeans)
    h = np.array(h)
    
    ij = np.ones((1, J))
    ik = np.ones((1, K))
    cj = np.eye(J - 1, J)
    for i in range(J - 1):
        cj[i, i+1] = -1
    ck = np.eye(K - 1, K)
    for i in range(K - 1):
        ck[i, i+1] = -1
        
    # Factor A (Between)
    cmat_a = np.kron(cj, ik)
    qa = johansp(cmat_a, tmeans, v, h, J, K)
    
    # Factor B (Within)
    cmat_b = np.kron(ij, ck)
    qb = johansp(cmat_b, tmeans, v, h, J, K)
    
    # Interaction
    cmat_ab = np.kron(cj, ck)
    qab = johansp(cmat_ab, tmeans, v, h, J, K)
    
    return {
        "Qa": qa["teststat"], "A_p_value": qa["p_value"],
        "Qb": qb["teststat"], "B_p_value": qb["p_value"],
        "Qab": qab["teststat"], "AB_p_value": qab["p_value"]
    }

def rmanova(m1, tr=0.2):
    """
    One-way repeated measures ANOVA for trimmed means.
    m1: n by J matrix (wide format).
    """
    m1 = np.array(m1)
    # remove rows with ANY NaN (R: x=elimna(x) often implies this for matrices)
    m1 = m1[~np.any(np.isnan(m1), axis=1)]
    
    n, J = m1.shape
    g = int(np.floor(tr * n))
    
    m2 = np.zeros_like(m1)
    xvec = []
    for j in range(J):
        m2[:, j] = winval(m1[:, j], tr)
        xvec.append(trim_mean(m1[:, j], tr))
    
    xvec = np.array(xvec)
    xbar = np.mean(xvec)
    
    qc = (n - 2 * g) * np.sum((xvec - xbar)**2)
    
    # Sweep-out logic
    row_means = np.mean(m2, axis=1, keepdims=True)
    col_means = np.mean(m2, axis=0, keepdims=True)
    grand_mean = np.mean(m2)
    
    m3 = m2 - row_means - col_means + grand_mean
    qe = np.sum(m3**2)
    
    test_stat = qc / (qe / (n - 2 * g - 1))
    
    # Adjusted df
    v = winall(m1, tr=tr)["cov"]
    vbar = np.mean(v)
    vbard = np.mean(np.diag(v))
    vbarj = np.mean(v, axis=1)
    
    A = J * J * (vbard - vbar)**2 / (J - 1)
    B = np.sum(v**2) - 2 * J * np.sum(vbarj**2) + J * J * vbar**2
    ehat = A / B
    
    etil = (n * (J - 1) * ehat - 2) / ((J - 1) * (n - 1 - (J - 1) * ehat))
    etil = min(1.0, etil)
    
    df1 = (J - 1) * etil
    df2 = (J - 1) * etil * (n - 2 * g - 1)
    p_value = 1.0 - stats.f.cdf(test_stat, df1, df2)
    
    return {
        "test": test_stat,
        "df1": df1,
        "df2": df2,
        "p_value": p_value
    }
