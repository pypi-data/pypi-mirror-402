
import numpy as np
import pywt
from typing import List, Union, Tuple

def compute_structure_functions(
    data: np.ndarray,
    wavelet: str,
    scales: np.ndarray,
    q_values: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute structure functions S_L(q,j).
    Returns (SL, js) where js matches scales.
    
    SL shape: (q_values.size, scales.size)
    """
    n = len(data)
    
    # Compute full DWT
    w = pywt.Wavelet(wavelet)
    # PyWT max level?
    # We need enough levels for the requested scales.
    # max(scales) implies level J?
    # Actually scales usually means 'j'.
    max_j = max(scales)
    coeffs = pywt.wavedec(data, w, mode='periodization', level=max_j)
    
    # coeffs: [approx, detail_J, detail_J-1, ..., detail_1] (pywt order)
    # Need to verify pywt output order again.
    # approximation, details(level J), details(level J-1), ..., details(level 1).
    # so coeffs[-1] is level 1. coeffs[-j] is level j.
    # _estimate_numpy used: `abs_details = [np.abs(c) for c in coeffs[-1:0:-1]]`
    # this means [level 1, level 2, ..., level J].
    # YES.
    
    details_ordered = coeffs[-1:0:-1]
    abs_details = [np.abs(c) for c in details_ordered]
    
    leaders = _leaders_from_dwt(abs_details)
    
    js = scales.astype(float)
    SL = np.zeros((q_values.size, js.size), dtype=float)
    
    for jj, j in enumerate(scales):
        # j is 1-based scale index. 1 -> leaders[0].
        idx = j - 1
        if 0 <= idx < len(leaders):
            Lj = leaders[idx]
            
            for qi, q in enumerate(q_values):
                if np.isclose(q, 0.0):
                    SL[qi, jj] = float(np.exp(np.mean(np.log(Lj + 1e-18))))
                else:
                    SL[qi, jj] = float(np.mean((Lj + 1e-18) ** q))
        else:
            SL[:, jj] = np.nan
            
    return SL, js

def _leaders_from_dwt(detail_coeffs: List[np.ndarray]) -> List[np.ndarray]:
    J = len(detail_coeffs)
    leaders = []
    for j in range(J):
        Dj = detail_coeffs[j]
        n_len = len(Dj)
        Ljk = np.zeros(n_len, dtype=float)
        
        # Vectorized Neighborhood? 
        # The loop in original code is explicit.
        # Can we vectorize? 
        # Use np.roll or sliding window view? 
        # Using simple loop for fidelity with original implementation now.
        # (Original loop was manual).
        
        # Optimization: Use convolution/maximum filter?
        # A 3-tap max filter on Dj, plus max-pooling from finer scales.
        # But finer scales Df aligns differently (2*k).
        
        # Keeping original manual logic for now to ensure correctness during refactor.
        # This backend is called 'numpy' but explicit looping in python is slow.
        # BUT this is the reference implementation from the class.
        
        for k in range(n_len):
            neigh = [Dj[max(0, k - 1) : min(n_len, k + 2)]]
            if j > 0:
                Df = detail_coeffs[j - 1]
                start = 2 * k - 2
                idx = np.arange(max(0, start), min(len(Df), start + 5))
                if idx.size > 0: neigh.append(Df[idx])
            if j > 1:
                Df2 = detail_coeffs[j - 2]
                start2 = 4 * k - 4
                idx2 = np.arange(max(0, start2), min(len(Df2), start2 + 9))
                if idx2.size > 0: neigh.append(Df2[idx2])
            
            if len(neigh) > 0:
                Ljk[k] = float(np.max(np.concatenate(neigh)))
            else:
                 Ljk[k] = float(np.abs(Dj[k]))
                 
        leaders.append(Ljk + 1e-18)
    return leaders
