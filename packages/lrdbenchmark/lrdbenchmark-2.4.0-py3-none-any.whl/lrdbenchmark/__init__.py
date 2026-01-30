"""
LRDBenchmark: Long-Range Dependence Benchmarking Toolkit

A comprehensive toolkit for benchmarking long-range dependence estimators
on synthetic and real-world time series data.
"""

import importlib
import logging
import os
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING
import warnings

from ._version import __version__


def _configure_cpu_defaults() -> None:
    """Apply safe CPU defaults unless explicitly disabled."""
    auto_cpu = os.environ.get("LRDBENCHMARK_AUTO_CPU", "1").lower()
    if auto_cpu in {"0", "false", "off"}:
        return

    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
    os.environ.setdefault("JAX_PLATFORM_NAME", "cpu")


_configure_cpu_defaults()

# Suppress JAX CUDA warnings and errors when using CPU-only mode
warnings.filterwarnings('ignore', category=UserWarning, module='jax')
warnings.filterwarnings('ignore', message='.*Jax plugin configuration error.*')
warnings.filterwarnings('ignore', message='.*CUDA_ERROR_NO_DEVICE.*')
warnings.filterwarnings('ignore', message='.*operation cuInit.*failed.*')

# Suppress JAX logging errors - set to CRITICAL to hide plugin initialization errors
logging.getLogger('jax._src.xla_bridge').setLevel(logging.CRITICAL)
logging.getLogger('jax_plugins').setLevel(logging.CRITICAL)

__author__ = "LRDBench Development Team"
__email__ = "lrdbench@example.com"

# Core data models
try:
    from .models.data_models import FBMModel, FGNModel, ARFIMAModel, MRWModel, AlphaStableModel
except ImportError as e:
    print(f"Warning: Could not import data models: {e}")
    FBMModel = None
    FGNModel = None
    ARFIMAModel = None
    MRWModel = None
    AlphaStableModel = None

# Classical estimators
# Classical estimators
try:
    # Temporal estimators
    from .analysis.temporal.rs_estimator import RSEstimator
    from .analysis.temporal.dfa_estimator import DFAEstimator
    from .analysis.temporal.dma_estimator import DMAEstimator
    from .analysis.temporal.higuchi_estimator import HiguchiEstimator
    
    # Spectral estimators
    from .analysis.spectral.whittle_estimator import WhittleEstimator
    from .analysis.spectral.gph_estimator import GPHEstimator
    from .analysis.spectral.periodogram_estimator import PeriodogramEstimator
    
    # Wavelet estimators
    from .analysis.wavelet.cwt_estimator import CWTEstimator
    from .analysis.wavelet.variance_estimator import WaveletVarianceEstimator
    from .analysis.wavelet.log_variance_estimator import WaveletLogVarianceEstimator
    from .analysis.wavelet.whittle_estimator import WaveletWhittleEstimator
    
    # Multifractal estimators
    from .analysis.multifractal.mfdfa_estimator import MFDFAEstimator
    from .analysis.multifractal.wavelet_leaders_estimator import MultifractalWaveletLeadersEstimator
    
except ImportError as e:
    print(f"Warning: Could not import classical estimators: {e}")
    # Temporal estimators
    RSEstimator = None
    DFAEstimator = None
    DMAEstimator = None
    HiguchiEstimator = None
    
    # Spectral estimators
    WhittleEstimator = None
    GPHEstimator = None
    PeriodogramEstimator = None
    
    # Wavelet estimators
    CWTEstimator = None
    WaveletVarianceEstimator = None
    WaveletLogVarianceEstimator = None
    WaveletWhittleEstimator = None
    
    # Multifractal estimators
    MFDFAEstimator = None
    MultifractalWaveletLeadersEstimator = None


# Main exports
__all__ = [
    # Data models
    "FBMModel",
    "FGNModel", 
    "ARFIMAModel",
    "MRWModel",
    "AlphaStableModel",
    # Classical estimators
    "RSEstimator",
    "DFAEstimator", 
    "DMAEstimator",
    "GHEEstimator",
    "HiguchiEstimator",
    "WhittleEstimator",
    "GPHEstimator",
    "PeriodogramEstimator",
    "CWTEstimator",
    "WaveletVarianceEstimator",
    "WaveletLogVarianceEstimator",
    "WaveletWhittleEstimator",
    "MFDFAEstimator",
    "MultifractalWaveletLeadersEstimator",
    # Machine Learning estimators
    "RandomForestEstimator",
    "SVREstimator",
    "GradientBoostingEstimator",
    "CNNEstimator",
    "LSTMEstimator",
    "GRUEstimator",
    "TransformerEstimator",
    # Neural Network Factory
    "NeuralNetworkFactory",
    # Benchmark system
    "ComprehensiveBenchmark",
    # GPU utilities
    "gpu_is_available",
    "get_device_info",
    # New Architecture
    "TimeSeriesGenerator",
    "ClassicalBenchmark",
    "MLBenchmark",
    "NNBenchmark",
    "clear_cache",
    "suggest_batch_size",
    "get_safe_device",
    "get_gpu_memory_info",
    "clear_gpu_cache",
    "monitor_gpu_memory",
    # Version info
    "__version__",
    "__author__",
    "__email__",
]

if TYPE_CHECKING:
    from .analysis.temporal.ghe_estimator import GHEEstimator as GHEEstimator
    from .analysis.machine_learning.random_forest_estimator_unified import RandomForestEstimator as RandomForestEstimator
    from .analysis.machine_learning.svr_estimator_unified import SVREstimator as SVREstimator
    from .analysis.machine_learning.gradient_boosting_estimator_unified import GradientBoostingEstimator as GradientBoostingEstimator
    from .analysis.machine_learning.cnn_estimator_unified import CNNEstimator as CNNEstimator
    from .analysis.machine_learning.lstm_estimator_unified import LSTMEstimator as LSTMEstimator
    from .analysis.machine_learning.gru_estimator_unified import GRUEstimator as GRUEstimator
    from .analysis.machine_learning.transformer_estimator_unified import TransformerEstimator as TransformerEstimator
    from .analysis.machine_learning.neural_network_factory import NeuralNetworkFactory as NeuralNetworkFactory
    from .analysis.benchmark.engine import ComprehensiveBenchmark as ComprehensiveBenchmark
    from .benchmarks import (
        ClassicalBenchmark, MLBenchmark, NNBenchmark
    )
    from .generation import TimeSeriesGenerator
    from .gpu import (
        is_available as gpu_is_available,
        get_device_info,
        clear_cache,
        suggest_batch_size,
        get_safe_device,
    )
    from .gpu.memory import get_gpu_memory_info, clear_gpu_cache, monitor_gpu_memory

_LOGGER = logging.getLogger(__name__)

_LAZY_ATTRS: Dict[str, str] = {
    # Machine learning estimators
    "RandomForestEstimator": "lrdbenchmark.analysis.machine_learning.random_forest_estimator_unified:RandomForestEstimator",
    "SVREstimator": "lrdbenchmark.analysis.machine_learning.svr_estimator_unified:SVREstimator",
    "GradientBoostingEstimator": "lrdbenchmark.analysis.machine_learning.gradient_boosting_estimator_unified:GradientBoostingEstimator",
    "CNNEstimator": "lrdbenchmark.analysis.machine_learning.cnn_estimator_unified:CNNEstimator",
    "LSTMEstimator": "lrdbenchmark.analysis.machine_learning.lstm_estimator_unified:LSTMEstimator",
    "GRUEstimator": "lrdbenchmark.analysis.machine_learning.gru_estimator_unified:GRUEstimator",
    "TransformerEstimator": "lrdbenchmark.analysis.machine_learning.transformer_estimator_unified:TransformerEstimator",
    # Factory & benchmarking
    "NeuralNetworkFactory": "lrdbenchmark.analysis.machine_learning.neural_network_factory:NeuralNetworkFactory",
    # Benchmarks
    "ComprehensiveBenchmark": "lrdbenchmark.benchmarks.comprehensive_benchmark:ComprehensiveBenchmark",
    "ClassicalBenchmark": "lrdbenchmark.benchmarks.classical_benchmark:ClassicalBenchmark",
    "MLBenchmark": "lrdbenchmark.benchmarks.ml_benchmark:MLBenchmark",
    "NNBenchmark": "lrdbenchmark.benchmarks.nn_benchmark:NNBenchmark",
    # Generation
    "TimeSeriesGenerator": "lrdbenchmark.generation.time_series_generator:TimeSeriesGenerator",
    # GPU utilities
    "gpu_is_available": "lrdbenchmark.gpu:is_available",
    "get_device_info": "lrdbenchmark.gpu:get_device_info",
    "clear_cache": "lrdbenchmark.gpu:clear_cache",
    "suggest_batch_size": "lrdbenchmark.gpu:suggest_batch_size",
    "get_safe_device": "lrdbenchmark.gpu:get_safe_device",
    "get_gpu_memory_info": "lrdbenchmark.gpu.memory:get_gpu_memory_info",
    "clear_gpu_cache": "lrdbenchmark.gpu.memory:clear_gpu_cache",
    "monitor_gpu_memory": "lrdbenchmark.gpu.memory:monitor_gpu_memory",
    "GHEEstimator": "lrdbenchmark.analysis.temporal.ghe_estimator:GHEEstimator",
}

_GPU_STUBS: Dict[str, Any] = {
    "gpu_is_available": lambda: False,
    "get_device_info": lambda: {"available": False},
    "clear_cache": lambda: None,
    "suggest_batch_size": lambda data_size, seq_len=None: min(32, data_size),
    "get_safe_device": lambda use_gpu=False: "cpu",
    "get_gpu_memory_info": lambda: {"torch_available": False, "jax_available": False},
    "clear_gpu_cache": lambda: None,
    "monitor_gpu_memory": lambda op_name="operation": None,
}


def __getattr__(name: str) -> Any:
    target = _LAZY_ATTRS.get(name)
    if not target:
        raise AttributeError(f"module 'lrdbenchmark' has no attribute '{name}'")

    module_path, attr_name = target.split(":")
    try:
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
    except ImportError as exc:
        stub = _GPU_STUBS.get(name)
        if stub is not None:
            _LOGGER.debug("Falling back to GPU stub for %s: %s", name, exc)
            value = stub
        else:
            _LOGGER.warning("Optional dependency missing for %s: %s", name, exc)
            value = None
    globals()[name] = value
    return value


def __dir__() -> Tuple[str, ...]:
    return tuple(sorted(__all__))
