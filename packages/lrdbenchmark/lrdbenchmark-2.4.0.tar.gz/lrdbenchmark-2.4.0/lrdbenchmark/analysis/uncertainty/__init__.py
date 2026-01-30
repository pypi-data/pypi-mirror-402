"""
Uncertainty quantification utilities for LRDBenchmark.

This package provides reusable confidence interval estimators based on
block bootstrap, wavelet-domain resampling, and parametric Monte Carlo
simulation. The utilities are designed to work with any estimator that
offers a ``get_params`` method (from :class:`~lrdbenchmark.analysis.base_estimator.BaseEstimator`)
and exposes a ``hurst_parameter`` in its results dictionary.
"""

from .quantifier import UncertaintyQuantifier
from .coverage_analyzer import CoverageAnalyzer, CoverageResult, run_comprehensive_coverage_analysis

__all__ = [
    "UncertaintyQuantifier",
    "CoverageAnalyzer",
    "CoverageResult",
    "run_comprehensive_coverage_analysis"
]
