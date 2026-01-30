
from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseBenchmark
from .classical_benchmark import ClassicalBenchmark
from .ml_benchmark import MLBenchmark
from .nn_benchmark import NNBenchmark

class ComprehensiveBenchmark(BaseBenchmark):
    """
    Unified interface running Classical, ML, and NN benchmarks.
    """
    
    def __init__(self, output_dir: Optional[str] = None, seed: Optional[int] = None):
        super().__init__("ComprehensiveBenchmark", output_dir, seed)
        self.classical = ClassicalBenchmark(output_dir, seed=seed)
        self.ml = MLBenchmark(output_dir, seed=seed)
        self.nn = NNBenchmark(output_dir, seed=seed)
        
    def run(
        self, 
        models: List[str] = ['fbm', 'fgn'],
        lengths: List[int] = [512, 1024],
        num_realizations: int = 10,
        params: Dict[str, Any] = {'H': 0.7},
        run_classical: bool = True,
        run_ml: bool = True,
        run_nn: bool = True
    ):
        """
        Run selected benchmarks.
        """
        all_results = []
        
        if run_classical:
            res = self.classical.run(models, lengths, num_realizations, params)
            all_results.extend(res)
            
        if run_ml:
            res = self.ml.run(models, lengths, num_realizations, params)
            all_results.extend(res)
            
        # NN usually has fixed length constraints or specific needs.
        # Check if lengths are compatible or use default?
        # For now, pass same configuration.
        if run_nn:
            res = self.nn.run(models, lengths, num_realizations, params)
            all_results.extend(res)
            
        self.results = all_results
        self.save_results()
        
        return self.results
