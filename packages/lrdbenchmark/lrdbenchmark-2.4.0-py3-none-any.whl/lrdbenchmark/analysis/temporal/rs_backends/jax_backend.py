
import numpy as np
import warnings

try:
    import jax
    import jax.numpy as jnp
    from jax import jit, vmap
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False
    # Dummies
    jnp = None
    jit = lambda x: x
    vmap = lambda x: x

def compute_rs(
    data: np.ndarray, 
    block_sizes: np.ndarray 
) -> np.ndarray:
    """
    Compute R/S statistic using JAX (GPU/TPU).
    """
    if not JAX_AVAILABLE:
        raise ImportError("JAX is not available.")
        
    # Move data to device once
    d_jax = jnp.array(data)
    n = len(d_jax)
    results = []
    
    for size in block_sizes:
        block_size = int(size)
        n_blocks = n // block_size
        
        if n_blocks < 1:
            results.append(np.nan)
            continue
            
        # Truncate and reshape
        # Reshaping with dynamic shapes in JAX can be tricky inside JIT,
        # but here we are in Python loop, manipulating JAX arrays.
        # reshape() is lazy.
        length = n_blocks * block_size
        truncated = d_jax[:length]
        segments = truncated.reshape((n_blocks, block_size))
        
        # Compute mean R/S for this block size
        val = _compute_rs_for_segments(segments)
        results.append(val)
        
    return np.array(results)

@jit
def _compute_rs_for_segments(segments: "jnp.ndarray") -> "jnp.ndarray":
    """
    Compute mean R/S for a batch of segments.
    segments shape: (n_blocks, block_size)
    """
    # Vectorized function for single segment
    def get_single_rs(block):
        # 1. Mean
        mean_val = jnp.mean(block)
        
        # 2. Deviations
        dev = block - mean_val
        cum_dev = jnp.cumsum(dev)
        
        # 3. Range
        R = jnp.max(cum_dev) - jnp.min(cum_dev)
        
        # 4. Std Dev
        S = jnp.std(block, ddof=1)
        
        # Safe division
        rs = jnp.where(S > 1e-10, R / S, jnp.nan)
        return rs

    # vmap over batch dimension (0)
    rs_values = vmap(get_single_rs)(segments)
    
    # Return mean, ignoring NaNs
    return jnp.nanmean(rs_values)
