#!/usr/bin/env python3
"""
Unified DFA (Detrended Fluctuation Analysis) Estimator.
Refactored to use modular backends (NumPy, JAX, Numba).
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from typing import Dict, Any, Optional, Union, Tuple, List
import warnings

from lrdbenchmark.analysis.backend_utils import select_backend, JAX_AVAILABLE, NUMBA_AVAILABLE
from lrdbenchmark.analysis.base_estimator import BaseEstimator
from .dfa_backends import numpy_backend

# Optional backends
try:
    from .dfa_backends import jax_backend
except ImportError:
    jax_backend = None

try:
    from .dfa_backends import numba_backend
except ImportError:
    numba_backend = None


class DFAEstimator(BaseEstimator):
    """
    Unified DFA Estimator with modular backend support.
    
    Backends:
    - 'jax': GPU/TPU accelerated (if available)
    - 'numba': CPU JIT compiled (parallelized)
    - 'numpy': Reference implementation
    """

    def __init__(
        self,
        min_scale: int = 10,
        max_scale: Optional[int] = None,
        num_scales: int = 10,
        order: int = 1,
        use_optimization: str = "auto",
    ):
        super().__init__()
        self.parameters = {
            "min_scale": min_scale,
            "max_scale": max_scale,
            "num_scales": num_scales,
            "order": order,
        }
        self.optimization_framework = select_backend(use_optimization)
        self.results = {}
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        if self.parameters["min_scale"] < 4:
            raise ValueError("min_scale must be at least 4")
        if self.parameters["max_scale"] is not None and self.parameters["max_scale"] <= self.parameters["min_scale"]:
            raise ValueError("max_scale must be greater than min_scale")
        if self.parameters["num_scales"] < 3:
            raise ValueError("num_scales must be at least 3")
        if self.parameters["order"] < 0:
            raise ValueError("order must be non-negative")

    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Estimate Hurst parameter using DFA.
        Delegates calculation to the selected backend.
        """
        data = np.asarray(data)
        n = len(data)
        
        if n < 100:
            warnings.warn("Data length is small, results may be unreliable")

        # Set max_scale if None
        max_scale = self.parameters["max_scale"]
        if max_scale is None:
            max_scale = n // 4
            
        # Generate scales
        scales = np.logspace(
            np.log10(self.parameters["min_scale"]),
            np.log10(max_scale),
            self.parameters["num_scales"],
            dtype=int
        )
        scales = np.unique(scales)
        scales = scales[scales <= n // 2]
        
        if len(scales) < 3:
            raise ValueError("Insufficient valid scales for analysis")

        # Select Backend Strategy
        backend_name = self.optimization_framework
        compute_func = self._get_compute_function(backend_name)
        
        # Execute Computation
        try:
            fluctuation_values = compute_func(data, scales, self.parameters["order"])
        except Exception as e:
            warnings.warn(f"Backend '{backend_name}' failed: {e}. Falling back to NumPy.")
            fluctuation_values = numpy_backend.compute_fluctuations(data, scales, self.parameters["order"])
            backend_name = "numpy (fallback)"

        # Post-Processing (Regression)
        # Ensure outputs are NumPy arrays (JAX might return jnp array on host)
        fluctuation_values = np.asarray(fluctuation_values)
        scales = np.asarray(scales)
        
        valid_mask = (fluctuation_values > 0) & ~np.isnan(fluctuation_values)
        if np.sum(valid_mask) < 3:
            raise ValueError("Insufficient valid fluctuation values for analysis")
            
        valid_scales = scales[valid_mask]
        valid_fluctuations = fluctuation_values[valid_mask]
        
        log_scales = np.log(valid_scales)
        log_fluctuations = np.log(valid_fluctuations)
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_scales, log_fluctuations)
        
        self.results = {
            "hurst_parameter": float(slope),
            "r_squared": float(r_value**2),
            "slope": float(slope),
            "intercept": float(intercept),
            "p_value": float(p_value),
            "std_error": float(std_err),
            "scales": valid_scales.tolist(),
            "fluctuation_values": valid_fluctuations.tolist(),
            "log_scales": log_scales.tolist(),
            "log_fluctuations": log_fluctuations.tolist(),
            "method": backend_name,
            "optimization_framework": self.optimization_framework
        }
        
        return self.results
        
    def _get_compute_function(self, backend: str):
        """Factory method for backend strategy."""
        if backend == 'jax':
            if jax_backend and jax_backend.JAX_AVAILABLE:
                return jax_backend.compute_fluctuations
            warnings.warn("JAX requested but not available. Falling back to NumPy.")
            return numpy_backend.compute_fluctuations
            
        if backend == 'numba':
            if numba_backend and numba_backend.NUMBA_AVAILABLE:
                return numba_backend.compute_fluctuations
            warnings.warn("Numba requested but not available. Falling back to NumPy.")
            return numpy_backend.compute_fluctuations
            
        return numpy_backend.compute_fluctuations

    def get_optimization_info(self) -> Dict[str, Any]:
        return {
            "current_framework": self.optimization_framework,
            "jax_available": getattr(jax_backend, 'JAX_AVAILABLE', False),
            "numba_available": getattr(numba_backend, 'NUMBA_AVAILABLE', False),
            "recommended_framework": self._get_recommended_framework()
        }

    def _get_recommended_framework(self) -> str:
        if getattr(jax_backend, 'JAX_AVAILABLE', False):
            return "jax"
        elif getattr(numba_backend, 'NUMBA_AVAILABLE', False):
            return "numba"
        else:
            return "numpy"

    def plot_analysis(self, figsize: Tuple[int, int] = (12, 8), save_path: Optional[str] = None) -> None:
        """Plot the DFA analysis results."""
        if not self.results:
            raise ValueError("No results available. Run estimate() first.")

        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('DFA Analysis Results', fontsize=16)

        # Plot 1: Log-log relationship
        ax1 = axes[0, 0]
        x = self.results["log_scales"]
        y = self.results["log_fluctuations"]
        ax1.scatter(x, y, s=60, alpha=0.7, label="Data points")
        
        slope = self.results["slope"]
        intercept = self.results["intercept"]
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = slope * x_fit + intercept
        ax1.plot(x_fit, y_fit, "r--", label=f"Linear fit (slope={slope:.3f})")
        
        ax1.set_xlabel("log(Scale)")
        ax1.set_ylabel("log(Fluctuation)")
        ax1.set_title("DFA Scaling")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Fluctuation vs Scale (log-log)
        ax2 = axes[0, 1]
        scales = self.results["scales"]
        fluctuations = self.results["fluctuation_values"]
        ax2.scatter(scales, fluctuations, s=60, alpha=0.7)
        ax2.set_xscale("log")
        ax2.set_yscale("log")
        ax2.set_xlabel("Scale")
        ax2.set_ylabel("Fluctuation")
        ax2.set_title("Fluctuation vs Scale (log-log)")
        ax2.grid(True, which="both", ls=":", alpha=0.3)

        # Plot 3: Hurst parameter estimate
        ax3 = axes[1, 0]
        hurst = self.results["hurst_parameter"]
        ax3.bar(["Hurst Parameter"], [hurst], alpha=0.7, color='skyblue')
        ax3.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='H=0.5 (no memory)')
        ax3.set_ylabel("Hurst Parameter")
        ax3.set_title(f"Hurst Parameter Estimate: {hurst:.3f}")
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Plot 4: R-squared
        ax4 = axes[1, 1]
        r_squared = self.results["r_squared"]
        ax4.bar(["R²"], [r_squared], alpha=0.7, color='lightgreen')
        ax4.set_ylabel("R²")
        ax4.set_title(f"Goodness of Fit: R² = {r_squared:.3f}")
        ax4.set_ylim(0, 1)
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.show()

    def get_method_recommendation(self, n: int) -> Dict[str, Any]:
        """Get method recommendation for a given data size."""
        # Kept for compatibility / completeness
        if n < 100:
            return {"recommended_method": "numpy", "reasoning": "Small size"}
        elif n < 1000:
            return {"recommended_method": "numba", "reasoning": "Medium size benefits from JIT"}
        else:
            return {"recommended_method": "jax", "reasoning": "Large size benefits from GPU"}
