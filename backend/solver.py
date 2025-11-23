import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

class PDESolver:
    def __init__(self, equation_str, domain, ic_str, bc_params):
        """
        Initialize the solver.
        
        :param equation_str: String representing implicit PDE: F(u, ut, utt, x, y, t, ux, uy, uxx, uyy) = 0
                             Examples: 
                             - Heat: "ut - uxx - uyy" (first-order)
                             - Wave: "utt - uxx - uyy" (second-order)
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
        """Parse implicit PDE and solve for time derivative."""
        # Define symbols
        x, y, t, u, ut, utt, ux, uy, uxx, uyy = sp.symbols('x y t u ut utt ux uy uxx uyy')
        
        try:
            # Parse the implicit equation F(...) = 0
            expr = parse_expr(self.equation_str)
            
            # Detect order: check if equation contains utt or just ut
            if utt in expr.free_symbols:
                # Second-order in time (wave equation)
                self.order = 2
                # Solve F = 0 for utt
                utt_expr = sp.solve(expr, utt)
                if not utt_expr:
                    raise ValueError("Could not solve equation for utt")
                # Take first solution
                utt_solved = utt_expr[0]
                # Create lambda function for utt = f(x, y, t, u, ut, ux, uy, uxx, uyy)
                self.rhs_func = sp.lambdify((x, y, t, u, ut, ux, uy, uxx, uyy), utt_solved, 'numpy')
                
            elif ut in expr.free_symbols:
                # First-order in time (heat/diffusion equation)
                self.order = 1
                # Solve F = 0 for ut
                ut_expr = sp.solve(expr, ut)
                if not ut_expr:
                    raise ValueError("Could not solve equation for ut")
                # Take first solution
                ut_solved = ut_expr[0]
                # Create lambda function for ut = f(x, y, t, u, ux, uy, uxx, uyy)
                self.rhs_func = sp.lambdify((x, y, t, u, ux, uy, uxx, uyy), ut_solved, 'numpy')
                
            else:
                raise ValueError("Equation must contain 'ut' or 'utt'")
                
        except Exception as e:
            raise ValueError(f"Invalid equation string: {e}")

    def _compile_ic(self):
        """Compile initial condition."""
        x, y = sp.symbols('x y')
        try:
            expr = parse_expr(self.ic_str)
            self.ic_func = sp.lambdify((x, y), expr, 'numpy')
        except Exception as e:
            raise ValueError(f"Invalid IC string: {e}")

    def _compute_spatial_derivatives(self, u):
        """Compute spatial derivatives using finite differences."""
        ux = (np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1)) / (2 * self.dx)
        uy = (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0)) / (2 * self.dy)
        uxx = (np.roll(u, -1, axis=1) - 2*u + np.roll(u, 1, axis=1)) / (self.dx**2)
        uyy = (np.roll(u, -1, axis=0) - 2*u + np.roll(u, 1, axis=0)) / (self.dy**2)
        return ux, uy, uxx, uyy

    def _apply_bc(self, u):
        """Apply Dirichlet boundary conditions (u=0 at boundaries)."""
        u[0, :] = 0
        u[-1, :] = 0
        u[:, 0] = 0
        u[:, -1] = 0
        return u

    def solve(self):
        """Solve the PDE using appropriate time-stepping scheme."""
        # Initialize u
        u = self.ic_func(self.X, self.Y)
        u = self._apply_bc(u)
        
        # Storage for results
        frames = [u.copy()]
        t = 0
        
        # Time stepping
        steps = int(self.domain['t_max'] / self.dt)
        save_interval = max(1, steps // 50)  # Save ~50 frames
        
        if self.order == 1:
            # First-order: Forward Euler
            for step in range(steps):
                ux, uy, uxx, uyy = self._compute_spatial_derivatives(u)
                
                # Evaluate ut = f(x, y, t, u, ux, uy, uxx, uyy)
                ut = self.rhs_func(self.X, self.Y, t, u, ux, uy, uxx, uyy)
                
                # Update: u_new = u + dt * ut
                u_new = u + self.dt * ut
                u_new = self._apply_bc(u_new)
                
                u = u_new
                t += self.dt
                
                if (step + 1) % save_interval == 0:
                    frames.append(u.copy())
                    
        elif self.order == 2:
            # Second-order: Velocity Verlet / Leapfrog
            # Initialize velocity (ut) to zero (or could be specified)
            ut = np.zeros_like(u)
            
            for step in range(steps):
                ux, uy, uxx, uyy = self._compute_spatial_derivatives(u)
                
                # Evaluate utt = f(x, y, t, u, ut, ux, uy, uxx, uyy)
                utt = self.rhs_func(self.X, self.Y, t, u, ut, ux, uy, uxx, uyy)
                
                # Velocity Verlet scheme:
                # u_new = u + dt * ut + 0.5 * dt^2 * utt
                u_new = u + self.dt * ut + 0.5 * self.dt**2 * utt
                u_new = self._apply_bc(u_new)
                
                # Compute new spatial derivatives
                ux_new, uy_new, uxx_new, uyy_new = self._compute_spatial_derivatives(u_new)
                
                # Compute new acceleration
                utt_new = self.rhs_func(self.X, self.Y, t + self.dt, u_new, ut, ux_new, uy_new, uxx_new, uyy_new)
                
                # ut_new = ut + 0.5 * dt * (utt + utt_new)
                ut_new = ut + 0.5 * self.dt * (utt + utt_new)
                
                u = u_new
                ut = ut_new
                t += self.dt
                
                if (step + 1) % save_interval == 0:
                    frames.append(u.copy())
                
        return {
            "x": self.x.tolist(),
            "y": self.y.tolist(),
            "t": np.linspace(0, self.domain['t_max'], len(frames)).tolist(),
            "frames": [f.tolist() for f in frames]
        }
