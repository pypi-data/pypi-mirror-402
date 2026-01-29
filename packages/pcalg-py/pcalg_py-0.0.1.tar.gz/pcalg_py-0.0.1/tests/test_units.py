
import unittest
import numpy as np
from pcalg_py.utils import getNextSet, pcorOrder, zStat, logQ1pm

class TestUtils(unittest.TestCase):
    def test_getNextSet(self):
        # Case 1: n=5, k=2
        # Sets: {0,1}, {0,2}, {0,3}, {0,4}, {1,2}, ...
        # Indices are 0-based.
        n = 5
        k = 2
        
        s = list(range(k)) # [0, 1]
        count = 1
        
        while True:
            # print(s)
            s, wasLast = getNextSet(n, k, s)
            if wasLast:
                break
            count += 1
            
        # Total combinations: 5 choose 2 = 10
        self.assertEqual(count, 10)
        
        # Test specific transition
        # [0, 4] -> [1, 2]
        s = [0, 4]
        s_next, last = getNextSet(n, k, s)
        self.assertEqual(s_next, [1, 2])
        self.assertFalse(last)

        # Test last
        # [3, 4] -> should be last
        s = [3, 4]
        s_next, last = getNextSet(n, k, s)
        self.assertTrue(last)
        
    def test_logQ1pm(self):
        self.assertAlmostEqual(logQ1pm(0), 0)
        self.assertEqual(logQ1pm(1.0), float('inf'))
        self.assertEqual(logQ1pm(-1.0), float('-inf'))
        # r = 0.5 -> log(1.5/0.5) = log(3) approx 1.0986
        self.assertAlmostEqual(logQ1pm(0.5), np.log(3))

    def test_pcorOrder(self):
        # 3 variables.
        # x, y, z.
        # If x, y indep given z.
        # Partial corr(x,y|z) should be 0.
        
        # Covariance matrix for X -> Z -> Y
        # X ~ N(0,1)
        # Z = X + e1
        # Y = Z + e2
        # Cor(X, Z) = 1 / sqrt(2) approx 0.707
        # Cor(Z, Y) = 0.707
        # Cor(X, Y) = 0.5
        
        C = np.array([
            [1.0, 0.5, 0.70710678],
            [0.5, 1.0, 0.70710678],
            [0.70710678, 0.70710678, 1.0]
        ])
        
        # pcor(0, 1 | 2) should be 0 (approx)
        r = pcorOrder(0, 1, [2], C)
        self.assertAlmostEqual(r, 0.0, places=5)
        
        # pcor(0, 1) should be 0.5
        r = pcorOrder(0, 1, [], C)
        self.assertAlmostEqual(r, 0.5, places=5)

if __name__ == '__main__':
    unittest.main()
