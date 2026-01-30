
from .numpy_backend import compute_structure_functions as compute_numpy

def compute_structure_functions(*args, **kwargs):
    return compute_numpy(*args, **kwargs)
