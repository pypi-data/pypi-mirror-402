#!/usr/bin/env python3
"""
Nonstationary Time Series Generators for LRDBenchmark.

This module provides generators for time series with time-varying Hurst parameters,
designed to test classical estimator failure under nonstationarity and nonequilibrium conditions.

Classes:
    - RegimeSwitchingProcess: Abrupt H transitions at specified change points
    - ContinuousDriftProcess: Smooth H(t) evolution (linear, sinusoidal, logistic)
    - StructuralBreakProcess: Single/multiple break points with severity control
    - EnsembleTimeAverageProcess: Generates data for ergodicity testing
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from scipy.fft import fft, ifft
from enum import Enum


class DriftType(Enum):
    """Types of continuous H drift."""
    LINEAR = "linear"
    SINUSOIDAL = "sinusoidal"
    LOGISTIC = "logistic"
    EXPONENTIAL = "exponential"


class NonstationaryProcessBase:
    """
    Base class for nonstationary process generators.
    
    All nonstationary processes generate time series where the Hurst parameter
    H(t) varies over time, violating the stationarity assumptions of classical
    LRD estimators.
    """
    
    def __init__(self, sigma: float = 1.0, random_state: Optional[int] = None):
        """
        Initialize base nonstationary process.
        
        Parameters
        ----------
        sigma : float
            Standard deviation scaling factor
        random_state : int, optional
            Random seed for reproducibility
        """
        self.sigma = sigma
        self.rng = np.random.default_rng(random_state)
    
    def _generate_fgn_segment(
        self, 
        length: int, 
        H: float, 
        rng: np.random.Generator
    ) -> np.ndarray:
        """
        Generate a segment of Fractional Gaussian Noise with given H.
        
        Uses the Davies-Harte algorithm for exact FGN simulation.
        
        Parameters
        ----------
        length : int
            Length of segment
        H : float
            Hurst parameter for this segment (0 < H < 1)
        rng : np.random.Generator
            Random generator to use
            
        Returns
        -------
        np.ndarray
            FGN segment of specified length
        """
        H = np.clip(H, 0.01, 0.99)  # Numerical stability
        
        # Davies-Harte algorithm
        k_extended = np.arange(length + 1)
        gamma_ext = (self.sigma**2 / 2.0) * (
            np.abs(k_extended + 1)**(2 * H) - 
            2 * np.abs(k_extended)**(2 * H) + 
            np.abs(k_extended - 1)**(2 * H)
        )
        
        first_row = np.concatenate([
            gamma_ext[:length], 
            [gamma_ext[length]], 
            gamma_ext[1:length][::-1]
        ])
        
        eigenvals = fft(first_row).real
        eigenvals = np.maximum(eigenvals, 0)  # Clip numerical noise
        
        V = rng.standard_normal(2 * length) + 1j * rng.standard_normal(2 * length)
        Y = ifft(np.sqrt(eigenvals) * V)
        
        return Y[:length].real * np.sqrt(2 * length)
    
    def _get_h_trajectory(self, length: int) -> np.ndarray:
        """
        Get the H(t) trajectory for the full time series.
        
        Must be implemented by subclasses.
        
        Parameters
        ----------
        length : int
            Length of time series
            
        Returns
        -------
        np.ndarray
            Array of H values at each time point
        """
        raise NotImplementedError("Subclasses must implement _get_h_trajectory")
    
    def generate(
        self, 
        length: int, 
        seed: Optional[int] = None,
        segment_length: int = 256
    ) -> Dict[str, Any]:
        """
        Generate nonstationary time series.
        
        Parameters
        ----------
        length : int
            Length of time series to generate
        seed : int, optional
            Random seed (overrides instance seed if provided)
        segment_length : int
            Length of segments for piecewise generation
            
        Returns
        -------
        dict
            Dictionary containing:
            - 'signal': Generated time series
            - 'h_trajectory': True H values at each time point
            - 'metadata': Process-specific metadata
        """
        local_rng = np.random.default_rng(seed) if seed is not None else self.rng
        
        # Get H trajectory
        h_trajectory = self._get_h_trajectory(length)
        
        # Generate signal in segments with locally constant H
        signal = np.zeros(length)
        n_segments = max(1, length // segment_length)
        segment_boundaries = np.linspace(0, length, n_segments + 1, dtype=int)
        
        for i in range(n_segments):
            start = segment_boundaries[i]
            end = segment_boundaries[i + 1]
            seg_len = end - start
            
            if seg_len > 0:
                # Use mean H for this segment
                local_h = np.mean(h_trajectory[start:end])
                segment = self._generate_fgn_segment(seg_len, local_h, local_rng)
                signal[start:end] = segment
        
        return {
            'signal': signal,
            'h_trajectory': h_trajectory,
            'metadata': self._get_metadata()
        }
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get process-specific metadata."""
        return {
            'process_type': self.__class__.__name__,
            'sigma': self.sigma,
            'stationary': False
        }


class RegimeSwitchingProcess(NonstationaryProcessBase):
    """
    Generate time series with abrupt H transitions at specified change points.
    
    Useful for testing estimator behavior under broken stationarity conditions.
    
    Example
    -------
    >>> gen = RegimeSwitchingProcess(h_regimes=[0.3, 0.8], change_points=[0.5])
    >>> result = gen.generate(1000)
    >>> # First half has H=0.3, second half has H=0.8
    """
    
    def __init__(
        self,
        h_regimes: List[float],
        change_points: Optional[List[float]] = None,
        sigma: float = 1.0,
        random_state: Optional[int] = None
    ):
        """
        Initialize regime switching process.
        
        Parameters
        ----------
        h_regimes : list of float
            H values for each regime (must be in (0, 1))
        change_points : list of float, optional
            Relative positions of change points in (0, 1).
            If None, creates equal-length regimes.
        sigma : float
            Standard deviation scaling
        random_state : int, optional
            Random seed
        """
        super().__init__(sigma, random_state)
        
        self.h_regimes = [np.clip(h, 0.01, 0.99) for h in h_regimes]
        
        if change_points is None:
            # Equal-length regimes
            n_regimes = len(h_regimes)
            self.change_points = [i / n_regimes for i in range(1, n_regimes)]
        else:
            self.change_points = sorted(change_points)
        
        # Validate
        if len(self.change_points) != len(self.h_regimes) - 1:
            raise ValueError(
                f"Need {len(self.h_regimes) - 1} change points for "
                f"{len(self.h_regimes)} regimes"
            )
    
    def _get_h_trajectory(self, length: int) -> np.ndarray:
        """Get step-function H trajectory."""
        h_trajectory = np.zeros(length)
        
        # Convert relative positions to indices
        boundaries = [0] + [int(cp * length) for cp in self.change_points] + [length]
        
        for i, h in enumerate(self.h_regimes):
            start = boundaries[i]
            end = boundaries[i + 1]
            h_trajectory[start:end] = h
        
        return h_trajectory
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get regime switching metadata."""
        base = super()._get_metadata()
        base.update({
            'h_regimes': self.h_regimes,
            'change_points': self.change_points,
            'n_regimes': len(self.h_regimes)
        })
        return base


class ContinuousDriftProcess(NonstationaryProcessBase):
    """
    Generate time series with smoothly varying H(t).
    
    Supports linear, sinusoidal, logistic, and exponential drift patterns.
    Useful for testing estimator behavior under gradual nonstationarity.
    
    Example
    -------
    >>> gen = ContinuousDriftProcess(h_start=0.3, h_end=0.8, drift_type='linear')
    >>> result = gen.generate(1000)
    >>> # H increases linearly from 0.3 to 0.8
    """
    
    def __init__(
        self,
        h_start: float = 0.3,
        h_end: float = 0.8,
        drift_type: Union[str, DriftType] = DriftType.LINEAR,
        drift_params: Optional[Dict[str, Any]] = None,
        sigma: float = 1.0,
        random_state: Optional[int] = None
    ):
        """
        Initialize continuous drift process.
        
        Parameters
        ----------
        h_start : float
            Initial H value
        h_end : float
            Final H value
        drift_type : str or DriftType
            Type of drift: 'linear', 'sinusoidal', 'logistic', 'exponential'
        drift_params : dict, optional
            Additional parameters for drift function:
            - sinusoidal: {'frequency': float, 'phase': float}
            - logistic: {'steepness': float, 'midpoint': float}
            - exponential: {'rate': float}
        sigma : float
            Standard deviation scaling
        random_state : int, optional
            Random seed
        """
        super().__init__(sigma, random_state)
        
        self.h_start = np.clip(h_start, 0.01, 0.99)
        self.h_end = np.clip(h_end, 0.01, 0.99)
        
        if isinstance(drift_type, str):
            drift_type = DriftType(drift_type.lower())
        self.drift_type = drift_type
        
        self.drift_params = drift_params or {}
    
    def _get_h_trajectory(self, length: int) -> np.ndarray:
        """Get smooth H trajectory based on drift type."""
        t = np.linspace(0, 1, length)
        
        if self.drift_type == DriftType.LINEAR:
            h_trajectory = self.h_start + (self.h_end - self.h_start) * t
        
        elif self.drift_type == DriftType.SINUSOIDAL:
            freq = self.drift_params.get('frequency', 1.0)
            phase = self.drift_params.get('phase', 0.0)
            h_mean = (self.h_start + self.h_end) / 2
            h_amp = (self.h_end - self.h_start) / 2
            h_trajectory = h_mean + h_amp * np.sin(2 * np.pi * freq * t + phase)
        
        elif self.drift_type == DriftType.LOGISTIC:
            steepness = self.drift_params.get('steepness', 10.0)
            midpoint = self.drift_params.get('midpoint', 0.5)
            logistic = 1 / (1 + np.exp(-steepness * (t - midpoint)))
            h_trajectory = self.h_start + (self.h_end - self.h_start) * logistic
        
        elif self.drift_type == DriftType.EXPONENTIAL:
            rate = self.drift_params.get('rate', 2.0)
            exp_curve = (np.exp(rate * t) - 1) / (np.exp(rate) - 1)
            h_trajectory = self.h_start + (self.h_end - self.h_start) * exp_curve
        
        else:
            raise ValueError(f"Unknown drift type: {self.drift_type}")
        
        return np.clip(h_trajectory, 0.01, 0.99)
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get continuous drift metadata."""
        base = super()._get_metadata()
        base.update({
            'h_start': self.h_start,
            'h_end': self.h_end,
            'drift_type': self.drift_type.value,
            'drift_params': self.drift_params
        })
        return base


class StructuralBreakProcess(NonstationaryProcessBase):
    """
    Generate time series with structural breaks (abrupt level/variance shifts).
    
    Combines H regime switching with additional level shifts and variance changes
    to create more realistic nonstationary scenarios.
    
    Example
    -------
    >>> gen = StructuralBreakProcess(
    ...     h_before=0.7, h_after=0.4, 
    ...     break_position=0.5, break_severity=0.3
    ... )
    >>> result = gen.generate(1000)
    """
    
    def __init__(
        self,
        h_before: float = 0.7,
        h_after: float = 0.4,
        break_position: float = 0.5,
        break_severity: float = 0.0,
        variance_change: float = 1.0,
        n_breaks: int = 1,
        sigma: float = 1.0,
        random_state: Optional[int] = None
    ):
        """
        Initialize structural break process.
        
        Parameters
        ----------
        h_before : float
            H value before break(s)
        h_after : float
            H value after break(s)
        break_position : float
            Relative position of break in (0, 1). For multiple breaks,
            positions are evenly distributed.
        break_severity : float
            Magnitude of level shift at break (0 = no shift)
        variance_change : float
            Multiplicative factor for variance after break (1 = no change)
        n_breaks : int
            Number of structural breaks
        sigma : float
            Standard deviation scaling
        random_state : int, optional
            Random seed
        """
        super().__init__(sigma, random_state)
        
        self.h_before = np.clip(h_before, 0.01, 0.99)
        self.h_after = np.clip(h_after, 0.01, 0.99)
        self.break_position = break_position
        self.break_severity = break_severity
        self.variance_change = variance_change
        self.n_breaks = n_breaks
        
        # Generate break positions
        if n_breaks == 1:
            self.break_positions = [break_position]
        else:
            self.break_positions = [
                (i + 1) / (n_breaks + 1) for i in range(n_breaks)
            ]
    
    def _get_h_trajectory(self, length: int) -> np.ndarray:
        """Get H trajectory with alternating regimes."""
        h_trajectory = np.full(length, self.h_before)
        
        current_h = self.h_before
        for i, bp in enumerate(self.break_positions):
            idx = int(bp * length)
            # Alternate between h_after and h_before
            new_h = self.h_after if (i % 2 == 0) else self.h_before
            h_trajectory[idx:] = new_h
            current_h = new_h
        
        return h_trajectory
    
    def generate(
        self, 
        length: int, 
        seed: Optional[int] = None,
        segment_length: int = 256
    ) -> Dict[str, Any]:
        """Generate signal with structural breaks including level shifts."""
        result = super().generate(length, seed, segment_length)
        
        # Apply level shifts and variance changes
        signal = result['signal']
        
        for i, bp in enumerate(self.break_positions):
            idx = int(bp * length)
            
            # Apply level shift
            if self.break_severity != 0:
                shift_direction = 1 if (i % 2 == 0) else -1
                signal[idx:] += shift_direction * self.break_severity * np.std(signal[:idx])
            
            # Apply variance change
            if self.variance_change != 1.0:
                var_factor = self.variance_change if (i % 2 == 0) else (1 / self.variance_change)
                signal[idx:] *= np.sqrt(var_factor)
        
        result['signal'] = signal
        result['break_indices'] = [int(bp * length) for bp in self.break_positions]
        
        return result
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get structural break metadata."""
        base = super()._get_metadata()
        base.update({
            'h_before': self.h_before,
            'h_after': self.h_after,
            'break_positions': self.break_positions,
            'break_severity': self.break_severity,
            'variance_change': self.variance_change,
            'n_breaks': self.n_breaks
        })
        return base


class EnsembleTimeAverageProcess(NonstationaryProcessBase):
    """
    Generate data for testing ergodicity violation.
    
    In equilibrium systems, ensemble averages equal time averages. This process
    generates data where this equivalence is broken, which is characteristic of
    aging/nonequilibrium systems where classical estimators fail.
    
    Example
    -------
    >>> gen = EnsembleTimeAverageProcess(H=0.7, aging_exponent=0.5)
    >>> result = gen.generate(1000)
    >>> # Signal exhibits aging behavior
    """
    
    def __init__(
        self,
        H: float = 0.7,
        aging_exponent: float = 0.5,
        aging_type: str = 'power_law',
        sigma: float = 1.0,
        random_state: Optional[int] = None
    ):
        """
        Initialize ensemble-time average process.
        
        Parameters
        ----------
        H : float
            Base Hurst parameter
        aging_exponent : float
            Exponent controlling aging rate (0 = no aging, 1 = strong aging)
        aging_type : str
            Type of aging: 'power_law', 'logarithmic', 'exponential'
        sigma : float
            Standard deviation scaling
        random_state : int, optional
            Random seed
        """
        super().__init__(sigma, random_state)
        
        self.H = np.clip(H, 0.01, 0.99)
        self.aging_exponent = aging_exponent
        self.aging_type = aging_type
    
    def _get_h_trajectory(self, length: int) -> np.ndarray:
        """Get H trajectory with aging-induced drift."""
        t = np.arange(1, length + 1)  # Avoid division by zero
        
        if self.aging_type == 'power_law':
            # H drifts as t^(-aging_exponent)
            drift = (t / length) ** (-self.aging_exponent)
            drift = (drift - drift.min()) / (drift.max() - drift.min() + 1e-10)
            h_trajectory = self.H + 0.2 * self.aging_exponent * (drift - 0.5)
        
        elif self.aging_type == 'logarithmic':
            # H drifts logarithmically
            drift = np.log(t) / np.log(length)
            h_trajectory = self.H + 0.2 * self.aging_exponent * (drift - 0.5)
        
        elif self.aging_type == 'exponential':
            # H drifts exponentially towards boundary
            drift = 1 - np.exp(-self.aging_exponent * t / length)
            target_H = 0.9 if self.H > 0.5 else 0.1
            h_trajectory = self.H + (target_H - self.H) * drift
        
        else:
            raise ValueError(f"Unknown aging type: {self.aging_type}")
        
        return np.clip(h_trajectory, 0.01, 0.99)
    
    def generate_ensemble(
        self,
        n_realizations: int,
        length: int,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate ensemble of realizations for ergodicity testing.
        
        Parameters
        ----------
        n_realizations : int
            Number of realizations
        length : int
            Length of each realization
        seed : int, optional
            Random seed
            
        Returns
        -------
        dict
            Dictionary containing:
            - 'ensemble': Array of shape (n_realizations, length)
            - 'ensemble_mean': Mean across realizations at each time
            - 'time_mean': Mean across time for each realization
            - 'h_trajectory': True H trajectory
        """
        local_rng = np.random.default_rng(seed) if seed is not None else self.rng
        
        ensemble = np.zeros((n_realizations, length))
        
        for i in range(n_realizations):
            result = self.generate(length, seed=local_rng.integers(0, 2**32))
            ensemble[i] = result['signal']
        
        return {
            'ensemble': ensemble,
            'ensemble_mean': np.mean(ensemble, axis=0),
            'time_mean': np.mean(ensemble, axis=1),
            'h_trajectory': self._get_h_trajectory(length),
            'metadata': self._get_metadata()
        }
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get ergodicity testing metadata."""
        base = super()._get_metadata()
        base.update({
            'base_H': self.H,
            'aging_exponent': self.aging_exponent,
            'aging_type': self.aging_type,
            'ergodic': False
        })
        return base


# Convenience factory function
def create_nonstationary_process(
    process_type: str,
    **kwargs
) -> NonstationaryProcessBase:
    """
    Factory function to create nonstationary processes.
    
    Parameters
    ----------
    process_type : str
        Type of process: 'regime_switching', 'continuous_drift', 
        'structural_break', 'ensemble_time_average'
    **kwargs
        Process-specific parameters
        
    Returns
    -------
    NonstationaryProcessBase
        Configured process instance
    """
    process_map = {
        'regime_switching': RegimeSwitchingProcess,
        'continuous_drift': ContinuousDriftProcess,
        'structural_break': StructuralBreakProcess,
        'ensemble_time_average': EnsembleTimeAverageProcess
    }
    
    process_type = process_type.lower().replace(' ', '_').replace('-', '_')
    
    if process_type not in process_map:
        raise ValueError(
            f"Unknown process type '{process_type}'. "
            f"Available: {list(process_map.keys())}"
        )
    
    return process_map[process_type](**kwargs)
