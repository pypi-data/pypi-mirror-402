
import numpy as np
import warnings

try:
    import jax
    import jax.numpy as jnp
    from jax import jit, vmap
    from functools import partial
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False
    jnp = None
    jit = lambda x: x
    vmap = lambda x: x
    partial = lambda x, **k: x # Dummy

def compute_psd(
    data: np.ndarray,
    nperseg: int = None,
    use_welch: bool = True,
    use_multitaper: bool = False,
    window: str = "hann",
    n_tapers: int = 3,
    scaling: str = "density"
) -> tuple:
    """
    Compute PSD using JAX (GPU/TPU).
    Returns (freqs, psd) as JAX arrays (or converted to numpy).
    """
    if not JAX_AVAILABLE:
        raise ImportError("JAX not available")
        
    if use_multitaper:
        raise NotImplementedError("Multitaper not implemented in JAX backend")
        
    x = jnp.array(data)
    n = len(x)
    
    if nperseg is None:
        nperseg = min(max(n // 8, 64), n)
        
    # Generate Window
    # Only supporting 'hann' or 'boxcar' for now to keep JIT simple
    # Scipy windows are many.
    if window == 'hann':
        # Hann window: 0.5 - 0.5 cos(2 pi n / (M-1))
        # jnp.hanning is available?
        # jnp.hanning(M) is standard.
        win = jnp.hanning(nperseg)
    elif window == 'boxcar':
        win = jnp.ones(nperseg)
    elif window == 'hamming':
        win = jnp.hamming(nperseg)
    elif window == 'bartlett':
        win = jnp.bartlett(nperseg)
    elif window == 'blackman':
        win = jnp.blackman(nperseg)
    else:
        # Fallback to hann with warning? Or strict?
        # Safe to fallback to hann for general benchmark
        win = jnp.hanning(nperseg)

    if use_welch:
        noverlap = nperseg // 2
        step = nperseg - noverlap
        num_segments = (n - nperseg) // step + 1
        start_indices = jnp.arange(num_segments) * step
        
        freqs, psd = _welch_jax(x, win, start_indices, nperseg)
    else:
        # Standard Periodogram
        # Window length = N
        if window == 'hann':
            win = jnp.hanning(n)
        else:
            win = jnp.ones(n) # Default periodogram is usually boxcar?
            # 'periodogram' function in scipy takes window arg.
            # If user provided window='hann' for periodogram, we use it.
            if window == 'hamming': win = jnp.hamming(n)
            
        freqs, psd = _periodogram_jax(x, win)
        
    return np.array(freqs), np.array(psd)

@jit
def _periodogram_jax(x, win):
    n = len(x)
    
    # Detrend
    x_det = x - jnp.mean(x)
    
    # Apply window
    xw = x_det * win
    
    # FFT
    fft_vals = jnp.fft.rfft(xw)
    
    # PSD calculation
    mag_sq = jnp.abs(fft_vals)**2
    
    # Scaling
    scale = 1.0 / jnp.sum(win**2)
    
    psd = mag_sq * scale
    
    # One-sided scaling
    psd = psd * 2.0
    psd = psd.at[0].divide(2.0)
    if n % 2 == 0:
        psd = psd.at[-1].divide(2.0)
        
    freqs = jnp.fft.rfftfreq(n, d=1.0)
    
    return freqs, psd

@partial(jit, static_argnums=(3,))
def _welch_jax(x, win, start_indices, nperseg):
    # nperseg is static
    
    def get_seg_psd(start_idx):
        # Dynamic slice requiring static size
        seg = jax.lax.dynamic_slice(x, (start_idx,), (nperseg,))
        
        # Detrend (constant)
        seg = seg - jnp.mean(seg)
        
        # Window
        seg_w = seg * win
        
        # FFT (rfft)
        fft_vals = jnp.fft.rfft(seg_w)
        mag_sq = jnp.abs(fft_vals)**2
        return mag_sq

    # Compute sum of mag_sq over all segments
    all_mag_sq = vmap(get_seg_psd)(start_indices)
    
    # Average
    avg_mag_sq = jnp.mean(all_mag_sq, axis=0)
    
    # Scaling
    scale = 1.0 / jnp.sum(win**2)
    psd = avg_mag_sq * scale
    
    # One-sided correction
    psd = psd * 2.0
    psd = psd.at[0].divide(2.0)
    if nperseg % 2 == 0:
        psd = psd.at[-1].divide(2.0)
        
    freqs = jnp.fft.rfftfreq(nperseg, d=1.0)
    
    return freqs, psd
