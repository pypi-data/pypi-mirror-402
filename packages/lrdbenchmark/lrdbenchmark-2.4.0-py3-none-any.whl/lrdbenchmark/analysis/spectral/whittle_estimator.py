#!/usr/bin/env python3
"""
Unified Whittle Estimator for Spectral Analysis.
Refactored to use modular backends (NumPy, JAX).
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats, optimize
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


class WhittleEstimator(BaseEstimator):
    """
    Whittle estimator for Hurst parameter estimation.
    
    Minimizes the Whittle likelihood function based on the fGn spectral density.
    Supports JAX acceleration for likelihood evaluation.
    """

    def __init__(
        self,
        min_freq_ratio: float = 0.01,
        max_freq_ratio: float = 0.5,
        use_optimization: str = "auto",
        **kwargs
    ):
        super().__init__()
        
        self.parameters = {
            "min_freq_ratio": min_freq_ratio,
            "max_freq_ratio": max_freq_ratio,
        }
        
        self.optimization_framework = select_backend(use_optimization)
        self.results = {}
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        if not (0 < self.parameters["min_freq_ratio"] < self.parameters["max_freq_ratio"] <= 0.5):
            raise ValueError("Frequency ratios must satisfy: 0 < min < max <= 0.5")

    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Estimate Hurst parameter using Whittle method.
        """
        data = np.asarray(data)
        n = len(data)
        
        if n < 100:
            warnings.warn("Data length is small, results may be unreliable")

        # Select Backend Strategy
        backend = self.optimization_framework
        if backend == 'jax' and jax_backend and jax_backend.JAX_AVAILABLE:
             return self._estimate_jax(data)
        
        # Fallback / Default to NumPy
        return self._estimate_numpy(data)

    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        # 1. Compute Periodogram using backend (NumPy)
        # Whittle uses raw periodogram (boxcar)
        try:
             freqs, psd = numpy_backend.compute_psd(
                 data, window='boxcar', use_welch=False, scaling='density'
             )
        except Exception as e:
             # Fallback
             from scipy import signal
             freqs, psd = signal.periodogram(data, window='boxcar', scaling='density')
             
        # 2. Select Range
        mask = (freqs > self.parameters["min_freq_ratio"]) & (freqs <= self.parameters["max_freq_ratio"])
        freqs_sel = freqs[mask]
        psd_sel = psd[mask]
        
        if len(freqs_sel) < 10:
             warnings.warn("Insufficient frequency points.")
             return {"hurst_parameter": 0.5, "method": "Whittle_NumPy", "optimization_framework": "numpy"}

        # 3. Define Likelihood (NumPy)
        def fgn_spectrum_shape(f, H):
            lam = 2 * np.pi * f
            s = np.zeros_like(lam)
            for k in range(-2, 3):
                s += np.abs(2 * np.pi * k + lam) ** (-2 * H - 1)
            return (1 - np.cos(lam)) * s

        def neg_log_likelihood(H):
            if not (0.01 <= H <= 0.99): return np.inf
            f_s = fgn_spectrum_shape(freqs_sel, H)
            ratio = psd_sel / f_s
            C_hat = np.mean(ratio)
            # NLL ~ m*log(C) + sum(log(f))
            return len(freqs_sel) * np.log(C_hat) + np.sum(np.log(f_s))

        # 4. Optimize
        res = optimize.minimize_scalar(neg_log_likelihood, bounds=(0.01, 0.99), method='bounded')
        hurst = res.x
        
        # Scale
        f_s = fgn_spectrum_shape(freqs_sel, hurst)
        scale = np.mean(psd_sel / f_s)
        
        self.results = {
            "hurst_parameter": float(hurst),
            "scale_parameter": float(scale),
            "optimization_success": res.success,
            "method": "Whittle_NumPy",
            "optimization_framework": "numpy",
            "frequencies": freqs_sel.tolist(),
            "periodogram": psd_sel.tolist()
        }
        return self.results

    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-accelerated Whittle estimation."""
        import jax.numpy as jnp
        from jax import jit

        try:
            # 1. Compute PSD (JAX)
            freqs, psd = jax_backend.compute_psd(
                data, window='boxcar', use_welch=False, scaling='density'
            )
            
            # Select Range (Need concrete mask for JAX?) 
            # freqs is array.
            # We can do selection on device or host.
            # Minimization scalar loop runs on host driving JAX kernel?
            # Or fully on device? 
            # minimize_scalar loop is python.
            # So masking can be done on JAX array then passed to kernel?
            # Or just move to numpy for selection?
            # Since selection reduces size, moving to host for selection is easiest, then back?
            # No, keep on device.
            
            mask = (freqs > self.parameters["min_freq_ratio"]) & (freqs <= self.parameters["max_freq_ratio"])
            # Boolean indexing in JAX returns known size? No, dynamic size.
            # This triggers recompilation if shape changes.
            # Masking:
            # freqs_sel = freqs[mask]
            # psd_sel = psd[mask]
            # This works.

            # We define JIT likelihood function that takes (H, freq, psd).
            
            @jit
            def fgn_spectrum_shape_jax(f, H):
                lam = 2 * jnp.pi * f
                # Explicit unroll loop
                s = jnp.zeros_like(lam)
                # k = -2, -1, 0, 1, 2
                s += jnp.abs(2 * jnp.pi * (-2) + lam) ** (-2 * H - 1)
                s += jnp.abs(2 * jnp.pi * (-1) + lam) ** (-2 * H - 1)
                s += jnp.abs(2 * jnp.pi * (0) + lam) ** (-2 * H - 1)
                s += jnp.abs(2 * jnp.pi * (1) + lam) ** (-2 * H - 1)
                s += jnp.abs(2 * jnp.pi * (2) + lam) ** (-2 * H - 1)
                return (1 - jnp.cos(lam)) * s

            @jit
            def nll_jax(H, f, p):
                # H is scalar
                f_s = fgn_spectrum_shape_jax(f, H)
                ratio = p / f_s
                C_hat = jnp.mean(ratio)
                return len(f) * jnp.log(C_hat) + jnp.sum(jnp.log(f_s))

            # Since selection is dynamic, we create the arrays once here.
            # To handle mask safely in JAX:
            # If we use boolean masking, we get a dynamically sized array.
            # Passing this to JIT function means function is recompiled for this size.
            # This is fine (once per estimate call).
            
            f_sel = freqs[mask]
            p_sel = psd[mask]
            
            if len(f_sel) < 10:
                warnings.warn("Insufficient frequency points.")
                return self._estimate_numpy(data) # Fallback

            # Wrap for scipy optimizer (needs host scalars)
            def func(h_val):
                val = nll_jax(h_val, f_sel, p_sel)
                return float(val) # Block until ready
            
            res = optimize.minimize_scalar(func, bounds=(0.01, 0.99), method='bounded')
            hurst = res.x
            
            # Recalculate scale
            # Can use JAX
            f_s = fgn_spectrum_shape_jax(f_sel, hurst)
            scale = float(jnp.mean(p_sel / f_s))
            
            self.results = {
                "hurst_parameter": float(hurst),
                "scale_parameter": float(scale),
                "optimization_success": res.success,
                "method": "Whittle_JAX",
                "optimization_framework": "jax",
                "frequencies": np.array(f_sel).tolist(),
                # "periodogram": ... skip large arrays in dict if not needed
            }
            return self.results

        except Exception as e:
            warnings.warn(f"JAX Whittle failed: {e}. Falling back to NumPy.")
            return self._estimate_numpy(data)

    def get_optimization_info(self) -> Dict[str, Any]:
        return {
            "current_framework": self.optimization_framework,
            "jax_available": getattr(jax_backend, 'JAX_AVAILABLE', False),
            "numba_available": False,
            "recommended_framework": "jax" if getattr(jax_backend, 'JAX_AVAILABLE', False) else "numpy"
        }
