
import numpy as np
from scipy import stats, integrate
from .utils import elimna

def winval(x, tr=0.2):
    """
    Winsorize the data in the vector x.
    tr is the amount of Winsorization which defaults to .2.
    """
    x = np.array(x)
    y = np.sort(x)
    n = len(x)
    ibot = int(np.floor(tr * n)) # R: floor(tr*n)+1 (1-based) vs Python 0-based: index floor(tr*n) matches 
    # Example: n=10, tr=0.2. floor(2)=2. R: 3rd element (idx 2). Python: idx 2. Matches.
    itop = n - ibot - 1 # R: length(x)-ibot+1. 
    # Example: n=10, ibot_R=3. itop_R=10-3+1=8 (8th element, idx 7).
    # Python: ibot=2. itop = 10-2-1 = 7. Matches.
    
    xbot = y[ibot]
    xtop = y[itop]
    
    wv = np.where(x <= xbot, xbot, x)
    wv = np.where(wv >= xtop, xtop, wv)
    return wv

def winmean(x, tr=0.2, na_rm=False):
    if na_rm:
        x = elimna(x)
    return np.mean(winval(x, tr))

def winvar(x, tr=0.2, na_rm=False):
    if na_rm:
        x = elimna(x)
    y = winval(x, tr)
    return np.var(y, ddof=1) # R var uses n-1

def dnormvar(x):
    return (x**2) * stats.norm.pdf(x)

def winvarN(x, tr=0.2, na_rm=True): # R winvarN seems to assume removing NAs or the user does it? R: x=elimna(x) inside.
    x = elimna(x)
    cterm = None
    if tr == 0:
        cterm = 1.0
    elif tr == 0.1:
        cterm = 0.6786546
    elif tr == 0.2:
        cterm = 0.4120867
    
    if cterm is None:
        # cterm=area(dnormvar,qnorm(tr),qnorm(1-tr))+2*(qnorm(tr)^2)*tr
        q1 = stats.norm.ppf(tr)
        q2 = stats.norm.ppf(1 - tr)
        integral, _ = integrate.quad(dnormvar, q1, q2)
        cterm = integral + 2 * (q1**2) * tr
        
    return winvar(x, tr=tr) / cterm

def trim_mean(x, tr=0.2, na_rm=False):
    if na_rm:
        x = elimna(x)
    return stats.trim_mean(x, proportiontocut=tr)

def pbos(x, beta=0.2):
    """
    Compute the one-step percentage bend measure of location.
    """
    x = np.array(x)
    med_x = np.median(x)
    abs_diff = np.sort(np.abs(x - med_x))
    n = len(x)
    # R: floor((1-beta)*length(x))
    # Python 0-based index: floor((1-beta)*n) might be off by 1?
    # R: floor(0.8 * 10) = 8. 8th element (idx 7).
    # Python: idx 7 is 8th element. Matches.
    idx = int(np.floor((1 - beta) * n)) - 1
    if idx < 0: idx = 0
    omhatx = abs_diff[idx]
    
    psi = (x - med_x) / omhatx
    i1 = np.sum(psi < -1)
    i2 = np.sum(psi > 1)
    
    sx = np.where(psi < -1, 0, x)
    sx = np.where(psi > 1, 0, sx)
    
    pb_loc = (np.sum(sx) + omhatx * (i2 - i1)) / (n - i1 - i2)
    return pb_loc

def trimse(x, tr=0.2, na_rm=False):
    """
    Standard error of the trimmed mean.
    """
    if na_rm:
        x = elimna(x)
    n = len(x)
    return np.sqrt(winvar(x, tr)) / ((1 - 2 * tr) * np.sqrt(n))
