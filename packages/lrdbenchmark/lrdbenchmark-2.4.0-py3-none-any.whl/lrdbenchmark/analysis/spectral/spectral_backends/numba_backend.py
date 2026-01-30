
# Numba backend for spectral analysis
# Currently delegates to NumPy/SciPy as Numba FFT support is limited in nopython mode
# and Scipy is already optimized.

from .numpy_backend import compute_psd as compute_psd_numpy
import warnings

NUMBA_AVAILABLE = False # No specific numba optimization provided

def compute_psd(*args, **kwargs):
    # Just pass through
    return compute_psd_numpy(*args, **kwargs)
