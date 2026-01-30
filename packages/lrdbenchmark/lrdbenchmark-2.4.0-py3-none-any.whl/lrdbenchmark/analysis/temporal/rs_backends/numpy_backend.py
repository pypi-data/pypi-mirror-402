
import numpy as np
from typing import List, Union

def compute_rs(
    data: np.ndarray, 
    block_sizes: np.ndarray 
) -> np.ndarray:
    """
    Compute R/S statistic for each block size using NumPy.
    
    Parameters
    ----------
    data : np.ndarray
        Input time series data.
    block_sizes : np.ndarray
        Array of block sizes to compute R/S for.
        
    Returns
    -------
    np.ndarray
        Mean R/S value for each block size.
        Returns NaN where computation is impossible.
    """
    n = len(data)
    results = []
    
    for block_size in block_sizes:
        block_size = int(block_size)
        n_blocks = n // block_size
        
        if n_blocks < 1:
            results.append(np.nan)
            continue
            
        rs_values = []
        for i in range(n_blocks):
            start_idx = i * block_size
            end_idx = start_idx + block_size
            block_data = data[start_idx:end_idx]
            
            # RS Calculation for this block
            # 1. Mean
            mean_val = np.mean(block_data)
            
            # 2. Deviations and Cumsum
            dev = block_data - mean_val
            cum_dev = np.cumsum(dev)
            
            # 3. Range R
            # R = max(Y) - min(Y). 
            # Note: Standard definition usually includes endpoints or Y starting at 0?
            # Usually: Y[k] = sum(x[i] - mean). k=1..N.
            # Range is max(Y) - min(Y).
            # Some defs use max(Y) - min(Y) where min(Y) can be negative.
            # Yes, correct.
            R = np.max(cum_dev) - np.min(cum_dev)
            
            # 4. Standard Deviation S
            # std(data)
            S = np.std(block_data, ddof=1)
            
            if S > 0:
                rs_values.append(R / S)
                
        if len(rs_values) == 0:
            results.append(np.nan)
        else:
            results.append(np.mean(rs_values))
            
    return np.array(results)
