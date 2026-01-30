#!/usr/bin/env python3
"""
Unified uncertainty quantification utilities for LRDBenchmark estimators.

This module supports three complementary strategies:

* Moving-block bootstrap for generic dependent time series.
* Wavelet-domain resampling that preserves scale-wise energy.
* Parametric Monte Carlo when the underlying data generator is known.

Each method returns calibrated confidence intervals and diagnostic
statistics that can be embedded directly into benchmark reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

import numpy as np

try:
    import pywt  # type: ignore

    PYWT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    pywt = None  # type: ignore
    PYWT_AVAILABLE = False


@dataclass
class IntervalSummary:
    """Container for interval statistics."""

    method: str
    n_samples: int
    mean: Optional[float]
    std: Optional[float]
    confidence_interval: Optional[Tuple[float, float]]
    status: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "n_samples": self.n_samples,
            "mean": self.mean,
            "std": self.std,
            "confidence_interval": self.confidence_interval,
            "status": self.status,
            "metadata": self.metadata,
        }


class UncertaintyQuantifier:
    """
    Compute confidence intervals for H estimators using reusable resampling strategies.
    """

    def __init__(
        self,
        n_block_bootstrap: int = 64,
        block_size: Optional[int] = None,
        n_wavelet_bootstrap: int = 64,
        wavelet: str = "db4",
        max_wavelet_level: Optional[int] = None,
        n_parametric: int = 48,
        confidence_level: float = 0.95,
        random_state: Optional[int] = None,
        max_failures: int = 16,
    ) -> None:
        self.n_block_bootstrap = n_block_bootstrap
        self.block_size = block_size
        self.n_wavelet_bootstrap = n_wavelet_bootstrap
        self.wavelet = wavelet
        self.max_wavelet_level = max_wavelet_level
        self.n_parametric = n_parametric
        self.confidence_level = confidence_level
        self.max_failures = max_failures
        self._rng_seed = random_state

    def compute_intervals(
        self,
        estimator: Any,
        data: np.ndarray,
        base_result: Dict[str, Any],
        true_value: Optional[float] = None,
        data_model_name: Optional[str] = None,
        data_model_params: Optional[Dict[str, Any]] = None,
        data_model_registry: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute uncertainty summaries for an estimator applied to `data`.
        """
        if base_result is None:
            return {
                "status": "unavailable",
                "reason": "No base result available for uncertainty computation.",
            }

        base_estimate = base_result.get("hurst_parameter")
        if base_estimate is None or not np.isfinite(base_estimate):
            return {
                "status": "unavailable",
                "reason": "Estimator did not return a finite 'hurst_parameter'.",
            }

        estimator_cls: Type[Any] = estimator.__class__
        estimator_params: Dict[str, Any] = {}
        if hasattr(estimator, "get_params"):
            try:
                estimator_params = dict(estimator.get_params())
            except Exception:
                estimator_params = getattr(estimator, "parameters", {}).copy()
        else:
            estimator_params = getattr(estimator, "parameters", {}).copy()

        rng = np.random.default_rng(self._rng_seed)
        data = np.asarray(data, dtype=np.float64)

        block_summary = self._block_bootstrap_interval(
            estimator_cls, estimator_params, data, rng
        )
        wavelet_summary = self._wavelet_bootstrap_interval(
            estimator_cls, estimator_params, data, rng
        )
        parametric_summary = self._parametric_interval(
            estimator_cls,
            estimator_params,
            data,
            rng,
            data_model_name,
            data_model_params,
            data_model_registry,
        )

        coverage: Dict[str, Optional[bool]] = {}
        if true_value is not None and np.isfinite(true_value):
            coverage = {
                "block_bootstrap": self._contains_true_value(block_summary, true_value),
                "wavelet_bootstrap": self._contains_true_value(
                    wavelet_summary, true_value
                ),
                "parametric_monte_carlo": self._contains_true_value(
                    parametric_summary, true_value
                ),
            }

        primary_interval = self._select_primary_interval(
            block_summary, wavelet_summary, parametric_summary
        )
        
        # Compute studentized bootstrap interval
        studentized_summary = self._studentized_bootstrap_interval(
            estimator_cls, estimator_params, data, rng, base_estimate
        )
        
        if true_value is not None and np.isfinite(true_value):
            coverage["studentized_bootstrap"] = self._contains_true_value(
                studentized_summary, true_value
            )

        return {
            "status": "ok",
            "confidence_level": self.confidence_level,
            "central_estimate": float(base_estimate),
            "block_bootstrap": block_summary.to_dict(),
            "wavelet_bootstrap": wavelet_summary.to_dict(),
            "parametric_monte_carlo": parametric_summary.to_dict(),
            "studentized_bootstrap": studentized_summary.to_dict(),
            "coverage": coverage,
            "primary_interval": primary_interval,
        }


    # ---------------------------------------------------------------------
    # Bootstrap helpers
    # ---------------------------------------------------------------------
    def _block_bootstrap_interval(
        self,
        estimator_cls: Type[Any],
        estimator_params: Dict[str, Any],
        data: np.ndarray,
        rng: np.random.Generator,
    ) -> IntervalSummary:
        samples: List[float] = []
        n = len(data)
        if n < 16:
            return IntervalSummary(
                method="block_bootstrap",
                n_samples=0,
                mean=None,
                std=None,
                confidence_interval=None,
                status="insufficient_data",
                metadata={"reason": "Time series too short for bootstrap."},
            )

        block_size = self.block_size or max(8, int(np.sqrt(n)))
        block_size = min(block_size, n)
        n_blocks = int(np.ceil(n / block_size))
        failures = 0

        for _ in range(self.n_block_bootstrap):
            if block_size >= n:
                resampled = np.copy(data)
            else:
                starts = rng.integers(0, n - block_size + 1, size=n_blocks)
                blocks = [data[s : s + block_size] for s in starts]
                resampled = np.concatenate(blocks)[:n]

            estimate = self._estimate_hurst(estimator_cls, estimator_params, resampled)
            if estimate is None:
                failures += 1
                if failures > self.max_failures:
                    break
                continue
            samples.append(estimate)

        return self._summarise_samples(
            samples,
            method="block_bootstrap",
            metadata={"block_size": block_size, "failures": failures},
        )

    def _wavelet_bootstrap_interval(
        self,
        estimator_cls: Type[Any],
        estimator_params: Dict[str, Any],
        data: np.ndarray,
        rng: np.random.Generator,
    ) -> IntervalSummary:
        samples: List[float] = []
        n = len(data)
        if n < 32:
            return IntervalSummary(
                method="wavelet_bootstrap",
                n_samples=0,
                mean=None,
                std=None,
                confidence_interval=None,
                status="insufficient_data",
                metadata={"reason": "Time series too short for wavelet bootstrap."},
            )

        if not PYWT_AVAILABLE:
            return IntervalSummary(
                method="wavelet_bootstrap",
                n_samples=0,
                mean=None,
                std=None,
                confidence_interval=None,
                status="unavailable",
                metadata={"reason": "PyWavelets is not installed."},
            )

        try:
            wavelet = pywt.Wavelet(self.wavelet)
        except Exception as exc:
            return IntervalSummary(
                method="wavelet_bootstrap",
                n_samples=0,
                mean=None,
                std=None,
                confidence_interval=None,
                status="unavailable",
                metadata={"reason": f"Wavelet '{self.wavelet}' unavailable: {exc}"},
            )

        max_level = pywt.dwt_max_level(len(data), wavelet.dec_len)
        level = self.max_wavelet_level or max_level
        level = max(1, min(level, max_level))

        coeffs = pywt.wavedec(data, wavelet, mode="periodization", level=level)
        failures = 0

        for _ in range(self.n_wavelet_bootstrap):
            resampled_coeffs = [coeffs[0].copy()]
            for detail in coeffs[1:]:
                resampled_coeffs.append(
                    rng.choice(detail, size=detail.shape, replace=True)
                )

            try:
                resampled = pywt.waverec(
                    resampled_coeffs, wavelet, mode="periodization"
                )
                resampled = resampled[:n]
            except Exception:
                failures += 1
                if failures > self.max_failures:
                    break
                continue

            estimate = self._estimate_hurst(estimator_cls, estimator_params, resampled)
            if estimate is None:
                failures += 1
                if failures > self.max_failures:
                    break
                continue
            samples.append(estimate)

        return self._summarise_samples(
            samples,
            method="wavelet_bootstrap",
            metadata={"wavelet": self.wavelet, "level": level, "failures": failures},
        )

    def _parametric_interval(
        self,
        estimator_cls: Type[Any],
        estimator_params: Dict[str, Any],
        data: np.ndarray,
        rng: np.random.Generator,
        data_model_name: Optional[str],
        data_model_params: Optional[Dict[str, Any]],
        data_model_registry: Optional[Dict[str, Any]],
    ) -> IntervalSummary:
        if (
            data_model_name is None
            or data_model_params is None
            or data_model_registry is None
            or data_model_name not in data_model_registry
        ):
            return IntervalSummary(
                method="parametric_monte_carlo",
                n_samples=0,
                mean=None,
                std=None,
                confidence_interval=None,
                status="unavailable",
                metadata={
                    "reason": "Data model information unavailable for parametric Monte Carlo."
                },
            )

        model_cls = data_model_registry[data_model_name]
        model_kwargs = {
            k: v
            for k, v in dict(data_model_params).items()
            if k not in {"model_name", "contamination"}
        }

        samples: List[float] = []
        failures = 0

        for _ in range(self.n_parametric):
            try:
                model_instance = model_cls(**model_kwargs)
                synthetic = model_instance.generate(
                    len(data), seed=int(rng.integers(0, 2**32 - 1))
                )
            except Exception:
                failures += 1
                if failures > self.max_failures:
                    break
                continue

            estimate = self._estimate_hurst(
                estimator_cls, estimator_params, np.asarray(synthetic)
            )
            if estimate is None:
                failures += 1
                if failures > self.max_failures:
                    break
                continue
            samples.append(estimate)

        return self._summarise_samples(
            samples,
            method="parametric_monte_carlo",
            metadata={"model": data_model_name, "failures": failures},
        )

    def _studentized_bootstrap_interval(
        self,
        estimator_cls: Type[Any],
        estimator_params: Dict[str, Any],
        data: np.ndarray,
        rng: np.random.Generator,
        base_estimate: float,
    ) -> IntervalSummary:
        """
        Studentized (bias-corrected) bootstrap interval.
        
        Uses t-distribution critical values and bias correction for
        improved coverage probability in small samples.
        """
        samples: List[float] = []
        n = len(data)
        if n < 16:
            return IntervalSummary(
                method="studentized_bootstrap",
                n_samples=0,
                mean=None,
                std=None,
                confidence_interval=None,
                status="insufficient_data",
                metadata={"reason": "Time series too short for bootstrap."},
            )

        block_size = self.block_size or max(8, int(np.sqrt(n)))
        block_size = min(block_size, n)
        n_blocks = int(np.ceil(n / block_size))
        failures = 0

        for _ in range(self.n_block_bootstrap):
            if block_size >= n:
                resampled = np.copy(data)
            else:
                starts = rng.integers(0, n - block_size + 1, size=n_blocks)
                blocks = [data[s : s + block_size] for s in starts]
                resampled = np.concatenate(blocks)[:n]

            estimate = self._estimate_hurst(estimator_cls, estimator_params, resampled)
            if estimate is None:
                failures += 1
                if failures > self.max_failures:
                    break
                continue
            samples.append(estimate)

        if len(samples) < 8:
            return IntervalSummary(
                method="studentized_bootstrap",
                n_samples=len(samples),
                mean=None,
                std=None,
                confidence_interval=None,
                status="insufficient_samples",
                metadata={"reason": "Insufficient successful resamples.", "failures": failures},
            )

        samples_arr = np.array(samples)
        mean = float(np.mean(samples_arr))
        std = float(np.std(samples_arr, ddof=1))
        
        # Bias correction
        bias = mean - base_estimate
        bias_corrected_mean = base_estimate - bias
        
        # Use t-distribution for studentized CI
        from scipy import stats
        df = len(samples_arr) - 1
        t_crit = stats.t.ppf((1 + self.confidence_level) / 2, df)
        
        se = std / np.sqrt(len(samples_arr))
        lower = bias_corrected_mean - t_crit * std
        upper = bias_corrected_mean + t_crit * std
        
        return IntervalSummary(
            method="studentized_bootstrap",
            n_samples=len(samples_arr),
            mean=bias_corrected_mean,
            std=std,
            confidence_interval=(float(lower), float(upper)),
            status="ok",
            metadata={
                "block_size": block_size,
                "failures": failures,
                "bias": float(bias),
                "t_critical": float(t_crit),
                "degrees_freedom": df
            },
        )

    # ---------------------------------------------------------------------
    # Utility helpers
    # ---------------------------------------------------------------------
    def _estimate_hurst(
        self,
        estimator_cls: Type[Any],
        estimator_params: Dict[str, Any],
        data: np.ndarray,
    ) -> Optional[float]:
        try:
            estimator_instance = estimator_cls(**estimator_params)
        except Exception:
            estimator_instance = estimator_cls()

        try:
            result = estimator_instance.estimate(data)
        except Exception:
            return None

        value = result.get("hurst_parameter")
        if value is None or not np.isfinite(value):
            return None
        return float(value)

    def _summarise_samples(
        self,
        samples: Iterable[float],
        method: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IntervalSummary:
        samples = [float(x) for x in samples if np.isfinite(x)]
        metadata = metadata or {}

        if len(samples) < 8:
            metadata = dict(metadata)
            metadata["reason"] = metadata.get(
                "reason", "Insufficient successful resamples."
            )
            return IntervalSummary(
                method=method,
                n_samples=len(samples),
                mean=None,
                std=None,
                confidence_interval=None,
                status="insufficient_samples",
                metadata=metadata,
            )

        mean = float(np.mean(samples))
        std = float(np.std(samples, ddof=1))
        lower_q = (1.0 - self.confidence_level) / 2.0 * 100
        upper_q = (1.0 + self.confidence_level) / 2.0 * 100
        ci = (
            float(np.percentile(samples, lower_q)),
            float(np.percentile(samples, upper_q)),
        )

        return IntervalSummary(
            method=method,
            n_samples=len(samples),
            mean=mean,
            std=std,
            confidence_interval=ci,
            status="ok",
            metadata=metadata,
        )

    def _contains_true_value(
        self, summary: IntervalSummary, true_value: float
    ) -> Optional[bool]:
        if summary.status != "ok" or summary.confidence_interval is None:
            return None
        lower, upper = summary.confidence_interval
        return bool(lower <= true_value <= upper)

    def _select_primary_interval(
        self,
        block_summary: IntervalSummary,
        wavelet_summary: IntervalSummary,
        parametric_summary: IntervalSummary,
    ) -> Optional[Dict[str, Any]]:
        for summary in (block_summary, wavelet_summary, parametric_summary):
            if summary.status == "ok" and summary.confidence_interval is not None:
                data = summary.to_dict()
                return {
                    "method": data["method"],
                    "confidence_interval": data["confidence_interval"],
                    "n_samples": data["n_samples"],
                }
        return None

