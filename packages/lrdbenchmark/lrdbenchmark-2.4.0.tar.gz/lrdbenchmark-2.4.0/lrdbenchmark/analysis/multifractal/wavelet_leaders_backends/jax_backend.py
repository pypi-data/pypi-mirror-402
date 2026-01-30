
import numpy as np
import warnings
from typing import List, Union, Tuple

try:
    import jax
    import jax.numpy as jnp
    from lrdbenchmark.analysis.wavelet.jax_wavelet import dwt_periodized
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False
    jnp = None

def compute_structure_functions(
    data: np.ndarray,
    wavelet: str,
    scales: np.ndarray,
    q_values: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """JAX compute structure functions."""
    if not JAX_AVAILABLE:
        raise ImportError("JAX not available")
    
    n = len(data)
    data_jax = jnp.asarray(data, dtype=jnp.float64)
    # Scales max determines J.
    # Note: jax_wavelet dwt_periodized takes 'level' (J).
    max_j = int(jnp.max(scales))
    
    _, details = dwt_periodized(data_jax, wavelet, max_j)
    # details is [level 1, ..., level J]
    abs_details = [jnp.abs(d) for d in details]
    
    leaders = _compute_leaders_jax(abs_details)
    
    q_jax = jnp.asarray(q_values, dtype=jnp.float64)
    js = scales.astype(np.float64)
    
    SL_rows = []
    
    # Compute SL for each q (rows)
    # We iterate q_values, and for each 'j' (col) we compute.
    
    # Matrix SL (q, scale)
    # Using loop over scales for clarity (few scales)
    
    for q in q_values:
        row_vals = []
        for j in scales:
            idx = int(j - 1)
            # Handle out of bounds if scale > len(leaders)?
            # Should be safe if max_j = max(scales)
            if idx < len(leaders):
                Lj = leaders[idx]
                
                if jnp.isclose(q, 0.0):
                    val = jnp.exp(jnp.mean(jnp.log(Lj)))
                else:
                    val = jnp.mean(Lj ** q) ** (1.0 / q)
                row_vals.append(val)
            else:
                row_vals.append(jnp.nan)
        SL_rows.append(jnp.asarray(row_vals))
        
    SL = jnp.stack(SL_rows)
    return SL, jnp.asarray(js) # Return as JAX arrays? Estimator expects NumPy usually?
    # Usually we convert to NumPy in the backend or Estimator.
    # Estimator calls backend.
    # numpy_backend returns numpy arrays.
    # jax_backend returning numpy arrays is safer for seamless integration.
    # I will cast to np.array.

def _compute_leaders_jax(abs_details: List):
    """JAX implementation of leaders."""
    # This logic matches _estimate_jax from original file.
    leaders = []
    for j, Dj in enumerate(abs_details):
        n_j = Dj.shape[0]
        # JAX loop or scan?
        # Original code used python loop over 'k' with .at[k].set(...) 
        # This is SLOW in JAX (scan is better, or vectorization).
        # Original code:
        # for k in range(n_j): Lj = Lj.at[k].set(...)
        # That is extremely inefficient if not compiled, and even if compiled, large loop unroll.
        # Ideally, we construct the neighborhoods using vectorized operations (padding + shifting).
        
        # Vectorized Leaders:
        # Neighborhoods are [k-1, k, k+1] at scale j.
        # Plus [2k-2 ... 2k+2] at scale j-1.
        # Plus [4k-4 ... 4k+4] at scale j-2.
        
        # Scale j: Max of 3 neighbors.
        # Can use simple shifting/padding.
        pad_Dj = jnp.pad(Dj, (1, 1), mode='edge')
        # Windows: Dj[k-1], Dj[k], Dj[k+1].
        # Can simply stack and max.
        # stack arrays of shape (n_j,).
        # s0 = pad_Dj[0:n_j] # equiv k-1?? No. 
        # pad indices: 0, 1..n_j, n_j+1.
        # k goes 0..n_j-1.
        # k-1 corresponds to pad index k. k to k+1. k+1 to k+2.
        # Yes.
        
        w0 = pad_Dj[0:n_j]
        w1 = pad_Dj[1:n_j+1]
        w2 = pad_Dj[2:n_j+2]
        current_max = jnp.maximum(jnp.maximum(w0, w1), w2)
        
        # Scale j-1 (Df): Indices 2k-2 to 2k+2 (5 elements).
        # We need to compute max of 5 elements starting at 2k-2 for each k.
        # This is effectively a max-pool operation with stride 2 and kernel 5?
        # No, for each k at CURRENT scale j, lookup range in j-1.
        # Wait, data size doubles at finer scales. N_{j-1} = 2 * N_j approx.
        # Yes. So we take window 2k-2...2k+2 in finer scale, compute max, aligns with k.
        
        if j > 0:
            Df = abs_details[j-1]
            # We want max over window of size 5 centered at 2k.
            # Stride 2.
            # Use lax.reduce_window? or simple reshapes?
            # Or jnp.pad Df then take slices.
            
            # Simple approach: MaxPool1D with kernel=5, stride=2, padding?
            # Df shape (N_fine,).
            # Output shape (N_current,).
            # MaxPool usually N_out = (N_in + 2p - k)/s + 1.
            # If N_in = 2*N_curr. stride=2. kernel=5.
            # We want specific alignment.
            # Center 2k. Range [2k-2, 2k+2].
            # This is standard max pooling.
            
            # Use jax.lax.reduce_window.
            # window=(5,), stride=(2,).
            # Df needs padding to match alignment.
            # Range 2k-2 means start index -2.
            # So pad Df with 2 on left, 2 on right.
            Df_pad = jnp.pad(Df, (2, 2), mode='edge')
            Df_max = _max_pool_1d(Df_pad, window_size=5, stride=2)
            
            # Ensure shape matches current_max (n_j).
            # Df_max might be slightly larger or smaller due to rounding.
            # Truncate or Pad.
            valid_len = min(current_max.shape[0], Df_max.shape[0])
            current_max = jnp.maximum(current_max[:valid_len], Df_max[:valid_len])
            
        if j > 1:
            Df2 = abs_details[j-2]
            # Range 4k-4 to 4k+4 (9 elements).
            # Stride 4.
            # Start 4k-4. Pad 4.
            Df2_pad = jnp.pad(Df2, (4, 4), mode='edge')
            Df2_max = _max_pool_1d(Df2_pad, window_size=9, stride=4)
            valid_len = min(current_max.shape[0], Df2_max.shape[0])
            current_max = jnp.maximum(current_max[:valid_len], Df2_max[:valid_len])

        leaders.append(current_max + 1e-18)
        
    return leaders

def _max_pool_1d(x, window_size, stride):
    # x shape (N,)
    # reshape to (1, 1, N) for lax
    x_in = x.reshape(1, 1, -1)
    
    out = jax.lax.reduce_window(
        x_in, 
        -jnp.inf, # init value
        jax.lax.max, 
        window_dimensions=(1, 1, window_size), 
        window_strides=(1, 1, stride),
        padding='VALID'
    )
    return out.reshape(-1)

