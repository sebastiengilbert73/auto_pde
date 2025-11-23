import unittest
import numpy as np
from solver import PDESolver

class TestPDESolver(unittest.TestCase):
    def test_heat_equation_decay(self):
        # u_t = u_xx + u_yy
        # Domain: [0, pi] x [0, pi]
        # IC: sin(x)*sin(y) -> decays as exp(-2t) * sin(x)*sin(y)
        
        domain = {
            'x_min': 0, 'x_max': np.pi,
            'y_min': 0, 'y_max': np.pi,
            't_max': 0.5,
            'nx': 20, 'ny': 20,
            'dt': 0.001
        }
        
        solver = PDESolver("uxx + uyy", domain, "sin(x)*sin(y)", {})
        result = solver.solve()
        
        frames = result['frames']
        initial_max = np.max(frames[0])
        final_max = np.max(frames[-1])
        
        print(f"Initial Max: {initial_max}, Final Max: {final_max}")
        
        # Check decay
        self.assertTrue(final_max < initial_max, "Solution should decay")
        
        # Theoretical decay at t=0.5 is exp(-2*0.5) = exp(-1) ~= 0.367
        # Initial max is ~1.0
        expected_final = np.exp(-2 * 0.5)
        # Allow some error due to discretization
        self.assertAlmostEqual(final_max, expected_final, delta=0.1)

if __name__ == '__main__':
    unittest.main()
