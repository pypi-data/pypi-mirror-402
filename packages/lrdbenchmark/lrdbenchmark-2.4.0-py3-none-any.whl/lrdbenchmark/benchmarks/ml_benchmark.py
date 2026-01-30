
from typing import List, Dict, Any, Optional
from .base import BaseBenchmark
import warnings

try:
    from ..models.pretrained_models.ml_pretrained import (
        RandomForestPretrainedModel,
        SVREstimatorPretrainedModel,
        GradientBoostingPretrainedModel,
    )
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    warnings.warn("ML pretrained models not available.")

class MLBenchmark(BaseBenchmark):
    """
    Benchmark for Machine Learning estimators (RF, SVR, GB).
    """
    
    def __init__(self, output_dir: Optional[str] = None, seed: Optional[int] = None):
        super().__init__("MLBenchmark", output_dir, seed)
        self.estimators = self._initialize_estimators()
        
    def _initialize_estimators(self):
        if not ML_AVAILABLE:
            return {}
            
        return {
            "RandomForest": RandomForestPretrainedModel(),
            "SVR": SVREstimatorPretrainedModel(),
            "GradientBoosting": GradientBoostingPretrainedModel()
        }
        
    def run(
        self, 
        models: List[str] = ['fbm', 'fgn'],
        lengths: List[int] = [512, 1024],
        num_realizations: int = 10,
        params: Dict[str, Any] = {'H': 0.7}
    ):
        if not self.estimators:
            print("No ML estimators available. Skipping.")
            return []
            
        print(f"Starting MLBenchmark: ~{len(models)*len(lengths)*num_realizations*len(self.estimators)} evaluations.")
        
        for model_name in models:
            for n in lengths:
                for i in range(num_realizations):
                    gen_result = self.generator.generate(
                        model=model_name,
                        length=n,
                        params=params,
                        preprocess=True
                    )
                    data = gen_result['signal']
                    meta = gen_result['metadata']
                    true_params = meta['true_params']
                    
                    for est_name, estimator in self.estimators.items():
                        res = self._evaluate_estimator(estimator, data, true_params)
                         
                        record = {
                            'benchmark_type': 'ML',
                            'model': model_name,
                            'length': n,
                            'realization': i,
                            'estimator': est_name,
                            **res,
                            **{f"param_{k}": v for k, v in true_params.items()}
                        }
                        self.results.append(record)
                        
        self.save_results()
        return self.results
