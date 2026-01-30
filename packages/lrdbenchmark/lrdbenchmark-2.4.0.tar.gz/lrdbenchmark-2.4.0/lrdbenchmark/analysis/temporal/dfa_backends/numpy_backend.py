
import numpy as np
from typing import Tuple, List, Union

def compute_fluctuations(
    signal: np.ndarray, 
    scales: np.ndarray, 
    order: int
) -> np.ndarray:
    """
    Compute DFA fluctuation function F(s) using NumPy.
    
    Parameters
    ----------
    signal : np.ndarray
        Input time series data (1D).
    scales : np.ndarray
        Array of scales (window sizes) to compute F(s) for.
    order : int
        Order of the detrending polynomial (1 = linear, 2 = quadratic).
        
    Returns
    -------
    np.ndarray
        Fluctuation values F(s) corresponding to each scale.
        Returns NaN for scales where computation is impossible.
    """
    # 1. Integration (Cumulative Sum) - Remove mean before cumsum to avoid drift
    # "Profile" Y(i)
    # Ideally subtract global mean first
    y = np.cumsum(signal - np.mean(signal))
    n = len(y)
    
    fluctuations = []
    
    for scale in scales:
        n_segments = n // scale
        if n_segments < 1:
            fluctuations.append(np.nan)
            continue
            
        # Reshape into segments (truncate leftover)
        # We can implement this vectorially for a SINGLE scale using reshape
        # This is faster than looping segments in python if n_segments is large
        
        # Truncate
        length = n_segments * scale
        y_truncated = y[:length]
        
        # Segments shape: (n_segments, scale)
        segments = y_truncated.reshape((n_segments, scale))
        
        # Detrending
        x = np.arange(scale)
        
        if order == 0:
            # Remove mean of each segment
            # segments.mean(axis=1) -> shape (n_segments,)
            # broadcast subtraction
            trends = np.mean(segments, axis=1, keepdims=True)
            detrended = segments - trends
        else:
            # Polynomial detrending
            # We need to fit poly for EACH segment.
            # Polyfit in numpy on 2D array: np.polyfit(x, y.T, deg)
            # x is shape (scale,), y.T is (scale, n_segments)
            # Returns coeffs shape (deg+1, n_segments)
            coeffs = np.polyfit(x, segments.T, order)
            
            # Evaluate trend
            # coeffs is (deg+1, n_segments)
            # x is (scale,)
            # np.polyval(coeffs, x) -> ?
            # Not directly broadcastable easily in standard polyval for multiple columns?
            # Actually standard polyval expects 1D p.
            # We can construct trend manually: Y = V @ C
            # Vandermonde matrix V: (scale, order+1)
            # C: (order+1, n_segments)
            # Trend = (V @ C).T -> (n_segments, scale)
            
            # coeffs from polyfit are high-to-low power.
            # method 1: manual construction
            trend_T = np.zeros_like(segments.T)
            # for i in range(order + 1):
            #    trend_T += coeffs[i, :] * (x ** (order - i)) # Broadcasting issues?
            
            # Faster approach: Vandermonde
            V = np.vander(x, order + 1) # (scale, order+1)
            # coeffs is (order+1, n_segments)
            trend = np.dot(V, coeffs).T # (n_segments, scale)
            
            detrended = segments - trend
            
        # RMS of detrended
        # Variance per segment: mean(detrended^2)
        # F2(s) = mean( variances )
        # F(s) = sqrt(F2(s))
        
        variances = np.mean(detrended**2, axis=1) # (n_segments,)
        f_s = np.sqrt(np.mean(variances))
        fluctuations.append(f_s)
        
    return np.array(fluctuations)
