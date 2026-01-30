#!/usr/bin/env python3
"""
Unified MFDFA Estimator for Multifractal Analysis.
Refactored to use modular backends.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from typing import Dict, Any, Optional, Union, Tuple, List
import warnings

from lrdbenchmark.analysis.base_estimator import BaseEstimator
from lrdbenchmark.analysis.backend_utils import select_backend

from .mfdfa_backends import numpy_backend
try:
    from .mfdfa_backends import jax_backend
except ImportError:
    jax_backend = None

class MFDFAEstimator(BaseEstimator):
    """
    Multifractal Detrended Fluctuation Analysis (MFDFA) Estimator.
    
    Estimates the generalized Hurst exponent H(q) and the multifractal spectrum D(h).
    Supports JAX acceleration.
    """

    def __init__(
        self,
        q_orders: Optional[Union[List[float], np.ndarray]] = None,
        scales: Optional[List[int]] = None,
        order: int = 1,
        use_optimization: str = "auto",
        **kwargs
    ):
        super().__init__()
        
        if q_orders is None:
            # Default q: -5 to 5
            q_orders = np.linspace(-5, 5, 21)
            
        self.parameters = {
            "q_orders": np.asarray(q_orders),
            "scales": scales,
            "order": order
        }
        
        self.optimization_framework = select_backend(use_optimization)
        self.results = {}

    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Perform MFDFA.
        """
        data = np.asarray(data)
        n = len(data)
        if n < 100: warnings.warn("Small data")
        
        # Determine scales
        order = self.parameters["order"] # Fetch order first
        scales = self.parameters["scales"]
        if scales is None:
            min_scale = 10
            max_scale = n // 5
            scales = np.unique(np.logspace(np.log10(min_scale), np.log10(max_scale), 30).astype(int))
            scales = scales[scales > order + 2] # now safe
            self.parameters["scales"] = scales
            
        if len(scales) < 4:
            raise ValueError("Insufficient scales")

        backend_name = self.optimization_framework
        compute_func = self._get_compute_function(backend_name)
        
        # order fetched above
        qs = self.parameters["q_orders"]
        
        try:
            fluctuations = compute_func(data, scales, qs, order)
        except Exception as e:
            warnings.warn(f"Backend {backend_name} failed: {e}. Fallback NumPy.")
            fluctuations = numpy_backend.compute_fluctuations(data, scales, qs, order)
            backend_name = "numpy (fallback)"
            
        # fluctuations: shape (len(scales), len(qs))
        # Perform regression for each q
        
        h_qs = []
        r2_qs = []
        intercepts = []
        
        log_scales = np.log(scales)
        log_flucts = np.log(fluctuations) # shape (n_scales, n_qs)
        
        # Loop over q (columns)
        for i in range(len(qs)):
            y = log_flucts[:, i]
            # Handle possible NaNs
            valid = np.isfinite(y)
            if np.sum(valid) < 3:
                h_qs.append(np.nan)
                r2_qs.append(0.0)
                intercepts.append(np.nan)
                continue
                
            slope, intercept, r_val, _, _ = stats.linregress(log_scales[valid], y[valid])
            h_qs.append(slope)
            r2_qs.append(r_val**2)
            intercepts.append(intercept)
            
        h_qs = np.array(h_qs)
        
        # Calculate Multifractal Spectrum
        # tau(q) = q * H(q) - 1
        tau_qs = qs * h_qs - 1
        
        # alpha = d(tau)/dq
        # f(alpha) = q*alpha - tau(q)
        # Numerical differentiation
        alpha = np.gradient(tau_qs, qs)
        f_alpha = qs * alpha - tau_qs
        
        self.results = {
            "q_orders": qs.tolist(),
            "h_qs": h_qs.tolist(),
            "tau_qs": tau_qs.tolist(),
            "alpha": alpha.tolist(),
            "f_alpha": f_alpha.tolist(),
            "scales": scales.tolist(),
            "fluctuations": fluctuations.tolist(),
            "method": "MFDFA",
            "optimization_framework": backend_name,
            "width": float(np.max(alpha) - np.min(alpha)), # Spectral Width
            "peak_location": float(alpha[np.argmax(f_alpha)])
        }
        
        return self.results
        
    def _get_compute_function(self, backend):
        if backend == 'jax' and jax_backend and jax_backend.JAX_AVAILABLE:
            return jax_backend.compute_fluctuations
        return numpy_backend.compute_fluctuations

    def get_optimization_info(self):
         return {
            "current_framework": self.optimization_framework,
            "jax_available": getattr(jax_backend, 'JAX_AVAILABLE', False)
        }
