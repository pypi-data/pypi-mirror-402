"""
Unified Random Forest Estimator for Hurst Parameter Estimation

This module provides a Random Forest estimator that uses the unified feature extraction
pipeline to work with pre-trained models.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

from lrdbenchmark.analysis.base_estimator import BaseEstimator
from lrdbenchmark.assets import ensure_model_artifact
from .unified_feature_extractor import UnifiedFeatureExtractor

logger = logging.getLogger(__name__)

class RandomForestEstimator(BaseEstimator):
    """
    Random Forest estimator using unified feature extraction.
    Works with pre-trained models expecting 76 features.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the Random Forest estimator.
        
        Args:
            model_path: Path to the pre-trained model. If None, uses default path.
        """
        super().__init__()
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.expected_features = None
        self.is_loaded = False
    
    def _validate_parameters(self) -> None:
        """Validate estimator parameters."""
        # For unified estimators, parameters are handled by the pre-trained models
        pass
        
    def _get_default_model_path(self) -> Optional[str]:
        """Resolve the default pretrained model path, downloading if required."""
        artifact_path = ensure_model_artifact("random_forest_estimator")
        if artifact_path:
            return str(artifact_path)
        return None
    
    def _load_model(self):
        """Load the pre-trained Random Forest model."""
        if self.is_loaded:
            return
            
        if not self.model_path or not os.path.exists(self.model_path):
            logger.warning(f"Pre-trained model not found at {self.model_path}")
            self.is_loaded = False
            return
            
        try:
            model_data = joblib.load(self.model_path)

            if isinstance(model_data, dict):
                self.model = model_data.get('model')
                self.scaler = model_data.get('scaler')
                self.feature_names = model_data.get(
                    'feature_names',
                    UnifiedFeatureExtractor.get_feature_names(),
                )
            elif isinstance(model_data, (list, tuple)):
                self.model = model_data[0] if model_data else None
                if len(model_data) > 1 and hasattr(model_data[1], "transform"):
                    self.scaler = model_data[1]
                else:
                    self.scaler = None
                self.feature_names = UnifiedFeatureExtractor.get_feature_names()
            else:
                self.model = model_data
                self.scaler = None
                self.feature_names = UnifiedFeatureExtractor.get_feature_names()

            if self.model is None:
                raise ValueError("Loaded model does not contain a valid estimator")

            self._update_feature_metadata()
            self.is_loaded = True
            logger.info(f"Random Forest model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load Random Forest model: {e}")
            self.is_loaded = False

    def _update_feature_metadata(self):
        """Update expected feature count and default feature names."""
        if self.model is None:
            return

        self.expected_features = getattr(self.model, "n_features_in_", None)

        if self.feature_names is not None:
            return

        if self.expected_features in (5, 8):
            self.feature_names = UnifiedFeatureExtractor.get_feature_names_8()[: self.expected_features or 8]
        elif self.expected_features == 54:
            self.feature_names = UnifiedFeatureExtractor.get_feature_names_54()
        elif self.expected_features == 29:
            self.feature_names = UnifiedFeatureExtractor.get_feature_names_29()
        else:
            self.feature_names = UnifiedFeatureExtractor.get_feature_names()

    def _extract_features_for_model(self, data: np.ndarray) -> np.ndarray:
        """Extract feature vector that matches the pretrained model."""
        expected = self.expected_features

        if expected in (5, 8):
            features = UnifiedFeatureExtractor.extract_features_8(data)
        elif expected == 54:
            features = UnifiedFeatureExtractor.extract_features_54(data)
        elif expected == 29:
            features = UnifiedFeatureExtractor.extract_features_29(data)
        else:
            features = UnifiedFeatureExtractor.extract_features_76(data)

        if expected is not None and len(features) != expected:
            if len(features) > expected:
                features = features[:expected]
            else:
                features = np.pad(features, (0, expected - len(features)), 'constant')

        return features
    
    def estimate(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Estimate Hurst parameter using Random Forest with unified features.
        
        Args:
            data: Time series data
            
        Returns:
            Dictionary containing estimation results
        """
        if not self.is_loaded:
            self._load_model()
            
        if not self.is_loaded:
            logger.error("Random Forest model not loaded")
            return {
                'hurst_parameter': np.nan,
                'method': 'random_forest',
                'error': 'Model not loaded',
                'features_used': 0
            }
        
        try:
            features = self._extract_features_for_model(data)
            
            feature_array = features.reshape(1, -1)

            if self.scaler is not None:
                try:
                    features_scaled = self.scaler.transform(feature_array)
                except Exception as e:
                    logger.warning(f"Scaler transform failed ({e}), using raw features")
                    features_scaled = feature_array
            else:
                features_scaled = feature_array
            
            # Make prediction
            H_estimate = self.model.predict(features_scaled)[0]
            
            return {
                'hurst_parameter': float(H_estimate),
                'method': 'random_forest',
                'features_used': len(features),
                'feature_names': self.feature_names[:len(features)] if self.feature_names else None
            }
            
        except Exception as e:
            logger.error(f"Random Forest estimation failed: {e}")
            return {
                'hurst_parameter': np.nan,
                'method': 'random_forest',
                'error': str(e),
                'features_used': len(features)
            }
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """
        Get feature importance from the Random Forest model.
        
        Returns:
            Array of feature importances or None if model not loaded
        """
        if not self.is_loaded:
            self._load_model()
            
        if not self.is_loaded or self.model is None:
            return None
            
        try:
            return self.model.feature_importances_
        except Exception as e:
            logger.error(f"Failed to get feature importance: {e}")
            return None
    
    def get_feature_names(self) -> Optional[List[str]]:
        """
        Get feature names used by the model.
        
        Returns:
            List of feature names or None if not available
        """
        if not self.is_loaded:
            self._load_model()
            
        return self.feature_names
    
    def is_model_available(self) -> bool:
        """
        Check if the pre-trained model is available.
        
        Returns:
            True if model is available and loaded
        """
        if not self.is_loaded:
            self._load_model()
        return self.is_loaded