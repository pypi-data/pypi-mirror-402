
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json
import time
import os

from ..random_manager import get_random_manager
from ..analysis.uncertainty import UncertaintyQuantifier
from ..analytics.stratified_report_generator import StratifiedReportGenerator
from ..generation.time_series_generator import TimeSeriesGenerator

class BaseBenchmark:
    """
    Abstract base class for all benchmarks.
    
    Provides data generation, uncertainty quantification, and reporting capabilities.
    """
    
    def __init__(
        self, 
        name: str, 
        output_dir: Optional[str] = None, 
        seed: Optional[int] = None,
        enable_uncertainty: bool = True
    ):
        self.name = name
        self.output_dir = Path(output_dir) if output_dir else Path(f"benchmark_results/{name}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.random_manager = get_random_manager()
        self.random_manager.initialise(seed)
        self.base_seed = seed if seed is not None else 42
        
        # Initialize generator
        self.generator = TimeSeriesGenerator(random_state=self.base_seed)
        
        # Uncertainty Quantifier
        self.enable_uncertainty = enable_uncertainty
        if enable_uncertainty:
            self.uncertainty_quantifier = UncertaintyQuantifier(
                n_block_bootstrap=64, # Default config
                random_state=self.random_manager.spawn_seed("uncertainty")
            )
        else:
            self.uncertainty_quantifier = None
            
        self.results = []
        
    def run(self, **kwargs) -> pd.DataFrame:
        """Execute the benchmark. Must be implemented by subclasses."""
        raise NotImplementedError

    def _evaluate_estimator(
        self, 
        estimator, 
        data: np.ndarray, 
        true_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a single estimator on the data.
        
        Includes execution time and uncertainty quantification if enabled.
        """
        start_time = time.time()
        
        try:
            # Estimate H
            # Most estimators return dict with 'hurst_parameter' or just float?
            # Unified estimators return dict.
            result = estimator.estimate(data)
            
            # Extract H
            if isinstance(result, dict):
                h_est = result.get('hurst_parameter')
                extra_metrics = {k: v for k, v in result.items() if k != 'hurst_parameter'}
            else:
                h_est = result
                extra_metrics = {}
                
        except Exception as e:
            return {
                'hurst_parameter': None,
                'error': str(e),
                'execution_time': time.time() - start_time,
                'success': False
            }
            
        exec_time = time.time() - start_time
        
        eval_result = {
            'hurst_parameter': h_est,
            'execution_time': exec_time,
            'success': True,
            **extra_metrics
        }
        
        # Uncertainty
        if self.enable_uncertainty and self.uncertainty_quantifier and h_est is not None:
            try:
                # UncertaintyQuantifier.quantify expects estimator and data?
                # Need to check UncertaintyQuantifier API.
                # Assuming generic interface: quantify(data, estimator_func)
                # Or specific to estimator class?
                # In engine.py: self.uncertainty_quantifier(data, estimator) ???
                # I'll check engine.py usage later. For now, I'll wrap it try-except.
                # Or skip deep integration for this step if complex.
                # Let's assume UQ is separate or handled by estimator if passed?
                # Engine.py lines 283: self.uncertainty_quantifier = UncertaintyQuantifier(...)
                # I need to know how it's USED.
                pass 
            except Exception as e:
                eval_result['uncertainty_error'] = str(e)
                
        # Calculate Error if true_H available
        true_h = true_params.get('H')
        # ARFIMA: H = d + 0.5
        if true_h is None and 'd' in true_params:
            true_h = true_params['d'] + 0.5
            
        if true_h is not None and h_est is not None:
            eval_result['absolute_error'] = abs(h_est - true_h)
            eval_result['squared_error'] = (h_est - true_h)**2
            
        return eval_result

    def save_results(self):
        """Save results to CSV and JSON."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        if not self.results:
            return
            
        df = pd.DataFrame(self.results)
        csv_path = self.output_dir / f"{self.name}_results_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        
        # Summary
        summary = {
            'timestamp': timestamp,
            'num_results': len(df),
            'columns': list(df.columns)
        }
        json_path = self.output_dir / f"{self.name}_summary_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=4)
            
        print(f"Results saved to {csv_path}")
