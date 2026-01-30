#!/usr/bin/env python3
"""
Unified Periodogram-based Hurst parameter estimator.
Refactored to use modular backends (NumPy, JAX).
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from typing import Dict, Any, Optional, Union, Tuple
import warnings

from lrdbenchmark.analysis.base_estimator import BaseEstimator
from lrdbenchmark.analysis.backend_utils import select_backend, JAX_AVAILABLE, NUMBA_AVAILABLE

from .spectral_backends import numpy_backend

# Optional backends
try:
    from .spectral_backends import jax_backend
except ImportError:
    jax_backend = None

try:
    from .spectral_backends import numba_backend
except ImportError:
    numba_backend = None


class PeriodogramEstimator(BaseEstimator):
    """
    Unified Periodogram-based Hurst parameter estimator.
    
    This estimator computes the power spectral density (PSD) of the time series
    and fits a power law to the low-frequency portion to estimate the Hurst
    parameter. The relationship is: PSD(f) ~ f^(-beta) where beta = 2H - 1.

    Backends:
    - 'jax': GPU-accelerated FFT (Welch/Periodogram).
    - 'numpy': SciPy-based (Periodogram/Welch/Multitaper).
    - 'numba': Defaults to NumPy backend.
    """

    def __init__(
        self,
        min_freq_ratio: float = 0.01,
        max_freq_ratio: float = 0.1,
        use_welch: bool = True,
        window: str = "hann",
        nperseg: Optional[int] = None,
        use_multitaper: bool = False,
        n_tapers: int = 3,
        use_optimization: str = "auto",
    ):
        super().__init__()
        
        self.parameters = {
            "min_freq_ratio": min_freq_ratio,
            "max_freq_ratio": max_freq_ratio,
            "use_welch": use_welch,
            "window": window,
            "nperseg": nperseg,
            "use_multitaper": use_multitaper,
            "n_tapers": n_tapers,
        }
        
        self.optimization_framework = select_backend(use_optimization)
        self.results = {}
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        if not (0 < self.parameters["min_freq_ratio"] < self.parameters["max_freq_ratio"] < 0.5):
            raise ValueError("Frequency ratios must satisfy: 0 < min_freq_ratio < max_freq_ratio < 0.5")
        if self.parameters["n_tapers"] < 1:
            raise ValueError("n_tapers must be at least 1")
        if self.parameters["nperseg"] is not None and self.parameters["nperseg"] < 2:
            raise ValueError("nperseg must be at least 2")

    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Estimate Hurst parameter using periodogram analysis.
        """
        data = np.asarray(data)
        n = len(data)
        
        if n < 100:
            warnings.warn("Data length is small, results may be unreliable")

        # Select Backend Strategy
        backend_name = self.optimization_framework
        compute_func = self._get_compute_function(backend_name)
        
        # Prepare parameters for backend
        psd_params = {
            "nperseg": self.parameters["nperseg"],
            "use_welch": self.parameters["use_welch"],
            "use_multitaper": self.parameters["use_multitaper"],
            "window": self.parameters["window"],
            "n_tapers": self.parameters["n_tapers"]
        }
        
        # Compute PSD
        try:
            freqs, psd = compute_func(data, **psd_params)
        except Exception as e:
            warnings.warn(f"Backend '{backend_name}' failed: {e}. Falling back to NumPy.")
            freqs, psd = numpy_backend.compute_psd(data, **psd_params)
            backend_name = "numpy (fallback)"
            
        # Perform Regression
        return self._fit_power_law(freqs, psd, backend_name)

    def _fit_power_law(self, freqs, psd, backend_name):
        """Fit power law to the PSD."""
        # Ensure arrays
        freqs = np.asarray(freqs)
        psd = np.asarray(psd)
        
        # Select frequency range for fitting
        nyquist = 0.5
        min_freq = self.parameters["min_freq_ratio"] * nyquist
        max_freq = self.parameters["max_freq_ratio"] * nyquist

        mask = (freqs >= min_freq) & (freqs <= max_freq)
        freqs_sel = freqs[mask]
        psd_sel = psd[mask]

        if len(freqs_sel) < 3:
            raise ValueError("Insufficient frequency points for fitting")

        # Filter out zero/negative PSD values (log safety)
        valid_mask = psd_sel > 0
        freqs_sel = freqs_sel[valid_mask]
        psd_sel = psd_sel[valid_mask]

        if len(freqs_sel) < 3:
            raise ValueError("Insufficient valid PSD points for fitting")

        # Log-log regression: log(PSD) vs log(frequency)
        log_freq = np.log(freqs_sel)
        log_psd = np.log(psd_sel)

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_freq, log_psd)
        
        # Power law exponent: PSD(f) ~ f^(-beta)
        beta = -slope
        
        # Hurst: beta = 2H - 1 => H = (beta + 1) / 2
        hurst = (beta + 1) / 2
        hurst = np.clip(hurst, 0.01, 0.99)

        self.results = {
            "hurst_parameter": float(hurst),
            "beta": float(beta),
            "intercept": float(intercept),
            "slope": float(slope),
            "r_squared": float(r_value**2),
            "p_value": float(p_value),
            "std_error": float(std_err),
            "m": int(len(freqs_sel)),
            "log_freq": log_freq,
            "log_psd": log_psd,
            "frequency": freqs_sel,
            "periodogram": psd_sel,
            "method": "periodogram",
            "optimization_framework": backend_name,
        }
        return self.results

    def _get_compute_function(self, backend: str):
        if backend == 'jax':
            if jax_backend and jax_backend.JAX_AVAILABLE:
                return jax_backend.compute_psd
            warnings.warn("JAX requested but not available. Falling back to NumPy.")
            return numpy_backend.compute_psd
            
        if backend == 'numba':
            # Numba backend essentially delegates to numpy, but allows future extensions
            return numpy_backend.compute_psd
            
        return numpy_backend.compute_psd

    def get_optimization_info(self) -> Dict[str, Any]:
        return {
            "current_framework": self.optimization_framework,
            "jax_available": getattr(jax_backend, 'JAX_AVAILABLE', False),
            "numba_available": False, # Numba FFT not explicitly optimized
            "recommended_framework": "jax" if getattr(jax_backend, 'JAX_AVAILABLE', False) else "numpy"
        }

    def plot_scaling(self, save_path: Optional[str] = None) -> None:
        """Plot the scaling relationship and PSD."""
        if not self.results:
            raise ValueError("No results available. Run estimate() first.")

        plt.figure(figsize=(15, 4))

        # Log-log scaling relationship
        plt.subplot(1, 3, 1)
        x = self.results["log_freq"]
        y = self.results["log_psd"]
        plt.scatter(x, y, s=40, alpha=0.7, label="Data points")
        slope = self.results["slope"]
        intercept = self.results["intercept"]
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = slope * x_fit + intercept
        plt.plot(x_fit, y_fit, "r--", label="Linear fit")
        plt.xlabel("log(Frequency)")
        plt.ylabel("log(PSD)")
        plt.title("Periodogram Power Law Regression")
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Log-log components
        plt.subplot(1, 3, 2)
        plt.scatter(np.exp(x), np.exp(y), s=30, alpha=0.7)
        plt.xscale("log")
        plt.yscale("log")
        plt.xlabel("Frequency")
        plt.ylabel("Power Spectral Density")
        plt.title("Power Law Components (log-log)")
        plt.grid(True, which="both", ls=":", alpha=0.3)

        # Plain PSD view
        plt.subplot(1, 3, 3)
        plt.plot(self.results["frequency"], self.results["periodogram"], alpha=0.7)
        plt.xlabel("Frequency")
        plt.ylabel("Power Spectral Density")
        plt.title("Power Spectral Density")
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.show()
