#!/usr/bin/env python3
"""
Utilities for backend selection in unified estimators.
"""
import logging
import os
import warnings
from typing import Optional

# --- Backend Availability ---
JAX_AVAILABLE = False
JAX_GPU_AVAILABLE = False
JAX_DEFAULT_DEVICE: Optional[str] = None

try:
    import jax
    from jax import config as jax_config

    # Suppress noisy plugin warnings that can occur during device discovery
    logging.getLogger("jax._src.xla_bridge").setLevel(logging.CRITICAL)
    logging.getLogger("jax_plugins").setLevel(logging.CRITICAL)

    # Respect explicit opt-in/out flags
    force_cpu = os.environ.get("LRDBENCHMARK_FORCE_CPU", "").lower() in {"1", "true", "yes"}

    # Enable higher precision by default for numerical stability
    jax_config.update("jax_enable_x64", True)

    if force_cpu:
        jax_config.update("jax_platform_name", "cpu")

    try:
        devices = jax.devices()
    except RuntimeError:
        if not force_cpu:
            # Retry on CPU fallback if GPU probing failed (e.g., CUDA error with no visible device)
            jax_config.update("jax_platform_name", "cpu")
            devices = jax.devices()
        else:
            devices = []

    if devices:
        JAX_AVAILABLE = True
        JAX_GPU_AVAILABLE = any(device.platform.lower() in {"gpu", "cuda"} for device in devices)
        JAX_DEFAULT_DEVICE = devices[0].platform
except ImportError:
    JAX_AVAILABLE = False
    JAX_GPU_AVAILABLE = False
    JAX_DEFAULT_DEVICE = None
except Exception as exc:  # pragma: no cover - defensive fallback
    warnings.warn(f"Failed to initialize JAX backend: {exc}")
    JAX_AVAILABLE = False
    JAX_GPU_AVAILABLE = False
    JAX_DEFAULT_DEVICE = None

try:
    import numba

    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

# --- Selection Logic ---
def select_backend(requested_backend: str = 'auto') -> str:
    """
    Selects the best available compute backend.

    Priority: JAX (GPU/TPU) > Numba (CPU JIT) > NumPy (fallback).

    Args:
        requested_backend: The user-requested backend ('auto', 'jax', 
                           'numba', 'numpy').

    Returns:
        The name of the selected backend.
    """
    if requested_backend == 'auto':
        if JAX_AVAILABLE:
            return 'jax'
        if NUMBA_AVAILABLE:
            warnings.warn("JAX not available. Falling back to Numba.")
            return 'numba'
        warnings.warn("JAX and Numba not available. Falling back to NumPy.")
        return 'numpy'
    
    if requested_backend == 'jax':
        if JAX_AVAILABLE:
            return 'jax'
        warnings.warn("Requested backend 'jax' not available. Falling back to auto-selection.")
        return select_backend('auto')

    if requested_backend == 'numba':
        if NUMBA_AVAILABLE:
            return 'numba'
        warnings.warn("Requested backend 'numba' not available. Falling back to auto-selection.")
        return select_backend('auto')

    if requested_backend == 'numpy':
        return 'numpy'

    warnings.warn(f"Unknown backend '{requested_backend}' requested. Falling back to auto-selection.")
    return select_backend('auto')
