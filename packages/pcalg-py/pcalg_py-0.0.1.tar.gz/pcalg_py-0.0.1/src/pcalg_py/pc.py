
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Union, Callable, Optional, Tuple
from pcalg_py.indep_test import SuffStat
from pcalg_py.utils import getNextSet

def skeleton(suffStat: SuffStat, indepTest: Callable, alpha: float, labels: List[str], p: int = None,
             fixedGaps: np.ndarray = None, fixedEdges: np.ndarray = None, 
             NAdelete: bool = True, m_max: float = float('inf'), numCores: int = 1, verbose: bool = False):
    """
    Perform undirected part of PC-Algorithm.
    Estimate skeleton of DAG given data.
    """
    if p is None:
        p = len(labels)
        
    seq_p = list(range(p))
    
    # G := !fixedGaps. True means edge exists (to be investigated).
    if fixedGaps is None:
        G = np.ones((p, p), dtype=bool)
    else:
        G = ~fixedGaps
        
    np.fill_diagonal(G, False)
    
    if fixedEdges is None:
        fixedEdges = np.zeros((p, p), dtype=bool)
        
    # sepset: list of lists. sepset[i][j] contains the separating set for i, j.
    # In R: sepset[[x]][[y]]
    sepset = [[None for _ in range(p)] for _ in range(p)]
    
    pMax = np.full((p, p), -np.inf)
    np.fill_diagonal(pMax, 1)
    
    done = False
    ord_val = 0
    n_edgetests = {} 
    
    while not done and np.any(G) and ord_val <= m_max:
        n_edgetests[ord_val] = 0
        done = True
        
        # ind <- which(G, arr.ind = TRUE) -> Use argwhere
        # Note: we need to handle the undirected nature. R iterates over all edges.
        # But G is symmetric usually in concept, but R implementation iterates over all G[y,x].
        
        # Let's get all True indices
        ind = np.argwhere(G)
        
        # Order by first column to match R (optional but good for consistency)
        ind = ind[np.argsort(ind[:, 0])]
        
        remEdges = len(ind)
        if verbose:
            print(f"Order={ord_val}; remaining edges:{remEdges}")
            
        # For stability, R splits G.l in "stable" method. We will implement standard logic first
        # which corresponds to "original" or "stable" depending on how we handle `G` updates.
        # The provided R code handles "stable" by default using `G.l` copy.
        # "stable": Order-independent version: Compute the adjacency sets for any vertex
        # Then don't update when edges are deleted (during the current order).
        
        # Emulate "stable" method
        G_l = G.copy()
        
        for i in range(remEdges):
            x, y = ind[i]
            
            # if (G[y, x] && !fixedEdges[y, x])
            if G[y, x] and not fixedEdges[y, x]:
                
                # nbrsBool <- if(method == "stable") G.l[[x]] else G[,x]
                # In Python numpy: G_l[x, :] gives the row, which are neighbors of x
                nbrsBool = G_l[x, :].copy() 
                nbrsBool[y] = False
                
                nbrs = np.where(nbrsBool)[0]
                length_nbrs = len(nbrs)
                
                if length_nbrs >= ord_val:
                    if length_nbrs > ord_val:
                        done = False
                    
                    S = list(range(ord_val)) # Initial set indices from nbrs
                    # We need a way to iterate over subsets of size ord_val from nbrs.
                    # getNextSet returns indices into nbrs? No, getNextSet returns indices 
                    # relative to the set being chosen from?
                    # R: getNextSet(n, k, set) -> returns subset of 1:n.
                    # Here n = length_nbrs.
                    
                    # Initialize set idx
                    S_idx = list(range(ord_val))
                    
                    while True:
                        n_edgetests[ord_val] += 1
                        
                        # Map S_idx to actual nodes
                        S_nodes = [nbrs[idx] for idx in S_idx]
                        
                        pval = indepTest(x, y, S_nodes, suffStat)
                        
                        if verbose:
                            print(f"x={x}, y={y}, S={S_nodes}, pval={pval}")
                        
                        if np.isnan(pval):
                            pval = 1.0 if NAdelete else 0.0 # Standardize
                            
                        if pMax[x, y] < pval:
                            pMax[x, y] = pval
                            
                        if pval >= alpha:
                            # Independent
                            G[x, y] = False
                            G[y, x] = False
                            sepset[x][y] = S_nodes
                            break
                        else:
                            # Next set
                            S_idx, wasLast = getNextSet(length_nbrs, ord_val, S_idx)
                            if wasLast:
                                break
        
        ord_val += 1
        
    # Symmetrize pMax to match R behavior
    for i in range(p):
        for j in range(i + 1, p):
            val = max(pMax[i, j], pMax[j, i])
            pMax[i, j] = val
            pMax[j, i] = val

    # Transform G to NetworkX graph
    g_graph = nx.Graph()
    g_graph.add_nodes_from(range(p))
    
    # Add edges
    edges = np.argwhere(G)
    for u, v in edges:
        if u < v: # Add once
            g_graph.add_edge(u, v)
            
    # Relabel nodes
    mapping = {i: labels[i] for i in range(p)}
    g_graph = nx.relabel_nodes(g_graph, mapping)
            
    return {
        "graph": g_graph,
        "sepset": sepset,
        "pMax": pMax,
        "n_edgetests": n_edgetests,
        "G": G 
    }

def pc(suffStat: SuffStat, indepTest: Callable, alpha: float, labels: List[str], p: int = None,
       fixedGaps: np.ndarray = None, fixedEdges: np.ndarray = None, NAdelete: bool = True, m_max: float = float('inf'),
       u2pd: str = "relaxed", skel_method: str = "stable", conservative: bool = False, maj_rule: bool = False,
       solve_confl: bool = False, verbose: bool = False) -> Dict[str, Any]:
    
    # 1. Skeleton
    skel_res = skeleton(suffStat, indepTest, alpha, labels, p, fixedGaps, fixedEdges, NAdelete, m_max, verbose=verbose)
    G = skel_res["G"]
    sepset = skel_res["sepset"]
    
    # 2. Orientation
    # We will implement "relaxed" strategy (udag2pdagRelaxed) as it matches the default/common path in R code used.
    # Note: R's pc() calls udag2pdagRelaxed by default if u2pd="relaxed".
    
    from pcalg_py.graph_utils import udag2pdagRelaxed
    
    # Convert G (adj matrix) to some graph object suitable for orientation or pass matrix directly
    # udag2pdagRelaxed in R takes pcalg object or adjacency?
    # R: udag2pdagRelaxed(skel) where skel is the result of skeleton (pcAlgo class).
    # Inside, it extracts graph -> matrix.
    
    pdag = udag2pdagRelaxed(G, sepset, verbose=verbose, solve_confl=solve_confl)
    
    # Convert PDAG matrix to NetworkX DiGraph
    # pdag matrix: 1 means tail, 0 means head?
    # R: pdag[x,y]=1 and pdag[y,x]=0 means x -> y.
    #    pdag[x,y]=1 and pdag[y,x]=1 means x - y (undirected).
    #    pdag[x,y]=2 and pdag[y,x]=2 means x <-> y (bidirected/undirected conflicting?)
    
    g_out = nx.DiGraph() # Using DiGraph to represent mixed graph?
    # NetworkX doesn't natively support mixed graphs easily without custom attributes.
    # We will use DiGraph and add edges (u,v) and (v,u) for undirected.
    
    p = len(labels)
    g_out.add_nodes_from(labels)
    
    for i in range(p):
        for j in range(p):
            if pdag[i, j] == 1 and pdag[j, i] == 0:
                g_out.add_edge(labels[i], labels[j]) # i -> j
            elif pdag[i, j] == 1 and pdag[j, i] == 1:
                # Undirected
                # Add both ways or handle as undirected?
                # Usually standard to add both for "undirected" in DiGraph
                if not g_out.has_edge(labels[i], labels[j]):
                    g_out.add_edge(labels[i], labels[j])
                    g_out.add_edge(labels[j], labels[i])
            # What about 2?
            
    return {
        "graph": g_out,
        "skel": skel_res,
        "pdag_matrix": pdag
    }
