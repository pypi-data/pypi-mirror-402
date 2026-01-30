#!/usr/bin/env python3
"""
JAX-native utilities for discrete wavelet transforms used by GPU estimators.
"""
from __future__ import annotations

import functools
from typing import Callable, List, Tuple

import pywt

try:
    import jax.numpy as jnp
    from jax import jit

    JAX_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when JAX optional dependency missing
    jnp = None  # type: ignore[assignment]
    jit = None  # type: ignore[assignment]
    JAX_AVAILABLE = False


def _raise_missing_jax(*_args, **_kwargs):  # type: ignore[no-untyped-def]
    raise ImportError(
        "JAX is required for GPU-accelerated wavelet utilities. "
        "Install the optional dependency via `pip install lrdbenchmark[accel-jax]` "
        "or install `jax` and `jaxlib` manually."
    )


def _wrap_if_available(func: Callable):  # type: ignore[no-untyped-def]
    if JAX_AVAILABLE:
        return func
    return _raise_missing_jax


if JAX_AVAILABLE:

    @functools.lru_cache(maxsize=None)
    def _wavelet_filters(wavelet_name: str) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """Return time-reversed decomposition filters for the requested wavelet."""
        wavelet = pywt.Wavelet(wavelet_name)
        dec_lo = jnp.asarray(wavelet.dec_lo[::-1], dtype=jnp.float64)
        dec_hi = jnp.asarray(wavelet.dec_hi[::-1], dtype=jnp.float64)
        return dec_lo, dec_hi

    def _periodic_pad(signal: jnp.ndarray, pad: int) -> jnp.ndarray:
        """Apply periodization padding compatible with PyWavelets' 'periodization' mode."""
        if pad <= 0:
            return signal
        left = signal[-pad:]
        right = signal[:pad]
        return jnp.concatenate([left, signal, right])

    @jit
    def _dwt_single_level(
        signal: jnp.ndarray, lo: jnp.ndarray, hi: jnp.ndarray
    ) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """Single-level orthonormal DWT with periodization boundary handling."""
        filter_len = lo.shape[0]
        padded = _periodic_pad(signal, filter_len - 1)
        approx_full = jnp.convolve(padded, lo, mode="valid")
        detail_full = jnp.convolve(padded, hi, mode="valid")
        approx = approx_full[::2]
        detail = detail_full[::2]
        return approx, detail

    def dwt_periodized(
        signal: jnp.ndarray, wavelet_name: str, level: int
    ) -> Tuple[jnp.ndarray, List[jnp.ndarray]]:
        """
        Perform a multi-level discrete wavelet transform using periodization padding.

        Returns the final approximation coefficients and a list of detail coefficients
        ordered from finest (level 1) to coarsest (level = J).
        """
        if level <= 0:
            return signal, []

        lo, hi = _wavelet_filters(wavelet_name)
        approx = signal
        details: List[jnp.ndarray] = []

        for _ in range(level):
            approx, detail = _dwt_single_level(approx, lo, hi)
            details.append(detail)

        return approx, details

    def wavelet_detail_variances(
        details: List[jnp.ndarray], robust: bool = False
    ) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """
        Compute per-scale variance (or robust MAD-based variance) and coefficient counts.
        Returns arrays aligned with the provided details list.
        """
        variances = []
        counts = []
        for coeffs in details:
            counts.append(coeffs.shape[0])
            if robust:
                med = jnp.median(coeffs)
                mad = jnp.median(jnp.abs(coeffs - med))
                sigma = mad / 0.6744897501960817
                variances.append(sigma**2)
            else:
                variances.append(jnp.var(coeffs, ddof=1))
        return jnp.asarray(variances, dtype=jnp.float64), jnp.asarray(counts, dtype=jnp.int32)

else:
    # Provide callables that raise with a clear diagnostic while preserving importability
    dwt_periodized = _wrap_if_available(lambda *_args, **_kwargs: None)  # type: ignore[assignment]
    wavelet_detail_variances = _wrap_if_available(lambda *_args, **_kwargs: None)  # type: ignore[assignment]


