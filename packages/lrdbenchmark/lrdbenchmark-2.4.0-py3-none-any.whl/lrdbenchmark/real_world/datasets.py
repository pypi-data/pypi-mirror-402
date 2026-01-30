#!/usr/bin/env python3
"""
Deterministic, portable dataset definitions for real-world validation.

The goal of these specifications is not to mirror full-scale datasets but to
provide representative signals that capture the qualitative characteristics of
the domains we care about (financial, physiological, climate, network, etc.)
while remaining fully reproducible and lightweight.

Expanded to 15 scenarios for comprehensive benchmarking (300 samples total):
- Traffic networks: 3 scenarios
- Biomedical: 4 scenarios
- Climate: 3 scenarios
- Economic: 3 scenarios
- Geophysical: 2 scenarios
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable

import numpy as np


@dataclass(frozen=True)
class DatasetSpec:
    """Metadata and generator for a deterministic validation dataset."""

    name: str
    domain: str
    description: str
    default_length: int
    base_seed: int
    generator: Callable[[int, np.random.Generator], np.ndarray]


# =============================================================================
# TRAFFIC NETWORK SCENARIOS (3)
# =============================================================================

def _network_backbone(length: int, rng: np.random.Generator) -> np.ndarray:
    """Backbone network traffic with LRD characteristics."""
    time = np.linspace(0, 1, length)
    baseline = 150 + 40 * np.sin(4 * np.pi * time)
    burst_prob = np.clip(0.1 + 0.2 * np.sin(2 * np.pi * time), 0, 0.9)
    bursts = rng.binomial(1, burst_prob, size=length) * rng.normal(50, 10, size=length)
    noise = rng.normal(0, 5, length)
    return baseline + bursts + noise


def _network_p2p(length: int, rng: np.random.Generator) -> np.ndarray:
    """P2P file sharing traffic with heavy-tailed bursts."""
    time = np.linspace(0, 2 * np.pi, length)
    baseline = 80 + 20 * np.sin(0.5 * time)
    # Pareto-like bursts for heavy-tailed behavior
    bursts = rng.pareto(2.5, length) * 10 * rng.binomial(1, 0.15, length)
    trend = 0.005 * np.arange(length)
    noise = rng.normal(0, 3, length)
    return baseline + bursts + trend + noise


def _network_iot(length: int, rng: np.random.Generator) -> np.ndarray:
    """IoT sensor network with periodic transmissions and anomalies."""
    time = np.linspace(0, 4 * np.pi, length)
    # Multiple periodic components from different sensor types
    periodic1 = 30 * np.sin(time)
    periodic2 = 15 * np.sin(3 * time + 0.5)
    periodic3 = 8 * np.sin(7 * time + 1.2)
    # Occasional anomalies
    anomalies = rng.binomial(1, 0.02, length) * rng.normal(50, 15, length)
    noise = rng.normal(0, 2, length)
    return 50 + periodic1 + periodic2 + periodic3 + anomalies + noise


# =============================================================================
# BIOMEDICAL SCENARIOS (4)
# =============================================================================

def _physiological_hrv(length: int, rng: np.random.Generator) -> np.ndarray:
    """Heart-rate variability with respiratory sinus arrhythmia."""
    t = np.linspace(0, 8 * np.pi, length)
    baseline = 0.8 + 0.1 * np.sin(0.2 * t)
    respiration = 0.05 * np.sin(0.35 * t + 0.3)
    noise = rng.normal(0, 0.02, length)
    return baseline + respiration + noise


def _physiological_eeg(length: int, rng: np.random.Generator) -> np.ndarray:
    """EEG-like signal with alpha/beta rhythms and artifacts."""
    t = np.linspace(0, 4 * np.pi, length)
    alpha = 0.5 * np.sin(10 * t)
    beta = 0.2 * np.sin(20 * t + 1.3)
    artifacts = 0.1 * np.sin(1.5 * t) + 0.05 * np.sign(np.sin(0.3 * t + 0.8))
    noise = rng.normal(0, 0.05, length)
    return alpha + beta + artifacts + noise


def _physiological_emg(length: int, rng: np.random.Generator) -> np.ndarray:
    """EMG signal with muscle activation bursts."""
    t = np.linspace(0, 6 * np.pi, length)
    # Baseline muscle tone
    baseline = 0.1 * np.abs(np.sin(0.1 * t))
    # Bursts of muscle activation
    activation_prob = 0.15 + 0.1 * np.sin(0.3 * t)
    activations = rng.binomial(1, np.clip(activation_prob, 0, 1), length)
    burst_signal = activations * np.abs(rng.normal(0.5, 0.2, length))
    # High-frequency noise component
    noise = rng.normal(0, 0.03, length)
    return baseline + burst_signal + noise


def _physiological_respiratory(length: int, rng: np.random.Generator) -> np.ndarray:
    """Respiratory flow signal with breathing pattern variability."""
    t = np.linspace(0, 10 * np.pi, length)
    # Normal breathing rate ~12-20 breaths/min
    breathing = 0.8 * np.sin(0.5 * t)
    # Rate variability
    rate_var = 0.15 * np.sin(0.05 * t) * np.sin(0.5 * t)
    # Occasional sighs/deep breaths
    sighs = rng.binomial(1, 0.01, length) * rng.uniform(0.3, 0.6, length)
    noise = rng.normal(0, 0.02, length)
    return breathing + rate_var + sighs + noise


# =============================================================================
# CLIMATE SCENARIOS (3)
# =============================================================================

def _climate_temperature(length: int, rng: np.random.Generator) -> np.ndarray:
    """Temperature anomaly with annual and multi-annual cycles."""
    t = np.linspace(0, 2 * np.pi, length)
    seasonal = 0.6 * np.sin(t) + 0.2 * np.sin(2 * t + 0.4)
    multi_year = 0.05 * np.sin(0.2 * t + 1.1)
    trend = 0.0015 * np.arange(length)
    noise = rng.normal(0, 0.03, length)
    return 15 + seasonal + multi_year + trend + noise


def _climate_precipitation(length: int, rng: np.random.Generator) -> np.ndarray:
    """Precipitation with seasonal patterns and heavy-tailed events."""
    t = np.linspace(0, 2 * np.pi, length)
    # Seasonal baseline
    seasonal = 50 + 30 * np.sin(t)
    # Wet/dry period modulation
    modulation = 0.7 + 0.3 * np.sin(0.5 * t + 0.8)
    # Heavy-tailed extreme events
    extremes = rng.exponential(10, length) * rng.binomial(1, 0.05, length)
    noise = rng.gamma(2, 3, length)
    return np.maximum(0, seasonal * modulation + extremes + noise - 50)


def _climate_pressure(length: int, rng: np.random.Generator) -> np.ndarray:
    """Atmospheric pressure with synoptic-scale variations."""
    t = np.linspace(0, 4 * np.pi, length)
    # Mean sea level pressure baseline
    baseline = 1013.25
    # Synoptic variations (weather systems)
    synoptic = 15 * np.sin(0.3 * t) + 8 * np.sin(0.7 * t + 0.5)
    # Diurnal cycle
    diurnal = 1.5 * np.sin(2 * t)
    # Random frontal passages
    fronts = rng.normal(0, 3, length)
    return baseline + synoptic + diurnal + fronts


# =============================================================================
# ECONOMIC SCENARIOS (3)
# =============================================================================

def _financial_stock(length: int, rng: np.random.Generator) -> np.ndarray:
    """Stock log-returns with volatility clustering."""
    t = np.linspace(0, 6 * np.pi, length)
    trend = 0.002 * np.arange(length)
    seasonal = 0.04 * np.sin(0.5 * t) + 0.02 * np.sin(1.3 * t + 0.6)
    volatility = 0.03 * np.sin(0.1 * t + 1.5)
    noise = rng.normal(0, 0.01, length)
    return trend + seasonal + volatility * noise.cumsum() / max(length, 1)


def _financial_forex(length: int, rng: np.random.Generator) -> np.ndarray:
    """Foreign exchange rate with mean reversion tendencies."""
    t = np.linspace(0, 4 * np.pi, length)
    # Mean-reverting component
    mean_level = 1.0
    reversion_speed = 0.02
    rate = np.zeros(length)
    rate[0] = mean_level + rng.normal(0, 0.01)
    for i in range(1, length):
        drift = reversion_speed * (mean_level - rate[i-1])
        rate[i] = rate[i-1] + drift + rng.normal(0, 0.005)
    # Add periodic interventions
    interventions = 0.01 * np.sin(0.5 * t)
    return rate + interventions


def _financial_commodity(length: int, rng: np.random.Generator) -> np.ndarray:
    """Commodity prices with supply shocks and seasonal patterns."""
    t = np.linspace(0, 3 * np.pi, length)
    # Baseline trend
    trend = 100 + 0.01 * np.arange(length)
    # Seasonal pattern (harvest cycles)
    seasonal = 10 * np.sin(t) + 5 * np.sin(2 * t + 0.3)
    # Supply shocks (heavy-tailed)
    shocks = rng.standard_t(3, length) * 2
    # Autocorrelated noise
    noise = np.zeros(length)
    noise[0] = rng.normal(0, 1)
    for i in range(1, length):
        noise[i] = 0.7 * noise[i-1] + rng.normal(0, 1)
    return trend + seasonal + shocks + noise


# =============================================================================
# GEOPHYSICAL SCENARIOS (2)
# =============================================================================

def _geophysical_seismic(length: int, rng: np.random.Generator) -> np.ndarray:
    """Seismic background noise with occasional events."""
    t = np.linspace(0, 8 * np.pi, length)
    # Microseismic background
    background = 0.1 * np.sin(0.8 * t) + 0.05 * np.sin(2.3 * t + 0.7)
    # Random seismic events (Poisson process with magnitude)
    event_times = rng.binomial(1, 0.005, length)
    magnitudes = rng.exponential(0.5, length)
    events = event_times * magnitudes
    # Decay after events
    decay = np.zeros(length)
    for i in range(length):
        if events[i] > 0:
            decay_length = min(50, length - i)
            decay[i:i+decay_length] += events[i] * np.exp(-np.arange(decay_length) / 10)
    noise = rng.normal(0, 0.02, length)
    return background + decay + noise


def _geophysical_river(length: int, rng: np.random.Generator) -> np.ndarray:
    """River discharge with seasonal and flood patterns."""
    t = np.linspace(0, 2 * np.pi, length)
    # Seasonal base flow
    seasonal = 100 + 50 * np.sin(t - np.pi/4)
    # Snowmelt peak
    snowmelt = 30 * np.exp(-((t - np.pi/2)**2) / 0.5)
    # Storm events (Poisson with gamma magnitude)
    storms = rng.binomial(1, 0.03, length) * rng.gamma(3, 20, length)
    # Baseflow recession
    noise = rng.gamma(2, 5, length)
    return np.maximum(10, seasonal + snowmelt + storms + noise)


def _biophysics_protein(length: int, rng: np.random.Generator) -> np.ndarray:
    """Protein folding energy landscape surrogate."""
    t = np.linspace(0, 3 * np.pi, length)
    folding = 2 * np.exp(-0.3 * t) * np.sin(3 * t)
    micro_fluctuations = rng.normal(0, 0.1, length)
    return folding + micro_fluctuations


# =============================================================================
# DATASET SPECIFICATIONS (15 total)
# =============================================================================

DATASETS: Iterable[DatasetSpec] = (
    # Traffic Networks (3)
    DatasetSpec(
        name="network_backbone",
        domain="network",
        description="Backbone network traffic with bursty behavior and LRD.",
        default_length=1024,
        base_seed=101,
        generator=_network_backbone,
    ),
    DatasetSpec(
        name="network_p2p",
        domain="network",
        description="P2P file sharing traffic with heavy-tailed bursts.",
        default_length=1024,
        base_seed=102,
        generator=_network_p2p,
    ),
    DatasetSpec(
        name="network_iot",
        domain="network",
        description="IoT sensor network with periodic transmissions.",
        default_length=1024,
        base_seed=103,
        generator=_network_iot,
    ),
    # Biomedical (4)
    DatasetSpec(
        name="physiological_hrv",
        domain="biomedical",
        description="Heart-rate variability with respiratory modulation.",
        default_length=1024,
        base_seed=201,
        generator=_physiological_hrv,
    ),
    DatasetSpec(
        name="physiological_eeg",
        domain="biomedical",
        description="EEG signal with alpha/beta rhythms and artifacts.",
        default_length=2048,
        base_seed=202,
        generator=_physiological_eeg,
    ),
    DatasetSpec(
        name="physiological_emg",
        domain="biomedical",
        description="EMG signal with muscle activation bursts.",
        default_length=1024,
        base_seed=203,
        generator=_physiological_emg,
    ),
    DatasetSpec(
        name="physiological_respiratory",
        domain="biomedical",
        description="Respiratory flow with breathing pattern variability.",
        default_length=1024,
        base_seed=204,
        generator=_physiological_respiratory,
    ),
    # Climate (3)
    DatasetSpec(
        name="climate_temperature",
        domain="climate",
        description="Temperature anomaly with seasonal and multi-annual cycles.",
        default_length=1200,
        base_seed=301,
        generator=_climate_temperature,
    ),
    DatasetSpec(
        name="climate_precipitation",
        domain="climate",
        description="Precipitation with heavy-tailed extreme events.",
        default_length=1024,
        base_seed=302,
        generator=_climate_precipitation,
    ),
    DatasetSpec(
        name="climate_pressure",
        domain="climate",
        description="Atmospheric pressure with synoptic-scale variations.",
        default_length=1024,
        base_seed=303,
        generator=_climate_pressure,
    ),
    # Economic (3)
    DatasetSpec(
        name="financial_stock",
        domain="economic",
        description="Stock log-returns with volatility clustering.",
        default_length=1024,
        base_seed=401,
        generator=_financial_stock,
    ),
    DatasetSpec(
        name="financial_forex",
        domain="economic",
        description="Foreign exchange rate with mean reversion.",
        default_length=1024,
        base_seed=402,
        generator=_financial_forex,
    ),
    DatasetSpec(
        name="financial_commodity",
        domain="economic",
        description="Commodity prices with supply shocks.",
        default_length=1024,
        base_seed=403,
        generator=_financial_commodity,
    ),
    # Geophysical (2)
    DatasetSpec(
        name="geophysical_seismic",
        domain="geophysical",
        description="Seismic background noise with occasional events.",
        default_length=2048,
        base_seed=501,
        generator=_geophysical_seismic,
    ),
    DatasetSpec(
        name="geophysical_river",
        domain="geophysical",
        description="River discharge with seasonal and flood patterns.",
        default_length=1024,
        base_seed=502,
        generator=_geophysical_river,
    ),
)


def dataset_map() -> Dict[str, DatasetSpec]:
    """Return dataset specifications keyed by their canonical name."""
    return {spec.name: spec for spec in DATASETS}

