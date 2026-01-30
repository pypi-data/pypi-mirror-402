
import numpy as np
import torch
import torch.nn as nn
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .base_pretrained_model import BasePretrainedModel

class LSTMModel(nn.Module):
    """LSTM model for Hurst parameter estimation."""
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True, 
            dropout=dropout
        )
        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)

class LSTMPretrainedModel(BasePretrainedModel):
    def __init__(self, model_path: Optional[str] = None, input_length: int = 1024):
        super().__init__(model_path)
        self.input_length = input_length
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model()
    
    def _get_default_model_path(self) -> Path:
        current_dir = Path(os.path.dirname(__file__))
        return current_dir.parent.parent / "assets" / "models" / "lstm_model.pth"
    
    def _load_model(self) -> nn.Module:
        model = LSTMModel().to(self.device)
        if self.model_path and os.path.exists(self.model_path):
            try:
                state_dict = torch.load(self.model_path, map_location=self.device)
                model.load_state_dict(state_dict)
                model.eval()
            except Exception as e:
                print(f"Warning: Failed to load model weights from {self.model_path}: {e}")
        else:
            print(f"Warning: Pre-trained model not found at {self.model_path}.")
        return model
        
    def estimate(self, data: np.ndarray) -> Dict[str, Any]:
        data = self._preprocess(data)
        data_tensor = torch.FloatTensor(data).unsqueeze(0).unsqueeze(-1).to(self.device)
        with torch.no_grad():
            prediction = self.model(data_tensor).item()
        return {
            "hurst_parameter": prediction,
            "confidence_interval": [max(0.05, prediction - 0.05), min(0.95, prediction + 0.05)],
            "std_error": 0.05,
            "method": "LSTM (Pre-trained Neural Network)",
            "model_info": "PyTorch LSTM"
        }

    def _preprocess(self, data: np.ndarray) -> np.ndarray:
        data = np.asarray(data)
        if len(data) > self.input_length:
            data = data[:self.input_length]
        elif len(data) < self.input_length:
            pad_width = self.input_length - len(data)
            data = np.pad(data, (0, pad_width), mode='constant')
        if np.std(data) > 0:
            data = (data - np.mean(data)) / np.std(data)
        return data
