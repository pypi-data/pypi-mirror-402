
import jax
import jax.numpy as jnp
from .psi import rho_bisquare, rho_huber

def mad(x, center=None, constant=1.4826):
    """
    Compute Median Absolute Deviation using JAX.
    """
    if center is None:
        center = jnp.median(x)
    return constant * jnp.median(jnp.abs(x - center))

def sum_rho_sc(r, scale, n, p, c, psi_func_name):
    """
    Sum of rho values scaled: sum(rho(r_i / scale)) / (n - p)
    """
    scale = jnp.maximum(scale, 1e-12)
    scaled_r = r / scale
    
    # We use a functional approach to avoid strings inside JIT if possible, 
    # but for now, we'll keep the logic and assume psi_func_name is handled.
    # Actually, JAX likes static arguments for branching on strings.
    if psi_func_name == 'bisquare':
        rho_vals = rho_bisquare(scaled_r, c)
    elif psi_func_name == 'huber':
        rho_vals = rho_huber(scaled_r, c)
    else:
        # Fallback for JIT: this branch should be avoided by providing valid name
        rho_vals = rho_bisquare(scaled_r, c)
        
    return jnp.sum(rho_vals) / (n - p)

def find_scale(r, b, c, psi_func_name, initial_scale, n, p, max_iter=200, scale_tol=1e-10):
    """
    Find the robust scale s using JAX loop.
    """
    def cond_fun(state):
        i, scale, prev_scale, converged = state
        # Continue if NOT converged and i < max_iter
        return jnp.logical_and(i < max_iter, jnp.logical_not(converged))

    def body_fun(state):
        i, scale, prev_scale, converged = state
        avg_rho = sum_rho_sc(r, scale, n, p, c, psi_func_name)
        new_scale = scale * jnp.sqrt(avg_rho / b)
        
        # Check convergence: |new - old| <= tol * old
        has_converged = jnp.abs(new_scale - scale) <= scale_tol * scale
        return (i + 1, new_scale, scale, has_converged)

    # Initial state: (iter, current_scale, previous_scale, converged_flag)
    init_state = (0, initial_scale, initial_scale, jnp.array(False))
    
    # Use lax.while_loop for JIT-compatibility
    _, final_scale, _, _ = jax.lax.while_loop(cond_fun, body_fun, init_state)
    
    return final_scale
