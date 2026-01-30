#!/usr/bin/env python3
"""
Unified Continuous Wavelet Transform (CWT) Estimator for Long-Range Dependence Analysis.

This module implements the CWT estimator with automatic optimization framework
selection (JAX, Numba, NumPy) for the best performance on the available hardware.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import pywt
from typing import Dict, Any, Optional, Union, Tuple, List
import warnings

# Import optimization frameworks
try:
    import jax
    import jax.numpy as jnp
    from jax import vmap
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False

try:
    import numba
    from numba import jit as numba_jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

# Import base estimator (single source of truth)
from lrdbenchmark.analysis.base_estimator import BaseEstimator
from lrdbenchmark.analysis.calibration_utils import apply_srd_bias_correction


class CWTEstimator(BaseEstimator):
    """
    Unified Continuous Wavelet Transform (CWT) Estimator for Long-Range Dependence Analysis.

    This estimator uses continuous wavelet transforms to analyze the scaling behavior
    of time series data and estimate the Hurst parameter for fractional processes.

    Features:
    - Automatic optimization framework selection (JAX, Numba, NumPy)
    - GPU acceleration with JAX when available
    - JIT compilation with Numba for CPU optimization
    - Graceful fallbacks when optimization frameworks fail

    Parameters
    ----------
    wavelet : str, optional (default='cmor1.5-1.0')
        Wavelet type for continuous transform
    scales : np.ndarray, optional (default=None)
        Array of scales for analysis. If None, uses automatic scale selection
    confidence : float, optional (default=0.95)
        Confidence level for confidence intervals
    use_optimization : str, optional (default='auto')
        Optimization framework to use: 'auto', 'jax', 'numba', 'numpy'
    """

    def __init__(
        self,
        wavelet: str = "morl",
        scales: Optional[np.ndarray] = None,
        confidence: float = 0.95,
        use_optimization: str = "auto",
        robust: bool = False,
        scale_range: Optional[Tuple[float, float]] = None,
        trim_ends: int = 0,
    ):
        super().__init__()
        
        # Estimator parameters
        self.parameters = {
            "wavelet": wavelet,
            "scales": scales,
            "confidence": confidence,
            "robust": robust,
            "scale_range": scale_range,
            "trim_ends": int(max(0, trim_ends)),
        }
        
        # Optimization framework
        self.optimization_framework = self._select_optimization_framework(use_optimization)
        
        # Results storage
        self.results = {}
        
        # Validation
        self._validate_parameters()

    def _select_optimization_framework(self, use_optimization: str) -> str:
        """Select the optimal optimization framework."""
        if use_optimization == "auto":
            if JAX_AVAILABLE:
                return "jax"  # Best for GPU acceleration
            elif NUMBA_AVAILABLE:
                return "numba"  # Good for CPU optimization
            else:
                return "numpy"  # Fallback
        elif use_optimization == "jax" and JAX_AVAILABLE:
            return "jax"
        elif use_optimization == "numba" and NUMBA_AVAILABLE:
            return "numba"
        else:
            return "numpy"

    def _validate_parameters(self) -> None:
        """Validate estimator parameters."""
        if not isinstance(self.parameters["wavelet"], str):
            raise ValueError("wavelet must be a string")
        
        if self.parameters["scales"] is not None:
            if not isinstance(self.parameters["scales"], np.ndarray) or len(self.parameters["scales"]) == 0:
                raise ValueError("scales must be a non-empty numpy array")
        
        if not (0 < self.parameters["confidence"] < 1):
            raise ValueError("confidence must be between 0 and 1")
        if self.parameters["scale_range"] is not None:
            lo, hi = self.parameters["scale_range"]
            if not (lo > 0 and hi > lo):
                raise ValueError("scale_range must satisfy 0 < lo < hi")

    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Estimate the Hurst parameter using Continuous Wavelet Transform analysis with automatic optimization.

        Parameters
        ----------
        data : array-like
            Input time series data

        Returns
        -------
        dict
            Dictionary containing estimation results including:
            - hurst_parameter: Estimated Hurst parameter
            - confidence_interval: Confidence interval for the estimate
            - r_squared: R-squared value of the fit
            - scales: Scales used in the analysis
            - wavelet_type: Wavelet type used
            - slope: Slope of the log-log regression
            - intercept: Intercept of the log-log regression
            - scale_powers: Power at each scale
        """
        data = np.asarray(data)
        n = len(data)

        if n < 50:
            raise ValueError("Data length must be at least 50 for CWT analysis")

        if n < 100:
            warnings.warn("Data length is small, results may be unreliable")

        # Select optimal method based on data size and framework
        if self.optimization_framework == "jax" and JAX_AVAILABLE:
            try:
                return self._estimate_jax(data)
            except Exception as e:
                warnings.warn(f"JAX implementation failed: {e}, falling back to NumPy")
                return self._estimate_numpy(data)
        elif self.optimization_framework == "numba" and NUMBA_AVAILABLE:
            try:
                return self._estimate_numba(data)
            except Exception as e:
                warnings.warn(f"Numba implementation failed: {e}, falling back to NumPy")
                return self._estimate_numpy(data)
        else:
            return self._estimate_numpy(data)

    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of CWT estimation."""
        n = len(data)
        
        # Set default scales if not provided
        if self.parameters["scales"] is None:
            # Geometric scales roughly covering [2, n/8]
            s_min = 2
            s_max = max(8, int(n // 8))
            self.parameters["scales"] = np.unique((np.geomspace(s_min, s_max, num=24)).astype(float))
        
        # Adjust scales for shorter data
        if n < 100:
            # Use fewer scales for shorter data
            max_scale = min(max(self.parameters["scales"]), n // 4)
            self.parameters["scales"] = np.array([s for s in self.parameters["scales"] if s <= max_scale])
            if len(self.parameters["scales"]) < 2:
                raise ValueError("Insufficient scales available for data length")

        # Optionally restrict scale range and trim ends
        scales = self.parameters["scales"].astype(float)
        if self.parameters["scale_range"] is not None:
            lo, hi = self.parameters["scale_range"]
            mask = (scales >= lo) & (scales <= hi)
            scales = scales[mask]
        if self.parameters["trim_ends"] > 0 and len(scales) > 2 * self.parameters["trim_ends"]:
            t = self.parameters["trim_ends"]
            scales = scales[t:-t]
        # Cap maximum scale to reduce SRD bias
        scale_cap = min(np.max(scales), 64.0)
        scales = scales[scales <= scale_cap]
        if len(scales) < 2:
            raise ValueError("Insufficient scales after trimming/range selection")

        # Perform continuous wavelet transform
        wavelet_coeffs, frequencies = pywt.cwt(data, scales, self.parameters["wavelet"])

        # Calculate power spectrum (squared magnitude of coefficients)
        power_spectrum = np.abs(wavelet_coeffs) ** 2

        # Calculate average power at each scale
        scale_powers = {}
        scale_logs = []
        power_logs = []
        power_log_variances = []
        n_time = power_spectrum.shape[1]

        for i, scale in enumerate(scales):
            coeff_row = power_spectrum[i, :]
            avg_power = np.mean(coeff_row)
            scale_powers[scale] = avg_power

            scale_logs.append(np.log2(scale))
            power_logs.append(np.log2(avg_power))

            var_power = np.var(coeff_row, ddof=1)
            if not np.isfinite(var_power) or var_power <= 0:
                var_power = (avg_power**2) / max(n_time, 1)
            var_mean = var_power / max(n_time, 1)
            var_log = var_mean / (avg_power**2 * (np.log(2.0) ** 2))
            power_log_variances.append(max(var_log, 1e-12))

        x = np.asarray(scale_logs, dtype=float)
        y = np.asarray(power_logs, dtype=float)
        weights = 1.0 / np.clip(np.asarray(power_log_variances, dtype=float), 1e-12, None)
        X = np.column_stack((np.ones_like(x), x))
        XtWX = X.T @ (weights[:, None] * X)
        XtWy = X.T @ (weights * y)

        if self.parameters["robust"]:
            slope, intercept = self._huber_regression(x, y)
        else:
            beta = np.linalg.solve(XtWX, XtWy)
            intercept, slope = beta

        r_squared, slope_se = self._regression_statistics(x, y, weights, slope, intercept, XtWX)

        # Empirical mapping consistent with PyWavelets normalization: H ≈ (slope + 1)/2
        # This provides low-bias estimates across tested FBM signals
        estimated_hurst = 0.5 * (slope + 1.0)

        # Calculate confidence interval
        confidence_interval = self._get_confidence_interval(
            estimated_hurst,
            slope_se,
            len(scale_logs),
        )

        corrected_hurst, applied_bias = apply_srd_bias_correction(
            "CWT", float(estimated_hurst)
        )
        if applied_bias != 0.0 and confidence_interval is not None:
            lower = max(0.01, min(0.99, confidence_interval[0] - applied_bias))
            upper = max(0.01, min(0.99, confidence_interval[1] - applied_bias))
            confidence_interval = (lower, upper)
        estimated_hurst = corrected_hurst

        # Store results
        self.results = {
            "hurst_parameter": float(estimated_hurst),
            "confidence_interval": confidence_interval,
            "r_squared": float(r_squared),
            "scales": scales.tolist(),
            "wavelet_type": self.parameters["wavelet"],
            "slope": float(slope),
            "intercept": float(intercept),
            "scale_powers": scale_powers,
            "scale_logs": scale_logs,
            "power_logs": power_logs,
            "regression_weights": weights.tolist(),
            "bias_correction": applied_bias,
            "wavelet_coeffs": wavelet_coeffs,
            "power_spectrum": power_spectrum,
            "method": "numpy",
            "optimization_framework": self.optimization_framework,
        }
        
        return self.results

    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of CWT estimation."""
        # For now, use NumPy implementation with Numba JIT compilation
        # This can be enhanced with custom Numba kernels for specific operations
        return self._estimate_numpy(data)

    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of Wavelet Log Variance estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)

        if self.parameters["wavelet"] != "morl":
            raise NotImplementedError("JAX CWT currently supports the 'morl' wavelet only")

        data_np = np.asarray(data, dtype=float)
        n = len(data_np)
        demeaned = data_np - np.mean(data_np)
        x = jnp.asarray(demeaned, dtype=jnp.float64)

        if self.parameters["scales"] is None:
            s_min = 2
            s_max = max(8, int(n // 8))
            self.parameters["scales"] = np.unique((np.geomspace(s_min, s_max, num=24)).astype(float))

        scales = self.parameters["scales"].astype(float)
        if n < 100:
            max_scale = min(max(scales), n // 4)
            scales = np.array([s for s in scales if s <= max_scale])
            if len(scales) < 2:
                raise ValueError("Insufficient scales available for data length")

        trim = self.parameters["trim_ends"]
        if trim > 0 and len(scales) > 2 * trim:
            scales = scales[trim:-trim]
        if len(scales) < 2:
            raise ValueError("Insufficient scales after trimming")

        padded_len = int(2 ** np.ceil(np.log2(n)))
        padded = jnp.pad(x, (0, padded_len - n))
        fft_data = jnp.fft.fft(padded)
        omega = 2 * jnp.pi * jnp.fft.fftfreq(padded_len, d=1.0)

        def morlet_fft(scale: float) -> jnp.ndarray:
            w0 = 6.0
            factor = jnp.sqrt(scale)
            return factor * jnp.exp(-0.5 * (scale * omega - w0) ** 2)

        def compute_coeff(scale: float) -> jnp.ndarray:
            wavelet_fft = morlet_fft(scale)
            coeff = jnp.fft.ifft(fft_data * wavelet_fft)
            return coeff[:n]

        coeffs = vmap(compute_coeff)(jnp.asarray(scales, dtype=jnp.float64))
        power_spectrum = jnp.abs(coeffs) ** 2

        scale_powers = jnp.mean(power_spectrum, axis=1)
        n_time = power_spectrum.shape[1]

        scale_logs = jnp.log2(jnp.asarray(scales, dtype=jnp.float64))
        power_logs = jnp.log2(scale_powers + 1e-300)

        variances = jnp.var(power_spectrum, axis=1, ddof=1)
        variances = jnp.where(variances <= 0, (scale_powers**2) / max(n_time, 1), variances)
        var_mean = variances / max(n_time, 1)
        var_log = var_mean / (scale_powers**2 * (jnp.log(2.0) ** 2))
        weights = 1.0 / jnp.clip(var_log, 1e-12, None)

        X = jnp.stack([jnp.ones_like(scale_logs), scale_logs], axis=1)
        XtWX = X.T @ (weights[:, None] * X)
        XtWy = X.T @ (weights * power_logs)
        beta = jnp.linalg.solve(XtWX, XtWy)
        intercept, slope = beta

        y_fit = slope * scale_logs + intercept
        y_mean = jnp.average(power_logs, weights=weights)
        ss_res = jnp.sum(weights * (power_logs - y_fit) ** 2)
        ss_tot = jnp.sum(weights * (power_logs - y_mean) ** 2)
        r_squared = jnp.where(ss_tot > 0, 1.0 - ss_res / ss_tot, 0.0)

        estimated_hurst = 0.5 * (slope + 1.0)
        slope_se = jnp.sqrt(jnp.clip(jnp.linalg.inv(XtWX)[1, 1], 1e-12, None))
        confidence_interval = self._get_confidence_interval(
            float(estimated_hurst),
            float(slope_se),
            len(scale_logs),
        )

        corrected_hurst, applied_bias = apply_srd_bias_correction(
            "CWT", float(estimated_hurst)
        )
        if applied_bias != 0.0 and confidence_interval is not None:
            lower = max(0.01, min(0.99, confidence_interval[0] - applied_bias))
            upper = max(0.01, min(0.99, confidence_interval[1] - applied_bias))
            confidence_interval = (lower, upper)
        estimated_hurst = corrected_hurst

        power_log_variances = (1.0 / weights).tolist()
        scale_powers_dict = {float(scales[i]): float(scale_powers[i]) for i in range(len(scales))}

        self.results = {
            "hurst_parameter": float(estimated_hurst),
            "confidence_interval": confidence_interval,
            "r_squared": float(r_squared),
            "scales": scales.tolist(),
            "wavelet_type": self.parameters["wavelet"],
            "slope": float(slope),
            "intercept": float(intercept),
            "scale_powers": scale_powers_dict,
            "power_log_variances": power_log_variances,
            "method": "jax",
            "optimization_framework": self.optimization_framework,
            "bias_correction": applied_bias,
        }

        return self.results

    def _regression_statistics(
        self,
        x: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray,
        slope: float,
        intercept: float,
        XtWX: np.ndarray,
    ) -> Tuple[float, float]:
        """Compute weighted regression diagnostics for slope."""
        residuals = y - (slope * x + intercept)
        dof = max(len(x) - 2, 1)
        ss_res = float(np.sum(weights * residuals**2))
        y_mean = np.average(y, weights=weights)
        ss_tot = float(np.sum(weights * (y - y_mean) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        sigma2 = ss_res / dof if dof > 0 else 0.0
        if sigma2 < 1e-10:
            sigma2 = np.mean(1.0 / weights)
        cov_beta = sigma2 * np.linalg.inv(XtWX)
        slope_se = float(np.sqrt(max(cov_beta[1, 1], 1e-12)))
        return r_squared, slope_se

    def _get_confidence_interval(
        self,
        estimated_hurst: float,
        slope_se: float,
        n_points: int,
    ) -> Tuple[float, float]:
        """Calculate confidence interval for the Hurst parameter estimate."""
        confidence = self.parameters["confidence"]
        hurst_se = 0.5 * slope_se
        dof = max(n_points - 2, 1)
        t_value = stats.t.ppf((1 + confidence) / 2, df=dof)
        margin = float(t_value * hurst_se)
        return (float(estimated_hurst - margin), float(estimated_hurst + margin))

    def _huber_regression(self, X: np.ndarray, y: np.ndarray, c: float = 1.345, iters: int = 50, tol: float = 1e-8) -> Tuple[float, float]:
        X1 = np.vstack([X, np.ones_like(X)]).T
        beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
        for _ in range(iters):
            r = y - X1 @ beta
            s = 1.4826 * np.median(np.abs(r - np.median(r)) + 1e-12)
            u = r / (s + 1e-12)
            w = np.clip(c / np.maximum(np.abs(u), 1e-12), 0.0, 1.0)
            W = np.diag(w)
            XtWX = X1.T @ W @ X1
            XtWy = X1.T @ W @ y
            beta_new, *_ = np.linalg.lstsq(XtWX, XtWy, rcond=None)
            if np.linalg.norm(beta_new - beta) < tol:
                beta = beta_new
                break
            beta = beta_new
        return float(beta[0]), float(beta[1])

    def get_optimization_info(self) -> Dict[str, Any]:
        """Get information about available optimizations and current selection."""
        return {
            "current_framework": self.optimization_framework,
            "jax_available": JAX_AVAILABLE,
            "numba_available": NUMBA_AVAILABLE,
            "recommended_framework": self._get_recommended_framework()
        }

    def _get_recommended_framework(self) -> str:
        """Get the recommended optimization framework."""
        if JAX_AVAILABLE:
            return "jax"  # Best for GPU acceleration
        elif NUMBA_AVAILABLE:
            return "numba"  # Good for CPU optimization
        else:
            return "numpy"  # Fallback

    def plot_analysis(self, data: np.ndarray, figsize: Tuple[int, int] = (15, 10), save_path: Optional[str] = None) -> None:
        """Plot the CWT analysis results."""
        if not self.results:
            raise ValueError("No results available. Run estimate() first.")

        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle(f'CWT Analysis - {self.parameters["wavelet"]} Wavelet', fontsize=16)

        # Plot 1: Original time series
        ax1 = axes[0, 0]
        ax1.plot(data, alpha=0.7)
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Amplitude")
        ax1.set_title("Original Time Series")
        ax1.grid(True, alpha=0.3)

        # Plot 2: Log-log scaling relationship
        ax2 = axes[0, 1]
        x = self.results["scale_logs"]
        y = self.results["power_logs"]

        ax2.scatter(x, y, s=60, alpha=0.7, label="Data points")

        # Plot fitted line
        slope = self.results["slope"]
        intercept = self.results["intercept"]
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = slope * x_fit + intercept
        ax2.plot(x_fit, y_fit, "r--", label=f"Linear fit (slope={slope:.3f})")

        ax2.set_xlabel("log₂(Scale)")
        ax2.set_ylabel("log₂(Power)")
        ax2.set_title("CWT Power Scaling")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Plot 3: Power vs Scale (log-log)
        ax3 = axes[0, 2]
        scales = self.results["scales"]
        powers = [self.results["scale_powers"][s] for s in scales]
        
        ax3.scatter(scales, powers, s=60, alpha=0.7)
        ax3.set_xscale("log")
        ax3.set_yscale("log")
        ax3.set_xlabel("Scale")
        ax3.set_ylabel("Power")
        ax3.set_title("Power vs Scale (log-log)")
        ax3.grid(True, which="both", ls=":", alpha=0.3)

        # Plot 4: Hurst parameter estimate
        ax4 = axes[1, 0]
        hurst = self.results["hurst_parameter"]
        conf_interval = self.results["confidence_interval"]
        
        ax4.bar(["Hurst Parameter"], [hurst], yerr=[[hurst-conf_interval[0]], [conf_interval[1]-hurst]], 
                capsize=10, alpha=0.7, color='skyblue')
        ax4.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='H=0.5 (no memory)')
        ax4.set_ylabel("Hurst Parameter")
        ax4.set_title(f"Hurst Parameter Estimate: {hurst:.3f}")
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # Plot 5: R-squared
        ax5 = axes[1, 1]
        r_squared = self.results["r_squared"]
        
        ax5.bar(["R²"], [r_squared], alpha=0.7, color='lightgreen')
        ax5.set_ylabel("R²")
        ax5.set_title(f"Goodness of Fit: R² = {r_squared:.3f}")
        ax5.set_ylim(0, 1)
        ax5.grid(True, alpha=0.3)

        # Plot 6: Wavelet scalogram (power spectrum)
        ax6 = axes[1, 2]
        power_spectrum = self.results["power_spectrum"]
        scales = self.results["scales"]
        
        im = ax6.imshow(power_spectrum, aspect='auto', extent=[0, len(data), min(scales), max(scales)])
        ax6.set_xlabel("Time")
        ax6.set_ylabel("Scale")
        ax6.set_title("Wavelet Scalogram")
        ax6.set_yscale("log")
        plt.colorbar(im, ax=ax6, label="Power")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.show()

    def get_method_recommendation(self, n: int) -> Dict[str, Any]:
        """Get method recommendation for a given data size."""
        if n < 50:
            return {
                "recommended_method": "numpy",
                "reasoning": f"Data size n={n} is too small for CWT analysis",
                "method_details": {
                    "description": "NumPy implementation",
                    "best_for": "Small datasets (n < 50)",
                    "complexity": "O(n log n)",
                    "memory": "O(n)",
                    "accuracy": "Low (insufficient data)"
                }
            }
        elif n < 100:
            return {
                "recommended_method": "numpy",
                "reasoning": f"Data size n={n} is too small for optimization benefits",
                "method_details": {
                    "description": "NumPy implementation",
                    "best_for": "Small datasets (50 ≤ n < 100)",
                    "complexity": "O(n log n)",
                    "memory": "O(n)",
                    "accuracy": "Medium"
                }
            }
        elif n < 1000:
            return {
                "recommended_method": "numba",
                "reasoning": f"Data size n={n} benefits from JIT compilation",
                "method_details": {
                    "description": "Numba JIT-compiled implementation",
                    "best_for": "Medium datasets (100 ≤ n < 1000)",
                    "complexity": "O(n log n)",
                    "memory": "O(n)",
                    "accuracy": "High"
                }
            }
        else:
            return {
                "recommended_method": "jax",
                "reasoning": f"Data size n={n} benefits from GPU acceleration",
                "method_details": {
                    "description": "JAX GPU-accelerated implementation",
                    "best_for": "Large datasets (n ≥ 1000)",
                    "complexity": "O(n log n)",
                    "memory": "O(n)",
                    "accuracy": "High"
                }
            }
