
import numpy as np
import warnings

try:
    import numba
    from numba import jit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

def compute_rs(
    data: np.ndarray, 
    block_sizes: np.ndarray 
) -> np.ndarray:
    """
    Compute R/S statistic using Numba (CPU JIT).
    """
    if not NUMBA_AVAILABLE:
        raise ImportError("Numba is not available.")
        
    return _compute_numba_jit(data, block_sizes)

@jit(nopython=True)
def _compute_numba_jit(data: np.ndarray, block_sizes: np.ndarray) -> np.ndarray:
    n = len(data)
    n_scales = len(block_sizes)
    results = np.empty(n_scales, dtype=np.float64)
    
    for i in range(n_scales):
        block_size = int(block_sizes[i])
        n_blocks = n // block_size
        
        if n_blocks < 1:
            results[i] = np.nan
            continue
            
        sum_rs = 0.0
        count = 0
        
        # Pre-allocate buffers for this block size to avoid allocation in inner loop
        # (Since we are serial, this is safe and efficient)
        dev_buffer = np.empty(block_size, dtype=np.float64)
        cum_dev_buffer = np.empty(block_size, dtype=np.float64)
        
        for j in range(n_blocks):
            start_idx = j * block_size
            # Access data manually or slice? Slice creates view or copy?
            # In Numba, slice usually creates view if possible?
            # But calculating variance/mean requires pass.
            
            # 1. Calculate Mean
            # Manual loop is often faster or safer in Numba than np.mean(slice) which might create view object overhead?
            # Actually np.mean is well optimized.
            # But we need to fill dev_buffer anyway.
            
            # Let's compute mean manually to avoid double pass or allocation?
            
            current_sum = 0.0
            sum_sq = 0.0
            # Getting data slice
            # To avoid creating a slice object, we can index data[start_idx + k]
            
            # First pass: Mean
            for k in range(block_size):
                val = data[start_idx + k]
                current_sum += val
            
            mean_val = current_sum / block_size
            
            # Second pass: Dev, CumDev, Variance
            # We can accumulate variance and fill cum_dev in same loop?
            # CumDev depends on previous dev.
            
            running_cum = 0.0
            min_cum = 0.0 # Starts at 0?
            max_cum = 0.0
            
            # cum_dev starts at dev[0].
            # Actually range R is max(cum_dev) - min(cum_dev).
            # cum_dev[k] = sum(dev[0]..dev[k]).
            # Since sum(dev) over all block is 0 (by definition of mean), cum_dev ends at 0.
            
            # We need standard deviation S too. S^2 = sum(dev^2) / (B-1).
            
            current_sum_sq_dev = 0.0
            
            # Single pass for std dev and cum range?
            for k in range(block_size):
                val = data[start_idx + k]
                d = val - mean_val
                
                # Variance part
                current_sum_sq_dev += d * d
                
                # Cumsum part
                running_cum += d
                # Update min/max
                if k == 0:
                    min_cum = running_cum
                    max_cum = running_cum
                else:
                    if running_cum < min_cum:
                        min_cum = running_cum
                    if running_cum > max_cum:
                        max_cum = running_cum
                        
            # R
            R = max_cum - min_cum
            
            # S
            # ddof=1
            if block_size > 1:
                S = np.sqrt(current_sum_sq_dev / (block_size - 1))
            else:
                S = 0.0
                
            if S > 1e-12:
                sum_rs += R / S
                count += 1
                
        if count > 0:
            results[i] = sum_rs / count
        else:
            results[i] = np.nan
            
    return results
