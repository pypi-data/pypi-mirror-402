
# pcalg-py

A Python implementation of the PC algorithm for causal structure learning, ported from the R package `pcalg`.

This package provides a strict re-implementation of the PC algorithm (Spirtes et al., 2000) and related functions (Skeleton estimation, separation sets, etc.), verified to match the reference R implementation exactly.

## Features

*   **PC Algorithm**: Estimate the equivalence class of a DAG (Patterns/PDAG) from observational data.
*   **Skeleton Estimation**: Infer the undirected skeleton graph.
*   **Separation Sets**: Record condition sets that d-separate variables.
*   **Parsimonious**: Strict port of the `stable` method from `pcalg` ensuring order-independence.
*   **Verified**: Numerically comparable to R output (see `COMPARISON_REPORT.md`).

## Installation

You can install the package via pip (after building or if published):

```bash
pip install pcalg-py
```

Or install from source:

```bash
git clone https://github.com/yourusername/pcalg-py.git
cd pcalg-py
pip install .
```

## Usage

```python
import numpy as np
import pandas as pd
from pcalg_py.pc import pc
from pcalg_py.indep_test import gaussCItest, SuffStat

# 1. Prepare Data (Correlation matrix and sample size)
# Example: Generate random data
np.random.seed(42)
data = np.random.randn(100, 5)
C = np.corrcoef(data.T)
n = 100
labels = [str(i) for i in range(5)]

# 2. Create Sufficient Statistics object
suffStat = SuffStat(C=C, n=n)

# 3. Run PC Algorithm
# alpha is the significance level for the independence test
res = pc(suffStat, gaussCItest, alpha=0.01, labels=labels, verbose=True)

# 4. Access Results
graph = res["graph"] # NetworkX DiGraph (CPDAG)
pdag_matrix = res["pdag_matrix"]
sepset = res["skel"]["sepset"]

print("Edges:", graph.edges())
```

## Structure

*   `src/pcalg_py/`: Source code.
*   `tests/`: Verification scripts comparing R vs Python.

## License

GPLv2 (Derived from `pcalg` R package)
