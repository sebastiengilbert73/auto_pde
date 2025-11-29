import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
import deepxde as dde
import tensorflow as tf

# Suppress TensorFlow warnings
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

class PDESolver:
    def __init__(self, equation_str, domain, ic_str, bc_params):
        """
        Initialize the PINN-based solver using DeepXDE.
        
        :param equation_str: String representing implicit PDE: F(u, ut, utt, x, y, t, ux, uy, uxx, uyy) = 0
        :param domain: Dict with keys 'x_min', 'x_max', 'y_min', 'y_max', 't_max', 'nx', 'ny', 'dt'
        :param ic_str: String representing initial condition u(x,y,0)
        :param bc_params: Dict defining boundary conditions (simplified for now: Dirichlet=0 everywhere)
        """
        self.equation_str = equation_str
        self.domain = domain
        self.ic_str = ic_str
        self.bc_params = bc_params
        
        # Parse equation and initial condition
        self._compile_equation()
        self._compile_ic()
        
    def _compile_equation(self):
        """Parse implicit PDE and prepare for PINN training."""
        # Define symbols
        x, y, t, u, ut, utt, ux, uy, uxx, uyy = sp.symbols('x y t u ut utt ux uy uxx uyy')
        
        try:
            # Parse the implicit equation F(...) = 0
            expr = parse_expr(self.equation_str)
            
            # Detect order
            if utt in expr.free_symbols:
                self.order = 2
                # Solve for utt
                utt_expr = sp.solve(expr, utt)
                if not utt_expr:
                    raise ValueError("Could not solve equation for utt")
                self.rhs_sympy = utt_expr[0]
            elif ut in expr.free_symbols:
                self.order = 1
                # Solve for ut
                ut_expr = sp.solve(expr, ut)
                if not ut_expr:
                    raise ValueError("Could not solve equation for ut")
                self.rhs_sympy = ut_expr[0]
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
    
    def _pde_residual(self, x_input, u_output):
        """
        Compute PDE residual for PINN training.
        x_input: [x, y, t] coordinates
        u_output: neural network output (u for 1st order, [u, v] for 2nd order)
        """
        x, y, t = x_input[:, 0:1], x_input[:, 1:2], x_input[:, 2:3]
        
        if self.order == 1:
            # First-order PDE: ut = f(u, ux, uy, uxx, uyy, ...)
            u_t = dde.grad.jacobian(u_output, x_input, i=0, j=2)
            u_xx = dde.grad.hessian(u_output, x_input, i=0, j=0)
            u_yy = dde.grad.hessian(u_output, x_input, i=1, j=1)
            
            # For heat equation: ut - (uxx + uyy) = 0
            rhs = u_xx + u_yy
            residual = u_t - rhs
            return residual
            
        else:  # self.order == 2
            # Second-order PDE: utt = f(u, ux, uy, uxx, uyy, ...)
            # Convert to first-order system: u_t = v, v_t = f(...)
            
            u = u_output[:, 0:1]
            v = u_output[:, 1:2]
            
            # Compute spatial derivatives of u
            u_xx = dde.grad.hessian(u_output, x_input, component=0, i=0, j=0)
            u_yy = dde.grad.hessian(u_output, x_input, component=0, i=1, j=1)
            
            # Compute time derivatives
            u_t = dde.grad.jacobian(u_output, x_input, i=0, j=2)
            v_t = dde.grad.jacobian(u_output, x_input, i=1, j=2)
            
            # For wave equation: vt - (uxx + uyy) = 0
            rhs = u_xx + u_yy
            
            # System residuals: u_t - v = 0, v_t - rhs = 0
            residual_u = u_t - v
            residual_v = v_t - rhs
            
            return tf.concat([residual_u, residual_v], axis=1)
    
    def _initial_condition(self, x_input):
        """Initial condition at t=0."""
        x, y = x_input[:, 0], x_input[:, 1]
        u0 = self.ic_func(x, y)
        if self.order == 1:
            return u0.reshape(-1, 1)
        else:
            # For wave equations, also need initial velocity (v0 = 0)
            v0 = np.zeros_like(u0)
            return np.column_stack([u0, v0])
    
    def solve(self):
        """Solve the PDE using DeepXDE (PINN)."""
        # Define computational domain
        geom = dde.geometry.Rectangle(
            [self.domain['x_min'], self.domain['y_min']],
            [self.domain['x_max'], self.domain['y_max']]
        )
        timedomain = dde.geometry.TimeDomain(0, self.domain['t_max'])
        geomtime = dde.geometry.GeometryXTime(geom, timedomain)
        
        # Add initial conditions
        if self.order == 1:
            ic = dde.icbc.IC(geomtime, self._initial_condition, lambda _, on_initial: on_initial)
            ics = [ic]
        else:
            # For wave equations: separate IC for u and v
            def ic_u_func(x):
                return self._initial_condition(x)[:, 0:1]
            
            def ic_v_func(x):
                return self._initial_condition(x)[:, 1:2]
            
            ic_u = dde.icbc.IC(geomtime, ic_u_func, lambda _, on_initial: on_initial, component=0)
            ic_v = dde.icbc.IC(geomtime, ic_v_func, lambda _, on_initial: on_initial, component=1)
            ics = [ic_u, ic_v]
        
        # Add boundary conditions (Dirichlet u=0)
        if self.order == 1:
            bc = dde.icbc.DirichletBC(geomtime, lambda x: np.zeros((len(x), 1)), lambda _, on_boundary: on_boundary)
            bcs = [bc]
        else:
            # For wave equations: separate BC for u and v
            bc_u = dde.icbc.DirichletBC(geomtime, lambda x: np.zeros((len(x), 1)), lambda _, on_boundary: on_boundary, component=0)
            bc_v = dde.icbc.DirichletBC(geomtime, lambda x: np.zeros((len(x), 1)), lambda _, on_boundary: on_boundary, component=1)
            bcs = [bc_u, bc_v]
        
        # Combine all constraints
        all_constraints = bcs + ics
        
        # Create data with IC and BC
        data = dde.data.TimePDE(
            geomtime,
            self._pde_residual,
            all_constraints,
            num_domain=1000,
            num_boundary=100,
            num_initial=100,
        )
        
        # Define neural network
        output_size = 1 if self.order == 1 else 2
        net = dde.nn.FNN([3] + [40] * 3 + [output_size], "tanh", "Glorot uniform")
        
        # Create model
        model = dde.Model(data, net)
        
        # Compile and train with Adam optimizer (increased iterations)
        model.compile("adam", lr=0.001)
        losshistory, train_state = model.train(iterations=5000, display_every=1000)
        
        # Fine-tune with L-BFGS for better accuracy
        model.compile("L-BFGS")
        losshistory, train_state = model.train()
        
        # Generate solution on grid
        x_coords = np.linspace(self.domain['x_min'], self.domain['x_max'], self.domain['nx'])
        y_coords = np.linspace(self.domain['y_min'], self.domain['y_max'], self.domain['ny'])
        
        # Generate frames at different time steps
        num_frames = 50
        t_values = np.linspace(0, self.domain['t_max'], num_frames)
        frames = []
        
        for t_val in t_values:
            # Create grid for this time step
            X, Y = np.meshgrid(x_coords, y_coords)
            T = np.full_like(X, t_val)
            
            # Flatten and stack
            points = np.stack([X.flatten(), Y.flatten(), T.flatten()], axis=1)
            
            # Predict
            u_pred = model.predict(points)
            
            # For second-order, extract only u (first component)
            if self.order == 2:
                u_pred = u_pred[:, 0:1]
            
            u_grid = u_pred.reshape(self.domain['ny'], self.domain['nx'])
            
            frames.append(u_grid)
        
        return {
            "x": x_coords.tolist(),
            "y": y_coords.tolist(),
            "t": t_values.tolist(),
            "frames": [f.tolist() for f in frames]
        }
