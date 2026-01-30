
import numpy as np
from typing import Dict, Any, Optional, Tuple, Union, List

from ..models.data_models.fbm_model import FractionalBrownianMotion
from ..models.data_models.fgn_model import FractionalGaussianNoise
from ..models.data_models.arfima_model import ARFIMAModel
from ..models.data_models.mrw_model import MultifractalRandomWalk
from ..models.contamination.contamination_factory import ContaminationFactory, ConfoundingScenario
from ..robustness.adaptive_preprocessor import AdaptiveDataPreprocessor

class TimeSeriesGenerator:
    """
    Unified Time Series Generator for LRD Benchmark.
    
    This class handles the end-to-end generation process:
    1. Base signal generation (FBM, FGN, ARFIMA, MRW)
    2. Contamination application (Noise, Trends, Artifacts)
    3. Preprocessing (Detrending, Winsorizing, Normalization) -- "Baked In"
    """
    
    def __init__(self, random_state: Optional[int] = None):
        """
        Initialize the generator.
        
        Parameters
        ----------
        random_state : int, optional
            Global random seed.
        """
        self.rng = np.random.default_rng(random_state)
        self.contamination_factory = ContaminationFactory()
        
        # Default preprocessor configuration
        self.preprocessor = AdaptiveDataPreprocessor(
            outlier_threshold=3.0,
            winsorize_limits=(0.01, 0.99),
            # Defaults; can be overridden in preprocess method
            enable_winsorize=True,
            enable_detrend=True 
        )
        
        self.supported_models = {
            'fbm': FractionalBrownianMotion,
            'fgn': FractionalGaussianNoise,
            'arfima': ARFIMAModel,
            'mrw': MultifractalRandomWalk
        }

    def generate(
        self,
        model: str,
        length: int,
        params: Dict[str, Any],
        contamination: Optional[List[Dict[str, Any]]] = None,
        preprocess: bool = True,
        preprocess_params: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a processed time series.

        Parameters
        ----------
        model : str
            Model name ('fbm', 'fgn', 'arfima', 'mrw'). Case-insensitive.
        length : int
            Length of the time series.
        params : dict
            Parameters for the model (e.g., {'H': 0.7}).
        contamination : list of dicts, optional
            List of contamination specs to apply sequentially.
            Each dict should have:
                - 'scenario': ConfoundingScenario enum or str name
                - 'intensity': float (0.0 to 1.0)
                - 'params': dict (scenario-specific parameters)
        preprocess : bool, default=True
            Whether to apply the baked-in preprocessing pipeline.
        preprocess_params : dict, optional
            Overrides for preprocessing configuration (e.g. {'enable_detrend': False}).
        seed : int, optional
            Specific seed for this generation.

        Returns
        -------
        dict
            Result dictionary containing:
            - 'signal': The final processed numpy array
            - 'clean_signal': The clean signal before contamination
            - 'contaminated_signal': Signal after contamination but before preprocessing
            - 'metadata': Full generation metadata (true params, contamination info, preprocessing info)
        """
        local_rng = np.random.default_rng(seed) if seed is not None else self.rng
        
        # 1. Base Signal Generation
        model_key = model.lower()
        if model_key not in self.supported_models:
            raise ValueError(f"Unknown model '{model}'. Supported: {list(self.supported_models.keys())}")
            
        model_cls = self.supported_models[model_key]
        # We need to instantiate the model with params
        # Note: Some models take params in __init__, others might use different structures.
        # Assuming standard __init__(**kwargs) structure from our refactoring.
        base_model = model_cls(**params)
        
        # Generate clean signal
        # Pass seed to generate if supported, or rely on internal RNG handling
        # Our updated models accept 'rng' or 'seed'.
        # For reproducibility, we pass a seed derived from local_rng
        gen_seed = local_rng.integers(0, 2**32)
        clean_signal = base_model.generate(length=length, seed=gen_seed)
        
        current_signal = clean_signal.copy()
        contamination_meta = []
        
        # 2. Sequential Contamination
        if contamination:
            for c_spec in contamination:
                scenario_input = c_spec.get('scenario')
                intensity = c_spec.get('intensity', 0.1)
                c_params = c_spec.get('params', {})
                
                # Resolve scenario enum if string provided
                scenario = scenario_input
                if isinstance(scenario_input, str):
                    try:
                        # Try to find in ConfoundingScenario
                        # Assuming ConfoundingScenario keys are UPPERCASE
                        scenario = getattr(ConfoundingScenario, scenario_input.upper())
                    except AttributeError:
                        # Or maybe it's passed as full value?
                        pass
                
                # Apply contamination
                # ContaminationFactory.apply_confounding returns (contaminated_data, description)
                current_signal, desc = self.contamination_factory.apply_confounding(
                    current_signal,
                    scenario,
                    intensity=intensity,
                    **c_params
                )
                
                contamination_meta.append({
                    'scenario': str(scenario),
                    'intensity': intensity,
                    'description': desc,
                    'params': c_params
                })
        
        contaminated_signal = current_signal.copy()
        
        # 3. Preprocessing (The "Bake-in")
        preprocess_meta = {'applied': False}
        if preprocess:
            # Apply overrides if any
            pp_config = preprocess_params or {}
            
            # Since AdaptiveDataPreprocessor is configured in __init__, we might need to 
            # re-configure it or just modify its behavior for this run.
            # Its 'preprocess' method doesn't take config args generally, it uses self state.
            # But we can create a temporary instance or update parameters if methods allow.
            # Looking at engine.py usage, it seems instantiated once.
            # Ideally AdaptiveDataPreprocessor.preprocess() takes data.
            # If we want to override 'detrend', we should probably construct a new one or modify the existing one.
            # For simplicity/speed, let's construct a lightweight one if overrides exist, or use default.
            
            if pp_config:
                temp_preprocessor = AdaptiveDataPreprocessor(
                    outlier_threshold=pp_config.get('outlier_threshold', 3.0),
                    winsorize_limits=pp_config.get('winsorize_limits', (0.01, 0.99)),
                    enable_winsorize=pp_config.get('enable_winsorize', True),
                    enable_detrend=pp_config.get('enable_detrend', True)
                )
                final_signal, pp_meta = temp_preprocessor.preprocess(current_signal)
            else:
                final_signal, pp_meta = self.preprocessor.preprocess(current_signal)
                
            preprocess_meta = pp_meta
            preprocess_meta['applied'] = True
        else:
            final_signal = current_signal
            
        return {
            'signal': final_signal,
            'clean_signal': clean_signal,
            'contaminated_signal': contaminated_signal,
            'metadata': {
                'model': model_key,
                'true_params': params,
                'length': length,
                'contamination': contamination_meta,
                'preprocessing': preprocess_meta,
                'seed': gen_seed # The seed used for generation
            }
        }
