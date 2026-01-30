"""
Common base class for LRDBenchmark estimators.

All estimators should inherit from BaseEstimator and follow a consistent
results contract. This module is intentionally light-weight and has
no heavy dependencies so it can be imported universally.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class BaseEstimator:
    """
    Minimal common interface for estimators.

    Conventions
    - parameters: dict of user-specified configuration
    - results: dict of computed outputs. At minimum for H estimators:
      - 'hurst_parameter': float
      - 'method': str
      Optional keys: 'r_squared', 'confidence_interval', 'diagnostics'
    """

    def __init__(self, **kwargs: Any) -> None:
        self.parameters: Dict[str, Any] = dict(kwargs)
        self.results: Dict[str, Any] = {}

    def __repr__(self) -> str:
        """String representation of the estimator."""
        class_name = self.__class__.__name__
        params_str = ", ".join(f"{k}={v!r}" for k, v in self.parameters.items())
        if params_str:
            return f"{class_name}({params_str})"
        return f"{class_name}()"

    def set_params(self, **kwargs: Any) -> "BaseEstimator":
        self.parameters.update(kwargs)
        return self

    def get_params(self) -> Dict[str, Any]:
        return dict(self.parameters)

    def get_results(self) -> Dict[str, Any]:
        if not self.results:
            raise ValueError("No results available. Run estimate() first.")
        return dict(self.results)

    # Backward-compatible aliases for legacy API
    def get_parameters(self) -> Dict[str, Any]:
        """Alias for get_params() for backward compatibility."""
        return self.get_params()

    def set_parameters(self, **kwargs: Any) -> None:
        """Alias for set_params() for backward compatibility."""
        self.set_params(**kwargs)

    def _validate_parameters(self) -> None:
        """Validate estimator parameters. Override in subclasses if needed."""
        pass

    # Subclasses must implement:
    # def estimate(self, data: np.ndarray) -> Dict[str, Any]: ...


