"""
Base model class for all stochastic processes.

This module provides the abstract base class that all stochastic models
should inherit from, ensuring consistent interface and functionality.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
import numpy as np


class BaseModel(ABC):
    """
    Abstract base class for all stochastic models.

    This class defines the interface that all stochastic models must implement,
    including methods for parameter validation, data generation, and model
    information retrieval.
    """

    def __init__(self, **kwargs):
        """
        Initialize the base model.

        Parameters
        ----------
        **kwargs : dict
            Model-specific parameters
        """
        self.parameters = kwargs
        self._validate_parameters()

    @abstractmethod
    def _validate_parameters(self) -> None:
        """
        Validate model parameters.

        This method should be implemented by each model to ensure
        that the provided parameters are valid for the specific model.
        """
        pass

    @abstractmethod
    def generate(
        self,
        length: Optional[int] = None,
        seed: Optional[int] = None,
        n: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """
        Generate synthetic data from the model.

        Parameters
        ----------
        length : int, optional
            Length of the time series to generate (preferred parameter name)
        seed : int, optional
            Random seed for reproducibility
        n : int, optional
            Alternate parameter name for length (for backward compatibility)
        rng : numpy.random.Generator, optional
            Pre-configured generator to use.  When provided it takes precedence
            over ``seed`` and is used directly to drive the simulation.

        Returns
        -------
        np.ndarray
            Generated time series

        Notes
        -----
        Either 'length' or 'n' must be provided. If both are provided, 'length' takes precedence.
        """
        pass
    
    def _analyze_convergence(self, data: np.ndarray, window_size: int = 500) -> int:
        """
        Analyze convergence of statistical properties to find optimal starting point.
        
        Parameters
        ----------
        data : np.ndarray
            Time series data to analyze
        window_size : int, default=500
            Size of sliding window for analysis
            
        Returns
        -------
        int
            Optimal starting point for analysis
        """
        n = len(data)
        if n < window_size * 2:
            return 0  # Not enough data for convergence analysis
        
        convergence_points = []
        
        # Test different starting points
        for start in range(0, n - window_size, max(1, window_size // 10)):
            window = data[start:start + window_size]
            
            # Calculate key statistics
            mean_val = np.mean(window)
            std_val = np.std(window)
            
            # Calculate autocorrelation at lag 1
            if len(window) > 1:
                acf_lag1 = np.corrcoef(window[:-1], window[1:])[0, 1]
            else:
                acf_lag1 = 0
                
            convergence_points.append({
                'start': start,
                'mean': mean_val,
                'std': std_val,
                'acf_lag1': acf_lag1
            })
        
        # Find point where statistics stabilize
        if len(convergence_points) < 3:
            return 0
            
        means = [p['mean'] for p in convergence_points]
        stds = [p['std'] for p in convergence_points]
        
        # Find where mean and std become relatively stable
        mean_stable = np.where(np.abs(np.diff(means)) < 0.01)[0]
        std_stable = np.where(np.abs(np.diff(stds)) < 0.01)[0]
        
        if len(mean_stable) > 0 and len(std_stable) > 0:
            optimal_start = max(mean_stable[0], std_stable[0]) * max(1, window_size // 10)
        else:
            # Fallback: use 20% of the data as burn-in
            optimal_start = max(0, n // 5)
            
        return min(optimal_start, n - window_size)
    
    def generate_converged(
        self,
        length: int,
        seed: Optional[int] = None,
        convergence_factor: float = 2.0,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """
        Generate converged data by generating extra data and discarding initial transients.
        
        Parameters
        ----------
        length : int
            Desired length of the final time series
        seed : int, optional
            Random seed for reproducibility
        convergence_factor : float, default=2.0
            Factor to multiply length by for convergence analysis
            
        Returns
        -------
        np.ndarray
            Generated time series of length n with converged behavior
        """
        local_rng = self._resolve_generator(seed, rng)

        # Generate extra data for convergence analysis
        extended_length = int(length * convergence_factor)
        extended_data = self.generate(extended_length, rng=local_rng)
        
        # Analyze convergence
        optimal_start = self._analyze_convergence(extended_data)
        
        # Return the converged portion
        converged_data = extended_data[optimal_start:optimal_start + length]
        
        # If we don't have enough data, pad with more generation
        if len(converged_data) < length:
            additional_length = length - len(converged_data)
            additional_data = self.generate(additional_length, rng=local_rng)
            converged_data = np.concatenate([converged_data, additional_data])
        
        return converged_data[:length]
    
    def generate_analysis_ready(
        self,
        length: int,
        seed: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """
        Generate data ready for analysis (converged by default).
        
        This is the recommended method for generating data for analysis,
        as it automatically handles convergence and returns settled data.
        
        Parameters
        ----------
        length : int
            Desired length of the final time series
        seed : int, optional
            Random seed for reproducibility
            
        Returns
        -------
        np.ndarray
            Generated time series of length n with converged behavior
        """
        return self.generate_converged(length, seed=seed, rng=rng)

    def expected_hurst(self) -> Optional[float]:
        """
        Return the theoretical Hurst exponent implied by the current parameters.

        By default this method looks for an ``H`` entry in ``self.parameters``.
        Models where \\( H \\) is derived from other parameters (e.g., ARFIMA with
        fractional differencing ``d``) should override this method accordingly.
        """
        return self.parameters.get("H")

    @staticmethod
    def _resolve_generator(
        seed: Optional[int], rng: Optional[np.random.Generator]
    ) -> np.random.Generator:
        """
        Choose or construct the generator to use for simulation.

        Priority: explicit ``rng`` argument > ``seed`` > fresh generator.
        """
        if rng is not None:
            return rng
        return np.random.default_rng(seed)
    
    def generate_batch(
        self,
        n_series: int,
        length: int,
        seed: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """
        Generate multiple time series from the model.

        Parameters
        ----------
        n_series : int
            Number of time series to generate
        length : int
            Length of each time series
        seed : int, optional
            Random seed for reproducibility

        Returns
        -------
        np.ndarray
            Generated time series array of shape (n_series, length)
        """
        batch = np.zeros((n_series, length))
        base_rng = self._resolve_generator(seed, rng)
        seeds = base_rng.integers(0, 2**63 - 1, size=n_series)
        for i, series_seed in enumerate(seeds):
            series_rng = np.random.default_rng(int(series_seed))
            batch[i] = self.generate(length, rng=series_rng)
        
        return batch
    
    def generate_streaming(
        self,
        length: int,
        chunk_size: int = 1000,
        seed: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
    ):
        """
        Generate data in streaming fashion for very large datasets.

        Parameters
        ----------
        length : int
            Total length of the time series to generate
        chunk_size : int, default=1000
            Size of each chunk
        seed : int, optional
            Random seed for reproducibility

        Yields
        ------
        np.ndarray
            Chunks of generated data
        """
        stream_rng = self._resolve_generator(seed, rng)
        for start in range(0, length, chunk_size):
            end = min(start + chunk_size, length)
            chunk_length = end - start
            yield self.generate(chunk_length, rng=stream_rng)

    @abstractmethod
    def get_theoretical_properties(self) -> Dict[str, Any]:
        """
        Get theoretical properties of the model.

        Returns
        -------
        dict
            Dictionary containing theoretical properties such as
            autocorrelation function, power spectral density, etc.
        """
        pass

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current model parameters.

        Returns
        -------
        dict
            Current model parameters
        """
        return self.parameters.copy()

    def set_parameters(self, **kwargs) -> None:
        """
        Set model parameters.

        Parameters
        ----------
        **kwargs : dict
            New parameter values
        """
        self.parameters.update(kwargs)
        self._validate_parameters()

    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}({self.parameters})"

    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return f"{self.__class__.__name__}(parameters={self.parameters})"
