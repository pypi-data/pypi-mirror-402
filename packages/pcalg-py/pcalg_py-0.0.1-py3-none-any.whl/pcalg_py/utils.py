
import numpy as np
from scipy.stats import norm
from typing import List, Union, Dict, Any, Tuple
import math

def getNextSet(n: int, k: int, set_idx: List[int]) -> Tuple[List[int], bool]:
    """
    Generate the next set in a list of all possible sets of size k out of 1:n (0:n-1 in Python).
    
    Args:
        n: Total number of elements.
        k: Size of the subset.
        set_idx: Current subset indices (0-based).
        
    Returns:
        nextSet: The next subset.
        wasLast: Boolean indicating if the returned set was the last one (so this call wraps around or finishes).
                 However, following the R logic:
                 R code:
                   chInd <- k - (zeros <- sum((seq(n-k+1,n)-set) == 0))
                   wasLast <- (chInd == 0)
                 
                 If set is None, we return the first set.
    """
    # In R, 1-based indexing is used. inputs are 1:n.
    # Here we assume 0-based indexing for external interface, but might convert internally if needed to match logic strictly.
    # Let's write it natively for 0-based to avoid confusion.
    
    # R logic translation:
    # set is vector of length k.
    # seq(n-k+1, n) in R corresponds to range(n-k, n) in Python (sorted).
    
    # Check if set is the last one: [n-k, n-k+1, ..., n-1]
    
    # Implementation based on R's logic but 0-indexed:
    # chInd <- k - sum( ( (n-k .. n-1) - set ) == 0 )
    # Check elements from right to left, find first one that is NOT at its maximum value.
    
    # If set is not provided, return the first one [0, 1, ..., k-1]
    if set_idx is None:
         return list(range(k)), False

    set_idx = sorted(set_idx)
    
    # Find the rightmost element that can be incremented
    # Max value for position i (0-indexed) is n - k + i
    
    chInd = -1
    for i in range(k - 1, -1, -1):
        if set_idx[i] < n - k + i:
            chInd = i
            break
            
    if chInd == -1:
        # This was the last set
        return set_idx, True
    
    # Increment the found element diff
    set_idx[chInd] += 1
    
    # Reset following elements
    # for j from chInd+1 to k-1: set[j] = set[j-1] + 1
    for i in range(chInd + 1, k):
        set_idx[i] = set_idx[i-1] + 1
        
    return set_idx, False

def pseudoinverse(m: np.ndarray) -> np.ndarray:
    return np.linalg.pinv(m)

def pcorOrder(i: int, j: int, k: List[int], C: np.ndarray, cut_at: float = 0.9999999) -> float:
    """
    Compute partial correlation of i and j given k.
    """
    if len(k) == 0:
        r = C[i, j]
    elif len(k) == 1:
        # r <- (C[i, j] - C[i, k] * C[j, k])/sqrt((1 - C[j, k]^2) * (1 - C[i, k]^2))
        k_idx = k[0]
        r = (C[i, j] - C[i, k_idx] * C[j, k_idx]) / math.sqrt((1 - C[j, k_idx]**2) * (1 - C[i, k_idx]**2))
    else:
        # PM <- pseudoinverse(C[c(i,j,k), c(i,j,k)])
        # r <- -PM[1, 2]/sqrt(PM[1, 1] * PM[2, 2])
        indices = [i, j] + k
        # np.ix_ works for extracting submatrix
        sub_C = C[np.ix_(indices, indices)]
        PM = pseudoinverse(sub_C)
        # In R: PM[1, 2] is row 1, col 2 -> Python PM[0, 1]
        r = -PM[0, 1] / math.sqrt(PM[0, 0] * PM[1, 1])
        
    if np.isnan(r):
        return 0.0
    else:
        return min(cut_at, max(-cut_at, r))

def logQ1pm(r: float) -> float:
    """
    Computes log((1+r)/(1-r))
    """
    if r >= 1.0:
        return float('inf')
    if r <= -1.0:
        return float('-inf')
        
    return math.log((1 + r) / (1 - r))

def zStat(x: int, y: int, S: List[int], C: np.ndarray, n: int) -> float:
    """
    Fisher's z-transform statistic of partial corr.(x,y | S)
    """
    r = pcorOrder(x, y, S, C)
    
    # res <- sqrt(n - length(S) - 3) * 0.5 * logQ1pm(r)
    try:
        factor = math.sqrt(n - len(S) - 3)
    except ValueError:
        # n is too small
        return 0.0
        
    val = logQ1pm(r)
    res = factor * 0.5 * val
    
    if math.isnan(res):
        return 0.0
    return res

