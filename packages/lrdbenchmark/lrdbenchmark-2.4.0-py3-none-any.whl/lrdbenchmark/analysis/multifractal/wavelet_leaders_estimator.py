#!/usr/bin/env python3
"""
Unified Multifractal Wavelet Leaders Estimator.
Refactored to use modular backends.
"""

import numpy as np
import matplotlib.pyplot as plt
import pywt
from typing import Dict, Any, Optional, Union, Tuple, List
import warnings

from lrdbenchmark.analysis.base_estimator import BaseEstimator
from lrdbenchmark.analysis.backend_utils import select_backend

from .wavelet_leaders_backends import numpy_backend
try:
    from .wavelet_leaders_backends import jax_backend
except ImportError:
    jax_backend = None

class MultifractalWaveletLeadersEstimator(BaseEstimator):
    """
    Unified Multifractal Wavelet Leaders Estimator.
    """

    def __init__(
        self,
        wavelet: str = "db3",
        scales: Optional[List[int]] = None,
        min_scale: int = 2,
        max_scale: int = 32,
        num_scales: int = 10,
        q_values: Optional[List[float]] = None,
        use_optimization: str = "numpy",
    ):
        super().__init__()
        
        if q_values is None:
            q_values = [-2, -1, -0.5, 0, 0.5, 1, 2, 3, 4]

        if scales is None:
            # Default scales generation if not provided
            # We defer actual generation to 'estimate' if n is needed, 
            # BUT original code generated it in __init__ based on defaults.
            # I'll enable dynamic adjustment in estimate.
            scales = np.arange(min_scale, max_scale + 1, max(1, (max_scale - min_scale) // max(1, num_scales - 1)))
        
        self.parameters = {
            "wavelet": wavelet, "scales": scales,
            "min_scale": min_scale, "max_scale": max_scale,
            "num_scales": num_scales, "q_values": np.asarray(q_values)
        }
        self.optimization_framework = select_backend(use_optimization)
        self.results = {}

    def estimate(self, data):
        data = np.asarray(data)
        n = len(data)
        if n < 100: warnings.warn("Data small")
        
        # Scale Adjustment Logic
        max_safe = min(self.parameters["max_scale"], n // 8)
        if max_safe < self.parameters["min_scale"]:
            raise ValueError("Data too short")
            
        current_scales = self.parameters["scales"]
        if max_safe < self.parameters["max_scale"]:
            # Filter
            filt = [s for s in current_scales if s <= max_safe]
            if len(filt) < 3: warnings.warn("Few scales remaining")
            current_scales = np.array(filt) if len(filt)>0 else current_scales # fallback
            
        scales = np.asarray(current_scales, dtype=int)
        q_values = np.asarray(self.parameters["q_values"], dtype=float)
        
        backend_name = self.optimization_framework
        compute = self._get_compute(backend_name)
        
        try:
             SL, js = compute(data, self.parameters["wavelet"], scales, q_values)
        except Exception as e:
             warnings.warn(f"Backend {backend_name} failed: {e}. Fallback NumPy.")
             SL, js = numpy_backend.compute_structure_functions(data, self.parameters["wavelet"], scales, q_values)
             backend_name = "numpy (fallback)"
             
        # Post-Processing (Zeta, Spectrum)
        # Convert JAX arrays to numpy if needed
        SL = np.array(SL)
        js = np.array(js)
        
        zeta = np.zeros(len(q_values))
        for i in range(len(q_values)):
            y = np.log2(SL[i, :] + 1e-300)
            # fit y vs log2(scale)? 
            # Original code: np.polyfit(js, y, 1). 'js' = scales (linear). 
            # Is scaling log2(SL) linear with j?
            # Yes, if scales j=1,2,3... (levels). 
            # But here scales are [min_scale, ...]. Are they levels or time-scales?
            # In Wavelet Leaders, scales usually refers to LEVELS j.
            # Original default: min_scale=2, max=32. Step size...
            # If j is Level, then it's linear.
            # So polyfit(js, y) is correct.
            slope, _ = np.polyfit(js, y, 1)
            zeta[i] = slope
            
        # C1, C0
        # Fit zeta(q) vs q
        slope_c1, intercept_c0 = np.polyfit(q_values, zeta, 1)
        
        self.results = {
            "hurst_parameter": float(slope_c1),
            "generalized_hurst": {q: float(z/q) if abs(q)>1e-6 else float(slope_c1) for q,z in zip(q_values, zeta)},
            "multifractal_spectrum": self._compute_spectrum(zeta, q_values),
            "q_values": q_values.tolist(),
            "scales": scales.tolist(),
            "structure_functions": {q: SL[i].tolist() for i,q in enumerate(q_values)},
            "zeta": zeta.tolist(),
            "method": "wavelet_leaders",
            "optimization_framework": backend_name
        }
        return self.results
            
    def _compute_spectrum(self, zeta, qs):
         # f(alpha) = q*alpha - tau(q); tau(q) = zeta(q)*log2(2)? No zeta(q) includes scaling log factor?
         # Standard: SL ~ 2^(j * zeta(q)).
         # tau(q) = zeta(q) - 1? Or tau(q) = zeta(q).
         # Definition varies. Usually tau(q) = zeta(q) - 1.
         # Actually, in leaders: S_q(j) ~ 2^(j * zeta(q)).
         # tau(q) is defined via partition function Z_q(s) ~ s^tau(q).
         # s = 2^j.
         # S_q(j) ~ (2^j)^zeta(q).
         # So tau(q) = zeta(q).
         # BUT Partition function sums over N/s boxes.
         # Structure function averages over N/s boxes.
         # Sum ~ Average * (N/s).
         # Z_q(s) ~ S_q(j) * (N/2^j).
         # s^tau = 2^(j*zeta) * 2^(-j).
         # 2^(j*tau) = 2^(j*(zeta - 1)).
         # So tau(q) = zeta(q) - 1.
         
         tau = zeta - 1
         alpha = np.gradient(tau, qs)
         f_alpha = qs * alpha - tau
         return {"alpha": alpha.tolist(), "f_alpha": f_alpha.tolist()}
         
    def _get_compute(self, backend):
        if backend == 'jax' and jax_backend and jax_backend.JAX_AVAILABLE:
            return jax_backend.compute_structure_functions
        return numpy_backend.compute_structure_functions

    def get_optimization_info(self):
        return {"current": self.optimization_framework}
