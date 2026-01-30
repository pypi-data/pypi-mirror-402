#!/usr/bin/env python3
"""
Unified R/S (Rescaled Range) Estimator.
Refactored to use modular backends (NumPy, JAX, Numba).
"""

import math
import os
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, Union, Tuple, List, Sequence
import warnings
from scipy import stats

from lrdbenchmark.analysis.base_estimator import BaseEstimator
from lrdbenchmark.analysis.backend_utils import select_backend, JAX_AVAILABLE, NUMBA_AVAILABLE

from .rs_backends import numpy_backend

# Optional backends
try:
    from .rs_backends import jax_backend
except ImportError:
    jax_backend = None

try:
    from .rs_backends import numba_backend
except ImportError:
    numba_backend = None


class RSEstimator(BaseEstimator):
    """
    Unified R/S (Rescaled Range) Estimator for Long-Range Dependence Analysis.
    
    Backends:
    - 'jax': GPU/TPU accelerated (if available)
    - 'numba': CPU JIT compiled
    - 'numpy': Reference implementation
    """

    def __init__(
        self,
        min_block_size: Optional[int] = None,
        max_block_size: Optional[int] = None,
        num_blocks: Optional[int] = None,
        use_optimization: str = "auto",
        *,
        min_window_size: Optional[int] = None,
        max_window_size: Optional[int] = None,
        num_windows: Optional[int] = None,
        window_sizes: Optional[Sequence[int]] = None,
        overlap: bool = False,
    ) -> None:
        # Legacy parameter bridging
        if min_window_size is not None: min_block_size = min_window_size
        if max_window_size is not None: max_block_size = max_window_size
        if num_windows is not None: num_blocks = num_windows

        # Defaults
        min_block_size = 10 if min_block_size is None else int(min_block_size)
        num_blocks = 10 if num_blocks is None else int(num_blocks)

        sanitized_windows = None
        if window_sizes is not None:
            sanitized_windows = self._sanitize_window_sizes(window_sizes)
            params_window = sanitized_windows.tolist()
        else:
            params_window = None

        super().__init__()
        self.parameters = {
            "min_block_size": int(min_block_size),
            "max_block_size": int(max_block_size) if max_block_size is not None else None,
            "num_blocks": int(num_blocks),
            "window_sizes": params_window,
            "overlap": bool(overlap),
        }
        
        self.optimization_framework = select_backend(use_optimization)
        self.results = {}
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        if self.parameters["min_block_size"] < 4:
            raise ValueError("min_block_size must be at least 4")
        if self.parameters["max_block_size"] is not None and self.parameters["max_block_size"] <= self.parameters["min_block_size"]:
            raise ValueError("max_block_size must be greater than min_block_size")
        if self.parameters["num_blocks"] < 3 and self.parameters["window_sizes"] is None:
            raise ValueError("num_blocks must be at least 3")
            
        if self.parameters["window_sizes"] is not None:
             windows = np.asarray(self.parameters["window_sizes"], dtype=int)
             if len(windows) < 3:
                 raise ValueError("Need at least 3 window sizes")

    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Estimate Hurst parameter using R/S analysis.
        """
        data = np.asarray(data)
        n = len(data)
        
        if n < 50:
            warnings.warn("Data length is very small, results may be unreliable")

        # Resolve block sizes
        block_sizes = self._resolve_block_sizes(n)
        
        # Select Backend Strategy
        backend_name = self.optimization_framework
        compute_func = self._get_compute_function(backend_name)
        
        # Execute
        try:
            rs_values = compute_func(data, block_sizes)
        except Exception as e:
            warnings.warn(f"Backend '{backend_name}' failed: {e}. Falling back to NumPy.")
            rs_values = numpy_backend.compute_rs(data, block_sizes)
            backend_name = "numpy (fallback)"
            
        # Post-Processing
        rs_values = np.asarray(rs_values)
        block_sizes = np.asarray(block_sizes)
        
        valid_mask = (rs_values > 0) & ~np.isnan(rs_values)
        if np.sum(valid_mask) < 3:
            raise ValueError("Insufficient valid R/S values for regression")
            
        valid_blocks = block_sizes[valid_mask]
        valid_rs = rs_values[valid_mask]
        
        return self._build_results(
            block_sizes=valid_blocks,
            rs_values=valid_rs,
            method="rs_analysis",
            framework=backend_name
        )

    def _get_compute_function(self, backend: str):
        if backend == 'jax':
            if jax_backend and jax_backend.JAX_AVAILABLE:
                return jax_backend.compute_rs
            warnings.warn("JAX requested but not available. Falling back to NumPy.")
            return numpy_backend.compute_rs
            
        if backend == 'numba':
            if numba_backend and numba_backend.NUMBA_AVAILABLE:
                return numba_backend.compute_rs
            warnings.warn("Numba requested but not available. Falling back to NumPy.")
            return numpy_backend.compute_rs
            
        return numpy_backend.compute_rs

    def _resolve_block_sizes(self, n: int) -> np.ndarray:
        """Construct block sizes."""
        if self.parameters["window_sizes"] is not None:
            windows = np.array(self.parameters["window_sizes"], dtype=int)
        else:
            max_block = self.parameters["max_block_size"]
            if max_block is None:
                max_block = max(self.parameters["min_block_size"] + 1, n // 4)
            
            # Logspace
            windows = np.logspace(
                np.log10(self.parameters["min_block_size"]),
                np.log10(max_block),
                self.parameters["num_blocks"],
                dtype=int
            )
            windows = np.unique(windows)
            
        # Filter
        valid = windows[(windows >= self.parameters["min_block_size"]) & (windows <= n // 2)]
        if len(valid) < 3:
            # Fallback if aggressive expectations failed?
            # Or raise error
            raise ValueError(f"Need at least 3 valid window sizes (found {len(valid)}). Data length {n} might be too short for current parameters.")
        return valid

    def _sanitize_window_sizes(self, window_sizes: Sequence[int]) -> np.ndarray:
        windows = np.array(window_sizes, dtype=int)
        if np.any(windows <= 0):
            raise ValueError("Window sizes must be positive integers")
        return windows

    def _build_results(self, block_sizes, rs_values, method, framework):
        log_blocks = np.log(block_sizes)
        log_rs = np.log(rs_values)
        
        slope, intercept, r_squared, p_value, std_err = self._linear_regression(log_blocks, log_rs)
        
        hurst = slope
        conf_int = self._compute_confidence_interval(hurst, std_err, len(block_sizes))
        
        results = {
            "hurst_parameter": float(hurst),
            "r_squared": float(r_squared),
            "slope": float(slope),
            "intercept": float(intercept),
            "p_value": float(p_value),
            "std_error": float(std_err),
            "block_sizes": block_sizes.tolist(),
            "rs_values": rs_values.tolist(),
            "log_block_sizes": log_blocks.tolist(),
            "log_rs_values": log_rs.tolist(),
            "confidence_interval": conf_int,
            "method": method,
            "optimization_framework": framework
        }
        self.results = results
        return results

    def _linear_regression(self, x, y):
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return slope, intercept, r_value**2, p_value, std_err

    def _compute_confidence_interval(self, hurst, std_err, n, confidence=0.95):
        if not np.isfinite(std_err) or std_err <= 0 or n < 3:
            return [float("nan"), float("nan")]
        alpha = 1.0 - confidence
        dof = max(n - 2, 1)
        critical = stats.t.ppf(1 - alpha / 2, dof)
        margin = critical * std_err
        return [float(hurst - margin), float(hurst + margin)]

    def get_optimization_info(self) -> Dict[str, Any]:
        return {
            "current_framework": self.optimization_framework,
            "jax_available": getattr(jax_backend, 'JAX_AVAILABLE', False),
            "numba_available": getattr(numba_backend, 'NUMBA_AVAILABLE', False),
            "recommended_framework": "jax" if getattr(jax_backend, 'JAX_AVAILABLE', False) else ("numba" if getattr(numba_backend, 'NUMBA_AVAILABLE', False) else "numpy")
        }

    # API Compatibility
    def get_confidence_intervals(self, confidence_level=0.95):
        # Stub or implement if needed. 
        # Original just returned dict?
        # Leaving minimal impl
        return {}
