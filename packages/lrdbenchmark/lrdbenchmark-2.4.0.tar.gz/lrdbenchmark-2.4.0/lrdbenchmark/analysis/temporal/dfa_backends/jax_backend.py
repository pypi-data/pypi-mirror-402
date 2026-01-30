
import numpy as np
import warnings

try:
    import jax
    import jax.numpy as jnp
    from jax import jit, vmap
    from functools import partial
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False
    # Define dummies to avoid NameError if imported but not used (e.g. by tools scanning)
    jnp = None
    jit = lambda x: x
    vmap = lambda x: x
    partial = lambda x, **k: x

def compute_fluctuations(
    signal: np.ndarray, 
    scales: np.ndarray, 
    order: int
) -> np.ndarray:
    """
    Compute DFA fluctuation function F(s) using JAX (GPU/TPU accelerated).
    """
    if not JAX_AVAILABLE:
        raise ImportError("JAX is not available.")
        
    # Transfer to device once
    y = jnp.array(signal)
    y = jnp.cumsum(y - jnp.mean(y))
    
    fluctuations = []
    
    # We loop over scales in Python because they determine shapes, which are static for JIT.
    # Re-compiling for every new scale size is expected in DFA (scales ~ 20-50).
    # Since scales are constant for a given config, subsequent calls with same scales reuse cache?
    # Yes, if we use static_argnums for scale.
    
    for scale in scales:
        # Scale must be int for JIT static arg
        s = int(scale)
        val = _compute_single_scale(y, s, order)
        fluctuations.append(val)
        
    # Transfer back to host
    return np.array(fluctuations)

@partial(jit, static_argnums=(1, 2))
def _compute_single_scale(cumsum: "jnp.ndarray", scale: int, order: int) -> "jnp.ndarray":
    """
    Compute F(s) for a single scale.
    """
    n = cumsum.shape[0]
    n_segments = n // scale
    
    if n_segments < 1:
        return jnp.nan
        
    # Truncate and reshape
    length = n_segments * scale
    # Use dynamic slice or simple slice? Simple slice works if length is computed from shape?
    # Actually 'length' depends on 'scale' (static) and 'n' (dynamic).
    # JAX prefers static shapes for reshape. 
    # n is dynamic usually?
    # If n is dynamic, reshape might fail if dimension is data-dependent.
    # However, standard JAX usage with variable data size often triggers recompilation
    # or requires masking.
    # But here we reshape to (n_segments, scale). 
    # n_segments depends on n.
    # This implies we can only JIT if n is static?
    # Or we JIT the *segment processing* part (vmap) and leave reshaping outside?
    
    # Current implementation in dfa_estimator.py line 78 did:
    # def _dfa_fluctuation_jax(cumsum, scale, order):
    #    n_segments = cumsum.shape[0] // scale ...
    #    trimmed = cumsum[:n_segments*scale]
    #    segments = trimmed.reshape((n_segments, scale))
    # checks out.
    
    trimmed = cumsum[:length]
    segments = trimmed.reshape((n_segments, scale))
    
    x = jnp.arange(scale, dtype=cumsum.dtype)
    
    # Detrending
    if order == 0:
        trends = jnp.mean(segments, axis=1, keepdims=True)
        detrended = segments - trends
        variances = jnp.mean(detrended**2, axis=1)
        return jnp.sqrt(jnp.mean(variances))
        
    # Polynomial detrending
    # Linear algebra apporach: Project onto orthogonal complement of poly basis
    # Construct Vandermonde matrix X: (scale, order+1)
    X = jnp.vander(x, N=order + 1)
    
    # We want to solve min ||y - Xc||^2
    # Fits are c = (X^T X)^-1 X^T y
    # Trend is Xc = X (X^T X)^-1 X^T y
    # Projector P = X (X^T X)^-1 X^T
    # Residual r = y - Py = (I - P)y
    # This is effectively what we want.
    # We can precompute P or (I-P) since X depends only on scale (static).
    
    # X_pinv = jnp.linalg.pinv(X) # (order+1, scale)
    # Projector = X @ X_pinv # (scale, scale)
    # But for vmap, we want to apply to segments (n_segments, scale).
    # segments is (N, S).
    # residuals = segments @ (I - P).T ?
    # Let's verify dimensions.
    # segment (1, S). 
    # trend = P @ segment.T -> (S, 1).
    # We need to treat segments as rows?
    # Projector P acts on column vectors usually.
    
    # Let's use the logic from dfa_estimator.py line 92 which worked well.
    # It computed XtX_inv etc. inside the function.
    
    XtX = X.T @ X
    XtX_inv = jnp.linalg.inv(XtX)
    # Projector maps coefficients c = (XtX_inv @ X.T) @ y
    # Wait, existing code: projector = XtX_inv @ X.T
    # Then coeffs = projector @ segment
    # trend = X @ coeffs
    # This works for 1D segment.
    # vmap handles batching.
    
    # Efficient vmap:
    # Precompute operators outside vmap.
    projector = XtX_inv @ X.T # (order+1, scale)
    
    # Define function for ONE segment
    def get_variance(seg):
        coeffs = projector @ seg # (order+1,)
        trend = X @ coeffs # (scale,)
        detrended = seg - trend
        return jnp.mean(detrended**2)
        
    variances = vmap(get_variance)(segments)
    return jnp.sqrt(jnp.mean(variances))
