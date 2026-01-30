#!/usr/bin/env python3
"""
Comprehensive Benchmark Module for LRDBench
A unified interface for running all types of benchmarks and analyses
"""

import numpy as np
import time
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
import warnings
from itertools import combinations
import os
import sys

from scipy import stats

# Import advanced metrics
from .advanced_metrics import (
    ConvergenceAnalyzer,
    MeanSignedErrorAnalyzer,
    AdvancedPerformanceProfiler,
    RobustnessStressTester,
    ScalingInfluenceAnalyzer,
    calculate_convergence_rate,
    calculate_mean_signed_error,
    profile_estimator_performance
)
from .uncertainty import UncertaintyQuantifier
from ..robustness.adaptive_preprocessor import AdaptiveDataPreprocessor

# Import new diagnostic and reporting systems
from .diagnostics import (
    PowerLawDiagnostics,
    ScaleWindowSensitivityAnalyser,
    run_comprehensive_diagnostics
)
from ..analytics.provenance import ProvenanceTracker, create_provenance_bundle
from ..analytics.stratified_report_generator import StratifiedReportGenerator
from ..random_manager import get_random_manager

# Import estimators
from .temporal.rs.rs_estimator_unified import RSEstimator
from .temporal.dfa.dfa_estimator_unified import DFAEstimator
from .temporal.dma.dma_estimator_unified import DMAEstimator
from .temporal.higuchi.higuchi_estimator_unified import HiguchiEstimator
from .spectral.gph.gph_estimator_unified import GPHEstimator
from .spectral.whittle.whittle_estimator_unified import WhittleEstimator
from .spectral.periodogram.periodogram_estimator_unified import PeriodogramEstimator
from .wavelet.cwt.cwt_estimator_unified import CWTEstimator
from .wavelet.variance.variance_estimator_unified import WaveletVarianceEstimator
from .wavelet.log_variance.log_variance_estimator_unified import (
    WaveletLogVarianceEstimator,
)
from .wavelet.whittle.whittle_estimator_unified import WaveletWhittleEstimator
from .multifractal.mfdfa.mfdfa_estimator_unified import MFDFAEstimator
from .multifractal.wavelet_leaders.wavelet_leaders_estimator_unified import (
    MultifractalWaveletLeadersEstimator,
)

# Note: Neural network estimators now use pretrained models instead of unified estimators

# Import data models
from ..models.data_models.fbm.fbm_model import FractionalBrownianMotion as FBMModel
from ..models.data_models.fgn.fgn_model import FractionalGaussianNoise as FGNModel
from ..models.data_models.arfima.arfima_model import ARFIMAModel
from ..models.data_models.mrw.mrw_model import MultifractalRandomWalk as MRWModel
from ..analytics.error_analyzer import ErrorAnalyzer


# Import contamination models
# Simple contamination classes for benchmarking
class AdditiveGaussianNoise:
    def __init__(self, rng: np.random.Generator, noise_level=0.1, std=0.1):
        self.noise_level = noise_level
        self.std = std
        self.rng = rng

    def apply(self, data):
        noise = self.rng.normal(0, self.std * self.noise_level, len(data))
        return data + noise


class MultiplicativeNoise:
    def __init__(self, rng: np.random.Generator, noise_level=0.05, std=0.05):
        self.noise_level = noise_level
        self.std = std
        self.rng = rng

    def apply(self, data):
        noise = self.rng.normal(1, self.std * self.noise_level, len(data))
        return data * noise


class OutlierContamination:
    def __init__(
        self,
        rng: np.random.Generator,
        outlier_fraction=0.1,
        outlier_magnitude=3.0,
    ):
        self.outlier_fraction = outlier_fraction
        self.outlier_magnitude = outlier_magnitude
        self.rng = rng

    def apply(self, data):
        contaminated = data.copy()
        n_outliers = int(len(data) * self.outlier_fraction)
        outlier_indices = self.rng.choice(len(data), n_outliers, replace=False)
        contaminated[outlier_indices] += self.rng.normal(
            0, self.outlier_magnitude, n_outliers
        )
        return contaminated


class TrendContamination:
    def __init__(
        self,
        rng: Optional[np.random.Generator] = None,
        trend_strength=0.1,
        trend_type="linear",
    ):
        self.trend_strength = trend_strength
        self.trend_type = trend_type
        self.rng = rng

    def apply(self, data):
        n = len(data)
        if self.trend_type == "linear":
            trend = np.linspace(0, self.trend_strength, n)
        else:
            trend = np.zeros(n)
        return data + trend


class SeasonalContamination:
    def __init__(
        self,
        rng: Optional[np.random.Generator] = None,
        seasonal_strength=0.1,
        period=None,
    ):
        self.seasonal_strength = seasonal_strength
        self.period = period
        self.rng = rng

    def apply(self, data):
        n = len(data)
        if self.period is None:
            self.period = n // 4
        t = np.arange(n)
        seasonal = self.seasonal_strength * np.sin(2 * np.pi * t / self.period)
        return data + seasonal


class MissingDataContamination:
    def __init__(
        self,
        rng: np.random.Generator,
        missing_fraction=0.1,
        missing_pattern="random",
    ):
        self.missing_fraction = missing_fraction
        self.missing_pattern = missing_pattern
        self.rng = rng

    def apply(self, data):
        contaminated = data.copy()
        n_missing = int(len(data) * self.missing_fraction)
        if self.missing_pattern == "random":
            missing_indices = self.rng.choice(len(data), n_missing, replace=False)
            contaminated[missing_indices] = np.nan
        return contaminated


# Import pre-trained ML models for production use
try:
    from ..models.pretrained_models.ml_pretrained import (
        RandomForestPretrainedModel,
        SVREstimatorPretrainedModel,
        GradientBoostingPretrainedModel,
    )
    
    # Import pre-trained neural models
    from ..models.pretrained_models.cnn_pretrained import CNNPretrainedModel
    from ..models.pretrained_models.transformer_pretrained import TransformerPretrainedModel
    from ..models.pretrained_models.lstm_pretrained import LSTMPretrainedModel
    from ..models.pretrained_models.gru_pretrained import GRUPretrainedModel
    
    PRETRAINED_MODELS_AVAILABLE = True
except ImportError:
    # Pretrained models not available
    RandomForestPretrainedModel = None
    SVREstimatorPretrainedModel = None
    GradientBoostingPretrainedModel = None
    CNNPretrainedModel = None
    TransformerPretrainedModel = None
    LSTMPretrainedModel = None
    GRUPretrainedModel = None
    PRETRAINED_MODELS_AVAILABLE = False


class ComprehensiveBenchmark:
    """
    Comprehensive benchmark class for testing all estimators and data models.
    """

    def __init__(self, output_dir: Optional[str] = None, runtime_profile: str = "auto"):
        """
        Initialize the benchmark system.

        Parameters
        ----------
        output_dir : str, optional
            Directory to save benchmark results
        runtime_profile : str, optional
            Runtime profile to control computational intensity. Options:
            - "auto": determine automatically (default)
            - "quick": minimise expensive diagnostics (useful for tests)
            - "full": enable all diagnostics and resampling routines
        """
        self.output_dir = Path(output_dir) if output_dir else Path("benchmark_results")
        self.output_dir.mkdir(exist_ok=True)

        self.protocol_config_path = Path("config/benchmark_protocol.yaml")
        self.protocol_config = self._load_protocol_config(self.protocol_config_path)
        self.runtime_profile = self._resolve_runtime_profile(runtime_profile)

        data_generation_cfg = self.protocol_config.get("data_generation", {})
        self.random_manager = get_random_manager()
        self.random_manager.initialise(data_generation_cfg.get("random_seed"))

        preprocessing_cfg = self.protocol_config.get("preprocessing", {})
        winsor_limits = preprocessing_cfg.get("winsorize_limits", (0.01, 0.99))
        if isinstance(winsor_limits, list):
            winsor_limits = tuple(winsor_limits)
        self.data_preprocessor = AdaptiveDataPreprocessor(
            outlier_threshold=preprocessing_cfg.get("outlier_threshold", 3.0),
            winsorize_limits=winsor_limits,
            enable_winsorize=preprocessing_cfg.get("apply_winsorize", True),
            enable_detrend=preprocessing_cfg.get("detrend", True),
        )

        # Initialize all estimator categories
        self.all_estimators = self._initialize_all_estimators()
        benchmark_cfg = self.protocol_config.get("benchmark", {})
        diagnostics_cfg = self.protocol_config.get("diagnostics", {})

        advanced_metrics_cfg = benchmark_cfg.get("advanced_metrics", {})
        uncertainty_cfg = benchmark_cfg.get("uncertainty", {})
        robustness_cfg = benchmark_cfg.get("robustness", {})

        self.enable_advanced_metrics = bool(advanced_metrics_cfg.get("enabled", True))
        self.enable_uncertainty = bool(uncertainty_cfg.get("enabled", True))
        self.enable_robustness = bool(robustness_cfg.get("enabled", True))
        log_log_cfg = diagnostics_cfg.get("log_log_checks", {})
        self.enable_diagnostics = bool(log_log_cfg.get("enabled", True))

        if self.runtime_profile == "quick":
            self.enable_advanced_metrics = False
            self.enable_uncertainty = False
            self.enable_robustness = False
            self.enable_diagnostics = False

        # Initialize advanced metrics analyzers
        if self.enable_advanced_metrics:
            self.convergence_analyzer = ConvergenceAnalyzer()
            self.mse_analyzer = MeanSignedErrorAnalyzer()
        else:
            self.convergence_analyzer = None
            self.mse_analyzer = None

        profiler_seed = self.random_manager.spawn_seed("benchmark:advanced_profiler")
        self.advanced_profiler = AdvancedPerformanceProfiler(random_state=profiler_seed)

        if self.enable_uncertainty:
            uncertainty_seed = self.random_manager.spawn_seed(
                "benchmark:uncertainty", seed=uncertainty_cfg.get("random_state")
            )
            self.uncertainty_quantifier = UncertaintyQuantifier(
                n_block_bootstrap=uncertainty_cfg.get("n_block_bootstrap", 64),
                block_size=uncertainty_cfg.get("block_size"),
                n_wavelet_bootstrap=uncertainty_cfg.get("n_wavelet_bootstrap", 64),
                wavelet=uncertainty_cfg.get("wavelet", "db4"),
                max_wavelet_level=uncertainty_cfg.get("max_wavelet_level"),
                n_parametric=uncertainty_cfg.get("n_parametric", 48),
                confidence_level=benchmark_cfg.get("confidence_level", 0.95),
                random_state=uncertainty_seed,
            )
        else:
            self.uncertainty_quantifier = None

        self.error_analyzer = ErrorAnalyzer()

        # Initialize robustness stress tester
        if self.enable_robustness:
            robustness_config = robustness_cfg.get("config", {})
            robustness_seed = self.random_manager.spawn_seed(
                "benchmark:robustness", seed=robustness_cfg.get("random_state")
            )
            self.robustness_tester = RobustnessStressTester(
                random_state=robustness_seed,
                config=robustness_config
            )
        else:
            self.robustness_tester = None

        # Initialize new diagnostic and reporting systems
        if self.enable_diagnostics:
            self.power_law_diagnostics = PowerLawDiagnostics(
                min_r_squared=log_log_cfg.get("min_r_squared", 0.5),
                min_points=log_log_cfg.get("min_points", 6)
            )

            sensitivity_cfg = diagnostics_cfg.get("scale_window_sensitivity", {})
            self.scale_sensitivity_analyser = ScaleWindowSensitivityAnalyser(
                perturbation_levels=sensitivity_cfg.get("perturbation_levels", [0.9, 0.95, 1.05, 1.1]),
                leave_one_out=sensitivity_cfg.get("leave_one_out", True)
            )

            self.scaling_influence_analyser = ScalingInfluenceAnalyzer()
        else:
            self.power_law_diagnostics = None
            self.scale_sensitivity_analyser = None
            self.scaling_influence_analyser = None
        
        # Initialize provenance tracker
        self.provenance_tracker = ProvenanceTracker(self.protocol_config)
        
        # Initialize stratified report generator
        self.stratified_report_generator = StratifiedReportGenerator(self.protocol_config)

        # Initialize data models
        self.data_models = self._initialize_data_models()

        # Initialize contamination models
        self.contamination_models = self._initialize_contamination_models()

        # Results storage
        self.results = {}
        self.performance_metrics = {}

    def _resolve_runtime_profile(self, runtime_profile: Optional[str]) -> str:
        """
        Determine the runtime profile controlling benchmark intensity.
        """
        env_override = os.getenv("LRDBENCHMARK_RUNTIME_PROFILE")
        if env_override:
            runtime_profile = env_override

        if not runtime_profile:
            runtime_profile = "auto"

        runtime_profile = runtime_profile.lower()

        if runtime_profile == "auto":
            quick_flag = os.getenv("LRDBENCHMARK_QUICK_MODE")
            if quick_flag and quick_flag.strip().lower() in {"1", "true", "yes", "on"}:
                return "quick"
            if os.getenv("PYTEST_CURRENT_TEST"):
                return "quick"
            if "pytest" in sys.modules:
                return "quick"
            return "full"

        if runtime_profile in {"quick", "full"}:
            return runtime_profile

        warnings.warn(
            f"Unknown runtime_profile '{runtime_profile}'. Falling back to 'full'."
        )
        return "full"

    def _load_protocol_config(self, path: Path) -> Dict[str, Any]:
        """Load benchmark protocol configuration from YAML/JSON file."""
        default_config: Dict[str, Any] = {
            "version": "2.0",
            "preprocessing": {
                "outlier_threshold": 3.0,
                "winsorize_limits": [0.01, 0.99],
                "detrend": True,
                "apply_winsorize": True,
            },
            "scale_selection": {
                "spectral": {
                    "min_freq_ratio": 0.01,
                    "max_freq_ratio": 0.1,
                    "low_freq_trim": 0.0,
                },
                "temporal": {
                    "min_window": 16,
                    "max_window": 256,
                    "window_density": "log",
                },
                "wavelet": {"min_level": 1, "max_level": 8, "wavelet": "db4"},
            },
            "data_models": {},
            "estimator_overrides": {},
            "benchmark": {
                "confidence_level": 0.95,
                "uncertainty": {
                    "n_block_bootstrap": 64,
                    "n_wavelet_bootstrap": 64,
                    "n_parametric": 48,
                },
                "robustness": {
                    "enabled": True,
                    "config": {},
                },
            },
        }

        try:
            with open(path, "r") as f:
                # Try YAML first, then JSON
                if path.suffix.lower() in ['.yaml', '.yml']:
                    try:
                        import yaml
                        config_data = yaml.safe_load(f)
                    except ImportError:
                        warnings.warn(
                            "PyYAML not installed. Install with 'pip install pyyaml' to use YAML configs. "
                            "Falling back to JSON parsing."
                        )
                        f.seek(0)
                        config_data = json.load(f)
                else:
                    config_data = json.load(f)
            
            # Merge with defaults, handling both new unified schema and legacy format
            merged = self._deep_merge_dicts(default_config, config_data)
            
            # Map new unified schema to legacy format for backward compatibility
            if "data_generation" in merged:
                # Extract data models from new schema
                if "models" in merged["data_generation"]:
                    merged["data_models"] = merged["data_generation"]["models"]
            
            if "estimators" in merged and "overrides" in merged["estimators"]:
                merged["estimator_overrides"] = merged["estimators"]["overrides"]
            
            # Ensure robustness config exists
            if "benchmark" in merged:
                if "robustness" not in merged["benchmark"]:
                    merged["benchmark"]["robustness"] = {"enabled": True, "config": {}}
            
            return merged
        except FileNotFoundError:
            warnings.warn(
                f"Protocol configuration '{path}' not found. Using defaults."
            )
        except (json.JSONDecodeError, ValueError) as exc:
            warnings.warn(
                f"Failed to parse protocol configuration '{path}': {exc}. Using defaults."
            )

        return default_config

    def _deep_merge_dicts(
        self, base: Dict[str, Any], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge dictionaries without mutating inputs."""
        merged = dict(base)
        for key, value in updates.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._deep_merge_dicts(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _initialize_all_estimators(self) -> Dict[str, Dict[str, Any]]:
        """Initialize all available estimators organized by category."""
        estimators = {
            "classical": {
                # Temporal estimators
                "R/S": RSEstimator(),
                "DFA": DFAEstimator(),
                "DMA": DMAEstimator(),
                "Higuchi": HiguchiEstimator(),
                # Spectral estimators
                "GPH": GPHEstimator(),
                "Whittle": WhittleEstimator(),
                "Periodogram": PeriodogramEstimator(),
                # Wavelet estimators
                "CWT": CWTEstimator(),
                "WaveletVar": WaveletVarianceEstimator(),
                "WaveletLogVar": WaveletLogVarianceEstimator(),
                "WaveletWhittle": WaveletWhittleEstimator(),
                # Multifractal estimators
                "MFDFA": MFDFAEstimator(),
                "WaveletLeaders": MultifractalWaveletLeadersEstimator(),
            },
            "ML": {
                "RandomForest": RandomForestPretrainedModel() if RandomForestPretrainedModel is not None else None,
                "GradientBoosting": GradientBoostingPretrainedModel() if GradientBoostingPretrainedModel is not None else None,
                "SVR": SVREstimatorPretrainedModel() if SVREstimatorPretrainedModel is not None else None,
            },
            "neural": {
                "CNN": CNNPretrainedModel(input_length=500) if CNNPretrainedModel is not None else None,
                "LSTM": LSTMPretrainedModel(input_length=500) if LSTMPretrainedModel is not None else None,
                "GRU": GRUPretrainedModel(input_length=500) if GRUPretrainedModel is not None else None,
                "Transformer": TransformerPretrainedModel(input_length=500) if TransformerPretrainedModel is not None else None,
            },
        }

        overrides = self.protocol_config.get("estimator_overrides", {})
        if overrides:
            estimators = self._apply_estimator_overrides(estimators, overrides)

        return estimators

    def _apply_estimator_overrides(
        self,
        estimators: Dict[str, Dict[str, Any]],
        overrides: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Apply protocol-defined parameter overrides to initialized estimators."""
        for estimator_map in estimators.values():
            for name, estimator in estimator_map.items():
                if estimator is None:
                    continue
                override = overrides.get(name)
                if override:
                    setter = getattr(estimator, "set_params", None)
                    if callable(setter):
                        try:
                            setter(**override)
                        except Exception as exc:
                            warnings.warn(
                                f"Failed to apply override for estimator '{name}': {exc}"
                            )
        return estimators

    def _initialize_data_models(self) -> Dict[str, Any]:
        """Initialize all available data models."""
        data_models = {
            "fBm": FBMModel,
            "fGn": FGNModel,
            "ARFIMAModel": ARFIMAModel,
            "MRW": MRWModel,
        }
        return data_models

    def _initialize_contamination_models(self) -> Dict[str, Any]:
        """Initialize all available contamination models."""
        contamination_models = {
            "additive_gaussian": AdditiveGaussianNoise,
            "multiplicative_noise": MultiplicativeNoise,
            "outliers": OutlierContamination,
            "trend": TrendContamination,
            "seasonal": SeasonalContamination,
            "missing_data": MissingDataContamination,
        }
        return contamination_models

    def _infer_estimator_family(self, estimator_name: str) -> Optional[str]:
        """Return the estimator family/category for a given estimator name."""
        for family, estimator_map in self.all_estimators.items():
            if estimator_name in estimator_map:
                return family
        return None

    def get_estimators_by_type(
        self, benchmark_type: str = "comprehensive", data_length: int = 1000
    ) -> Dict[str, Any]:
        """
        Get estimators based on the specified benchmark type.

        Parameters
        ----------
        benchmark_type : str
            Type of benchmark to run:
            - 'comprehensive': All estimators (default)
            - 'classical': Only classical statistical estimators
            - 'ML': Only machine learning estimators (non-neural)
            - 'neural': Only neural network estimators
        data_length : int
            Length of data to be tested (used for adaptive wavelet estimators)

        Returns
        -------
        dict
            Dictionary of estimators for the specified type
        """
        if benchmark_type == "comprehensive":
            # Combine all estimators
            all_est = {}
            for category in self.all_estimators.values():
                all_est.update(category)

            # Filter out None estimators
            all_est = {name: estimator for name, estimator in all_est.items() if estimator is not None}
            return all_est
        elif benchmark_type in self.all_estimators:
            estimators = self.all_estimators[benchmark_type].copy()

            # Filter out None estimators
            estimators = {name: estimator for name, estimator in estimators.items() if estimator is not None}
            return estimators
        else:
            raise ValueError(
                f"Unknown benchmark type: {benchmark_type}. "
                f"Available types: {list(self.all_estimators.keys()) + ['comprehensive']}"
            )

    def generate_test_data(
        self, model_name: str, data_length: int = 1000, **kwargs
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Generate test data using specified model.

        Parameters
        ----------
        model_name : str
            Name of the data model to use
        data_length : int
            Length of data to generate
        **kwargs : dict
            Additional parameters for the data model

        Returns
        -------
        tuple
            (data, parameters)
        """
        if model_name not in self.data_models:
            raise ValueError(f"Unknown data model: {model_name}")

        model_class = self.data_models[model_name]

        protocol_defaults = {
            key: value
            for key, value in self.protocol_config.get("data_models", {}).get(model_name, {}).items()
            if key != "enabled"
        }

        # Set default parameters if not provided
        if model_name == "fBm":
            base_params = {"H": 0.7, "sigma": 1.0}
            params = {**base_params, **protocol_defaults, **kwargs}
        elif model_name == "fGn":
            base_params = {"H": 0.7, "sigma": 1.0}
            params = {**base_params, **protocol_defaults, **kwargs}
        elif model_name == "ARFIMAModel":
            base_params = {"d": 0.3, "ar_params": [0.5], "ma_params": [0.2]}
            params = {**base_params, **protocol_defaults, **kwargs}
        elif model_name == "MRW":
            base_params = {"H": 0.7, "lambda_param": 0.5, "sigma": 1.0}
            params = {**base_params, **protocol_defaults, **kwargs}
        else:
            params = {**protocol_defaults, **kwargs}

        seed_override = params.pop("random_state", None)
        model = model_class(**params)
        stream_name = f"data_model:{model_name}"
        data_seed = self.random_manager.spawn_seed(stream_name, seed=seed_override)
        data_rng = self.random_manager.spawn_generator(stream_name, seed=data_seed)
        data = model.generate(length=data_length, rng=data_rng)

        params["model_name"] = model_name
        if seed_override is not None:
            params["requested_random_seed"] = seed_override
        params["random_seed"] = data_seed

        return data, params

    def apply_contamination(
        self,
        data: np.ndarray,
        contamination_type: str,
        contamination_level: float = 0.1,
        **kwargs,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply contamination to the data.

        Parameters
        ----------
        data : np.ndarray
            Original clean data
        contamination_type : str
            Type of contamination to apply
        contamination_level : float
            Level/intensity of contamination (0.0 to 1.0)
        **kwargs : dict
            Additional parameters for specific contamination types

        Returns
        -------
        tuple
            (contaminated_data, contamination_info)
        """
        if contamination_type not in self.contamination_models:
            raise ValueError(
                f"Unknown contamination type: {contamination_type}. "
                f"Available types: {list(self.contamination_models.keys())}"
            )

        contamination_class = self.contamination_models[contamination_type]

        # Set default parameters based on contamination type
        if contamination_type == "additive_gaussian":
            default_params = {"noise_level": contamination_level, "std": 0.1}
        elif contamination_type == "multiplicative_noise":
            default_params = {"noise_level": contamination_level, "std": 0.05}
        elif contamination_type == "outliers":
            default_params = {
                "outlier_fraction": contamination_level,
                "outlier_magnitude": 3.0,
            }
        elif contamination_type == "trend":
            default_params = {
                "trend_strength": contamination_level,
                "trend_type": "linear",
            }
        elif contamination_type == "seasonal":
            default_params = {
                "seasonal_strength": contamination_level,
                "period": len(data) // 4,
            }
        elif contamination_type == "missing_data":
            default_params = {
                "missing_fraction": contamination_level,
                "missing_pattern": "random",
            }
        else:
            default_params = {}

        # Update with provided kwargs
        contamination_params = {**default_params, **kwargs}

        # Apply contamination
        stream_name = f"contamination:{contamination_type}"
        seed_override = contamination_params.get("random_state")
        contamination_seed = self.random_manager.spawn_seed(
            stream_name, seed=seed_override
        )
        contamination_rng = self.random_manager.spawn_generator(
            stream_name, seed=contamination_seed
        )
        model_kwargs = dict(contamination_params)
        model_kwargs.pop("random_state", None)
        model_kwargs.setdefault("rng", contamination_rng)
        contamination_model = contamination_class(**model_kwargs)
        contaminated_data = contamination_model.apply(data)

        contamination_info = {
            "type": contamination_type,
            "level": contamination_level,
            "parameters": contamination_params,
            "original_data_shape": data.shape,
            "contaminated_data_shape": contaminated_data.shape,
            "random_seed": contamination_seed,
        }

        return contaminated_data, contamination_info

    def run_single_estimator_test(
        self, estimator_name: str, data: np.ndarray, true_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a single estimator test.

        Parameters
        ----------
        estimator_name : str
            Name of the estimator to test
        data : np.ndarray
            Test data
        true_params : dict
            True parameters of the data

        Returns
        -------
        dict
            Test results
        """
        # Get the estimator from the comprehensive list
        all_estimators = self.get_estimators_by_type("comprehensive")
        estimator = all_estimators[estimator_name]
        estimator_family = self._infer_estimator_family(estimator_name)

        # Measure execution time
        start_time = time.time()

        processed_data = np.asarray(data, dtype=np.float64)
        preprocessing_metadata: Dict[str, Any] = {}
        try:
            processed_data, preprocessing_metadata = self.data_preprocessor.preprocess(
                processed_data
            )
            preprocessing_metadata["config"] = self.protocol_config.get(
                "preprocessing", {}
            )
        except Exception as exc:
            warnings.warn(f"Preprocessing failed for estimator {estimator_name}: {exc}")
            preprocessing_metadata = {
                "status": "failed",
                "error": str(exc),
                "config": self.protocol_config.get("preprocessing", {}),
            }

        try:
            result = estimator.estimate(processed_data)
            execution_time = time.time() - start_time

            # Extract key metrics
            hurst_est = result.get("hurst_parameter", None)
            if hurst_est is not None:
                # Try different parameter names for different data models
                true_hurst = None
                if "H" in true_params:
                    true_hurst = true_params["H"]
                elif "d" in true_params:
                    # For ARFIMA models, use d parameter directly
                    true_hurst = true_params["d"]

                if true_hurst is not None:
                    error = abs(hurst_est - true_hurst)
                else:
                    # If we can't calculate error, still mark as successful but with no error metric
                    error = None

                # Update true_hurst in the result for consistency
                if true_hurst is not None:
                    true_params["H"] = true_hurst
            else:
                error = None

            # Advanced metrics analysis
            advanced_metrics: Dict[str, Any] = {}
            if (
                self.enable_advanced_metrics
                and self.convergence_analyzer is not None
                and true_params.get("H") is not None
            ):
                try:
                    # Convergence analysis
                    convergence_results = self.convergence_analyzer.analyze_convergence_rate(
                        estimator, processed_data, true_params.get("H")
                    )
                    advanced_metrics["convergence_rate"] = convergence_results.get("convergence_rate")
                    advanced_metrics["convergence_achieved"] = convergence_results.get("convergence_achieved")
                    advanced_metrics["stability_metric"] = convergence_results.get("stability_metric")

                    # Mean signed error analysis (Monte Carlo)
                    mse_results = self._calculate_monte_carlo_mse(
                        estimator, processed_data, true_params.get("H")
                    )
                    advanced_metrics["mean_signed_error"] = mse_results.get("mean_signed_error")
                    advanced_metrics["bias_percentage"] = mse_results.get("bias_percentage")
                    advanced_metrics["significant_bias"] = mse_results.get("significant_bias")

                except Exception as e:
                    warnings.warn(f"Advanced metrics calculation failed: {e}")
                    advanced_metrics = {
                        "convergence_rate": None,
                        "convergence_achieved": None,
                        "stability_metric": None,
                        "mean_signed_error": None,
                        "bias_percentage": None,
                        "significant_bias": None,
                    }
            elif not self.enable_advanced_metrics:
                advanced_metrics = {
                    "status": "skipped",
                    "reason": (
                        "Advanced metrics disabled by runtime profile."
                        if self.runtime_profile == "quick"
                        else "Advanced metrics disabled by benchmark configuration."
                    ),
                }

            # Uncertainty quantification
            if hurst_est is not None:
                if self.enable_uncertainty and self.uncertainty_quantifier is not None:
                    try:
                        uncertainty_details = self.uncertainty_quantifier.compute_intervals(
                            estimator=estimator,
                            data=processed_data,
                            base_result=result,
                            true_value=true_params.get("H"),
                            data_model_name=true_params.get("model_name"),
                            data_model_params=true_params,
                            data_model_registry=self.data_models,
                        )
                    except Exception as exc:
                        warnings.warn(f"Uncertainty quantification failed: {exc}")
                        uncertainty_details = {
                            "status": "failed",
                            "error": str(exc),
                        }
                else:
                    reason = (
                        "Uncertainty quantification disabled by runtime profile."
                        if self.runtime_profile == "quick"
                        else "Uncertainty quantification disabled in benchmark configuration."
                    )
                    uncertainty_details = {
                        "status": "disabled",
                        "reason": reason,
                    }
            else:
                uncertainty_details = {
                    "status": "unavailable",
                    "reason": "No hurst estimate available for uncertainty quantification.",
                }

            if not self.enable_uncertainty:
                result["confidence_interval"] = None

            if isinstance(uncertainty_details, dict):
                result["uncertainty"] = uncertainty_details
                primary_interval = uncertainty_details.get("primary_interval")
                if (
                    primary_interval
                    and isinstance(primary_interval, dict)
                    and primary_interval.get("confidence_interval") is not None
                ):
                    result.setdefault("confidence_interval", tuple(primary_interval["confidence_interval"]))
            
            # Robustness stress panels: before/after H comparisons
            robustness_panel = None
            if (
                self.enable_robustness
                and self.robustness_tester is not None
                and hurst_est is not None
            ):
                try:
                    # Use original data (before preprocessing) for robustness tests
                    # The stress tester will apply its own transformations
                    robustness_panel = self.robustness_tester.run_panels(
                        estimator=estimator,
                        data=data,  # Original data before preprocessing
                        baseline_result=result,  # Baseline result with H estimate
                        true_value=true_params.get("H"),
                    )
                except Exception as exc:
                    warnings.warn(f"Robustness stress panel failed for {estimator_name}: {exc}")
                    robustness_panel = {
                        "status": "failed",
                        "error": str(exc),
                    }
            elif not self.enable_robustness:
                robustness_panel = {
                    "status": "skipped",
                    "reason": (
                        "Robustness analysis disabled by runtime profile."
                        if self.runtime_profile == "quick"
                        else "Robustness analysis disabled by benchmark configuration."
                    ),
                }
            
            # Run comprehensive diagnostics on power-law fit
            diagnostics_results: Dict[str, Any] = {}
            diagnostics_cfg = self.protocol_config.get("diagnostics", {})

            if (
                self.enable_diagnostics
                and self.power_law_diagnostics is not None
                and hurst_est is not None
            ):
                try:
                    # Try to extract scale data from result
                    scales, statistics = self._extract_scale_data(result, estimator)
                    
                    if scales is not None and statistics is not None:
                        # Run power-law diagnostics
                        diag_results = self.power_law_diagnostics.diagnose(
                            scales, 
                            statistics,
                            slope=result.get("slope"),
                            intercept=result.get("intercept")
                        )
                        diagnostics_results["power_law"] = diag_results
                        
                        # Run scaling influence analysis if enabled
                        if (
                            diagnostics_cfg.get("log_log_checks", {}).get("influence_analysis", True)
                            and self.scaling_influence_analyser is not None
                        ):
                            try:
                                influence_results = self.scaling_influence_analyser.analyse(
                                    scales, statistics, min_points=6
                                )
                                diagnostics_results["scaling_influence"] = influence_results
                            except Exception as exc_inf:
                                diagnostics_results["scaling_influence"] = {
                                    "status": "failed",
                                    "error": str(exc_inf)
                                }
                        
                        # Run scale window sensitivity if enabled
                        if (
                            diagnostics_cfg.get("scale_window_sensitivity", {}).get("enabled", True)
                            and self.scale_sensitivity_analyser is not None
                        ):
                            try:
                                sensitivity_results = self.scale_sensitivity_analyser.analyse(
                                    estimator, processed_data, result, scales
                                )
                                diagnostics_results["scale_sensitivity"] = sensitivity_results
                            except Exception as exc_sens:
                                diagnostics_results["scale_sensitivity"] = {
                                    "status": "failed",
                                    "error": str(exc_sens)
                                }
                except Exception as exc:
                    warnings.warn(f"Diagnostic analysis failed for {estimator_name}: {exc}")
                    diagnostics_results = {
                        "status": "failed",
                        "error": str(exc)
                    }
            elif not self.enable_diagnostics:
                diagnostics_results = {
                    "status": "skipped",
                    "reason": (
                        "Diagnostics disabled by runtime profile."
                        if self.runtime_profile == "quick"
                        else "Diagnostics disabled by benchmark configuration."
                    ),
                }
            
            # Build provenance for this result row
            result_provenance = self._build_result_row_provenance(
                {
                    "estimator": estimator_name,
                    "timestamp": datetime.now().isoformat(),
                    "estimated_hurst": hurst_est,
                    "true_hurst": true_params.get("H", None),
                    "error": error,
                    "preprocessing": preprocessing_metadata,
                    "robustness_panel": robustness_panel,
                    "uncertainty": uncertainty_details,
                },
                true_params
            )
            
            test_result = {
                "estimator": estimator_name,
                "success": True,
                "execution_time": execution_time,
                "estimated_hurst": hurst_est,
                "true_hurst": true_params.get("H", None),
                "error": error,
                "r_squared": result.get("r_squared", None),
                "p_value": result.get("p_value", None),
                "intercept": result.get("intercept", None),
                "slope": result.get("slope", None),
                "std_error": result.get("std_error", None),
                "confidence_interval": result.get("confidence_interval"),
                "advanced_metrics": advanced_metrics,
                "uncertainty": uncertainty_details,
                "robustness_panel": robustness_panel,
                "diagnostics": diagnostics_results,
                "preprocessing": preprocessing_metadata,
                "provenance": result_provenance,  # Per-row provenance artifact
                "full_result": result,
            }

            if self.enable_uncertainty:
                self._record_uncertainty_event(
                    estimator_name=estimator_name,
                    data_model=true_params.get("model_name"),
                    uncertainty=uncertainty_details,
                    estimate=hurst_est,
                    true_value=true_params.get("H"),
                    data_length=len(processed_data),
                    estimator_family=estimator_family,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            test_result = {
                "estimator": estimator_name,
                "success": False,
                "execution_time": execution_time,
                "error_message": str(e),
                "estimated_hurst": None,
                "true_hurst": true_params.get("H", None),
                "error": None,
                "r_squared": None,
                "p_value": None,
                "intercept": None,
                "slope": None,
                "std_error": None,
                "full_result": None,
            }

        return test_result

    def _calculate_monte_carlo_mse(
        self, 
        estimator, 
        data: np.ndarray, 
        true_value: float, 
        n_simulations: int = 50
    ) -> Dict[str, Any]:
        """
        Calculate mean signed error using Monte Carlo simulations.
        
        Parameters
        ----------
        estimator : BaseEstimator
            Estimator instance
        data : np.ndarray
            Original dataset
        true_value : float
            True parameter value
        n_simulations : int
            Number of Monte Carlo simulations
            
        Returns
        -------
        dict
            Mean signed error analysis results
        """
        if not self.enable_advanced_metrics or self.mse_analyzer is None:
            return {
                "mean_signed_error": None,
                "bias_percentage": None,
                "significant_bias": None,
            }

        if self.runtime_profile == "quick":
            n_simulations = min(n_simulations, 5)

        estimates = []
        rng = self.random_manager.spawn_generator(
            f"benchmark:mse:{estimator.__class__.__name__}"
        )

        for i in range(n_simulations):
            # Add small random noise to create variations
            noise_level = 0.01 * np.std(data)
            noisy_data = data + rng.normal(0, noise_level, len(data))
            
            try:
                result = estimator.estimate(noisy_data)
                estimate = result.get('hurst_parameter', None)
                if estimate is not None:
                    estimates.append(estimate)
            except:
                continue
        
        if len(estimates) == 0:
            return {
                'mean_signed_error': None,
                'bias_percentage': None,
                'significant_bias': None
            }
        
        # Create true values list (all same value)
        true_values = [true_value] * len(estimates)
        
        # Calculate mean signed error
        mse_results = self.mse_analyzer.calculate_mean_signed_error(estimates, true_values)
        
        return {
            'mean_signed_error': mse_results.get('mean_signed_error'),
            'bias_percentage': mse_results.get('bias_percentage'),
            'significant_bias': mse_results.get('significant_bias')
        }

    def _compute_significance_tests(
        self,
        results: Dict[str, Any],
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Compute omnibus and post-hoc significance tests across estimators.

        Parameters
        ----------
        results : Dict[str, Any]
            Raw benchmark results grouped by data model.
        alpha : float
            Significance level for hypothesis testing.

        Returns
        -------
        Dict[str, Any]
            Significance testing outcomes including Friedman statistics and
            Holm-adjusted pairwise Wilcoxon tests.
        """
        alpha = float(alpha)
        if not results:
            return {
                "status": "insufficient_data",
                "reason": "No benchmark results available for significance testing.",
            }

        records: List[Dict[str, Any]] = []
        for model_name, model_data in results.items():
            estimator_results = model_data.get("estimator_results", [])
            if not estimator_results:
                continue

            row: Dict[str, Any] = {"data_model": model_name}
            for est_result in estimator_results:
                if est_result.get("success") and est_result.get("error") is not None:
                    row[est_result["estimator"]] = est_result["error"]

            if len(row) > 2:
                records.append(row)

        if not records:
            return {
                "status": "insufficient_data",
                "reason": "No comparable estimator errors available across data models.",
            }

        performance_df = pd.DataFrame(records).set_index("data_model")
        performance_df = performance_df.dropna(axis=1, how="any")
        performance_df = performance_df.dropna(axis=0, how="any")

        if performance_df.shape[0] < 2:
            return {
                "status": "insufficient_data",
                "reason": "At least two data models with complete estimator coverage are required.",
            }

        if performance_df.shape[1] < 2:
            return {
                "status": "insufficient_data",
                "reason": "At least two estimators with complete coverage are required.",
            }

        rank_df = performance_df.rank(axis=1, method="average")
        estimator_names = list(rank_df.columns)

        significance_payload: Dict[str, Any] = {
            "status": "ok",
            "considered_data_models": list(performance_df.index),
            "considered_estimators": estimator_names,
            "error_table": {
                str(idx): {col: float(val) for col, val in row.items()}
                for idx, row in performance_df.iterrows()
            },
            "rank_table": {
                str(idx): {col: float(val) for col, val in row.items()}
                for idx, row in rank_df.iterrows()
            },
            "alpha": alpha,
        }

        if performance_df.shape[1] >= 3:
            try:
                friedman_stat, friedman_p = stats.friedmanchisquare(
                    *[performance_df[col].values for col in performance_df.columns]
                )
                significance_payload["friedman"] = {
                    "statistic": float(friedman_stat),
                    "p_value": float(friedman_p),
                    "n_data_models": int(performance_df.shape[0]),
                    "n_estimators": int(performance_df.shape[1]),
                    "alpha": alpha,
                }
            except Exception as exc:
                significance_payload["friedman"] = {
                    "statistic": None,
                    "p_value": None,
                    "n_data_models": int(performance_df.shape[0]),
                    "n_estimators": int(performance_df.shape[1]),
                    "error": str(exc),
                    "alpha": alpha,
                }
        else:
            significance_payload["friedman"] = {
                "statistic": None,
                "p_value": None,
                "n_data_models": int(performance_df.shape[0]),
                "n_estimators": int(performance_df.shape[1]),
                "error": "Friedman test requires at least three estimators.",
                "alpha": alpha,
            }

        friedman_p_value = significance_payload["friedman"].get("p_value")
        significance_payload["global_null_rejected"] = (
            friedman_p_value is not None and friedman_p_value < alpha
        )

        mean_ranks = {
            estimator: float(rank_df[estimator].mean())
            for estimator in estimator_names
        }
        significance_payload["mean_ranks"] = mean_ranks

        def _determine_better(est_a: str, est_b: str) -> Optional[str]:
            rank_a = mean_ranks.get(est_a)
            rank_b = mean_ranks.get(est_b)
            if rank_a is None or rank_b is None:
                return None
            if np.isclose(rank_a, rank_b, atol=1e-9):
                return None
            return est_a if rank_a < rank_b else est_b

        if len(estimator_names) >= 3 and performance_df.shape[0] >= 1:
            try:
                q_alpha = stats.studentized_range.ppf(
                    1 - alpha / 2.0, len(estimator_names), np.inf
                )
                critical_difference = float(
                    q_alpha
                    / np.sqrt(2.0)
                    * np.sqrt(
                        len(estimator_names)
                        * (len(estimator_names) + 1)
                        / (6.0 * performance_df.shape[0])
                    )
                )
                nemenyi_results: List[Dict[str, Any]] = []
                for est_a, est_b in combinations(estimator_names, 2):
                    diff = abs(mean_ranks[est_a] - mean_ranks[est_b])
                    better = _determine_better(est_a, est_b)
                    nemenyi_results.append(
                        {
                            "pair": [est_a, est_b],
                            "mean_rank_difference": float(diff),
                            "critical_difference": critical_difference,
                            "significant": bool(diff > critical_difference),
                            "better_estimator": better,
                        }
                    )
                significance_payload["nemenyi"] = {
                    "status": "ok",
                    "alpha": alpha,
                    "q_critical": float(q_alpha),
                    "critical_difference": critical_difference,
                    "results": nemenyi_results,
                }
            except Exception as exc:
                significance_payload["nemenyi"] = {
                    "status": "failed",
                    "alpha": alpha,
                    "reason": str(exc),
                    "results": [],
                }
        else:
            significance_payload["nemenyi"] = {
                "status": "insufficient_data",
                "alpha": alpha,
                "reason": "Nemenyi test requires at least three estimators and one data model.",
                "results": [],
            }

        def _apply_holm(
            records: List[Dict[str, Any]],
            alpha_level: float,
            p_key: str = "p_value",
        ) -> None:
            indices = [
                idx for idx, record in enumerate(records) if record.get(p_key) is not None
            ]
            if not indices:
                for record in records:
                    record.setdefault("holm_p_value", record.get(p_key))
                    record.setdefault("significant", False)
                return

            sorted_indices = sorted(
                indices, key=lambda idx: float(records[idx][p_key])
            )
            m = len(sorted_indices)
            previous = 0.0
            for order, idx in enumerate(sorted_indices):
                raw_p = float(records[idx][p_key])
                adjusted = min(1.0, raw_p * (m - order))
                adjusted = max(adjusted, previous)
                records[idx]["holm_p_value"] = adjusted
                records[idx]["significant"] = adjusted < alpha_level
                previous = adjusted

            for record in records:
                record.setdefault("holm_p_value", record.get(p_key))
                record.setdefault("significant", False)

        wilcoxon_results: List[Dict[str, Any]] = []
        for est_a, est_b in combinations(estimator_names, 2):
            ranks_a = rank_df[est_a].values
            ranks_b = rank_df[est_b].values

            if np.allclose(ranks_a, ranks_b):
                wilcoxon_results.append(
                    {
                        "pair": [est_a, est_b],
                        "statistic": 0.0,
                        "p_value": 1.0,
                        "holm_p_value": 1.0,
                        "significant": False,
                        "note": "Identical rank distributions",
                        "n": int(len(ranks_a)),
                        "better_estimator": None,
                    }
                )
                continue

            try:
                stat, p_value = stats.wilcoxon(
                    ranks_a,
                    ranks_b,
                    zero_method="pratt",
                    alternative="two-sided",
                )
                wilcoxon_results.append(
                    {
                        "pair": [est_a, est_b],
                        "statistic": float(stat),
                        "p_value": float(p_value),
                        "n": int(len(ranks_a)),
                        "better_estimator": _determine_better(est_a, est_b),
                    }
                )
            except ValueError as exc:
                wilcoxon_results.append(
                    {
                        "pair": [est_a, est_b],
                        "error": str(exc),
                        "statistic": None,
                        "p_value": None,
                        "holm_p_value": None,
                        "significant": False,
                        "n": int(len(ranks_a)),
                        "better_estimator": None,
                    }
                )

        _apply_holm(wilcoxon_results, alpha)
        significance_payload["wilcoxon_signed_rank"] = wilcoxon_results
        significance_payload["post_hoc"] = wilcoxon_results

        sign_results: List[Dict[str, Any]] = []
        for est_a, est_b in combinations(estimator_names, 2):
            diffs = performance_df[est_a].values - performance_df[est_b].values
            diffs = diffs[np.isfinite(diffs)]
            diffs = diffs[np.abs(diffs) > 1e-12]
            n = len(diffs)

            if n == 0:
                sign_results.append(
                    {
                        "pair": [est_a, est_b],
                        "p_value": None,
                        "holm_p_value": None,
                        "significant": False,
                        "n": 0,
                        "note": "No non-zero paired differences.",
                        "better_estimator": None,
                        "n_positive": 0,
                        "n_negative": 0,
                    }
                )
                continue

            n_positive = int(np.sum(diffs > 0))
            n_negative = int(np.sum(diffs < 0))

            try:
                binom_res = stats.binomtest(
                    n_positive, n_positive + n_negative, 0.5, alternative="two-sided"
                )
                p_value = float(binom_res.pvalue)
            except Exception as exc:
                sign_results.append(
                    {
                        "pair": [est_a, est_b],
                        "p_value": None,
                        "holm_p_value": None,
                        "significant": False,
                        "n": int(n_positive + n_negative),
                        "error": str(exc),
                        "better_estimator": None,
                        "n_positive": n_positive,
                        "n_negative": n_negative,
                    }
                )
                continue

            better = None
            if n_positive != n_negative:
                better = est_a if n_negative > n_positive else est_b

            sign_results.append(
                {
                    "pair": [est_a, est_b],
                    "p_value": p_value,
                    "n": int(n_positive + n_negative),
                    "n_positive": n_positive,
                    "n_negative": n_negative,
                    "better_estimator": better,
                }
            )

        _apply_holm(sign_results, alpha)
        significance_payload["sign_test"] = {
            "status": "ok" if sign_results else "insufficient_data",
            "alpha": alpha,
            "results": sign_results,
        }

        estimator_markers: Dict[str, Dict[str, List[str]]] = {
            estimator: {"nemenyi": [], "wilcoxon": [], "sign_test": []}
            for estimator in estimator_names
        }

        def _register_marker(
            winner: Optional[str],
            pair: List[str],
            test_key: str,
        ) -> None:
            if winner is None or winner not in pair or len(pair) != 2:
                return
            loser = pair[0] if winner == pair[1] else pair[1]
            bucket = estimator_markers.setdefault(
                winner, {"nemenyi": [], "wilcoxon": [], "sign_test": []}
            ).setdefault(test_key, [])
            if loser not in bucket:
                bucket.append(loser)

        nemenyi_results = significance_payload["nemenyi"].get("results", [])
        if isinstance(nemenyi_results, list):
            for record in nemenyi_results:
                if record.get("significant"):
                    _register_marker(
                        record.get("better_estimator"),
                        record.get("pair", []),
                        "nemenyi",
                    )

        for record in wilcoxon_results:
            if record.get("significant"):
                _register_marker(
                    record.get("better_estimator"), record.get("pair", []), "wilcoxon"
                )

        sign_section = significance_payload["sign_test"].get("results", [])
        if isinstance(sign_section, list):
            for record in sign_section:
                if record.get("significant"):
                    _register_marker(
                        record.get("better_estimator"),
                        record.get("pair", []),
                        "sign_test",
                    )

        for estimator, buckets in estimator_markers.items():
            for key, values in buckets.items():
                buckets[key] = sorted(set(values))

        significance_payload["estimator_markers"] = estimator_markers

        return significance_payload

    def _compute_stratified_metrics(
        self,
        results: Dict[str, Any],
        data_length: int,
        contamination_type: Optional[str],
        contamination_level: float,
    ) -> Dict[str, Any]:
        """
        Produce stratified summaries across H bands, tail classes, data length, and contamination regime.
        """
        if not results:
            return {
                "status": "insufficient_data",
                "reason": "No benchmark results available for stratified analysis.",
            }

        def init_bucket() -> Dict[str, Any]:
            return {
                "count": 0,
                "success": 0,
                "errors": [],
                "ci_widths": [],
                "coverage": [],
                "estimated_values": [],
                "true_values": [],
                "data_models": set(),
                "estimators": set(),
            }

        hurst_bands: Dict[str, Dict[str, Any]] = {}
        tail_classes: Dict[str, Dict[str, Any]] = {}
        length_bands: Dict[str, Dict[str, Any]] = {}
        contamination_bands: Dict[str, Dict[str, Any]] = {}

        length_band = self._categorise_length_band(data_length)
        contamination_key = (
            "clean"
            if contamination_type is None
            else f"{contamination_type} (level={contamination_level})"
        )

        def update_bucket(container: Dict[str, Dict[str, Any]], key: str) -> Dict[str, Any]:
            if key not in container:
                container[key] = init_bucket()
            return container[key]

        total_observations = 0

        for model_name, payload in results.items():
            estimator_results = payload.get("estimator_results", [])
            tail_class = self._infer_tail_class(model_name, payload.get("data_params"))
            for est_result in estimator_results:
                if not est_result.get("success"):
                    continue
                error = est_result.get("error")
                if error is None or not np.isfinite(error):
                    continue

                hurst_true = est_result.get("true_hurst")
                hurst_est = est_result.get("estimated_hurst")
                hurst_value = hurst_true if hurst_true is not None else hurst_est
                hurst_band = self._categorise_hurst_band(hurst_value)

                bucket_h = update_bucket(hurst_bands, hurst_band)
                bucket_tail = update_bucket(tail_classes, tail_class)
                bucket_length = update_bucket(length_bands, length_band)
                bucket_contamination = update_bucket(contamination_bands, contamination_key)

                for bucket in (bucket_h, bucket_tail, bucket_length, bucket_contamination):
                    bucket["count"] += 1
                    bucket["errors"].append(float(error))
                    bucket["data_models"].add(model_name)
                    bucket["estimators"].add(est_result.get("estimator"))
                    if est_result.get("success"):
                        bucket["success"] += 1

                    if hurst_est is not None and np.isfinite(hurst_est):
                        bucket["estimated_values"].append(float(hurst_est))
                    if hurst_true is not None and np.isfinite(hurst_true):
                        bucket["true_values"].append(float(hurst_true))

                    ci = est_result.get("confidence_interval")
                    if (
                        isinstance(ci, (list, tuple))
                        and len(ci) == 2
                        and ci[0] is not None
                        and ci[1] is not None
                    ):
                        try:
                            ci_width = float(ci[1]) - float(ci[0])
                            if np.isfinite(ci_width):
                                bucket["ci_widths"].append(ci_width)
                        except (TypeError, ValueError):
                            pass

                    uncertainty = est_result.get("uncertainty")
                    if isinstance(uncertainty, dict):
                        coverage = uncertainty.get("coverage")
                        primary = uncertainty.get("primary_interval")
                        method = primary.get("method") if isinstance(primary, dict) else None
                        coverage_flag = None
                        if isinstance(coverage, dict):
                            if method and method in coverage:
                                coverage_flag = coverage.get(method)
                            else:
                                for value in coverage.values():
                                    if value is not None:
                                        coverage_flag = value
                                        break
                        if coverage_flag is not None:
                            try:
                                bucket["coverage"].append(bool(coverage_flag))
                            except Exception:
                                pass

                total_observations += 1

        if total_observations == 0:
            return {
                "status": "insufficient_data",
                "reason": "No successful estimator runs with comparable errors.",
            }

        def summarise(container: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
            summary: Dict[str, Any] = {}
            for key, bucket in container.items():
                count = bucket["count"]
                success = bucket["success"]
                errors = bucket["errors"]
                ci_widths = bucket["ci_widths"]
                coverage = bucket["coverage"]
                estimates = bucket["estimated_values"]
                true_values = bucket["true_values"]

                if count == 0:
                    continue

                summary[key] = {
                    "n": int(count),
                    "success_rate": float(success / count) if count else 0.0,
                    "mean_error": float(np.mean(errors)) if errors else None,
                    "median_error": float(np.median(errors)) if errors else None,
                    "std_error": float(np.std(errors)) if len(errors) > 1 else 0.0,
                    "mean_ci_width": float(np.mean(ci_widths)) if ci_widths else None,
                    "coverage_rate": float(np.mean(coverage)) if coverage else None,
                    "mean_estimated_h": float(np.mean(estimates)) if estimates else None,
                    "mean_true_h": float(np.mean(true_values)) if true_values else None,
                    "data_models": sorted(bucket["data_models"]),
                    "estimators": sorted(
                        est for est in bucket["estimators"] if est is not None
                    ),
                }
            return summary

        return {
            "status": "ok",
            "total_observations": int(total_observations),
            "hurst_bands": summarise(hurst_bands),
            "tail_classes": summarise(tail_classes),
            "data_length_bands": summarise(length_bands),
            "contamination": summarise(contamination_bands),
        }

    def _categorise_hurst_band(self, hurst_value: Optional[float]) -> str:
        """Assign H estimates to qualitative persistence bands."""
        if hurst_value is None or not np.isfinite(hurst_value):
            return "unknown"
        if hurst_value < 0.4:
            return "short-range (H≤0.40)"
        if hurst_value < 0.55:
            return "borderline (0.40<H≤0.55)"
        if hurst_value < 0.7:
            return "moderate persistence (0.55<H≤0.70)"
        if hurst_value < 0.85:
            return "persistent (0.70<H≤0.85)"
        return "ultra-persistent (H>0.85)"

    def _categorise_length_band(self, data_length: Optional[int]) -> str:
        """Bucket data length into interpretable regimes."""
        if data_length is None:
            return "unknown length"
        if data_length < 512:
            return "short (≤512)"
        if data_length < 2048:
            return "medium (513–2048)"
        if data_length < 8192:
            return "long (2049–8192)"
        return "ultra-long (>8192)"

    def _extract_scale_data(
        self, 
        result: Dict[str, Any], 
        estimator: Any
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Extract scale and statistics data from estimator result for diagnostics.
        
        Parameters
        ----------
        result : dict
            Estimator result dictionary
        estimator : BaseEstimator
            Estimator instance
            
        Returns
        -------
        tuple
            (scales, statistics) arrays or (None, None) if unavailable
        """
        # Try various common keys in result dict
        scale_keys = ["scales", "log_scales", "windows", "frequencies", "freq", "wavelet_scales"]
        stat_keys = ["statistics", "values", "log_values", "fluctuations", "psd", "power", "variance"]
        
        scales = None
        statistics = None
        
        # Try to extract from result dict
        for scale_key in scale_keys:
            if scale_key in result:
                scales = result[scale_key]
                if isinstance(scales, (list, np.ndarray)):
                    scales = np.asarray(scales, dtype=np.float64)
                    break
        
        for stat_key in stat_keys:
            if stat_key in result:
                statistics = result[stat_key]
                if isinstance(statistics, (list, np.ndarray)):
                    statistics = np.asarray(statistics, dtype=np.float64)
                    break
        
        # If still None, try nested structures
        if scales is None or statistics is None:
            scale_stats = result.get("scale_statistics")
            if isinstance(scale_stats, dict):
                scales = scale_stats.get("scales")
                statistics = scale_stats.get("statistics") or scale_stats.get("values")
        
        # Try calling estimator method if available
        if (scales is None or statistics is None) and hasattr(estimator, "get_scaling_diagnostics"):
            try:
                diag_data = estimator.get_scaling_diagnostics()
                if isinstance(diag_data, dict):
                    scales = diag_data.get("scales")
                    statistics = diag_data.get("statistics") or diag_data.get("values")
            except Exception:
                pass
        
        # Convert to numpy arrays if successful
        if scales is not None and statistics is not None:
            try:
                scales = np.asarray(scales, dtype=np.float64)
                statistics = np.asarray(statistics, dtype=np.float64)
                
                # Validate
                if len(scales) == len(statistics) and len(scales) > 0:
                    return scales, statistics
            except Exception:
                pass
        
        return None, None
    
    def _infer_estimator_family(self, estimator_name: str) -> str:
        """
        Infer the family (classical, ML, neural) from estimator name.
        
        Parameters
        ----------
        estimator_name : str
            Name of the estimator
            
        Returns
        -------
        str
            Estimator family
        """
        family_keywords = {
            "classical": ["GPH", "Whittle", "Periodogram", "DFA", "DMA", "R/S", "Higuchi",
                         "CWT", "WaveletVar", "WaveletLogVar", "WaveletWhittle",
                         "MFDFA", "WaveletLeaders"],
            "ML": ["RandomForest", "GradientBoosting", "SVR", "XGBoost", "LightGBM"],
            "neural": ["CNN", "LSTM", "GRU", "Transformer", "ResNet"]
        }
        
        for family, keywords in family_keywords.items():
            if any(kw in estimator_name for kw in keywords):
                return family
        
        return "other"
    
    def _infer_tail_class(
        self,
        model_name: Optional[str],
        data_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Infer a qualitative tail/heaviness class based on the data model."""
        if model_name is None:
            return "unknown"
        mapping = {
            "fBm": "gaussian",
            "fGn": "gaussian",
            "ARFIMAModel": "linear-LRD",
            "MRW": "multifractal-heavy-tail",
            "alphaStable": "alpha-stable",
            "neural_fsde": "neural-fSDE",
        }
        if model_name in mapping:
            return mapping[model_name]
        if isinstance(model_name, str) and model_name.lower().startswith("alpha"):
            return "alpha-stable"
        return "unknown"

    def _build_provenance_bundle(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construct a comprehensive provenance bundle using ProvenanceTracker.
        
        This bundle includes all settings needed to reproduce the experiment:
        - Data generation parameters
        - Estimator configuration
        - Preprocessing settings
        - Scale selection parameters
        - Analytics configuration
        - Environment information
        """
        estimator_listing = {
            category: [
                name
                for name, estimator in self.all_estimators.get(category, {}).items()
                if estimator is not None
            ]
            for category in self.all_estimators
        }
        
        # Use the new provenance tracker
        benchmark_metadata = {
            "timestamp": summary.get("timestamp"),
            "benchmark_type": summary.get("benchmark_type"),
            "data_length": summary.get("data_length"),
            "contamination_type": summary.get("contamination_type"),
            "contamination_level": summary.get("contamination_level"),
            "total_tests": summary.get("total_tests"),
            "successful_tests": summary.get("successful_tests"),
            "success_rate": summary.get("success_rate"),
            "data_models_tested": summary.get("data_models_tested"),
            "estimators_tested": summary.get("estimators_tested")
        }
        rng_snapshot = self.random_manager.snapshot()
        benchmark_metadata["random_state"] = {
            "global_seed": rng_snapshot.global_seed,
            "streams": rng_snapshot.child_seeds,
        }
        
        return self.provenance_tracker.capture_provenance(
            benchmark_metadata,
            estimator_listing
        )
    
    def _attach_uncertainty_calibration_summary(
        self, summary: Dict[str, Any], lookback_days: int = 90
    ) -> None:
        """Augment benchmark summaries with uncertainty calibration diagnostics."""
        analyzer = getattr(self, "error_analyzer", None)
        if analyzer is None:
            return

        summariser = getattr(analyzer, "summarise_uncertainty_calibration", None)
        if summariser is None:
            return

        try:
            calibration_records = summariser(days=lookback_days)
        except Exception:
            return

        if not calibration_records:
            return

        summary["uncertainty_calibration"] = calibration_records

        plotter = getattr(analyzer, "plot_uncertainty_calibration", None)
        if plotter is None:
            return

        figures_dir = self.output_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        plot_filename = (
            f"uncertainty_calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        plot_path = figures_dir / plot_filename

        try:
            generated_path = plotter(str(plot_path), days=lookback_days)
        except Exception:
            generated_path = None

        if generated_path:
            summary["uncertainty_calibration_plot"] = generated_path
    
    def _build_result_row_provenance(self, result: Dict[str, Any], data_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build provenance bundle for a single result row.
        
        This creates a lightweight provenance artifact per result that includes:
        - Experiment-level provenance (reference)
        - Row-specific parameters (data model, estimator, etc.)
        - Result metadata
        """
        return {
            "experiment_id": self.protocol_config.get("experiment_id"),
            "timestamp": result.get("timestamp") or datetime.now().isoformat(),
            "estimator": result.get("estimator"),
            "data_model": data_params.get("model_name"),
            "data_params": data_params,
            "preprocessing": result.get("preprocessing", {}),
            "estimated_hurst": result.get("estimated_hurst"),
            "true_hurst": result.get("true_hurst"),
            "error": result.get("error"),
            "robustness_panel": result.get("robustness_panel"),
            "uncertainty": result.get("uncertainty", {}),
            "protocol_version": self.protocol_config.get("version", "2.0"),
            "protocol_path": str(self.protocol_config_path),
        }

    def _record_uncertainty_event(
        self,
        estimator_name: str,
        data_model: Optional[str],
        uncertainty: Any,
        estimate: Optional[float],
        true_value: Optional[float],
        data_length: int,
        estimator_family: Optional[str],
    ) -> None:
        """Persist uncertainty calibration data via the error analyzer."""
        analyzer = getattr(self, "error_analyzer", None)
        if analyzer is None:
            return

        if not isinstance(uncertainty, dict):
            return

        coverage_data = uncertainty.get("coverage")
        if not isinstance(coverage_data, dict):
            coverage_data = {}

        primary_interval = uncertainty.get("primary_interval")
        if isinstance(primary_interval, dict):
            primary_method = primary_interval.get("method")
        else:
            primary_method = None

        method_entries = [
            ("block_bootstrap", uncertainty.get("block_bootstrap")),
            ("wavelet_bootstrap", uncertainty.get("wavelet_bootstrap")),
            ("parametric_monte_carlo", uncertainty.get("parametric_monte_carlo")),
        ]

        for method_name, method_summary in method_entries:
            if not isinstance(method_summary, dict):
                continue

            ci = method_summary.get("confidence_interval")
            if not (isinstance(ci, (list, tuple)) and len(ci) == 2):
                continue

            try:
                ci_lower = float(ci[0])
                ci_upper = float(ci[1])
            except (TypeError, ValueError):
                continue

            if not np.isfinite(ci_lower) or not np.isfinite(ci_upper):
                continue

            coverage_flag = coverage_data.get(method_name)
            if coverage_flag is None:
                for value in coverage_data.values():
                    if value is not None:
                        coverage_flag = value
                        break
            metadata: Dict[str, Any] = {
                "confidence_level": uncertainty.get("confidence_level"),
                "n_samples": method_summary.get("n_samples"),
                "status": method_summary.get("status"),
                "data_length": data_length,
                "estimator_family": estimator_family,
                "is_primary": method_name == primary_method,
                "method_metadata": method_summary.get("metadata"),
            }
            if estimate is not None and np.isfinite(estimate):
                metadata["central_estimate"] = float(estimate)
            if true_value is not None and np.isfinite(true_value):
                metadata["true_value"] = float(true_value)

            try:
                analyzer.record_uncertainty_calibration(
                    estimator_name=estimator_name,
                    data_model=data_model,
                    ci_lower=ci_lower,
                    ci_upper=ci_upper,
                    estimate=float(estimate) if estimate is not None else None,
                    true_value=float(true_value) if true_value is not None else None,
                    method=method_name,
                    coverage_flag=coverage_flag,
                    metadata=metadata,
                )
            except Exception:
                continue

    def run_comprehensive_benchmark(
        self,
        data_length: int = 1000,
        benchmark_type: str = "comprehensive",
        contamination_type: Optional[str] = None,
        contamination_level: float = 0.1,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Run comprehensive benchmark across all estimators and data models.

        Parameters
        ----------
        data_length : int
            Length of test data to generate
        benchmark_type : str
            Type of benchmark to run:
            - 'comprehensive': All estimators (default)
            - 'classical': Only classical statistical estimators
            - 'ML': Only machine learning estimators (non-neural)
            - 'neural': Only neural network estimators
        contamination_type : str, optional
            Type of contamination to apply to the data
        contamination_level : float
            Level/intensity of contamination (0.0 to 1.0)
        save_results : bool
            Whether to save results to file

        Returns
        -------
        dict
            Comprehensive benchmark results
        """
        print("🚀 Starting LRDBench Benchmark")
        print("=" * 60)
        print(f"Benchmark Type: {benchmark_type.upper()}")
        if contamination_type:
            print(f"Contamination: {contamination_type} (level: {contamination_level})")
        print("=" * 60)

        # Get estimators based on benchmark type
        estimators = self.get_estimators_by_type(benchmark_type, data_length)
        print(f"Testing {len(estimators)} estimators...")

        all_results = {}
        total_tests = 0
        successful_tests = 0

        # Test with different data models
        for model_name in self.data_models:
            print(f"\n📊 Testing with {model_name} data model...")

            try:
                # Generate clean data
                data, params = self.generate_test_data(
                    model_name, data_length=data_length
                )
                print(f"   Generated {len(data)} clean data points")

                # Apply contamination if specified
                if contamination_type:
                    data, contamination_info = self.apply_contamination(
                        data, contamination_type, contamination_level
                    )
                    print(
                        f"   Applied {contamination_type} contamination (level: {contamination_level})"
                    )
                    params["contamination"] = contamination_info

                model_results = []

                # Test all estimators
                for estimator_name in estimators:
                    print(f"   🔍 Testing {estimator_name}...", end=" ")

                    result = self.run_single_estimator_test(
                        estimator_name, data, params
                    )
                    model_results.append(result)

                    if result["success"]:
                        print("✅")
                        successful_tests += 1
                    else:
                        print(f"❌ ({result['error_message']})")

                    total_tests += 1

                all_results[model_name] = {
                    "data_params": params,
                    "estimator_results": model_results,
                }

            except Exception as e:
                print(f"   ❌ Error with {model_name}: {e}")
                all_results[model_name] = {
                    "data_params": None,
                    "estimator_results": [],
                    "error": str(e),
                }

        # Compile summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_type": benchmark_type,
            "contamination_type": contamination_type,
            "contamination_level": contamination_level,
            "data_length": data_length,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "data_models_tested": len(self.data_models),
            "estimators_tested": len(estimators),
            "results": all_results,
            "protocol_config": json.loads(json.dumps(self.protocol_config)),
            "protocol_path": str(self.protocol_config_path),
        }
        rng_snapshot = self.random_manager.snapshot()
        summary["random_state"] = {
            "global_seed": rng_snapshot.global_seed,
            "streams": rng_snapshot.child_seeds,
        }

        summary["stratified_metrics"] = self._compute_stratified_metrics(
            all_results,
            data_length=data_length,
            contamination_type=contamination_type,
            contamination_level=contamination_level,
        )
        summary["provenance"] = self._build_provenance_bundle(summary)

        # Compute statistical significance analysis
        significance_results = self._compute_significance_tests(all_results)
        summary["significance_analysis"] = significance_results

        # Attach uncertainty calibration diagnostics
        self._attach_uncertainty_calibration_summary(summary)

        # Save results if requested
        if save_results:
            self.save_results(summary)

        # Print summary
        self.print_summary(summary)

        return summary

    def run_classical_benchmark(
        self,
        data_length: int = 1000,
        contamination_type: Optional[str] = None,
        contamination_level: float = 0.1,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """Run benchmark with only classical statistical estimators."""
        return self.run_comprehensive_benchmark(
            data_length=data_length,
            benchmark_type="classical",
            contamination_type=contamination_type,
            contamination_level=contamination_level,
            save_results=save_results,
        )

    def run_ml_benchmark(
        self,
        data_length: int = 1000,
        contamination_type: Optional[str] = None,
        contamination_level: float = 0.1,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """Run benchmark with only machine learning estimators (non-neural)."""
        return self.run_comprehensive_benchmark(
            data_length=data_length,
            benchmark_type="ML",
            contamination_type=contamination_type,
            contamination_level=contamination_level,
            save_results=save_results,
        )

    def run_neural_benchmark(
        self,
        data_length: int = 1000,
        contamination_type: Optional[str] = None,
        contamination_level: float = 0.1,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """Run benchmark with only neural network estimators."""
        return self.run_comprehensive_benchmark(
            data_length=data_length,
            benchmark_type="neural",
            contamination_type=contamination_type,
            contamination_level=contamination_level,
            save_results=save_results,
        )

    def run_classical_estimators(
        self,
        data_models: Optional[list] = None,
        n_samples: int = 1000,
        n_trials: int = 10,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Backward-compatible alias for run_classical_benchmark.
        
        This method maintains the old API for compatibility with existing code.
        """
        # Old API used n_samples for data_length
        return self.run_classical_benchmark(
            data_length=n_samples,
            save_results=save_results,
        )

    def run_advanced_metrics_benchmark(
        self,
        data_length: int = 1000,
        benchmark_type: str = "comprehensive",
        n_monte_carlo: int = 100,
        convergence_threshold: float = 1e-6,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Run advanced metrics benchmark focusing on convergence and bias analysis.
        
        Parameters
        ----------
        data_length : int
            Length of test data to generate
        benchmark_type : str
            Type of benchmark to run
        n_monte_carlo : int
            Number of Monte Carlo simulations for bias analysis
        convergence_threshold : float
            Threshold for convergence detection
        save_results : bool
            Whether to save results to file
            
        Returns
        -------
        dict
            Advanced metrics benchmark results
        """
        print("🚀 Starting Advanced Metrics Benchmark")
        print("=" * 60)
        print(f"Benchmark Type: {benchmark_type.upper()}")
        print(f"Monte Carlo Simulations: {n_monte_carlo}")
        print(f"Convergence Threshold: {convergence_threshold}")
        print("=" * 60)
        
        # Get estimators
        estimators = self.get_estimators_by_type(benchmark_type, data_length)
        print(f"Testing {len(estimators)} estimators...")
        
        # Initialize advanced profiler
        advanced_profiler = AdvancedPerformanceProfiler(
            convergence_threshold=convergence_threshold,
            max_iterations=100
        )
        
        all_results = {}
        total_tests = 0
        successful_tests = 0
        
        # Test with different data models
        for model_name in self.data_models:
            print(f"\n📊 Testing with {model_name} data model...")
            
            try:
                # Generate clean data
                data, params = self.generate_test_data(model_name, data_length=data_length)
                print(f"   Generated {len(data)} clean data points")
                
                true_value = params.get("H", None)
                if true_value is None:
                    print(f"   ⚠️  No true H value available for {model_name}, skipping advanced metrics")
                    continue
                
                model_results = []
                
                # Test all estimators with advanced profiling
                for estimator_name in estimators:
                    print(f"   🔍 Testing {estimator_name}...", end=" ")
                    
                    estimator = estimators[estimator_name]
                    
                    # Run advanced performance profiling
                    profile_results = advanced_profiler.profile_estimator_performance(
                        estimator, data, true_value, n_monte_carlo
                    )
                    
                    # Extract key metrics
                    basic_perf = profile_results['basic_performance']
                    convergence_analysis = profile_results['convergence_analysis']
                    bias_analysis = profile_results['bias_analysis']
                    scaling_diagnostics = profile_results.get('scaling_diagnostics')
                    robustness_panel = profile_results.get('robustness_panel')
                    comprehensive_score = profile_results['comprehensive_score']
                    
                    if basic_perf['success']:
                        print("✅")
                        successful_tests += 1
                        
                        result = {
                            "estimator": estimator_name,
                            "success": True,
                            "execution_time": basic_perf['execution_time'],
                            "estimated_hurst": basic_perf['result'].get('hurst_parameter'),
                            "true_hurst": true_value,
                            "comprehensive_score": comprehensive_score,
                            "convergence_analysis": convergence_analysis,
                            "bias_analysis": bias_analysis,
                            "scaling_diagnostics": scaling_diagnostics,
                            "robustness_panel": robustness_panel,
                            "full_result": basic_perf['result']
                        }
                    else:
                        print(f"❌ ({basic_perf['error_message']})")
                        result = {
                            "estimator": estimator_name,
                            "success": False,
                            "execution_time": basic_perf['execution_time'],
                            "error_message": basic_perf['error_message'],
                            "comprehensive_score": 0.0,
                            "scaling_diagnostics": None,
                            "robustness_panel": None,
                        }
                    
                    model_results.append(result)
                    total_tests += 1
                
                all_results[model_name] = {
                    "data_params": params,
                    "estimator_results": model_results,
                }
                
            except Exception as e:
                print(f"   ❌ Error with {model_name}: {e}")
                all_results[model_name] = {
                    "data_params": None,
                    "estimator_results": [],
                    "error": str(e),
                }
        
        # Compile summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_type": f"advanced_{benchmark_type}",
            "n_monte_carlo": n_monte_carlo,
            "convergence_threshold": convergence_threshold,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "data_models_tested": len(self.data_models),
            "estimators_tested": len(estimators),
            "results": all_results,
        }
        
        # Save results if requested
        if save_results:
            self.save_advanced_results(summary)
        
        # Print advanced summary
        self.print_advanced_summary(summary)
        
        return summary

    def save_advanced_results(self, results: Dict[str, Any]) -> None:
        """Save advanced benchmark results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results as JSON
        json_file = self.output_dir / f"advanced_benchmark_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save summary as CSV
        csv_data = []
        for model_name, model_data in results["results"].items():
            if "estimator_results" in model_data:
                for est_result in model_data["estimator_results"]:
                    convergence_analysis = est_result.get("convergence_analysis", {})
                    bias_analysis = est_result.get("bias_analysis", {})
                    scaling_diagnostics = est_result.get("scaling_diagnostics", {}) or {}
                    robustness_panel = est_result.get("robustness_panel", {}) or {}
                    robustness_summary = robustness_panel.get("summary", {}) if isinstance(robustness_panel, dict) else {}
                    
                    csv_data.append({
                        "data_model": model_name,
                        "estimator": est_result["estimator"],
                        "success": est_result["success"],
                        "execution_time": est_result["execution_time"],
                        "estimated_hurst": est_result.get("estimated_hurst"),
                        "true_hurst": est_result.get("true_hurst"),
                        "comprehensive_score": est_result.get("comprehensive_score"),
                        # Convergence metrics
                        "convergence_rate": convergence_analysis.get("convergence_rate"),
                        "convergence_achieved": convergence_analysis.get("convergence_achieved"),
                        "convergence_iteration": convergence_analysis.get("convergence_iteration"),
                        "stability_metric": convergence_analysis.get("stability_metric"),
                        # Bias metrics
                        "mean_signed_error": bias_analysis.get("mean_signed_error"),
                        "mean_absolute_error": bias_analysis.get("mean_absolute_error"),
                        "root_mean_squared_error": bias_analysis.get("root_mean_squared_error"),
                        "bias_percentage": bias_analysis.get("bias_percentage"),
                        "significant_bias": bias_analysis.get("significant_bias"),
                        "t_statistic": bias_analysis.get("t_statistic"),
                        "p_value": bias_analysis.get("p_value"),
                        # Scaling diagnostics
                        "scaling_status": scaling_diagnostics.get("status"),
                        "scaling_slope": scaling_diagnostics.get("slope"),
                        "scaling_r_squared": scaling_diagnostics.get("r_squared"),
                        "scaling_std_err": scaling_diagnostics.get("std_err"),
                        "scaling_break_scale": (
                            scaling_diagnostics.get("breakpoint", {}).get("break_scale")
                            if isinstance(scaling_diagnostics.get("breakpoint"), dict)
                            else None
                        ),
                        "scaling_n_points": scaling_diagnostics.get("n_points"),
                        # Robustness panels
                        "robust_successful_scenarios": robustness_summary.get("successful_scenarios"),
                        "robust_n_scenarios": robustness_summary.get("n_scenarios"),
                        "robust_mean_abs_delta": robustness_summary.get("mean_abs_delta"),
                        "robust_max_abs_delta": robustness_summary.get("max_abs_delta"),
                    })
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_file = self.output_dir / f"advanced_benchmark_summary_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            print(f"\n💾 Advanced results saved to:")
            print(f"   JSON: {json_file}")
            print(f"   CSV: {csv_file}")

    def print_advanced_summary(self, summary: Dict[str, Any]) -> None:
        """Print advanced benchmark summary."""
        print("\n" + "=" * 60)
        print("📊 ADVANCED METRICS BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"Benchmark Type: {summary.get('benchmark_type', 'Unknown').upper()}")
        print(f"Monte Carlo Simulations: {summary['n_monte_carlo']}")
        print(f"Convergence Threshold: {summary['convergence_threshold']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Data Models: {summary['data_models_tested']}")
        print(f"Estimators: {summary['estimators_tested']}")
        
        # Show top performers by comprehensive score
        print("\n🏆 TOP PERFORMING ESTIMATORS (By Comprehensive Score):")
        
        # Aggregate results by estimator
        estimator_scores = {}
        
        for model_name, model_data in summary["results"].items():
            if "estimator_results" in model_data:
                for est_result in model_data["estimator_results"]:
                    if est_result["success"]:
                        estimator_name = est_result["estimator"]
                        score = est_result.get("comprehensive_score", 0.0)
                        
                        if estimator_name not in estimator_scores:
                            estimator_scores[estimator_name] = []
                        
                        estimator_scores[estimator_name].append(score)
        
        if estimator_scores:
            # Calculate average comprehensive score for each estimator
            avg_scores = []
            for estimator_name, scores in estimator_scores.items():
                avg_score = np.mean(scores)
                avg_scores.append({
                    "estimator": estimator_name,
                    "avg_comprehensive_score": avg_score,
                    "data_models_tested": len(scores)
                })
            
            # Sort by average comprehensive score (higher is better)
            avg_scores.sort(key=lambda x: x["avg_comprehensive_score"], reverse=True)
            
            for i, score_data in enumerate(avg_scores[:5]):
                print(f"   {i+1}. {score_data['estimator']}")
                print(f"      Comprehensive Score: {score_data['avg_comprehensive_score']:.4f}")
                print(f"      Data Models Tested: {score_data['data_models_tested']}")

        # Scaling diagnostics overview
        scaling_entries = []
        robustness_entries = []
        for model_data in summary["results"].values():
            if "estimator_results" not in model_data:
                continue
            for est_result in model_data["estimator_results"]:
                scaling_diag = est_result.get("scaling_diagnostics")
                if isinstance(scaling_diag, dict) and scaling_diag.get("status") == "ok":
                    scaling_entries.append(
                        (
                            est_result["estimator"],
                            scaling_diag.get("slope"),
                            scaling_diag.get("r_squared"),
                            scaling_diag.get("n_points"),
                        )
                    )
                robustness_panel = est_result.get("robustness_panel")
                if isinstance(robustness_panel, dict):
                    summary_info = robustness_panel.get("summary", {})
                    if summary_info:
                        robustness_entries.append(
                            (
                                est_result["estimator"],
                                summary_info.get("successful_scenarios"),
                                summary_info.get("n_scenarios"),
                                summary_info.get("mean_abs_delta"),
                                summary_info.get("max_abs_delta"),
                            )
                        )

        if scaling_entries:
            scaling_entries.sort(
                key=lambda item: (
                    item[2] is None,
                    -(item[2] or 0.0),
                )
            )
            print("\n🔬 SCALING DIAGNOSTICS SNAPSHOT:")
            for estimator, slope, r_squared, n_points in scaling_entries[:5]:
                slope_display = f"{slope:.4f}" if slope is not None else "n/a"
                r2_display = f"{r_squared:.3f}" if r_squared is not None else "n/a"
                print(
                    f"   {estimator}: slope={slope_display}, R²={r2_display}, points={n_points}"
                )

        if robustness_entries:
            robustness_entries.sort(
                key=lambda item: (
                    item[3] is None,
                    -(item[3] or 0.0),
                )
            )
            print("\n🛡️ ROBUSTNESS STRESS PANELS:")
            for estimator, success, total, mean_delta, max_delta in robustness_entries[:5]:
                success_display = f"{success}/{total}" if success is not None else "n/a"
                mean_display = f"{mean_delta:.4f}" if mean_delta is not None else "n/a"
                max_display = f"{max_delta:.4f}" if max_delta is not None else "n/a"
                print(
                    f"   {estimator}: success={success_display}, mean |ΔH|={mean_display}, max |ΔH|={max_display}"
                )

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save benchmark results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save detailed results as JSON
        json_file = self.output_dir / f"comprehensive_benchmark_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Save summary as CSV
        csv_data = []
        for model_name, model_data in results["results"].items():
            if "estimator_results" in model_data:
                for est_result in model_data["estimator_results"]:
                    # Extract advanced metrics
                    advanced_metrics = est_result.get("advanced_metrics", {})
                    uncertainty = est_result.get("uncertainty", {})
                    primary_interval = None
                    coverage_flag = None

                    if isinstance(uncertainty, dict):
                        primary_interval = uncertainty.get("primary_interval")
                        coverage_data = uncertainty.get("coverage", {})
                        if isinstance(primary_interval, dict):
                            method_name = primary_interval.get("method")
                        else:
                            method_name = None
                        if isinstance(coverage_data, dict):
                            if method_name and method_name in coverage_data:
                                coverage_flag = coverage_data.get(method_name)
                            else:
                                for value in coverage_data.values():
                                    if value is not None:
                                        coverage_flag = value
                                        break
                    else:
                        method_name = None

                    if isinstance(primary_interval, dict):
                        primary_ci = primary_interval.get("confidence_interval")
                        if primary_ci is not None and len(primary_ci) == 2:
                            ci_lower = float(primary_ci[0])
                            ci_upper = float(primary_ci[1])
                        else:
                            ci_lower = None
                            ci_upper = None
                        uncertainty_samples = primary_interval.get("n_samples")
                    else:
                        ci_lower = None
                        ci_upper = None
                        uncertainty_samples = None
                    
                    csv_data.append(
                        {
                            "data_model": model_name,
                            "estimator": est_result["estimator"],
                            "success": est_result["success"],
                            "execution_time": est_result["execution_time"],
                            "estimated_hurst": est_result["estimated_hurst"],
                            "true_hurst": est_result["true_hurst"],
                            "error": est_result["error"],
                            "r_squared": est_result["r_squared"],
                            "p_value": est_result["p_value"],
                            "intercept": est_result["intercept"],
                            "slope": est_result["slope"],
                            "std_error": est_result["std_error"],
                            # Advanced metrics
                            "convergence_rate": advanced_metrics.get("convergence_rate"),
                            "convergence_achieved": advanced_metrics.get("convergence_achieved"),
                            "stability_metric": advanced_metrics.get("stability_metric"),
                            "mean_signed_error": advanced_metrics.get("mean_signed_error"),
                            "bias_percentage": advanced_metrics.get("bias_percentage"),
                            "significant_bias": advanced_metrics.get("significant_bias"),
                            "ci_lower": ci_lower,
                            "ci_upper": ci_upper,
                            "uncertainty_method": method_name,
                            "uncertainty_samples": uncertainty_samples,
                            "uncertainty_status": uncertainty.get("status") if isinstance(uncertainty, dict) else None,
                            "coverage_primary": coverage_flag,
                        }
                    )

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_file = self.output_dir / f"benchmark_summary_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            print(f"\n💾 Results saved to:")
            print(f"   JSON: {json_file}")
            print(f"   CSV: {csv_file}")
        else:
            print(f"\n💾 Results saved to:")
            print(f"   JSON: {json_file}")

        stratified_metrics = results.get("stratified_metrics")
        if isinstance(stratified_metrics, dict):
            stratified_file = self.output_dir / f"stratified_metrics_{timestamp}.json"
            with open(stratified_file, "w") as f:
                json.dump(stratified_metrics, f, indent=2, default=str)
            print(f"   Stratified: {stratified_file}")
        
        # Generate enhanced stratified reports
        try:
            stratified_report = self.stratified_report_generator.generate_report(
                results,
                output_dir=self.output_dir,
                formats=['markdown', 'json', 'csv']
            )
            print(f"   Enhanced stratified reports generated")
        except Exception as exc:
            warnings.warn(f"Enhanced stratified report generation failed: {exc}")

        provenance = results.get("provenance")
        if provenance:
            provenance_file = self.output_dir / f"benchmark_provenance_{timestamp}.json"
            with open(provenance_file, "w") as f:
                json.dump(provenance, f, indent=2, default=str)
            print(f"   Provenance: {provenance_file}")

        calibration_records = results.get("uncertainty_calibration")
        if calibration_records:
            calibration_dir = self.output_dir / "calibration"
            calibration_dir.mkdir(parents=True, exist_ok=True)
            calibration_file = calibration_dir / f"uncertainty_calibration_{timestamp}.json"
            with open(calibration_file, "w") as f:
                json.dump(calibration_records, f, indent=2, default=str)
            print(f"   Calibration: {calibration_file}")

        calibration_plot = results.get("uncertainty_calibration_plot")
        if calibration_plot:
            print(f"   Calibration plot: {calibration_plot}")

    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print benchmark summary."""
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"Benchmark Type: {summary.get('benchmark_type', 'Unknown').upper()}")
        if summary.get("contamination_type"):
            print(
                f"Contamination: {summary['contamination_type']} (level: {summary['contamination_level']})"
            )
        protocol_info = summary.get("protocol_config", {})
        protocol_version = protocol_info.get("version", "unknown")
        print(
            f"Protocol Config: {summary.get('protocol_path', 'config/benchmark_protocol.yaml')} "
            f"(version {protocol_version})"
        )
        preprocessing_cfg = protocol_info.get("preprocessing", {})
        print(
            f"Preprocessing settings: winsorize={preprocessing_cfg.get('winsorize_limits')} | "
            f"outlier_threshold={preprocessing_cfg.get('outlier_threshold')}"
        )
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Data Models: {summary['data_models_tested']}")
        print(f"Estimators: {summary['estimators_tested']}")

        # Show top performers (aggregated by estimator across all data models)
        print("\n🏆 TOP PERFORMING ESTIMATORS (Average across all data models):")

        # Aggregate results by estimator
        estimator_performance = {}

        for model_name, model_data in summary["results"].items():
            if "estimator_results" in model_data:
                for est_result in model_data["estimator_results"]:
                    if est_result["success"] and est_result["error"] is not None:
                        estimator_name = est_result["estimator"]

                        if estimator_name not in estimator_performance:
                            estimator_performance[estimator_name] = {
                                "errors": [],
                                "execution_times": [],
                                "data_models": [],
                                "convergence_rates": [],
                                "mean_signed_errors": [],
                                "bias_percentages": [],
                                "stability_metrics": [],
                                "ci_widths": [],
                                "coverage_flags": [],
                            }

                        estimator_performance[estimator_name]["errors"].append(
                            est_result["error"]
                        )
                        estimator_performance[estimator_name]["execution_times"].append(
                            est_result["execution_time"]
                        )
                        estimator_performance[estimator_name]["data_models"].append(
                            model_name
                        )
                        
                        # Add advanced metrics
                        advanced_metrics = est_result.get("advanced_metrics", {})
                        if advanced_metrics.get("convergence_rate") is not None:
                            estimator_performance[estimator_name]["convergence_rates"].append(
                                advanced_metrics["convergence_rate"]
                            )
                        if advanced_metrics.get("mean_signed_error") is not None:
                            estimator_performance[estimator_name]["mean_signed_errors"].append(
                                advanced_metrics["mean_signed_error"]
                            )
                        if advanced_metrics.get("bias_percentage") is not None:
                            estimator_performance[estimator_name]["bias_percentages"].append(
                                advanced_metrics["bias_percentage"]
                            )
                        if advanced_metrics.get("stability_metric") is not None:
                            estimator_performance[estimator_name]["stability_metrics"].append(
                                advanced_metrics["stability_metric"]
                            )

                        # Confidence interval statistics
                        ci = est_result.get("confidence_interval")
                        if (
                            isinstance(ci, (list, tuple))
                            and len(ci) == 2
                            and ci[0] is not None
                            and ci[1] is not None
                        ):
                            try:
                                width = float(ci[1]) - float(ci[0])
                                if np.isfinite(width):
                                    estimator_performance[estimator_name]["ci_widths"].append(width)
                            except (TypeError, ValueError):
                                pass

                        uncertainty = est_result.get("uncertainty", {})
                        if isinstance(uncertainty, dict):
                            coverage_data = uncertainty.get("coverage", {})
                            primary = uncertainty.get("primary_interval")
                            method = (
                                primary.get("method")
                                if isinstance(primary, dict)
                                else None
                            )
                            coverage_flag = None
                            if isinstance(coverage_data, dict):
                                if method and method in coverage_data:
                                    coverage_flag = coverage_data.get(method)
                                else:
                                    for value in coverage_data.values():
                                        if value is not None:
                                            coverage_flag = value
                                            break
                            if coverage_flag is not None:
                                estimator_performance[estimator_name]["coverage_flags"].append(
                                    bool(coverage_flag)
                                )

        if estimator_performance:
            # Calculate average performance for each estimator
            aggregated_performance = []
            for estimator_name, perf_data in estimator_performance.items():
                avg_error = np.mean(perf_data["errors"])
                avg_time = np.mean(perf_data["execution_times"])
                data_models_tested = len(perf_data["data_models"])

                # Calculate advanced metrics averages
                avg_convergence_rate = np.mean(perf_data["convergence_rates"]) if perf_data["convergence_rates"] else None
                avg_mean_signed_error = np.mean(perf_data["mean_signed_errors"]) if perf_data["mean_signed_errors"] else None
                avg_bias_percentage = np.mean(perf_data["bias_percentages"]) if perf_data["bias_percentages"] else None
                avg_stability_metric = np.mean(perf_data["stability_metrics"]) if perf_data["stability_metrics"] else None
                avg_ci_width = np.mean(perf_data["ci_widths"]) if perf_data["ci_widths"] else None
                coverage_rate = np.mean(perf_data["coverage_flags"]) if perf_data["coverage_flags"] else None

                aggregated_performance.append(
                    {
                        "estimator": estimator_name,
                        "avg_error": avg_error,
                        "avg_time": avg_time,
                        "data_models_tested": data_models_tested,
                        "min_error": min(perf_data["errors"]),
                        "max_error": max(perf_data["errors"]),
                        "avg_convergence_rate": avg_convergence_rate,
                        "avg_mean_signed_error": avg_mean_signed_error,
                        "avg_bias_percentage": avg_bias_percentage,
                        "avg_stability_metric": avg_stability_metric,
                        "avg_ci_width": avg_ci_width,
                        "coverage_rate": coverage_rate,
                    }
                )

            # Sort by average error (lower is better)
            aggregated_performance.sort(key=lambda x: x["avg_error"])

            for i, perf in enumerate(aggregated_performance[:5]):
                print(f"   {i+1}. {perf['estimator']}")
                print(
                    f"      Avg Error: {perf['avg_error']:.4f} (Range: {perf['min_error']:.4f}-{perf['max_error']:.4f})"
                )
                print(
                    f"      Avg Time: {perf['avg_time']:.3f}s | Data Models: {perf['data_models_tested']}"
                )
                
                # Display advanced metrics
                if perf['avg_convergence_rate'] is not None:
                    print(f"      Convergence Rate: {perf['avg_convergence_rate']:.4f}")
                if perf['avg_mean_signed_error'] is not None:
                    print(f"      Mean Signed Error: {perf['avg_mean_signed_error']:.4f}")
                if perf['avg_bias_percentage'] is not None:
                    print(f"      Bias: {perf['avg_bias_percentage']:.2f}%")
                if perf['avg_stability_metric'] is not None:
                    print(f"      Stability: {perf['avg_stability_metric']:.4f}")
                if perf['avg_ci_width'] is not None:
                    print(f"      Mean 95% CI width: {perf['avg_ci_width']:.4f}")
                if perf['coverage_rate'] is not None:
                    print(f"      Empirical coverage: {perf['coverage_rate']:.2%}")

                # Show estimated H values for this estimator across data models
                estimator_name = perf["estimator"]
                print(f"      Estimated H values:")
                for model_name, model_data in summary["results"].items():
                    if "estimator_results" in model_data:
                        for est_result in model_data["estimator_results"]:
                            if (
                                est_result["estimator"] == estimator_name
                                and est_result["success"]
                            ):
                                true_h = est_result["true_hurst"]
                                est_h = est_result["estimated_hurst"]
                                if est_h is not None:
                                    print(
                                        f"        {model_name}: H_est={est_h:.4f}, H_true={true_h:.4f}"
                                    )
                print()

        stratified = summary.get("stratified_metrics", {})
        if stratified:
            print("\n🔍 STRATIFIED INSIGHTS:")
            status = stratified.get("status", "unavailable")
            print(f"Status: {status}")
            if status == "ok":
                def _print_band(label: str, data: Dict[str, Any]) -> None:
                    if not data:
                        return
                    print(f"\n   {label}:")
                    sorted_items = sorted(
                        data.items(), key=lambda kv: (kv[1].get("mean_error") is None, kv[1].get("mean_error", 0.0))
                    )
                    for band, metrics in sorted_items:
                        mean_error = metrics.get("mean_error")
                        coverage_rate = metrics.get("coverage_rate")
                        success_rate = metrics.get("success_rate")
                        print(f"      • {band}:")
                        if mean_error is not None:
                            print(f"        mean error={mean_error:.4f}")
                        if coverage_rate is not None:
                            print(f"        coverage={coverage_rate:.2%}")
                        if success_rate is not None:
                            print(f"        success={success_rate:.2%}")
                        mean_ci = metrics.get("mean_ci_width")
                        if mean_ci is not None:
                            print(f"        mean CI width={mean_ci:.4f}")
                        data_models = metrics.get("data_models") or []
                        if data_models:
                            print(f"        data models: {', '.join(data_models)}")
                _print_band("Hurst regimes", stratified.get("hurst_bands", {}))
                _print_band("Tail classes", stratified.get("tail_classes", {}))
                _print_band("Length regimes", stratified.get("data_length_bands", {}))
                _print_band("Contamination regimes", stratified.get("contamination", {}))
            else:
                print(stratified.get("reason", "No stratified analysis available."))

        significance = summary.get("significance_analysis", {})
        if significance:
            print("\n🧪 SIGNIFICANCE ANALYSIS:")
            status = significance.get("status", "unavailable")
            print(f"Status: {status}")
            if status == "ok":
                friedman = significance.get("friedman", {})
                friedman_stat = friedman.get("statistic")
                friedman_p = friedman.get("p_value")
                if friedman_stat is not None and friedman_p is not None:
                    print(
                        f"Friedman χ²={friedman_stat:.4f} "
                        f"(p={friedman_p:.4f}) "
                        f"across {friedman.get('n_data_models', 0)} data models "
                        f"and {friedman.get('n_estimators', 0)} estimators"
                    )
                else:
                    reason = friedman.get("error", "Friedman test not available.")
                    print(
                        f"Friedman test unavailable: {reason} "
                        f"(considered {friedman.get('n_data_models', 0)} data models, "
                        f"{friedman.get('n_estimators', 0)} estimators)"
                    )
                print("Mean ranks (lower is better):")
                for estimator, rank in significance.get("mean_ranks", {}).items():
                    print(f"   {estimator}: {rank:.3f}")

                significant_pairs = [
                    res
                    for res in significance.get("post_hoc", [])
                    if res.get("significant")
                ]
                if significant_pairs:
                    print("Significant pairwise differences after Holm correction:")
                    for res in significant_pairs:
                        pair = res.get("pair", [])
                        print(
                            f"   {pair[0]} vs {pair[1]}: "
                            f"p={res.get('p_value'):.4f}, "
                            f"Holm-adjusted p={res.get('holm_p_value'):.4f}"
                        )
                else:
                    print("No pairwise differences remained significant after Holm correction.")
            else:
                reason = significance.get("reason", "insufficient data")
                print(f"Significance testing not performed: {reason}")

        calibration = summary.get("uncertainty_calibration")
        if isinstance(calibration, list) and calibration:
            print("\n🎯 UNCERTAINTY CALIBRATION:")
            method_stats: Dict[str, Dict[str, float]] = {}
            family_stats: Dict[str, Dict[str, float]] = {}
            for entry in calibration:
                coverage = entry.get("empirical_coverage")
                n = entry.get("n")
                if coverage is None or n in (None, 0):
                    continue
                method = entry.get("method") or "unknown"
                family = entry.get("estimator_family") or "unspecified"
                method_bucket = method_stats.setdefault(method, {"weighted": 0.0, "total": 0.0})
                method_bucket["weighted"] += float(coverage) * float(n)
                method_bucket["total"] += float(n)
                family_bucket = family_stats.setdefault(family, {"weighted": 0.0, "total": 0.0})
                family_bucket["weighted"] += float(coverage) * float(n)
                family_bucket["total"] += float(n)

            if method_stats:
                print("   Method-level empirical coverage:")
                for method, stats in sorted(method_stats.items(), key=lambda kv: kv[0]):
                    if stats["total"] > 0:
                        rate = stats["weighted"] / stats["total"]
                        print(f"      • {method}: {rate:.2%} across {int(stats['total'])} runs")

            if family_stats:
                print("   Family-level coverage (all methods combined):")
                for family, stats in sorted(family_stats.items(), key=lambda kv: kv[0]):
                    if stats["total"] > 0:
                        rate = stats["weighted"] / stats["total"]
                        print(f"      • {family}: {rate:.2%} across {int(stats['total'])} runs")

            calibration_plot = summary.get("uncertainty_calibration_plot")
            if calibration_plot:
                print(f"   Calibration plot: {calibration_plot}")

        # Show detailed breakdown by data model
        print("\n📊 DETAILED PERFORMANCE BY DATA MODEL:")
        for model_name, model_data in summary["results"].items():
            if "estimator_results" in model_data and model_data["estimator_results"]:
                print(f"\n   {model_name}:")
                successful_results = [
                    r
                    for r in model_data["estimator_results"]
                    if r["success"] and r["error"] is not None
                ]
                if successful_results:
                    # Sort by error for this data model
                    successful_results.sort(key=lambda x: x["error"])
                    for i, result in enumerate(
                        successful_results[:3]
                    ):  # Top 3 for each model
                        print(
                            f"     {i+1}. {result['estimator']}: Error {result['error']:.4f}, Time {result['execution_time']:.3f}s"
                        )
                else:
                    print("     No successful estimators")

        print("\n🎯 Benchmark completed successfully!")

    def export_results(self, results: Dict[str, Any], output_path: str) -> None:
        """
        Export benchmark results to a file.
        
        Parameters
        ----------
        results : dict
            Benchmark results dictionary
        output_path : str
            Path to save the results (JSON format)
        """
        import json
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results exported to: {output_file}")


def main():
    """
    Main function for running comprehensive benchmarks.
    This serves as the entry point for the lrdbench command.
    """
    print("🚀 LRDBench - Comprehensive Benchmark System")
    print("=" * 50)

    # Initialize benchmark system
    benchmark = ComprehensiveBenchmark()

    # Run comprehensive benchmark (default)
    print("\n📊 Running COMPREHENSIVE benchmark (all estimators)...")
    results = benchmark.run_comprehensive_benchmark(
        data_length=1000, benchmark_type="comprehensive", save_results=True
    )

    print(f"\n✅ Benchmark completed with {results['success_rate']:.1%} success rate!")
    print("\n💡 Available benchmark types:")
    print("   - 'comprehensive': All estimators (default)")
    print("   - 'classical': Only classical statistical estimators")
    print("   - 'ML': Only machine learning estimators (non-neural)")
    print("   - 'neural': Only neural network estimators")
    print("\n💡 Available contamination types:")
    print("   - 'additive_gaussian': Add Gaussian noise")
    print("   - 'multiplicative_noise': Multiplicative noise")
    print("   - 'outliers': Add outliers")
    print("   - 'trend': Add trend")
    print("   - 'seasonal': Add seasonal patterns")
    print("   - 'missing_data': Remove data points")
    print("\n   Use the ComprehensiveBenchmark class in your own code:")
    print("   from analysis.benchmark import ComprehensiveBenchmark")
    print("   benchmark = ComprehensiveBenchmark()")
    print("   results = benchmark.run_comprehensive_benchmark(")
    print("       benchmark_type='classical',  # or 'ML', 'neural'")
    print("       contamination_type='additive_gaussian',  # optional")
    print("       contamination_level=0.2  # 0.0 to 1.0")
    print("   )")


if __name__ == "__main__":
    main()
