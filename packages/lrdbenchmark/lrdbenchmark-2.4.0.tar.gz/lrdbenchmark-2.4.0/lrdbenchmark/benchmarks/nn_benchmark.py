
from typing import List, Dict, Any, Optional
from .base import BaseBenchmark
import warnings

try:
    from ..models.pretrained_models.cnn_pretrained import CNNPretrainedModel
    from ..models.pretrained_models.transformer_pretrained import TransformerPretrainedModel
    from ..models.pretrained_models.lstm_pretrained import LSTMPretrainedModel
    from ..models.pretrained_models.gru_pretrained import GRUPretrainedModel
    NN_AVAILABLE = True
except ImportError:
    NN_AVAILABLE = False
    warnings.warn("Neural Network pretrained models not available.")

class NNBenchmark(BaseBenchmark):
    """
    Benchmark for Deep Learning estimators (CNN, LSTM, GRU, Transformer).
    """
    
    def __init__(self, output_dir: Optional[str] = None, seed: Optional[int] = None):
        super().__init__("NNBenchmark", output_dir, seed)
        self.default_input_length = 500 # Models might be fixed length?
        self.estimators = self._initialize_estimators()
        
    def _initialize_estimators(self):
        if not NN_AVAILABLE:
            return {}
            
        # Note: NN models often require specific input lengths initialization
        # We will assume they can handle variable length or we must fix it.
        # Engine.py passed `input_length=500`.
        return {
            "CNN": CNNPretrainedModel(input_length=self.default_input_length),
            "LSTM": LSTMPretrainedModel(input_length=self.default_input_length),
            "GRU": GRUPretrainedModel(input_length=self.default_input_length),
            "Transformer": TransformerPretrainedModel(input_length=self.default_input_length)
        }
        
    def run(
        self, 
        models: List[str] = ['fbm', 'fgn'],
        lengths: List[int] = [500], # Default to 500 for NN
        num_realizations: int = 10,
        params: Dict[str, Any] = {'H': 0.7}
    ):
        if not self.estimators:
            print("No NN estimators available. Skipping.")
            return []
            
        print(f"Starting NNBenchmark: ~{len(models)*len(lengths)*num_realizations*len(self.estimators)} evaluations.")
        
        for model_name in models:
            for n in lengths:
                # Update estimator input length if possible?
                # For now assume models handle it or n matches default
                
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
                            'benchmark_type': 'NN',
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
