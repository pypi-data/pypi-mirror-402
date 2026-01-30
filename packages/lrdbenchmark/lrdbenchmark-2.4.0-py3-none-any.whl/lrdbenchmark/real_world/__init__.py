"""
Real-world data validation module.

This module provides tools for validating the presence of long-range dependence
in real-world datasets.
"""

from .validation import (
    RealWorldValidator,
    ValidationResult,
    ValidationMetrics
)

__all__ = [
    "RealWorldValidator",
    "ValidationResult",
    "ValidationMetrics",
]
