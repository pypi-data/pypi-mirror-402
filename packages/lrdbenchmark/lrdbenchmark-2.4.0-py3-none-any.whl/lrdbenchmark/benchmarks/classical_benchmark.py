
from typing import List, Dict, Any, Optional
import numpy as np

from .base import BaseBenchmark
from ..analysis.temporal.rs_estimator import RSEstimator
from ..analysis.temporal.dfa_estimator import DFAEstimator
from ..analysis.temporal.dma_estimator import DMAEstimator
from ..analysis.temporal.higuchi_estimator import HiguchiEstimator
from ..analysis.temporal.ghe_estimator import GHEEstimator

from ..analysis.spectral.gph_estimator import GPHEstimator
from ..analysis.spectral.periodogram_estimator import PeriodogramEstimator
from ..analysis.spectral.whittle_estimator import WhittleEstimator

from ..analysis.wavelet.cwt_estimator import CWTEstimator
from ..analysis.wavelet.variance_estimator import WaveletVarianceEstimator
from ..analysis.wavelet.log_variance_estimator import WaveletLogVarianceEstimator

from ..analysis.multifractal.mfdfa_estimator import MFDFAEstimator

class ClassicalBenchmark(BaseBenchmark):
    """
    Benchmark for classical statistical estimators (Temporal, Spectral, Wavelet, Multifractal).
    """
    
    def __init__(self, output_dir: Optional[str] = None, seed: Optional[int] = None):
        super().__init__("ClassicalBenchmark", output_dir, seed)
        self.estimators = self._initialize_estimators()
        
    def _initialize_estimators(self):
        return {
            # Temporal
            "RS": RSEstimator(),
            "DFA": DFAEstimator(),
            "DMA": DMAEstimator(),
            "Higuchi": HiguchiEstimator(),
            "GHE": GHEEstimator(),
            # Spectral
            "GPH": GPHEstimator(),
            "Periodogram": PeriodogramEstimator(),
            "Whittle": WhittleEstimator(),
            # Wavelet
            "CWT": CWTEstimator(),
            "WaveletVar": WaveletVarianceEstimator(),
            "WaveletLogVar": WaveletLogVarianceEstimator(),
            # Multifractal (estimating H from H(2) or scaling)
            "MFDFA": MFDFAEstimator()
        }
        
    def run(
        self, 
        models: List[str] = ['fbm', 'fgn'],
        lengths: List[int] = [512, 1024],
        num_realizations: int = 10,
        params: Dict[str, Any] = {'H': 0.7}
    ):
        """
        Run the classical benchmark.
        
        Iterates over models, lengths, realizations, and estimators.
        """
        total_runs = len(models) * len(lengths) * num_realizations * len(self.estimators)
        print(f"Starting ClassicalBenchmark: ~{total_runs} evaluations.")
        
        for model_name in models:
            for n in lengths:
                for i in range(num_realizations):
                    # Generate data
                    gen_result = self.generator.generate(
                        model=model_name,
                        length=n,
                        params=params,
                        preprocess=True # Always preprocess for classical? Or configurable.
                    )
                    data = gen_result['signal']
                    meta = gen_result['metadata']
                    true_params = meta['true_params']
                    
                    # Run all estimators
                    for est_name, estimator in self.estimators.items():
                        res = self._evaluate_estimator(estimator, data, true_params)
                        
                        # Pack result
                        record = {
                            'benchmark_type': 'Classical',
                            'model': model_name,
                            'length': n,
                            'realization': i,
                            'estimator': est_name,
                            **res,
                            # Flattent params for CSV
                            **{f"param_{k}": v for k, v in true_params.items()}
                        }
                        self.results.append(record)
                        
        self.save_results()
        return self.results
