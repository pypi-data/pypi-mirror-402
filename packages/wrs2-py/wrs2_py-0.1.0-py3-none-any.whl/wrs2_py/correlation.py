
import numpy as np
from scipy import stats
from .location import winval, pbos
from .utils import elimna

def wincor(x, y, tr=0.2):
    """
    Compute the Winsorized correlation and covariance between x and y.
    """
    x = np.array(x)
    y = np.array(y)
    if len(x) != len(y):
        raise ValueError("Lengths of vectors are not equal")
    
    m1 = np.column_stack([x, y])
    m1 = m1[~np.any(np.isnan(m1), axis=1)]
    n = len(m1)
    x = m1[:, 0]
    y = m1[:, 1]
    
    xvec = winval(x, tr)
    yvec = winval(y, tr)
    
    wcor = np.corrcoef(xvec, yvec)[0, 1]
    # R var(xvec, yvec) is covariance
    wcov = np.cov(xvec, yvec, ddof=1)[0, 1]
    
    return {"cor": wcor, "cov": wcov}

def winall(m, tr=0.2):
    """
    Compute the Winsorized correlation and covariance matrix for an n by p matrix m.
    """
    m = np.array(m)
    n, p = m.shape
    wcor = np.eye(p)
    wcov = np.zeros((p, p))
    
    for i in range(p):
        for j in range(i, p):
            res = wincor(m[:, i], m[:, j], tr=tr)
            wcor[i, j] = wcor[j, i] = res["cor"]
            wcov[i, j] = wcov[j, i] = res["cov"]
            
    return {"cor": wcor, "cov": wcov}

def pbcor(x, y, beta=0.2):
    """
    Compute the percentage bend correlation between x and y.
    """
    x = np.array(x)
    y = np.array(y)
    m1 = np.column_stack([x, y])
    m1 = m1[~np.any(np.isnan(m1), axis=1)]
    n = len(m1)
    if n == 0:
        return {"cor": np.nan, "test": np.nan, "p_value": np.nan, "n": 0}
    x = m1[:, 0]
    y = m1[:, 1]
    
    med_x = np.median(x)
    abs_diff_x = np.sort(np.abs(x - med_x))
    idx_x = int(np.floor((1 - beta) * n)) - 1
    if idx_x < 0: idx_x = 0
    omhatx = abs_diff_x[idx_x]
    
    med_y = np.median(y)
    abs_diff_y = np.sort(np.abs(y - med_y))
    idx_y = int(np.floor((1 - beta) * n)) - 1
    if idx_y < 0: idx_y = 0
    omhaty = abs_diff_y[idx_y]
    
    a = (x - pbos(x, beta)) / omhatx
    b = (y - pbos(y, beta)) / omhaty
    
    a = np.clip(a, -1, 1)
    b = np.clip(b, -1, 1)
    
    pb_cor = np.sum(a * b) / np.sqrt(np.sum(a**2) * np.sum(b**2))
    test_stat = pb_cor * np.sqrt((n - 2) / (1 - pb_cor**2))
    p_value = 2 * (1 - stats.t.cdf(np.abs(test_stat), n - 2))
    
    return {"cor": pb_cor, "test": test_stat, "p_value": p_value, "n": n}
