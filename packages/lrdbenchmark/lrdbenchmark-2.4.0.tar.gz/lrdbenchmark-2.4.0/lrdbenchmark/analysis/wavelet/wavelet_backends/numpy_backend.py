
import numpy as np
import pywt
from typing import Dict, Any, List, Optional, Tuple, Union

def compute_variances(
    data: np.ndarray,
    wavelet: str,
    scales: List[int],
    robust: bool = False
) -> Tuple[Dict[int, float], Dict[int, int]]:
    """
    Compute wavelet variances for specified scales using PyWavelets.
    
    Returns:
        variances: Dict[scale, variance]
        counts: Dict[scale, num_coeffs]
    """
    n = len(data)
    
    # We need DWT up to max scale.
    # wavedec returns [cA_n, cD_n, cD_n-1, ..., cD_1]
    # Level j corresponds to cD_j.
    # In pywt list, level 1 is LAST element. Level J is SECOND element (after approx).
    
    max_scale = max(scales)
    coeffs = pywt.wavedec(
        data,
        wavelet,
        level=max_scale,
        mode="periodization",
    )
    
    # coeffs[0] is approximation at level=max_scale
    # coeffs[1] is detail at level=max_scale
    # coeffs[-j] is detail at level=j
    
    variances = {}
    counts = {}
    
    for j in scales:
        # Get details for level j
        # In wavedec output:
        # index -1 -> level 1
        # index -j -> level j
        try:
             detail_coeffs = coeffs[-j]
        except IndexError:
             # Should not happen if max_scale is correct
             continue
             
        counts[j] = len(detail_coeffs)

        if robust:
            med = np.median(detail_coeffs)
            mad = np.median(np.abs(detail_coeffs - med))
            sigma = mad / 0.6744897501960817
            variance = float(sigma ** 2)
        else:
            variance = float(np.var(detail_coeffs, ddof=1))
            
        variances[j] = variance
        
    return variances, counts
