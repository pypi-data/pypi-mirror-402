
import jax
import jax.numpy as jnp
from .fast_s import fast_s, get_weights, solve_wls
from .psi import wgt_bisquare, wgt_huber

class LMROB:
    def __init__(self, method='MM', psi='bisquare', init='S', 
                 n_resample=500, max_it=50, refinement_steps=200, seed=42):
        self.method = method
        self.psi = psi
        self.init = init
        self.n_resample = n_resample
        self.max_it = max_it # RWLS max iter
        self.refinement_steps = refinement_steps
        self.seed = seed
        self.key = jax.random.PRNGKey(seed)
        
        # Tuning constants for bisquare
        if psi == 'bisquare':
            self.c_chi = 1.54764 # breakdown point 0.5
            self.c_psi = 4.685061 # efficiency 0.95
        elif psi == 'huber':
            self.c_chi = 1.345 # dummy check
            self.c_psi = 1.345
        else:
            raise NotImplementedError(f"Psi {psi} not fully supported yet")

    def fit(self, X, y):
        # Convert to JAX arrays
        X = jnp.array(X)
        y = jnp.array(y)
        n, p = X.shape
        
        # 1. Initial Estimator (S-estimator)
        if self.init == 'S':
            beta_s, scale_s = fast_s(
                X, y, 
                n_resample=self.n_resample,
                k_max=self.refinement_steps,
                c=self.c_chi, 
                psi_func_name=self.psi,
                key=self.key
            )
            self.init_coef_ = beta_s
            self.scale_ = scale_s
        else:
            raise NotImplementedError("Only S-initialization supported")
            
        # 2. MM-Estimator
        if self.method == 'MM':
            beta_m = self._rwls_iterations(X, y, beta_s, scale_s, self.c_psi)
            self.coef_ = beta_m
            self.residuals_ = y - X @ beta_m
            self.weights_ = get_weights(self.residuals_, self.scale_, self.c_psi, self.psi)
            
        elif self.method == 'S':
            self.coef_ = beta_s
            self.residuals_ = y - X @ beta_s
            self.weights_ = get_weights(self.residuals_, self.scale_, self.c_chi, self.psi)
            
        return self

    def _rwls_iterations(self, X, y, beta_init, scale, c):
        """
        RWLS implementation using JAX while_loop for speed.
        """
        def cond_fun(state):
            i, beta, _, converged = state
            return jnp.logical_and(i < self.max_it, jnp.logical_not(converged))

        def body_fun(state):
            i, beta, _, converged = state
            res = y - X @ beta
            weights = get_weights(res, scale, c, self.psi)
            beta_new = solve_wls(X, y, weights)
            
            # Convergence check
            has_converged = jnp.allclose(beta, beta_new, rtol=1e-7)
            return (i + 1, beta_new, beta, has_converged)

        init_state = (0, beta_init, beta_init, jnp.array(False))
        _, final_beta, _, _ = jax.lax.while_loop(cond_fun, body_fun, init_state)
        
        return final_beta
