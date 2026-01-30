
import numpy as np
from functools import partial

try:
    import jax
    import jax.numpy as jnp
    from jax import jit, vmap
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False
    jnp = None
    jit = lambda x: x
    vmap = lambda x: x
    partial = lambda x: x

def compute_fluctuations(
    signal: np.ndarray,
    scales: np.ndarray,
    qs: np.ndarray,
    order: int
) -> np.ndarray:
    """MDFDA JAX Backend."""
    if not JAX_AVAILABLE:
        raise ImportError("JAX not available")
        
    y_profile = jnp.cumsum(signal - jnp.mean(signal)) # On device
    n = len(signal)
    
    scales_jax = jnp.array(scales)
    qs_jax = jnp.array(qs)
    
    # We must scan over scales because n_segments changes.
    # vmap over scales is hard because output shape changes (intermediate trend).
    # But output F_q is (len(qs),).
    # so we can vmap over scales if we pad or just Python loop + JIT kernel.
    # Python loop over scales + JIT single-scale kernel is efficient enough (scales ~ 50).
    
    # Pre-compile the kernel for a given scale size?
    # Scale size changes each iter. JIT recompilation for each unique scale.
    # If scales are many unique values, extensive recompilations.
    # However, standard DFA scales are logarithmic (e.g. 50 scales). Recompiling 50 times is fast.
    # NOTE: To avoid overhead, we can use a single JIT kernel that takes padded/reshaped input?
    # Or just loop. 50 compiles is fine.
    
    fluctuations = []
    
    for scale in scales:
        n_segs = n // int(scale)
        if n_segs < 1:
            fluctuations.append(np.full(len(qs), np.nan))
            continue
            
        f_qs = _compute_scale_jax(y_profile, int(scale), n_segs, qs_jax, order)
        fluctuations.append(f_qs)
        
    return np.array(fluctuations)

@partial(jit, static_argnums=(1, 2, 4))
def _compute_scale_jax(profile, scale, n_segments, qs, order):
    # Truncate
    length = n_segments * scale
    # Dynamic slice? 
    # Since scale/n_segments are static (passed as static_argnums), we can reshape directly?
    # No, reshaping requires static shape.
    # But JIT function receives them as static, so they ARE static inside trace.
    # profile is dynamic shape.
    
    y = profile[:length]
    segments = y.reshape((n_segments, scale))
    x = jnp.arange(scale) # broadcasted later
    
    # Detrend
    # Vectorized least squares for all segments
    # X_design = vander(x). (scale, order+1)
    # Y = segments.T (scale, n_segments)
    # Coeffs = lstsq(X, Y)
    
    # Construct Vandermonde
    # jnp.vander is available?
    # Yes.
    V = jnp.vander(x, order + 1)
    
    # lstsq
    # jnp.linalg.lstsq(a, b). a=(M, N), b=(M, K).
    coeffs, _, _, _ = jnp.linalg.lstsq(V, segments.T, rcond=None)
    
    trend = (V @ coeffs).T
    detrended = segments - trend
    
    # Variance
    variances = jnp.mean(detrended**2, axis=1) # (n_segments,)
    
    # Compute F_q for all qs
    # q=0 handling:
    # safe_var for log
    safe_var = jnp.where(variances < 1e-16, 1e-16, variances)
    log_mean = jnp.mean(jnp.log(safe_var))
    f_q0 = jnp.exp(0.5 * log_mean)
    
    def get_fq(q):
        # Branch for q=0?
        # JAX doesn't like python control flow on dynamic q.
        # But q is from qs array.
        # We can implement using jnp.where
        
        # F_q = mean( var^(q/2) )^(1/q)
        # If q approx 0.
        is_zero = jnp.abs(q) < 1e-10
        
        # q != 0 calculation
        # Complex numbers? Variances are positive (squared residuals).
        # q can be negative. 
        # var^(q/2) can be large.
        term = variances ** (q / 2.0)
        mean_term = jnp.mean(term)
        res_nonzero = jnp.power(mean_term, 1.0 / q)
        
        return jnp.where(is_zero, f_q0, res_nonzero)
        
    f_qs = vmap(get_fq)(qs)
    return f_qs
