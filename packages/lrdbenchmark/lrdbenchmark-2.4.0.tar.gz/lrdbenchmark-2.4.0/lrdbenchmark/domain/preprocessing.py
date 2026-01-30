#!/usr/bin/env python3
"""
Domain-specific preprocessing utilities for biomedical time series.

The helper class intentionally follows a single-dispatch pattern: the public
``preprocess`` method selects the appropriate pipeline based on the provided
domain label while exposing shared sampling-rate guidance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

SAMPLING_RATE_GUIDANCE: Dict[str, Dict[str, object]] = {
    "eeg": {
        "recommended_range_hz": (128, 512),
        "comment": "Use ≥256 Hz when analysing beta activity or higher.",
    },
    "ecg": {
        "recommended_range_hz": (100, 500),
        "comment": "For HRV, 250 Hz provides robust R-peak localisation.",
    },
    "hrv": {
        "recommended_range_hz": (4, 16),
        "comment": "Resampled RR-intervals at 4 Hz are standard for HRV metrics.",
    },
}


def _bandpass(data: np.ndarray, low: float, high: float, fs: float, order: int = 4):
    nyquist = 0.5 * fs
    b, a = butter(order, [low / nyquist, high / nyquist], btype="band")
    return filtfilt(b, a, data)


def _highpass(data: np.ndarray, cutoff: float, fs: float, order: int = 4):
    nyquist = 0.5 * fs
    b, a = butter(order, cutoff / nyquist, btype="high")
    return filtfilt(b, a, data)


def _notch(data: np.ndarray, freq: float, fs: float, quality: float = 30.0):
    w0 = freq / (fs / 2)
    b, a = iirnotch(w0, quality)
    return filtfilt(b, a, data)


@dataclass
class DomainPreprocessor:
    """Switchboard for EEG/ECG preprocessing along with sampling guidance."""

    def preprocess(
        self,
        data: np.ndarray,
        domain: str,
        sampling_rate_hz: Optional[float],
    ) -> Tuple[np.ndarray, Dict[str, object]]:
        domain = domain.lower()
        if sampling_rate_hz is None:
            raise ValueError("sampling_rate_hz must be provided for domain preprocessing")

        if domain == "eeg":
            return self._preprocess_eeg(data, sampling_rate_hz)
        if domain in {"ecg", "hrv"}:
            return self._preprocess_ecg(data, sampling_rate_hz)

        raise ValueError(f"Unsupported domain '{domain}' for domain-specific preprocessing.")

    def sampling_guidance(self) -> Dict[str, Dict[str, object]]:
        """Return recommended sampling rate guidance per supported domain."""
        return SAMPLING_RATE_GUIDANCE.copy()

    # ------------------------------------------------------------------ pipelines
    def _preprocess_eeg(
        self, data: np.ndarray, sampling_rate_hz: float
    ) -> Tuple[np.ndarray, Dict[str, object]]:
        processed = np.asarray(data, dtype=np.float64)

        # Band-pass 1–45 Hz to retain canonical rhythms.
        processed = _bandpass(processed, low=1.0, high=45.0, fs=sampling_rate_hz, order=4)

        # Notch filter line noise (50 Hz unless a 60 Hz system is specified).
        notch_freq = 60.0 if sampling_rate_hz % 60 == 0 else 50.0
        processed = _notch(processed, freq=notch_freq, fs=sampling_rate_hz)

        metadata = {
            "domain": "eeg",
            "sampling_rate_hz": sampling_rate_hz,
            "bandpass_hz": (1.0, 45.0),
            "notch_hz": notch_freq,
        }
        return processed, metadata

    def _preprocess_ecg(
        self, data: np.ndarray, sampling_rate_hz: float
    ) -> Tuple[np.ndarray, Dict[str, object]]:
        processed = np.asarray(data, dtype=np.float64)

        # Remove baseline drift and high-frequency noise.
        processed = _highpass(processed, cutoff=0.5, fs=sampling_rate_hz, order=2)
        processed = _bandpass(processed, low=0.5, high=40.0, fs=sampling_rate_hz, order=4)

        # Suppress mains interference.
        notch_freq = 60.0 if sampling_rate_hz % 60 == 0 else 50.0
        processed = _notch(processed, freq=notch_freq, fs=sampling_rate_hz)

        metadata = {
            "domain": "ecg",
            "sampling_rate_hz": sampling_rate_hz,
            "highpass_hz": 0.5,
            "bandpass_hz": (0.5, 40.0),
            "notch_hz": notch_freq,
        }
        return processed, metadata

