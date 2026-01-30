
import numpy as np
from typing import Tuple, List, Union

def compute_fluctuations(
    signal: np.ndarray, 
    scales: np.ndarray, 
    qs: np.ndarray,
    order: int
) -> np.ndarray:
    """
    Compute MFDFA fluctuation functions F_q(s).
    
    Returns array of shape (len(scales), len(qs)).
    """
    # 1. Profile
    y = np.cumsum(signal - np.mean(signal))
    n = len(y)
    
    fluctuations = np.zeros((len(scales), len(qs)))
    
    for i, scale in enumerate(scales):
        n_segments = n // scale
        if n_segments < 1:
            fluctuations[i, :] = np.nan
            continue
            
        length = n_segments * scale
        y_truncated = y[:length]
        segments = y_truncated.reshape((n_segments, scale))
        x = np.arange(scale)
        
        # Detrending (Vectorized polynomial fit)
        if order == 0:
            trends = np.mean(segments, axis=1, keepdims=True)
            detrended = segments - trends
        else:
            coeffs = np.polyfit(x, segments.T, order)
            # Eval trend
            # V: (scale, order+1)
            # coeffs: (order+1, n_segments)
            V = np.vander(x, order + 1)
            trend = np.dot(V, coeffs).T
            detrended = segments - trend
            
        # Variances (RMS^2)
        # F^2(v) = mean(residual^2)
        variances = np.mean(detrended**2, axis=1) # (n_segments,)
        
        # q-fluctuations
        # F_q(s) = [ 1/N * sum( (F^2(v))^(q/2) ) ]^(1/q)
        
        for j, q in enumerate(qs):
            if abs(q) < 1e-10:
                # q -> 0 case: exp(0.5 * mean(log(variances)))
                # Handling zero variance?
                # Usually we ignore or replace with epsilon.
                # However, exact zeros in F^2 are rare unless perfect fit.
                # Adding small epsilon for log stability
                
                # Filter zeros?
                # Only if variances <= 0
                valid = variances > 1e-16
                if np.sum(valid) == 0:
                    f_q = np.nan
                else:
                    log_v = np.log(variances[valid])
                    f_q = np.exp(0.5 * np.mean(log_v))
            else:
                # F_q(s) = mean( variances^(q/2) )^(1/q)
                # variances can be 0.
                term = variances ** (q / 2.0)
                mean_term = np.mean(term)
                f_q = np.power(mean_term, 1.0 / q)
                
            fluctuations[i, j] = f_q
            
    return fluctuations
