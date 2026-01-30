
import numpy as np
from typing import Optional, Dict, Any, Union
from .base_model import BaseModel
from .fgn_model import FractionalGaussianNoise

class FractionalBrownianMotion(BaseModel):
    """
    Fractional Brownian Motion (fBm) generator.
    
    Generates fBm by cumulatively summing fGn increments.
    """
    def __init__(self, H: float = 0.7, sigma: float = 1.0, **kwargs):
        """
        Initialize the fBm model.
        
        Parameters
        ----------
        H : float
            Hurst parameter (0 < H < 1)
        sigma : float
            Standard deviation of the increments (fGn)
        """
        super().__init__(H=H, sigma=sigma, **kwargs)
        self.fgn = FractionalGaussianNoise(H=H, sigma=sigma, **kwargs)

    def _validate_parameters(self) -> None:
        """Validate model parameters."""
        H = self.parameters.get('H')
        sigma = self.parameters.get('sigma')
        
        if H is not None and not (0 < H < 1):
            raise ValueError("Hurst parameter H must be in (0, 1)")
        if sigma is not None and sigma <= 0:
            raise ValueError("Sigma must be positive")
            
        method = self.parameters.get('method')
        valid_methods = ['davies_harte', 'cholesky', 'circulant']
        if method is not None and method not in valid_methods:
            raise ValueError(f"Method must be one of {valid_methods}")

    def generate(
        self, 
        length: Optional[int] = None, 
        seed: Optional[int] = None,
        n: Optional[int] = None,
        rng: Optional[np.random.Generator] = None
    ) -> np.ndarray:
        """
        Generate fBm time series.
        """
        # Handle backward compatibility: accept both 'length' and 'n'
        if length is None and n is None:
            raise ValueError("Either 'length' or 'n' must be provided")
        data_length = length if length is not None else n
        
        # Resolve generator
        local_rng = self._resolve_generator(seed, rng)
        
        # Generate fGn increments
        # We pass the resolved rng to fgn
        noise = self.fgn.generate(length=data_length, rng=local_rng)
        
        # Cumulate to get fBm. Start from 0? Usually fBm(0) = 0.
        # np.cumsum starts from first element. 
        # Standard fBm definition: B_H(0) = 0.
        # If we just cumsum noise, we get x[0], x[0]+x[1], ...
        # Usually it's better to verify if users expect B_H(0) explicitly prepended, 
        # but usually generate(N) returns N points. 
        # The common convention for discrete fBm is just cumsum of fGn.
        fbm = np.cumsum(noise)
        
        return fbm

    def get_theoretical_properties(self) -> Dict[str, Any]:
        """Get theoretical properties of fBm."""
        H = self.parameters.get('H', 0.7)
        sigma = self.parameters.get('sigma', 1.0)
        
        return {
            'hurst_parameter': H,
            'variance': sigma**2,  # Variance of increments
            'self_similarity_exponent': H,
            'long_range_dependence': H > 0.5,
            'stationary_increments': True,
            'gaussian': True,
            'stationary': False # fBm itself is non-stationary
        }

    def get_increments(self, data: np.ndarray) -> np.ndarray:
        """Get increments (fGn)."""
        return np.diff(data)
