import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

class PDESolver:
    def __init__(self, equation_str, domain, ic_str, bc_params):
        """
        Initialize the solver.
        
        :param equation_str: String representing the RHS of u_t = ...
                             Variables allowed: x, y, u, ux, uy, uxx, uyy
        :param domain: Dict with keys 'x_min', 'x_max', 'y_min', 'y_max', 't_max', 'nx', 'ny', 'dt'
        :param ic_str: String representing initial condition u(x,y,0)
        :param bc_params: Dict defining boundary conditions (simplified for now: Dirichlet=0 everywhere)
        """
        self.equation_str = equation_str
        self.domain = domain
        self.ic_str = ic_str
        self.bc_params = bc_params
        
        # Grid setup
        self.x = np.linspace(domain['x_min'], domain['x_max'], domain['nx'])
        self.y = np.linspace(domain['y_min'], domain['y_max'], domain['ny'])
        self.dx = self.x[1] - self.x[0]
        self.dy = self.y[1] - self.y[0]
        self.dt = domain['dt']
        self.X, self.Y = np.meshgrid(self.x, self.y)
        
        # Compile functions
        self._compile_equation()
        self._compile_ic()

    def _compile_equation(self):
        # Define symbols
        x, y, u, ux, uy, uxx, uyy = sp.symbols('x y u ux uy uxx uyy')
        
        # Parse equation string
        # Expecting input like "uxx + uyy" for heat equation
        try:
            expr = parse_expr(self.equation_str)
            self.rhs_func = sp.lambdify((x, y, u, ux, uy, uxx, uyy), expr, 'numpy')
        except Exception as e:
            raise ValueError(f"Invalid equation string: {e}")

    def _compile_ic(self):
        x, y = sp.symbols('x y')
        try:
            expr = parse_expr(self.ic_str)
            self.ic_func = sp.lambdify((x, y), expr, 'numpy')
        except Exception as e:
            raise ValueError(f"Invalid IC string: {e}")

    def solve(self):
        # Initialize u
        u = self.ic_func(self.X, self.Y)
        
        # Storage for results (store every k-th frame to save memory)
        frames = [u.copy()]
        t = 0
        
        # Time stepping
        steps = int(self.domain['t_max'] / self.dt)
        save_interval = max(1, steps // 50) # Save ~50 frames
        
        for step in range(steps):
            # Compute derivatives (Finite Differences)
            # Central difference for space
            # Pad u for vectorization (Dirichlet BC = 0 at boundaries for now)
            # For more complex BCs, we'd need ghost nodes or specific handling
            
            # Naive implementation with loops first (slow but clear), then optimize
            # Actually, let's use np.roll for vectorized derivatives
            
            ux = (np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1)) / (2 * self.dx)
            uy = (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0)) / (2 * self.dy)
            
            uxx = (np.roll(u, -1, axis=1) - 2*u + np.roll(u, 1, axis=1)) / (self.dx**2)
            uyy = (np.roll(u, -1, axis=0) - 2*u + np.roll(u, 1, axis=0)) / (self.dy**2)
            
            # Fix boundaries (derivatives at boundaries are not valid with roll)
            # For Dirichlet u=0, the rolls wrap around, which is wrong.
            # We should enforce BCs after the step, but for derivatives we need care.
            # Let's assume 0 boundary for derivatives calculation where valid?
            # Better: calculate internal points only.
            
            # Evaluate RHS
            # u_t = F(...)
            # u_new = u + dt * F
            
            rhs = self.rhs_func(self.X, self.Y, u, ux, uy, uxx, uyy)
            
            u_new = u + self.dt * rhs
            
            # Enforce Dirichlet BCs (u=0 at boundary)
            u_new[0, :] = 0
            u_new[-1, :] = 0
            u_new[:, 0] = 0
            u_new[:, -1] = 0
            
            u = u_new
            t += self.dt
            
            if (step + 1) % save_interval == 0:
                frames.append(u.copy())
                
        return {
            "x": self.x.tolist(),
            "y": self.y.tolist(),
            "t": np.linspace(0, self.domain['t_max'], len(frames)).tolist(),
            "frames": [f.tolist() for f in frames]
        }
