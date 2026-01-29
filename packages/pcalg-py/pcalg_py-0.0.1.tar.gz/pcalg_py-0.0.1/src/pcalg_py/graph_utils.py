
import numpy as np

def udag2pdagRelaxed(gInput: np.ndarray, sepset: list, verbose: bool = False, solve_confl: bool = False, 
                     orientCollider: bool = True, rules: list = [True, True, True]) -> np.ndarray:
    """
    Orient edges in the Skeleton to form a PDAG.
    
    Args:
        gInput: Adjacency matrix of the skeleton (symmetric, boolean or 0/1).
        sepset: Separating sets identified during skeleton phase.
        
    Returns:
        pdag: Adjacency matrix of the estimated PDAG.
              1 at [i,j] and 0 at [j,i] => i -> j
              1 at [i,j] and 1 at [j,i] => i - j
              2 means bi-directed or conflict (depending on interpretation), usually treated as undirected in simple output.
    """
    p = gInput.shape[0]
    pdag = gInput.astype(int) # 1 for edge, 0 for no edge
    
    # Orient Colliders
    if orientCollider:
        # ind <- which(g == 1, arr.ind = TRUE)
        ind = np.argwhere(gInput == 1)
        # Match R's column-major order
        ind = ind[np.lexsort((ind[:,0], ind[:,1]))]
        
        for i in range(len(ind)):
            x, y = ind[i]
            # allZ <- setdiff(which(g[y, ] == 1), x) ## x - y - z
            # Neighbors of y, excluding x
            allZ = np.where(gInput[y, :] == 1)[0]
            allZ = allZ[allZ != x]
            
            for z in allZ:
                # Check collider condition: x and z are NOT adjacent
                if gInput[x, z] == 0:
                    # Check if y is NOT in sepset(x, z) and NOT in sepset(z, x)
                    sepset_xz = sepset[x][z]
                    sepset_zx = sepset[z][x]
                    
                    y_in_sepset = False
                    if sepset_xz is not None and y in sepset_xz:
                        y_in_sepset = True
                    if sepset_zx is not None and y in sepset_zx:
                        y_in_sepset = True
                        
                    if not y_in_sepset:
                        # Orient x -> y <- z
                        # Don't solve conflicts for now (simplify) unless asked
                        if not solve_confl:
                             pdag[x, y] = 1
                             pdag[z, y] = 1
                             pdag[y, x] = 0
                             pdag[y, z] = 0
                        else:
                             # orientConflictCollider logic
                             pass 
                             
    # Rules 1-3
    while True:
        old_pdag = pdag.copy()
        
        if rules[0]:
            pdag = rule1(pdag, solve_confl, verbose)
        if rules[1]:
            pdag = rule2(pdag, solve_confl, verbose)
        if rules[2]:
            pdag = rule3(pdag, solve_confl, verbose)
            
        if np.array_equal(pdag, old_pdag):
            break
            
    return pdag

def rule1(pdag: np.ndarray, solve_confl: bool, verbose: bool):
    """
    Rule 1: a -> b - c implies a -> b -> c if a, c not adjacent.
    """
    # Search for directed edges a -> b
    # pdag[a,b]=1, pdag[b,a]=0
    ind = np.argwhere((pdag == 1) & (pdag.T == 0))
    ind = ind[np.lexsort((ind[:,0], ind[:,1]))]
    
    for i in range(len(ind)):
        a, b = ind[i]
        
        # Find undirected neighbors of b: b - c
        # pdag[b,c]=1, pdag[c,b]=1
        # Also c must not be adjacent to a
        
        # c such that (b->c or b-c) and (c->b or c-b) -> undirected is both 1
        isC = np.where((pdag[b, :] == 1) & (pdag[:, b] == 1) &
                       (pdag[a, :] == 0) & (pdag[:, a] == 0))[0]
                       
        if len(isC) > 0:
            for c in isC:
                # Orient b -> c
                if not solve_confl or (pdag[b, c] == 1 and pdag[c, b] == 1):
                    pdag[b, c] = 1
                    pdag[c, b] = 0
                    if verbose:
                        print(f"Rule 1: {a} -> {b} -> {c}")
    return pdag

def rule2(pdag: np.ndarray, solve_confl: bool, verbose: bool):
    """
    Rule 2: a -> c -> b with a - b implies a -> b
    """
    # Search for a - b
    ind = np.argwhere((pdag == 1) & (pdag.T == 1))
    ind = ind[np.lexsort((ind[:,0], ind[:,1]))]
    
    for i in range(len(ind)):
        a, b = ind[i]
        
        # Search for c such that a -> c -> b
        # a->c: pdag[a,c]=1, pdag[c,a]=0
        # c->b: pdag[c,b]=1, pdag[b,c]=0
        
        isC = np.where((pdag[a, :] == 1) & (pdag[:, a] == 0) &
                       (pdag[:, b] == 1) & (pdag[b, :] == 0))[0]
                       
        if len(isC) > 0:
            if not solve_confl or (pdag[a, b] == 1 and pdag[b, a] == 1):
                 pdag[a, b] = 1
                 pdag[b, a] = 0
                 if verbose:
                     print(f"Rule 2: {a} -> {b} due to chain {a}->{isC}->{b}")
                     
    return pdag

def rule3(pdag: np.ndarray, solve_confl: bool, verbose: bool):
    """
    Rule 3: a - b, a - c1, a - c2, c1 -> b, c2 -> b, c1, c2 not connected.
    Implies a -> b.
    """
    ind = np.argwhere((pdag == 1) & (pdag.T == 1))
    ind = ind[np.lexsort((ind[:,0], ind[:,1]))]
    
    for i in range(len(ind)):
        a, b = ind[i]
        
        # Find c such that a - c and c -> b
        # a-c: pdag[a,c]=1, pdag[c,a]=1
        # c->b: pdag[c,b]=1, pdag[b,c]=0
        
        c_candidates = np.where((pdag[a, :] == 1) & (pdag[:, a] == 1) &
                                (pdag[:, b] == 1) & (pdag[b, :] == 0))[0]
                                
        if len(c_candidates) >= 2:
            import itertools
            for c1, c2 in itertools.combinations(c_candidates, 2):
                # c1 and c2 not connected
                if pdag[c1, c2] == 0 and pdag[c2, c1] == 0:
                    if not solve_confl or (pdag[a, b] == 1 and pdag[b, a] == 1):
                        pdag[a, b] = 1
                        pdag[b, a] = 0
                        if verbose:
                            print(f"Rule 3: {a} -> {b}")
                        break
                        
    return pdag
