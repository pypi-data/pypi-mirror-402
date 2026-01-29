
import jax
import jax.numpy as jnp
from jax import vmap, jit
from .auxiliary import mad, sum_rho_sc
from .psi import wgt_bisquare, wgt_huber

def get_weights(r, scale, c, psi_func_name):
    scale = jnp.maximum(scale, 1e-12)
    scaled_r = r / scale
    if psi_func_name == 'bisquare':
        return wgt_bisquare(scaled_r, c)
    elif psi_func_name == 'huber':
        return wgt_huber(scaled_r, c)
    else:
        return wgt_bisquare(scaled_r, c)

def solve_wls(X, y, weights):
    sqrt_w = jnp.sqrt(weights)
    X_w = X * sqrt_w[:, jnp.newaxis]
    y_w = y * sqrt_w
    
    # lstsq is generally safer for WLS
    beta, _, _, _ = jnp.linalg.lstsq(X_w, y_w, rcond=None)
    return beta

def refine_fast_s(X, y, beta_cand, initial_scale, n, p, 
                  k_steps, b, c, psi_func_name, rel_tol=1e-7):
    """
    Refinement step for Fast-S using JAX loops.
    """
    def cond_fun(state):
        i, _, _, converged = state
        return jnp.logical_and(i < k_steps, jnp.logical_not(converged))

    def body_fun(state):
        i, beta, scale, converged = state
        res = y - X @ beta
        
        # Update scale
        avg_rho = sum_rho_sc(res, scale, n, p, c, psi_func_name)
        new_scale = scale * jnp.sqrt(avg_rho / b)
        
        # Compute weights and solve WLS
        weights = get_weights(res, new_scale, c, psi_func_name)
        beta_new = solve_wls(X, y, weights)
        
        # Check convergence
        diff = jnp.linalg.norm(beta_new - beta)
        norm_b = jnp.linalg.norm(beta)
        has_converged = diff <= rel_tol * jnp.maximum(rel_tol, norm_b)
        
        return (i + 1, beta_new, new_scale, has_converged)

    scale_start = jnp.where(initial_scale <= 0, mad(y - X @ beta_cand), initial_scale)
    scale_start = jnp.maximum(scale_start, 1e-12)
    
    init_state = (0, beta_cand, scale_start, jnp.array(False))
    _, final_beta, final_scale, _ = jax.lax.while_loop(cond_fun, body_fun, init_state)
    
    return final_beta, final_scale

def fast_s(X, y, n_resample=500, best_r=2, k_fast_s=2, k_max=200, 
           b=0.5, c=1.54764, psi_func_name='bisquare', key=None):
    """
    Fast-S implementation using JAX vmap for massive parallelization.
    """
    n, p = X.shape
    if key is None:
        key = jax.random.PRNGKey(42)
        
    # 1. Subsampling phase
    def run_one_subsample(subkey):
        indices = jax.random.choice(subkey, n, shape=(p,), replace=False)
        X_sub = X[indices]
        y_sub = y[indices]
        
        # Using lstsq for stability in sub-samples
        beta_cand, _, _, _ = jnp.linalg.lstsq(X_sub, y_sub, rcond=None)
        
        # Initial refinement (k_fast_s steps)
        beta_ref, scale_ref = refine_fast_s(X, y, beta_cand, -1.0, n, p, 
                                            k_fast_s, b, c, psi_func_name)
        return beta_ref, scale_ref

    # Parallelize subsampling
    keys = jax.random.split(key, n_resample)
    all_betas, all_scales = vmap(run_one_subsample)(keys)
    
    # 2. Pick top best_r candidates
    # Sort by scale
    sorted_indices = jnp.argsort(all_scales)
    top_indices = sorted_indices[:best_r]
    
    top_betas = all_betas[top_indices]
    top_scales = all_scales[top_indices]
    
    # 3. Full refinement phase
    def run_full_refine(beta_cand, scale_cand):
        return refine_fast_s(X, y, beta_cand, scale_cand, n, p, 
                             k_max, b, c, psi_func_name)
    
    final_betas, final_scales = vmap(run_full_refine)(top_betas, top_scales)
    
    # Pick the best of the refined ones
    best_idx = jnp.argmin(final_scales)
    return final_betas[best_idx], final_scales[best_idx]
