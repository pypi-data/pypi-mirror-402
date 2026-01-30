"""
Spectral analysis estimators for LRDBench.

This module provides various spectral estimators for analyzing long-range dependence
in time series data using frequency domain methods.
"""

# Import unified estimators
# Import unified estimators
from .gph_estimator import GPHEstimator
from .periodogram_estimator import PeriodogramEstimator
from .whittle_estimator import WhittleEstimator

__all__ = [
    "GPHEstimator",
    "PeriodogramEstimator",
    "WhittleEstimator",
]
