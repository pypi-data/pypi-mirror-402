
import jax.numpy as jnp

def rho_huber(x, c):
    """
    Huber's rho function.
    """
    x_abs = jnp.abs(x)
    return jnp.where(x_abs <= c, 0.5 * x**2, c * (x_abs - c/2))

def psi_huber(x, c):
    """
    Huber's psi function (derivative of rho).
    """
    return jnp.clip(x, -c, c)

def psip_huber(x, c):
    """
    Huber's psi' (derivative of psi).
    """
    return jnp.where(jnp.abs(x) >= c, 0.0, 1.0)

def wgt_huber(x, c):
    """
    Weights for Huber's loss: w(x) = psi(x)/x
    """
    x_abs = jnp.abs(x)
    # Using jnp.where avoids division by zero warnings better in JAX
    w = jnp.where(x_abs >= c, c / jnp.maximum(x_abs, 1e-12), 1.0)
    return w


def rho_bisquare(x, c):
    """
    Tukey's bisquare loss function.
    """
    x_abs = jnp.abs(x)
    t = (x / c)**2
    mask = x_abs > c
    rho = t * (3.0 + t * (-3.0 + t))
    return jnp.where(mask, 1.0, rho)

def psi_bisquare(x, c):
    """
    Tukey's bisquare psi function.
    """
    x_abs = jnp.abs(x)
    u = 1.0 - (x/c)**2
    psi = x * u * u
    return jnp.where(x_abs > c, 0.0, psi)

def psip_bisquare(x, c):
    """
    Tukey's bisquare psi' function.
    """
    x_abs = jnp.abs(x)
    fraction = (x/c)**2
    psip = (1.0 - fraction) * (1.0 - 5.0 * fraction)
    return jnp.where(x_abs > c, 0.0, psip)

def wgt_bisquare(x, c):
    """
    Tukey's bisquare weights.
    """
    x_abs = jnp.abs(x)
    u = 1.0 - (x/c)**2
    w = u * u
    return jnp.where(x_abs > c, 0.0, w)
