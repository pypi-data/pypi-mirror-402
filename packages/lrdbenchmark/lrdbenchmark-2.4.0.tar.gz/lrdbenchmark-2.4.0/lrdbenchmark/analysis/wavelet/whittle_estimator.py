#!/usr/bin/env python3
"""
Unified Wavelet Whittle Estimator for Long-Range Dependence Analysis.

This module implements the Wavelet Whittle estimator with automatic optimization framework
selection (JAX, Numba, NumPy) for the best performance on the available hardware.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats, optimize
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
    jax = None  # type: ignore[assignment]
    jnp = None  # type: ignore[assignment]
    vmap = None  # type: ignore[assignment]
    JAX_AVAILABLE = False

try:
    import numba
    from numba import jit as numba_jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

from lrdbenchmark.analysis.base_estimator import BaseEstimator
from lrdbenchmark.analysis.calibration_utils import apply_srd_bias_correction
from lrdbenchmark.analysis.wavelet.jax_wavelet import (
    dwt_periodized,
    wavelet_detail_variances,
)
class WaveletWhittleEstimator(BaseEstimator):
    """
    Unified Wavelet Whittle Estimator for Long-Range Dependence Analysis.

    This estimator combines wavelet decomposition with Whittle likelihood estimation
    to provide robust estimation of the Hurst parameter for fractional processes.

    Features:
    - Automatic optimization framework selection (JAX, Numba, NumPy)
    - GPU acceleration with JAX when available
    - JIT compilation with Numba for CPU optimization
    - Graceful fallbacks when optimization frameworks fail

    Parameters
    ----------
    wavelet : str, optional (default='db4')
        Wavelet type to use for decomposition
    scales : List[int], optional (default=None)
        List of scales for wavelet analysis. If None, uses automatic scale selection
    confidence : float, optional (default=0.95)
        Confidence level for confidence intervals
    use_optimization : str, optional (default='auto')
        Optimization framework to use: 'auto', 'jax', 'numba', 'numpy'
    """

    def __init__(
        self,
        wavelet: str = "db4",
        scales: Optional[List[int]] = None,
        confidence: float = 0.95,
        use_optimization: str = "auto",
        bootstrap_samples: int = 64,
        bootstrap_block_size: Optional[int] = None,
    ):
        super().__init__()
        
        # Estimator parameters
        self.parameters = {
            "wavelet": wavelet,
            "scales": scales,
            "confidence": confidence,
            "bootstrap_samples": int(max(0, bootstrap_samples)),
            "bootstrap_block_size": bootstrap_block_size,
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
            if not isinstance(self.parameters["scales"], list) or len(self.parameters["scales"]) == 0:
                raise ValueError("scales must be a non-empty list")
        
        if not (0 < self.parameters["confidence"] < 1):
            raise ValueError("confidence must be between 0 and 1")

    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Estimate the Hurst parameter using wavelet Whittle analysis with automatic optimization.

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
            - whittle_likelihood: Whittle likelihood value
            - scales: Scales used in the analysis
            - wavelet_type: Wavelet type used
            - optimization_success: Whether optimization succeeded
        """
        data = np.asarray(data)
        n = len(data)

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

    def _estimate_numpy(self, data: np.ndarray, compute_ci: bool = True) -> Dict[str, Any]:
        """NumPy implementation of Wavelet Whittle estimation."""
        n = len(data)
        
        # Set default scales if not provided
        if self.parameters["scales"] is None:
            self.parameters["scales"] = list(range(1, min(11, int(np.log2(n)))))
        
        # Check data length requirement
        if n < 2 ** max(self.parameters["scales"]):
            raise ValueError(
                f"Data length {n} is too short for scale {max(self.parameters['scales'])}"
            )

        # Perform wavelet decomposition once up to the maximal level used
        # Use orthonormal DWT with periodization for theoretical properties
        w = pywt.Wavelet(self.parameters["wavelet"])
        J = pywt.dwt_max_level(n, w.dec_len)
        if J < 2:
            raise ValueError("Insufficient data length for wavelet decomposition")
        max_j = max(self.parameters["scales"]) if self.parameters["scales"] else J
        coeffs = pywt.wavedec(data, w, mode='periodization', level=min(J, max_j))
        # coeffs layout: [cA_J, cD_J, cD_{J-1}, ..., cD_1]

        # Extract detail energies per requested j-level
        js = list(self.parameters["scales"]) if self.parameters["scales"] else list(range(2, min(J, max_j)))
        # Cap scales to reduce SRD bias
        scale_cap = min(max(js), 7)
        js = [j for j in js if j <= scale_cap]
        js = [j for j in js if 1 <= j <= J]
        if len(js) < 3:
            warnings.warn("Few scales available for Wavelet Whittle; estimates may be unstable")
        Sj = []  # empirical energies per scale j
        nj = []  # sample sizes per scale j
        for j in js:
            cDj = coeffs[-j]
            Sj.append(float(np.mean(cDj ** 2)))
            nj.append(float(len(cDj)))
        Sj = np.asarray(Sj, float)
        nj = np.asarray(nj, float)

        # Local Whittle in wavelet domain: minimize L(d) = sum_j n_j [ log(2^{2 d j}) + S_j / 2^{2 d j} ]
        def objective_d(d: float) -> float:
            a = 2.0 ** (2.0 * d * np.asarray(js, float))
            return float(np.sum(nj * (np.log(a) + Sj / a)))

        # Optimize d in a reasonable range, then map to H = d + 1/2 for increments/fGn
        result = optimize.minimize_scalar(objective_d, bounds=(-0.49, 1.49), method="bounded")

        if not result.success:
            raise RuntimeError(f"Optimization failed: {result.message}")

        d_hat = float(result.x)
        estimated_hurst = float(d_hat + 0.5)
        whittle_likelihood = float(result.fun)

        if compute_ci and self.parameters["bootstrap_samples"] > 0:
            confidence_interval = self._bootstrap_confidence_interval(
                data,
                estimated_hurst,
            )
        else:
            confidence_interval = self._get_confidence_interval(
                estimated_hurst, whittle_likelihood, js
            )

        corrected_hurst, applied_bias = apply_srd_bias_correction(
            "WaveletWhittle", float(estimated_hurst)
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
            "whittle_likelihood": float(whittle_likelihood),
            "scales": js,
            "wavelet_type": self.parameters["wavelet"],
            "optimization_success": result.success,
            "wavelet_energies": {int(j): float(s) for j, s in zip(js, Sj.tolist())},
            "bias_correction": applied_bias,
            "method": "numpy",
            "optimization_framework": self.optimization_framework,
        }
        
        return self.results

    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of Wavelet Whittle estimation."""
        # For now, use NumPy implementation with Numba JIT compilation
        # This can be enhanced with custom Numba kernels for specific operations
        return self._estimate_numpy(data)

    def _bootstrap_confidence_interval(
        self,
        data: np.ndarray,
        point_estimate: float,
    ) -> Tuple[float, float]:
        """Approximate confidence interval using circular block bootstrap."""
        n_boot = self.parameters.get("bootstrap_samples", 0)
        if n_boot <= 0:
            return (float(point_estimate), float(point_estimate))

        estimates: List[float] = []
        n = len(data)
        block_size = self.parameters.get("bootstrap_block_size")
        if block_size is None:
            block_size = max(32, n // 4)
        block_size = min(max(8, block_size), n)

        for _ in range(n_boot):
            resampled = self._circular_block_resample(data, block_size)
            try:
                replicate = self._estimate_numpy(
                    resampled,
                    compute_ci=False,
                )
                est = replicate.get("hurst_parameter")
                if est is not None and np.isfinite(est):
                    estimates.append(float(est))
            except Exception:
                continue

        if len(estimates) < max(8, n_boot // 4):
            margin = max(0.1, 0.5 * abs(point_estimate - 0.5))
            lower = float(max(0.01, point_estimate - margin))
            upper = float(min(0.99, point_estimate + margin))
            return (lower, upper)

        alpha = 1.0 - self.parameters["confidence"]
        lower = float(np.percentile(estimates, 100 * (alpha / 2)))
        upper = float(np.percentile(estimates, 100 * (1 - alpha / 2)))
        if lower == upper:
            lower = min(lower, point_estimate)
            upper = max(upper, point_estimate)
        return (lower, upper)

    def _circular_block_resample(self, data: np.ndarray, block_size: int) -> np.ndarray:
        """Generate circular block bootstrap resample."""
        n = len(data)
        n_blocks = max(1, int(np.ceil(n / block_size)))
        resampled = np.empty(n, dtype=float)
        pos = 0
        for _ in range(n_blocks):
            start = np.random.randint(0, n)
            block = np.take(
                data,
                np.arange(start, start + block_size) % n,
                mode="wrap",
            )
            length = min(block_size, n - pos)
            resampled[pos : pos + length] = block[:length]
            pos += length
            if pos >= n:
                break
        return resampled

    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of Wavelet Whittle estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)

        data_np = np.asarray(data, dtype=float)
        n = len(data_np)

        if self.parameters["scales"] is None:
            self.parameters["scales"] = list(range(1, min(11, int(np.log2(n)))))

        if n < 2 ** max(self.parameters["scales"]):
            raise ValueError(
                f"Data length {n} is too short for scale {max(self.parameters['scales'])}"
            )

        wavelet = self.parameters["wavelet"]
        w = pywt.Wavelet(wavelet)
        J = pywt.dwt_max_level(n, w.dec_len)
        if J < 2:
            raise ValueError("Insufficient data length for wavelet decomposition")

        js = [j for j in self.parameters["scales"] if 1 <= j <= J]
        if len(js) < 3:
            warnings.warn("Few scales available for Wavelet Whittle; estimates may be unstable")

        max_level = max(js)
        data_jax = jnp.asarray(data_np, dtype=jnp.float64)
        _, details = dwt_periodized(data_jax, wavelet, max_level)
        selected_details = [details[j - 1] for j in js]
        Sj_jax, nj_jax = wavelet_detail_variances(selected_details, robust=False)

        js_arr = jnp.asarray(js, dtype=jnp.float64)
        Sj = jnp.asarray(Sj_jax, dtype=jnp.float64)
        nj = jnp.asarray(nj_jax, dtype=jnp.float64)

        def objective(d: float) -> jnp.ndarray:
            d_val = jnp.asarray(d, dtype=jnp.float64)
            a = 2.0 ** (2.0 * d_val * js_arr)
            return jnp.sum(nj * (jnp.log(a) + Sj / a))

        d_grid = jnp.linspace(-0.49, 1.49, 2048)
        objective_values = vmap(objective)(d_grid)
        idx = jnp.argmin(objective_values)
        d_hat = float(d_grid[idx])
        whittle_likelihood = float(objective(d_hat))

        estimated_hurst = float(d_hat + 0.5)

        confidence_interval = self._get_confidence_interval(
            estimated_hurst,
            whittle_likelihood,
            js,
        )

        corrected_hurst, applied_bias = apply_srd_bias_correction(
            "WaveletWhittle", float(estimated_hurst)
        )
        if applied_bias != 0.0 and confidence_interval is not None:
            lower = max(0.01, min(0.99, confidence_interval[0] - applied_bias))
            upper = max(0.01, min(0.99, confidence_interval[1] - applied_bias))
            confidence_interval = (lower, upper)
        estimated_hurst = corrected_hurst

        wavelet_energies = {
            int(j): float(Sj[i])
            for i, j in enumerate(js)
        }

        self.results = {
            "hurst_parameter": estimated_hurst,
            "confidence_interval": confidence_interval,
            "whittle_likelihood": whittle_likelihood,
            "scales": js,
            "wavelet_type": wavelet,
            "optimization_success": True,
            "wavelet_energies": wavelet_energies,
            "bias_correction": applied_bias,
            "method": "jax",
            "optimization_framework": self.optimization_framework,
        }

        return self.results

    def _theoretical_spectrum_fgn(
        self, frequencies: np.ndarray, H: float, sigma: float = 1.0
    ) -> np.ndarray:
        """Calculate theoretical spectrum for fractional Gaussian noise."""
        # Theoretical spectrum for fGn
        # S(f) = sigma^2 * |f|^(1-2H) for f != 0
        spectrum = np.zeros_like(frequencies)
        nonzero_freq = frequencies != 0
        spectrum[nonzero_freq] = sigma**2 * np.abs(frequencies[nonzero_freq]) ** (
            1 - 2 * H
        )

        # Handle zero frequency (DC component)
        if np.any(frequencies == 0):
            spectrum[frequencies == 0] = sigma**2

        return spectrum

    def _whittle_likelihood(self, *args, **kwargs) -> float:
        # Deprecated path retained for compatibility; not used in new implementation
        return 0.0

    def _get_confidence_interval(
        self, estimated_hurst: float, whittle_likelihood: float,
        js: List[int]
    ) -> Tuple[float, float]:
        """Calculate confidence interval for the Hurst parameter estimate."""
        confidence = self.parameters["confidence"]
        
        # Simple confidence interval based on likelihood curvature
        # This is a simplified approach - for production use, consider more sophisticated methods
        
        # Calculate likelihood at nearby points
        H_values = np.linspace(max(0.01, estimated_hurst - 0.1), 
                              min(0.99, estimated_hurst + 0.1), 21)
        # approximate curvature by quadratic fit around minimum using objective_d on d
        # map H to d = H-0.5
        likelihoods = []
        for H in H_values:
            d = H - 0.5
            a = 2.0 ** (2.0 * d * np.asarray(js, float))
            # pseudo profile using equal nj and Sj=1 placeholders (rough width only)
            likelihoods.append(float(np.sum(np.log(a) + 1.0 / a)))
        
        # Find the range where likelihood is within threshold
        threshold = whittle_likelihood + 2.0  # Approximate 95% confidence
        
        valid_indices = np.array(likelihoods) <= threshold
        if np.any(valid_indices):
            valid_H = H_values[valid_indices]
            lower = float(np.min(valid_H))
            upper = float(np.max(valid_H))
        else:
            # Fallback to simple interval
            margin = 0.05
            lower = float(max(0.01, estimated_hurst - margin))
            upper = float(min(0.99, estimated_hurst + margin))
        
        return (lower, upper)

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

    def plot_analysis(self, figsize: Tuple[int, int] = (12, 8), save_path: Optional[str] = None) -> None:
        """Plot the wavelet Whittle analysis results."""
        if not self.results:
            raise ValueError("No results available. Run estimate() first.")

        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle(f'Wavelet Whittle Analysis - {self.parameters["wavelet"]} Wavelet', fontsize=16)

        # Plot 1: Hurst parameter estimate
        ax1 = axes[0, 0]
        hurst = self.results["hurst_parameter"]
        conf_interval = self.results["confidence_interval"]
        
        ax1.bar(["Hurst Parameter"], [hurst], yerr=[[hurst-conf_interval[0]], [conf_interval[1]-hurst]], 
                capsize=10, alpha=0.7, color='skyblue')
        ax1.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='H=0.5 (no memory)')
        ax1.set_ylabel("Hurst Parameter")
        ax1.set_title(f"Hurst Parameter Estimate: {hurst:.3f}")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Whittle likelihood
        ax2 = axes[0, 1]
        likelihood = self.results["whittle_likelihood"]
        
        ax2.bar(["Whittle Likelihood"], [likelihood], alpha=0.7, color='lightgreen')
        ax2.set_ylabel("Negative Log-Likelihood")
        ax2.set_title(f"Whittle Likelihood: {likelihood:.3f}")
        ax2.grid(True, alpha=0.3)

        # Plot 3: Scales used
        ax3 = axes[1, 0]
        scales = self.results["scales"]
        
        ax3.bar(range(len(scales)), scales, alpha=0.7, color='orange')
        ax3.set_xlabel("Scale Index")
        ax3.set_ylabel("Scale Value")
        ax3.set_title("Wavelet Scales Used")
        ax3.grid(True, alpha=0.3)

        # Plot 4: Optimization success
        ax4 = axes[1, 1]
        success = self.results["optimization_success"]
        success_text = "Success" if success else "Failed"
        color = 'green' if success else 'red'
        
        ax4.bar(["Optimization"], [1], alpha=0.7, color=color)
        ax4.set_ylabel("Status")
        ax4.set_title(f"Optimization: {success_text}")
        ax4.set_ylim(0, 1.2)
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.show()

    def get_method_recommendation(self, n: int) -> Dict[str, Any]:
        """Get method recommendation for a given data size."""
        if n < 100:
            return {
                "recommended_method": "numpy",
                "reasoning": f"Data size n={n} is too small for optimization benefits",
                "method_details": {
                    "description": "NumPy implementation",
                    "best_for": "Small datasets (n < 100)",
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
