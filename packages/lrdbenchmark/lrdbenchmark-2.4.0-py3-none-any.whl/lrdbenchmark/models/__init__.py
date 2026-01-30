"""
Models package for synthetic data generation.

This package contains implementations of various stochastic models:
- ARFIMA (AutoRegressive Fractionally Integrated Moving Average)
- fBm (Fractional Brownian Motion)
- fGn (Fractional Gaussian Noise)
- MRW (Multifractal Random Walk)
"""

__version__ = "0.1.0"
__author__ = "LRDBench Development Team"

# Import data models directly since they are now part of the package structure
try:
    from .data_models import (
        FBMModel,
        FGNModel,
        ARFIMAModel,
        MRWModel,
        AlphaStableModel
    )
except ImportError as e:
    # This might happen if dependencies are missing, e.g. numpy
    print(f"Warning: Could not import data models: {e}")
    FBMModel = None
    FGNModel = None
    ARFIMAModel = None
    MRWModel = None
    AlphaStableModel = None

__all__ = [
    "FBMModel",
    "FGNModel", 
    "ARFIMAModel",
    "MRWModel",
    "AlphaStableModel",
]
