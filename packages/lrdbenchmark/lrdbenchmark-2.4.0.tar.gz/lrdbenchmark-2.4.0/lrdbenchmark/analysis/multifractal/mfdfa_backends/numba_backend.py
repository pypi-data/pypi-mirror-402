
from .numpy_backend import compute_fluctuations as compute_fluctuations_numpy

def compute_fluctuations(*args, **kwargs):
    return compute_fluctuations_numpy(*args, **kwargs)
