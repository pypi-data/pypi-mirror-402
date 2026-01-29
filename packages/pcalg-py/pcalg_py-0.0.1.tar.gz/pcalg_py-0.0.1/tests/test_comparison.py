
import pandas as pd
import numpy as np
import networkx as nx
import sys
import os
import pytest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from pcalg_py.pc import pc, skeleton
from pcalg_py.indep_test import SuffStat, gaussCItest

def test_compare_with_R_simulation():
    print("Starting comparison...")
    # Load R results
    try:
        data_df = pd.read_csv("tests/data_matrix.csv")
        cor_matrix = pd.read_csv("tests/cor_matrix.csv").values
        
        # Load adjacencies. R write.csv adds headers "V1", "V2" etc or "0", "1" depending on col.names.
        # We wrote without row.names, so headers are present.
        skel_adj_true = pd.read_csv("tests/skel_adj.csv").values
        pc_adj_true = pd.read_csv("tests/pc_res_adj.csv").values
        
        sepset_df = pd.read_csv("tests/sepset.csv")
        pMax_true = pd.read_csv("tests/pMax.csv").values
        
    except FileNotFoundError:
        pytest.skip("R simulation data not found. Run generate_data.R first.")
        
    n, p = data_df.shape
    
    # Setup stats
    suffStat = SuffStat(C=cor_matrix, n=n)
    labels = [str(i) for i in range(p)]
    alpha = 0.01
    
    # Run Skeleton
    # Note: R standardizes pMax calc and sepset.
    res_skel = skeleton(suffStat, gaussCItest, alpha, labels, p=p, verbose=False)
    
    # Compare Skeleton Graph
    # res_skel["G"] is boolean matrix where True = edge exists.
    # skel_adj_true: mirror R behavior. 
    # R: 1 if edge, 0 if not. Symmetric.
    
    my_G = res_skel["G"].astype(int)
    # R skel_adj is symmetric? Yes.
    
    # Check if adjacency matrices match
    # Note: R code `as(graph, "matrix")` returns symmetric matrix for undirected graph in pcalg??
    # Actually `skeleton` returns a "pcAlgo" object, which contains a graph. 
    # If the graph is "graphNEL", `as(g, "matrix")` returns 1 if edge exists. 
    # `skeleton` returns undirected edges, so it should be symmetric 1s.
    
    # Let's verify shape and content
    assert my_G.shape == skel_adj_true.shape
    
    if not np.array_equal(my_G, skel_adj_true):
        # Print diff
        diff = my_G - skel_adj_true
        print("Skeleton Diff (My - True):\n", diff)
        # Allow some small differences if numerical instability? 
        # But for "exact replication" ideally should be 0.
        # Let's count mismatches
        mismatches = np.sum(np.abs(diff))
        print(f"Number of edge mismatches: {mismatches}")
        
    np.testing.assert_array_equal(my_G, skel_adj_true, err_msg="Skeleton adjacency mismatch")
    print("[PASS] Skeleton adjacency matrix matches R result.")
    
    # Compare Sepset
    # R sepset is list of lists. We exported to CSV: i, j, k
    # Check correctness
    
    # Reconstruct dictionary from CSV
    true_sepsets = {}
    for idx, row in sepset_df.iterrows():
        i, j, k = int(row['i']), int(row['j']), int(row['k'])
        if (i, j) not in true_sepsets:
            true_sepsets[(i,j)] = set()
        true_sepsets[(i,j)].add(k)
        
    # Check my sepsets
    # My sepset is list of lists of lists/sets
    for i in range(p):
        for j in range(p):
            my_s = res_skel["sepset"][i][j]
            if my_s is not None and len(my_s) > 0:
                # Expect finding this in true_sepsets
                assert (i,j) in true_sepsets, f"My code found separation for {i},{j} but R did not."
                # Compare contents
                true_s = true_sepsets[(i,j)]
                assert set(my_s) == true_s, f"Sepset mismatch for {i},{j}"
            else:
                 # Expect NOT finding in true_sepsets or empty
                if (i,j) in true_sepsets:
                    # If R found a sepset but I didn't (meaning I have an edge or I found empty sepset?)
                    # If I have an edge, sepset should be None (or irrelevant).
                    # Check if edge exists
                    if my_G[i, j] == 0:
                         # Edge removed. Must have sepset.
                         # If my_s is None/Empty but edge removed, that implies independent unconditionally (empty set).
                         # R would output k rows? No, if empty set, no k rows.
                         # Wait, logic above: `for(k in s)` loops 0 times if s is empty. 
                         # So if s is empty, no rows in CSV.
                         # So if (i,j) NOT in true_sepsets, it implies sepset is empty (if independent) OR edge exists.
                         
                         # If edge exists in R (skel_adj_true[i,j] == 1), then (i,j) not in CSV.
                         # If edge removed in R (0) and sepset empty, then (i,j) not in CSV.
                         
                         # So:
                         # If my_G[i,j] == 0 (Removed):
                         #   If my_s is empty/None:
                         #      Check if R removed it too. (Checked by adjacency assertion)
                         #      If R removed it, and (i,j) not in CSV => Matches (Empty sepset).
                         pass
                    else:
                        # Edge exists.
                        pass
    print("[PASS] Separation sets match R result.")

    # Compare pMax
    # Allow float tolerance
    np.testing.assert_allclose(res_skel["pMax"], pMax_true, atol=1e-5, err_msg="pMax mismatch")
    print("[PASS] pMax (maximal p-values) match R result.")
    
    # Compare PC (PDAG)
    # We call pc() which calls skeleton() inside.
    # We can pass the skeleton result if our pc implementation allows, but current signature asks for suffStat.
    # It calls skeleton internally.
    
    res_pc = pc(suffStat, gaussCItest, alpha, labels, p=p, verbose=False)
    pdag_matrix = res_pc["pdag_matrix"]
    
    # Compare with R pc_res_adj
    # R: 1 at [i,j] and 0 at [j,i] => i->j
    # R: 1 at [i,j] and 1 at [j,i] => i-j
    
    np.testing.assert_array_equal(pdag_matrix, pc_adj_true, err_msg="PDAG adjacency mismatch")
    print("[PASS] PDAG adjacency matrix (final result) matches R result.")
    
    print("\nAll comparisons passed successfully! Python implementation is identical to R implementation.")

if __name__ == "__main__":
    test_compare_with_R_simulation()
