#!/usr/bin/env python3
"""
Surrogate Data Generators for LRDBenchmark.

Provides methods for generating surrogate time series that preserve certain
statistical properties while destroying others. Used for hypothesis testing
of nonlinear dynamics and LRD properties.

Classes:
    - IAFFTSurrogate: Iterative Amplitude Adjusted Fourier Transform
    - PhaseRandomizedSurrogate: Phase randomization preserving power spectrum
    - ARSurrogatee: Autoregressive surrogates for linear null hypothesis
"""

import numpy as np
from typing import Dict, Any, Optional, List
from scipy.fft import fft, ifft


class IAFFTSurrogate:
    """
    Iterative Amplitude Adjusted Fourier Transform (IAAFT) surrogate generator.
    
    Generates surrogates that preserve both the power spectrum and the
    amplitude distribution of the original time series, while destroying
    any nonlinear temporal structure.
    
    Reference: Schreiber & Schmitz (1996)
    
    Example
    -------
    >>> gen = IAFFTSurrogate()
    >>> surrogate = gen.generate(original_data)
    """
    
    def __init__(
        self,
        max_iterations: int = 100,
        convergence_tol: float = 1e-6,
        random_state: Optional[int] = None
    ):
        """
        Initialize IAAFT surrogate generator.
        
        Parameters
        ----------
        max_iterations : int
            Maximum number of iterations
        convergence_tol : float
            Convergence tolerance for power spectrum matching
        random_state : int, optional
            Random seed
        """
        self.max_iterations = max_iterations
        self.convergence_tol = convergence_tol
        self.rng = np.random.default_rng(random_state)
    
    def generate(
        self,
        data: np.ndarray,
        n_surrogates: int = 1,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate IAAFT surrogates.
        
        Parameters
        ----------
        data : np.ndarray
            Original time series
        n_surrogates : int
            Number of surrogates to generate
        seed : int, optional
            Random seed
        
        Returns
        -------
        dict
            Dictionary with 'surrogates' array and 'metadata'
        """
        local_rng = np.random.default_rng(seed) if seed is not None else self.rng
        
        data = np.asarray(data, dtype=np.float64)
        n = len(data)
        
        # Store original amplitudes and sorted values
        original_fft = fft(data)
        original_amplitudes = np.abs(original_fft)
        sorted_data = np.sort(data)
        
        surrogates = []
        convergence_info = []
        
        for _ in range(n_surrogates):
            # Initialize with shuffled data
            surrogate = local_rng.permutation(data.copy())
            
            prev_spectrum_error = np.inf
            converged = False
            iterations = 0
            
            for iteration in range(self.max_iterations):
                iterations = iteration + 1
                
                # Step 1: Match power spectrum
                surrogate_fft = fft(surrogate)
                surrogate_phases = np.angle(surrogate_fft)
                adjusted_fft = original_amplitudes * np.exp(1j * surrogate_phases)
                surrogate = np.real(ifft(adjusted_fft))
                
                # Step 2: Match amplitude distribution
                ranks = np.argsort(np.argsort(surrogate))
                surrogate = sorted_data[ranks]
                
                # Check convergence
                current_fft = fft(surrogate)
                spectrum_error = np.mean(np.abs(np.abs(current_fft) - original_amplitudes)**2)
                
                if abs(prev_spectrum_error - spectrum_error) < self.convergence_tol:
                    converged = True
                    break
                
                prev_spectrum_error = spectrum_error
            
            surrogates.append(surrogate)
            convergence_info.append({
                'iterations': iterations,
                'converged': converged,
                'final_error': float(spectrum_error)
            })
        
        surrogates = np.array(surrogates)
        if n_surrogates == 1:
            surrogates = surrogates[0]
        
        return {
            'surrogates': surrogates,
            'metadata': {
                'method': 'IAAFT',
                'n_surrogates': n_surrogates,
                'max_iterations': self.max_iterations,
                'convergence_info': convergence_info
            }
        }


class PhaseRandomizedSurrogate:
    """
    Phase randomization surrogate generator.
    
    Generates surrogates by randomizing the Fourier phases while
    preserving the power spectrum (amplitude). Destroys all temporal
    correlations except those captured by the power spectrum.
    
    Example
    -------
    >>> gen = PhaseRandomizedSurrogate()
    >>> surrogate = gen.generate(original_data)
    """
    
    def __init__(self, random_state: Optional[int] = None):
        """
        Initialize phase randomization generator.
        
        Parameters
        ----------
        random_state : int, optional
            Random seed
        """
        self.rng = np.random.default_rng(random_state)
    
    def generate(
        self,
        data: np.ndarray,
        n_surrogates: int = 1,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate phase-randomized surrogates.
        
        Parameters
        ----------
        data : np.ndarray
            Original time series
        n_surrogates : int
            Number of surrogates
        seed : int, optional
            Random seed
        
        Returns
        -------
        dict
            Dictionary with 'surrogates' and 'metadata'
        """
        local_rng = np.random.default_rng(seed) if seed is not None else self.rng
        
        data = np.asarray(data, dtype=np.float64)
        n = len(data)
        
        # Compute FFT
        data_fft = fft(data)
        amplitudes = np.abs(data_fft)
        
        surrogates = []
        
        for _ in range(n_surrogates):
            # Generate random phases
            random_phases = local_rng.uniform(0, 2 * np.pi, n)
            
            # Ensure conjugate symmetry for real output
            if n % 2 == 0:
                random_phases[n//2] = 0
            random_phases[1:n//2] = random_phases[n//2+1:][::-1] * -1 if n % 2 == 0 else \
                                     random_phases[(n+1)//2:][::-1] * -1
            random_phases[0] = 0  # DC component has zero phase
            
            # Construct surrogate FFT
            surrogate_fft = amplitudes * np.exp(1j * random_phases)
            surrogate = np.real(ifft(surrogate_fft))
            surrogates.append(surrogate)
        
        surrogates = np.array(surrogates)
        if n_surrogates == 1:
            surrogates = surrogates[0]
        
        return {
            'surrogates': surrogates,
            'metadata': {
                'method': 'PhaseRandomization',
                'n_surrogates': n_surrogates,
                'preserves_spectrum': True,
                'destroys_nonlinearity': True
            }
        }


class ARSurrogate:
    """
    Autoregressive (AR) surrogate generator.
    
    Fits an AR model to the original data and generates surrogates
    from the fitted model. Provides a linear null hypothesis.
    
    Example
    -------
    >>> gen = ARSurrogate(order=10)
    >>> surrogate = gen.generate(original_data)
    """
    
    def __init__(
        self,
        order: int = 10,
        random_state: Optional[int] = None
    ):
        """
        Initialize AR surrogate generator.
        
        Parameters
        ----------
        order : int
            AR model order
        random_state : int, optional
            Random seed
        """
        self.order = order
        self.rng = np.random.default_rng(random_state)
    
    def _fit_ar(self, data: np.ndarray) -> tuple:
        """Fit AR model using Yule-Walker equations."""
        n = len(data)
        p = self.order
        
        # Demean data
        mean = np.mean(data)
        x = data - mean
        
        # Compute autocorrelations
        r = np.zeros(p + 1)
        for k in range(p + 1):
            r[k] = np.dot(x[:n-k], x[k:]) / n
        
        # Build Toeplitz matrix
        R = np.zeros((p, p))
        for i in range(p):
            for j in range(p):
                R[i, j] = r[abs(i - j)]
        
        # Solve Yule-Walker equations
        try:
            coeffs = np.linalg.solve(R, r[1:p+1])
        except np.linalg.LinAlgError:
            coeffs = np.zeros(p)
        
        # Compute innovation variance
        sigma2 = r[0] - np.dot(coeffs, r[1:p+1])
        sigma2 = max(sigma2, 1e-10)
        
        return coeffs, np.sqrt(sigma2), mean
    
    def generate(
        self,
        data: np.ndarray,
        n_surrogates: int = 1,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate AR surrogates.
        
        Parameters
        ----------
        data : np.ndarray
            Original time series
        n_surrogates : int
            Number of surrogates
        seed : int, optional
            Random seed
        
        Returns
        -------
        dict
            Dictionary with 'surrogates' and 'metadata'
        """
        local_rng = np.random.default_rng(seed) if seed is not None else self.rng
        
        data = np.asarray(data, dtype=np.float64)
        n = len(data)
        p = self.order
        
        # Fit AR model
        coeffs, sigma, mean = self._fit_ar(data)
        
        surrogates = []
        
        for _ in range(n_surrogates):
            # Initialize with noise
            surrogate = np.zeros(n + p)
            surrogate[:p] = local_rng.normal(0, sigma, p)
            
            # Generate AR process
            innovations = local_rng.normal(0, sigma, n)
            for t in range(p, n + p):
                surrogate[t] = np.dot(coeffs, surrogate[t-p:t][::-1]) + innovations[t - p]
            
            # Trim and add mean
            surrogate = surrogate[p:] + mean
            surrogates.append(surrogate)
        
        surrogates = np.array(surrogates)
        if n_surrogates == 1:
            surrogates = surrogates[0]
        
        return {
            'surrogates': surrogates,
            'ar_coefficients': coeffs.tolist(),
            'innovation_std': float(sigma),
            'metadata': {
                'method': 'AR',
                'order': self.order,
                'n_surrogates': n_surrogates,
                'linear_null': True
            }
        }


# Convenience factory function
def create_surrogate_generator(
    method: str,
    **kwargs
) -> Any:
    """
    Factory function for surrogate generators.
    
    Parameters
    ----------
    method : str
        'iaaft', 'phase_randomization', or 'ar'
    **kwargs
        Method-specific parameters
    """
    method_map = {
        'iaaft': IAFFTSurrogate,
        'iaft': IAFFTSurrogate,
        'phase_randomization': PhaseRandomizedSurrogate,
        'phase': PhaseRandomizedSurrogate,
        'ar': ARSurrogate,
        'autoregressive': ARSurrogate
    }
    
    method = method.lower().replace(' ', '_').replace('-', '_')
    
    if method not in method_map:
        raise ValueError(
            f"Unknown method '{method}'. "
            f"Available: iaaft, phase_randomization, ar"
        )
    
    return method_map[method](**kwargs)
