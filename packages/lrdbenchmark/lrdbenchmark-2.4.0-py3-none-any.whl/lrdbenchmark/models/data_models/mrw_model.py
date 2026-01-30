"""
Multifractal Random Walk (MRW) model implementation.

This module provides a class for generating multifractal random walk time series
using log-normal volatility cascades.
"""

import numpy as np
from typing import Optional, Dict, Any
import sys
import os

from .base_model import BaseModel


class MultifractalRandomWalk(BaseModel):
    """
    Multifractal Random Walk (MRW) model.

    MRW is a multifractal process that exhibits scale-invariant properties
    and is characterized by a log-normal volatility cascade. It is defined
    by the Hurst parameter H and the intermittency parameter λ.

    Parameters
    ----------
    H : float
        Hurst parameter (0 < H < 1)
    lambda_param : float
        Intermittency parameter (λ > 0)
    sigma : float, optional
        Base volatility (default: 1.0)
    method : str, optional
        Generation method (default: 'cascade')
    """

    def __init__(
        self, H: float, lambda_param: float, sigma: float = 1.0, method: str = "cascade"
    ):
        """
        Initialize the Multifractal Random Walk model.

        Parameters
        ----------
        H : float
            Hurst parameter (0 < H < 1)
        lambda_param : float
            Intermittency parameter (λ > 0)
        sigma : float, optional
            Base volatility (default: 1.0)
        method : str, optional
            Generation method (default: 'cascade')
        """
        super().__init__(H=H, lambda_param=lambda_param, sigma=sigma, method=method)
        self._current_rng: Optional[np.random.Generator] = None

    def _validate_parameters(self) -> None:
        """Validate model parameters."""
        H = self.parameters["H"]
        lambda_param = self.parameters["lambda_param"]
        sigma = self.parameters["sigma"]
        method = self.parameters["method"]

        if not 0 < H < 1:
            raise ValueError("Hurst parameter H must be in (0, 1)")

        if lambda_param <= 0:
            raise ValueError("Intermittency parameter λ must be positive")

        if sigma <= 0:
            raise ValueError("Base volatility sigma must be positive")

        valid_methods = ["cascade", "direct"]
        if method not in valid_methods:
            raise ValueError(f"Method must be one of {valid_methods}")

    def generate(
        self,
        length: Optional[int] = None,
        seed: Optional[int] = None,
        n: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """
        Generate multifractal random walk.

        Parameters
        ----------
        length : int, optional
            Length of the time series to generate
        seed : int, optional
            Random seed for reproducibility
        n : int, optional
            Alternate parameter name for length (for backward compatibility)

        Returns
        -------
        np.ndarray
            Generated MRW time series

        Notes
        -----
        Either 'length' or 'n' must be provided. If both are provided, 'length' takes precedence.
        """
        # Handle backward compatibility: accept both 'length' and 'n'
        if length is None and n is None:
            raise ValueError("Either 'length' or 'n' must be provided")
        data_length = length if length is not None else n
        self._current_rng = self._resolve_generator(seed, rng)

        H = self.parameters["H"]
        lambda_param = self.parameters["lambda_param"]
        sigma = self.parameters["sigma"]
        method = self.parameters["method"]

        if method == "cascade":
            return self._cascade_method(data_length, H, lambda_param, sigma)
        else:
            return self._direct_method(data_length, H, lambda_param, sigma)

    def _cascade_method(
        self, length: int, H: float, lambda_param: float, sigma: float
    ) -> np.ndarray:
        """
        Generate MRW using volatility cascade method.

        This method constructs a log-normal volatility cascade and applies
        it to a fractional Brownian motion.
        """
        # Generate the volatility cascade
        omega = self._generate_volatility_cascade(length, lambda_param)

        # Generate fractional Brownian motion
        fbm = self._generate_fbm(length, H, sigma)

        # Combine to get MRW
        mrw = fbm * np.exp(omega)

        return mrw

    def _generate_volatility_cascade(self, length: int, lambda_param: float) -> np.ndarray:
        """
        Generate log-normal volatility cascade.

        Parameters
        ----------
        length : int
            Length of the time series
        lambda_param : float
            Intermittency parameter

        Returns
        -------
        lengthp.ndarray
            Log-volatility cascade
        """
        # Initialize omega with zeros
        omega = np.zeros(length)

        # Generate the cascade at different scales
        scale = length
        while scale > 1:
            # Generate Gaussian noise at current scale
            noise = self._rng().normal(0, lambda_param, scale)

            # Interpolate to full length
            indices = np.linspace(0, length - 1, scale, dtype=int)
            omega_interp = np.interp(np.arange(length), indices, noise)

            # Add to the cascade
            omega += omega_interp

            # Move to next scale
            scale = scale // 2

        return omega

    def expected_hurst(self) -> float:
        """Return the configured large-scale Hurst exponent."""
        return float(self.parameters["H"])

    def _generate_fbm(self, length: int, H: float, sigma: float) -> np.ndarray:
        """
        Generate fractional Brownian motion using circulant embedding.

        Parameters
        ----------
        length : int
            Length of the time series
        H : float
            Hurst parameter
        sigma : float
            Standard deviation

        Returns
        -------
        lengthp.ndarray
            Fractional Brownian motion
        """
        # Calculate autocovariance function
        lags = np.arange(length)
        autocov = (
            sigma**2
            * 0.5
            * (
                (lags + 1) ** (2 * H)
                - 2 * lags ** (2 * H)
                + np.maximum(0, lags - 1) ** (2 * H)
            )
        )

        # Construct circulant matrix
        circulant_row = np.concatenate([autocov, autocov[1 : length - 1][::-1]])

        # Eigenvalue decomposition
        eigenvalues = np.fft.fft(circulant_row)
        eigenvalues = np.maximum(eigenvalues.real, 0)

        # Generate complex Gaussian noise
        noise = self._rng().normal(0, 1, len(eigenvalues)) + 1j * self._rng().normal(
            0, 1, len(eigenvalues)
        )
        noise = noise / np.sqrt(2)

        # Apply spectral filter
        filtered_noise = noise * np.sqrt(eigenvalues)

        # Inverse FFT
        fbm = np.real(np.fft.ifft(filtered_noise))[:length]

        return fbm

    def _direct_method(
        self, length: int, H: float, lambda_param: float, sigma: float
    ) -> np.ndarray:
        """
        Generate MRW using direct method.

        This method directly generates the MRW process using the
        multifractal formalism.
        """
        # Generate the increments directly
        increments = np.zeros(length)

        # Generate volatility cascade
        omega = self._generate_volatility_cascade(length, lambda_param)

        # Generate Gaussian noise
        noise = self._rng().normal(0, 1, length)

        # Combine to get increments
        increments = noise * np.exp(omega) * sigma

        # Cumsum to get the process
        mrw = np.cumsum(increments)

        return mrw

    def _rng(self) -> np.random.Generator:
        if self._current_rng is None:
            self._current_rng = np.random.default_rng()
        return self._current_rng

    def get_theoretical_properties(self) -> Dict[str, Any]:
        """
        Get theoretical properties of MRW.

        Returns
        -------
        dict
            Dictionary containing theoretical properties
        """
        H = self.parameters["H"]
        lambda_param = self.parameters["lambda_param"]
        sigma = self.parameters["sigma"]

        return {
            "hurst_parameter": H,
            "intermittency_parameter": lambda_param,
            "base_volatility": sigma,
            "multifractal": True,
            "scale_invariant": True,
            "long_range_dependence": H > 0.5,
            "volatility_clustering": True,
        }

    def get_increments(self, mrw: np.ndarray) -> np.ndarray:
        """
        Get the increments of MRW.

        Parameters
        ----------
        mrw : np.ndarray
            Multifractal random walk time series

        Returns
        -------
        lengthp.ndarray
            Increments
        """
        return np.diff(mrw)
