
import numpy as np
import warnings
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    import jax
    import jax.numpy as jnp
    from lrdbenchmark.analysis.wavelet.jax_wavelet import dwt_periodized, wavelet_detail_variances, JAX_AVAILABLE
except ImportError:
    JAX_AVAILABLE = False
    
def compute_variances(
    data: np.ndarray,
    wavelet: str,
    scales: List[int],
    robust: bool = False
) -> Tuple[Dict[int, float], Dict[int, int]]:
    """
    Compute wavelet variances for specified scales using JAX.
    """
    if not JAX_AVAILABLE:
        raise ImportError("JAX not available")
    
    # Ensure data is on device
    data_jax = jnp.asarray(data, dtype=jnp.float64)
    max_scale = max(scales)
    
    # Perform DWT
    # returns (approx, details_list)
    # details_list[0] is level 1, details_list[-1] is level J
    # Note: this order is different from pywt.wavedec output list structure!
    # jax_wavelet.dwt_periodized: "returns ... list of detail coefficients ordered from finest (level 1) to coarsest (level = J)."
    approx, details = dwt_periodized(data_jax, wavelet, max_scale)
    
    # Compute variances for *all* returned levels
    # wavelet_detail_variances returns arrays for the list
    variances_arr, counts_arr = wavelet_detail_variances(details, robust=robust)
    
    # Map back to requested scales
    # detail index i corresponds to level i+1
    # We want level j. It is at index j-1.
    
    variances = {}
    counts = {}
    
    # Move to host for dictionary creation?
    # Or keep as scalars?
    # Usually we return python dict for estimator regression (NumPy).
    
    variances_host = np.array(variances_arr)
    counts_host = np.array(counts_arr)
    
    for j in scales:
        idx = j - 1
        if 0 <= idx < len(variances_host):
            variances[j] = float(variances_host[idx])
            counts[j] = int(counts_host[idx])
            
    return variances, counts
