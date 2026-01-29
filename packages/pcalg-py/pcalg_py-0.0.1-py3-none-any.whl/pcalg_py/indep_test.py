
from typing import List, Union, Dict, Any
import numpy as np
from scipy.stats import norm
from pcalg_py.utils import zStat

class SuffStat:
    def __init__(self, C: np.ndarray, n: int):
        self.C = C
        self.n = n

def gaussCItest(x: int, y: int, S: List[int], suffStat: SuffStat) -> float:
    """
    Conditional independence test for Gaussian data.
    Returns the p-value of the null hypothesis: x and y are independent given S.
    """
    z = zStat(x, y, S, C=suffStat.C, n=suffStat.n)
    # 2*pnorm(abs(z), lower.tail = FALSE)
    # norm.sf is survival function (1 - cdf), equivalent to lower.tail = FALSE
    return 2 * norm.sf(abs(z))
