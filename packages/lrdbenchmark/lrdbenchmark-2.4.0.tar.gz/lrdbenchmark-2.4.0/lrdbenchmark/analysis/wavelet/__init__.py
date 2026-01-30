"""
Wavelet analysis estimators for LRDBench.

This module provides various wavelet-based estimators for analyzing long-range dependence
in time series data.
"""

# Import unified estimators
from .cwt_estimator import CWTEstimator
from .variance_estimator import WaveletVarianceEstimator
from .log_variance_estimator import WaveletLogVarianceEstimator
from .whittle_estimator import WaveletWhittleEstimator

__all__ = [
    "CWTEstimator",
    "WaveletVarianceEstimator",
    "WaveletLogVarianceEstimator",
    "WaveletWhittleEstimator",
]
