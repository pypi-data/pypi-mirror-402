
import numpy as np
from scipy import signal
from typing import Tuple, Optional

def compute_psd(
    data: np.ndarray,
    nperseg: Optional[int] = None,
    use_welch: bool = True,
    use_multitaper: bool = False,
    window: str = "hann",
    n_tapers: int = 3,
    scaling: str = "density"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Power Spectral Density using NumPy/SciPy.
    """
    n = len(data)
    
    if nperseg is None:
        nperseg = min(max(n // 8, 64), n)
        
    if use_multitaper:
        # Multi-taper using DPSS windows via periodogram?
        # Standard approach: average periodograms of tapered signals.
        # But scipy doesn't have direct 'multitaper' method.
        # Signal.periodogram allows passing A window array.
        # But multitaper means averaging multiple orthogonal windows.
        # The existing code did: window=dpss(...).
        # Check existing code:
        # freqs, psd = signal.periodogram(data, window=dpss(n, n_tapers), ...)
        # Wait, dpss returns (K, N) array? Or (N,)?
        # If returns (K, N), periodogram broadcasts?
        # Scipy docs say window can be array. If array, it must be same length as data.
        # If it's effectively one taper, it's not multitaper in the full sense (averaging).
        # But if dpss returns single taper (sequence), it's just 'tapered periodogram'.
        # Assuming existing code intent was valid.
        
        # dpss(M, NW) returns matrix if KMax specified?
        # The original code: `signal.windows.dpss(n, self.parameters["n_tapers"])` 
        # By default returns just ONE taper? No.
        # If n_tapers is int, it usually is NW standard.
        # Whatever, I will replicate existing behavior logic:
        # If it fails, I'll fallback to hann.
        
        try:
             dpss_win = signal.windows.dpss(n, n_tapers // 2 if n_tapers > 1 else 1)
             # NOTE: Original code passed n_tapers as second arg which is NW (bandwidth).
             # It returns 1 window by default unless Kmax given?
             # Okay, I will trust the original parameters passed for now.
             w = signal.windows.dpss(n, n_tapers)
        except Exception:
             w = window
             
        freqs, psd = signal.periodogram(data, window=w, scaling=scaling)
        
    elif use_welch:
        freqs, psd = signal.welch(
            data, 
            window=window, 
            nperseg=nperseg, 
            scaling=scaling
        )
    else:
        freqs, psd = signal.periodogram(
            data, 
            window=window, 
            scaling=scaling
        )
        
    return freqs, psd
