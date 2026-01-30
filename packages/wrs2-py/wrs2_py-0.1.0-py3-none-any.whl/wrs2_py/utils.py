
import numpy as np

def elimna(x):
    """
    Remove missing values (NaNs) from a numpy array or list.
    """
    if isinstance(x, list):
        x = np.array(x)
    return x[~np.isnan(x)]

def list2mat(x):
    """
    Convert a list of arrays (irregular) to a matrix?
    In R `matl` creates a matrix with NAs padding.
    In Python, we usually stick to list of arrays for ragged data.
    """
    pass # Not strictly needed if we handle list of arrays
