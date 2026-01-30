from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Tuple
import math


@lru_cache(None)
def _load_srd_bias_table() -> dict:
    """
    Load SRD (short-range) bias calibration table if available.

    Returns
    -------
    dict
        Mapping estimator name -> {'bias': float, 'std': float, 'n': int}
    """
    try:
        project_root = Path(__file__).resolve().parents[2]
        cal_path = project_root / "benchmark_results" / "calibration" / "srd_bias_estimates.json"
        if not cal_path.exists():
            return {}
        data = json.loads(cal_path.read_text())
        return data.get("bias", {})
    except Exception:
        return {}


def apply_srd_bias_correction(estimator_name: str, hurst_estimate: float) -> Tuple[float, float]:
    """
    Apply SRD bias correction to a Hurst estimate if calibration data are available.

    Parameters
    ----------
    estimator_name : str
        Name of the estimator as stored in the calibration table.
    hurst_estimate : float
        Raw Hurst parameter estimate.

    Returns
    -------
    Tuple[float, float]
        (corrected_hurst, applied_bias)
    """
    table = _load_srd_bias_table()
    entry = table.get(estimator_name)
    if not entry:
        return float(hurst_estimate), 0.0

    if not math.isfinite(hurst_estimate):
        return float(hurst_estimate), 0.0

    bias = float(entry.get("bias", 0.0))
    corrected = hurst_estimate - bias
    corrected = max(0.01, min(0.99, corrected))
    return float(corrected), bias

