
import numpy as np
from scipy.fft import fft, ifft
from typing import Optional, Dict, Any
from .base_model import BaseModel

class FractionalGaussianNoise(BaseModel):
    """
    Fractional Gaussian Noise (fGn) generator using the Davies-Harte method.
    
    Generates exact fGn with Hurst parameter H using the Davies-Harte algorithm,
    which exploits the property that the circulant matrix of covariances can be
    diagonalized by the Fourier transform.
    """
    def __init__(self, H: float = 0.7, sigma: float = 1.0, **kwargs):
        """
        Initialize the fGn model.
        
        Parameters
        ----------
        H : float
            Hurst parameter (0 < H < 1)
        sigma : float
            Standard deviation of the process
        """
        super().__init__(H=H, sigma=sigma, **kwargs)

    def _validate_parameters(self) -> None:
        """Validate model parameters."""
        H = self.parameters.get('H')
        sigma = self.parameters.get('sigma')
        
        if H is not None and not (0 < H < 1):
            raise ValueError("Hurst parameter H must be in (0, 1)")
        if sigma is not None and sigma <= 0:
            raise ValueError("Sigma must be positive")

    def generate(
        self, 
        length: Optional[int] = None, 
        seed: Optional[int] = None,
        n: Optional[int] = None,
        rng: Optional[np.random.Generator] = None
    ) -> np.ndarray:
        """
        Generate fGn time series.
        """
        # Handle backward compatibility: accept both 'length' and 'n'
        if length is None and n is None:
            raise ValueError("Either 'length' or 'n' must be provided")
        data_length = length if length is not None else n
        
        # Resolve generator
        local_rng = self._resolve_generator(seed, rng)
        
        return self._davies_harte(data_length, local_rng)

    def _davies_harte(self, N: int, rng: np.random.Generator) -> np.ndarray:
        """
        Internal Davies-Harte implementation.
        """
        H = self.parameters['H']
        sigma = self.parameters['sigma']
        
        # 1. Calculate autocovariance function for extended length
        # We use M = 2N
        k_extended = np.arange(N + 1)
        # Autocovariance of fGn: gamma(k) = (sigma^2 / 2) * (|k+1|^2H - 2|k|^2H + |k-1|^2H)
        gamma_ext = (sigma**2 / 2.0) * (
            np.abs(k_extended + 1)**(2 * H) - 
            2 * np.abs(k_extended)**(2 * H) + 
            np.abs(k_extended - 1)**(2 * H)
        )
        
        # 2. Construct the first row of the circulant matrix C
        # Circulant first row: g0, g1, ..., g(N-1), g(N), g(N-1), ..., g1
        first_row = np.concatenate([gamma_ext[:N], [gamma_ext[N]], gamma_ext[1:N][::-1]])
        
        # 3. Compute eigenvalues of C
        eigenvals = fft(first_row).real
        
        # Check for negative eigenvalues (numerical instability or invalid H)
        if np.any(eigenvals < 0):
            # If extremely small negative (numerical noise), clip to 0
            if np.min(eigenvals) > -1e-9:
                eigenvals[eigenvals < 0] = 0
            else:
                # This should technically not happen for valid fGn, but good to handle
                eigenvals[eigenvals < 0] = 0
                
        # 4. Generate complex Gaussian noise
        # V = (randn + j * randn)
        V = rng.standard_normal(2 * N) + 1j * rng.standard_normal(2 * N)
        
        # 5. Compute IFFT
        # We multiply by sqrt(eigenvals) as part of the Cholesky-like decomposition via FFT
        Y = ifft(np.sqrt(eigenvals) * V)
        
        # 6. Take real part and scale
        # The factor sqrt(2N) ensures the correct variance normalization from the FFT usage
        fgn = Y[:N].real * np.sqrt(2 * N)
        
        return fgn

    def get_theoretical_properties(self) -> Dict[str, Any]:
        """Get theoretical properties of fGn."""
        H = self.parameters.get('H', 0.7)
        sigma = self.parameters.get('sigma', 1.0)
        
        return {
            'hurst_parameter': H,
            'variance': sigma**2,
            'self_similarity_exponent': None, # fGn is not self-similar (fBm is)
            'long_range_dependence': H > 0.5,
            'stationary_increments': True,
            'gaussian': True,
            'stationary': True
        }
