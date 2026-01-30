#!/usr/bin/env python3
"""
Unified Wavelet Variance Estimator.
Refactored to use modular backends.
"""

# Same imports and structure as LogVarianceEstimator
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.special import polygamma
import pywt
from typing import Dict, Any, Optional, Union, Tuple, List
import warnings

from lrdbenchmark.analysis.base_estimator import BaseEstimator
from lrdbenchmark.analysis.backend_utils import select_backend

from .wavelet_backends import numpy_backend
try:
    from .wavelet_backends import jax_backend
except ImportError:
    jax_backend = None
try:
    from .wavelet_backends import numba_backend
except ImportError:
    numba_backend = None
from lrdbenchmark.analysis.calibration_utils import apply_srd_bias_correction

class WaveletVarianceEstimator(BaseEstimator):
    """
    Unified Wavelet Variance Estimator.
    Identical logic to LogVarianceEstimator, kept for compatibility/completeness.
    """
    
    def __init__(self, wavelet="db4", scales=None, confidence=0.95, use_optimization="auto", robust=False, j_min=2, j_max=None):
        super().__init__()
        self.parameters = {
            "wavelet": wavelet, "scales": scales, "confidence": confidence,
            "robust": robust, "j_min": int(max(1, j_min)), "j_max": j_max
        }
        self.optimization_framework = select_backend(use_optimization)
        self.results = {}

    def estimate(self, data):
        # ... Similar logic to LogVarianceEstimator ...
        # Can I copy-paste? Yes. Or inherit.
        # Effectively, WaveletLogVarianceEstimator and WaveletVarianceEstimator are the same DWT estimator.
        # I'll implement it explicitly to ensure robustness.
        
        data = np.asarray(data)
        n = len(data)
        if n < 100: warnings.warn("Small data length")

        scales = self.parameters["scales"]
        if scales is None:
            w = pywt.Wavelet(self.parameters["wavelet"])
            J = max(1, pywt.dwt_max_level(n, w.dec_len))
            j_min = min(self.parameters["j_min"], J)
            j_max = self.parameters["j_max"] if self.parameters["j_max"] is not None else max(1, J - 1)
            j_max = min(max(j_min, j_max), J)
            scales = list(range(j_min, j_max + 1))
            
            # Cap
            scale_cap = min(max(scales), 6)
            capped_scales = [s for s in scales if s <= scale_cap]
            if len(capped_scales) >= 3: scales = capped_scales
            self.parameters["scales"] = scales
            
        if not scales: raise ValueError("No valid scales")

        if n < 2 ** max(scales):
            raise ValueError(f"Data too short for scale {max(scales)}")
            
        backend_name = self.optimization_framework
        compute_func = self._get_compute_function(backend_name)
        
        try:
            variances, counts = compute_func(data, self.parameters["wavelet"], scales, self.parameters["robust"])
        except Exception as e:
            warnings.warn(f"Backend {backend_name} failed: {e}. Fallback NumPy.")
            variances, counts = numpy_backend.compute_variances(data, self.parameters["wavelet"], scales, self.parameters["robust"])
            backend_name = "numpy (fallback)"
            
        return self._fit_variance(variances, counts, backend_name)

    def _fit_variance(self, variances, counts, backend_name):
        scales = self.parameters["scales"]
        x_vals, y_vals, w_vals = [], [], []
        
        for j in scales:
            if j not in variances: continue
            var = variances[j]
            cnt = counts[j]
            
            x_vals.append(float(j))
            y_vals.append(np.log2(var))
            
            dof = max(cnt - 1, 1)
            var_log_nat = float(polygamma(1, 0.5 * dof))
            if var_log_nat <= 0: var_log_nat = 1.0/dof
            w = 1.0 / (var_log_nat / (np.log(2)**2))
            w_vals.append(w)
            
        x = np.array(x_vals)
        y = np.array(y_vals)
        w = np.array(w_vals)
        
        X = np.column_stack((np.ones_like(x), x))
        XtWX = X.T @ (w[:, None] * X)
        XtWy = X.T @ (w * y)
        try:
             beta = np.linalg.solve(XtWX, XtWy)
             slope = beta[1]
             intercept = beta[0]
        except:
             slope, intercept = 0, 0
             
        hurst = 0.5 * (slope + 1)
        
        # Bias Correction
        corrected_hurst, applied_bias = apply_srd_bias_correction("WaveletVar", float(hurst))
        hurst = corrected_hurst
        
        # R2
        y_pred = X @ beta
        ss_res = np.sum(w*(y - y_pred)**2)
        ss_tot = np.sum(w*(y - np.average(y, weights=w))**2)
        r2 = 1.0 - ss_res/ss_tot if ss_tot>0 else 0
        
        self.results = {
            "hurst_parameter": float(hurst),
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(r2),
            "method": "variance",
            "optimization_framework": backend_name,
            "scales": scales,
            "wavelet_variances": variances
        }
        return self.results
        
    def _get_compute_function(self, backend):
        if backend == 'jax' and jax_backend and jax_backend.JAX_AVAILABLE:
            return jax_backend.compute_variances
        return numpy_backend.compute_variances

    def get_optimization_info(self):
        return {
            "current_framework": self.optimization_framework,
            "jax_available": getattr(jax_backend, 'JAX_AVAILABLE', False)
        }
