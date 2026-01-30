
# Numba backend for wavelet analysis
# Currently delegates to NumPy (PyWavelets) as PyWt C-extensions are efficient.

from .numpy_backend import compute_variances as compute_variances_numpy

def compute_variances(*args, **kwargs):
    return compute_variances_numpy(*args, **kwargs)
