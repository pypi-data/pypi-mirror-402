"""
Utility functions for LRDBenchmark.

This module provides various utility functions used throughout the package,
including model loading utilities that can handle multiple file formats.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
import warnings

import joblib
import pickle

from .assets import ensure_model_artifact, get_model_config_path

logger = logging.getLogger(__name__)

# Suppress the sklearn version warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

def load_model_flexible(file_path: Union[str, Path], suppress_warnings: bool = True) -> Optional[Dict[str, Any]]:
    """
    Load a model from file, supporting both .pkl and .joblib formats.
    
    This function attempts to load models using different methods to handle
    version compatibility issues between sklearn versions.
    
    Args:
        file_path: Path to the model file
        suppress_warnings: Whether to suppress sklearn version warnings
        
    Returns:
        Dictionary containing the loaded model data, or None if loading failed
        
    Raises:
        FileNotFoundError: If the model file doesn't exist
        ValueError: If the file format is not supported
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Model file not found: {file_path}")
    
    # Determine the file extension
    suffix = file_path.suffix.lower()
    
    if suppress_warnings:
        # Suppress sklearn version warnings during loading
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
            return _load_model_with_method(file_path, suffix)
    else:
        return _load_model_with_method(file_path, suffix)

def _load_model_with_method(file_path: Path, suffix: str) -> Optional[Dict[str, Any]]:
    """Load model using the appropriate method based on file extension."""
    
    if suffix in ['.joblib', '.pkl']:
        # Try joblib first (preferred for sklearn models)
        try:
            logger.debug(f"Attempting to load {file_path} with joblib")
            return joblib.load(file_path)
        except Exception as joblib_error:
            logger.debug(f"joblib loading failed: {joblib_error}")
            
            # Fallback to pickle if joblib fails
            try:
                logger.debug(f"Attempting to load {file_path} with pickle")
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as pickle_error:
                logger.error(f"Both joblib and pickle loading failed for {file_path}")
                logger.error(f"joblib error: {joblib_error}")
                logger.error(f"pickle error: {pickle_error}")
                raise ValueError(f"Unable to load model from {file_path}. "
                               f"Tried joblib and pickle, both failed.")
    
    elif suffix == '.pkl':
        # Explicitly .pkl file - try pickle first, then joblib
        try:
            logger.debug(f"Attempting to load {file_path} with pickle")
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as pickle_error:
            logger.debug(f"pickle loading failed: {pickle_error}")
            
            # Fallback to joblib
            try:
                logger.debug(f"Attempting to load {file_path} with joblib")
                return joblib.load(file_path)
            except Exception as joblib_error:
                logger.error(f"Both pickle and joblib loading failed for {file_path}")
                logger.error(f"pickle error: {pickle_error}")
                logger.error(f"joblib error: {joblib_error}")
                raise ValueError(f"Unable to load model from {file_path}. "
                               f"Tried pickle and joblib, both failed.")
    
    else:
        raise ValueError(f"Unsupported file format: {suffix}. "
                        f"Supported formats: .pkl, .joblib")

def save_model_flexible(model_data: Dict[str, Any], 
                       file_path: Union[str, Path], 
                       prefer_joblib: bool = True) -> None:
    """
    Save a model to file, using the appropriate format based on file extension.
    
    Args:
        model_data: Dictionary containing the model data to save
        file_path: Path where to save the model
        prefer_joblib: Whether to prefer joblib format for sklearn models
        
    Raises:
        ValueError: If the file format is not supported
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    
    if suffix in ['.joblib', '.pkl']:
        if prefer_joblib:
            logger.debug(f"Saving {file_path} with joblib")
            joblib.dump(model_data, file_path)
        else:
            logger.debug(f"Saving {file_path} with pickle")
            with open(file_path, 'wb') as f:
                pickle.dump(model_data, f)
    elif suffix == '.pkl':
        logger.debug(f"Saving {file_path} with pickle")
        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. "
                        f"Supported formats: .pkl, .joblib")

def get_model_file_paths(base_name: str, model_dir: Union[str, Path] = "models") -> Dict[str, Path]:
    """
    Get possible model file paths for a given base name.
    
    Args:
        base_name: Base name of the model (without extension)
        model_dir: Directory containing the models
        
    Returns:
        Dictionary with format names as keys and file paths as values
    """
    model_dir = Path(model_dir)
    
    return {
        'joblib': model_dir / f"{base_name}.joblib",
        'pkl': model_dir / f"{base_name}.pkl"
    }

def find_available_model(base_name: str, model_dir: Union[str, Path] = "models") -> Optional[Path]:
    """
    Find the first available model file for a given base name.
    
    Args:
        base_name: Base name of the model (without extension)
        model_dir: Directory containing the models
        
    Returns:
        Path to the first available model file, or None if none found
    """
    file_paths = get_model_file_paths(base_name, model_dir)
    
    for format_name, file_path in file_paths.items():
        if file_path.exists():
            logger.debug(f"Found {format_name} model: {file_path}")
            return file_path
    
    return None

def get_pretrained_model_path(model_name: str, format_type: str = "joblib") -> Optional[str]:
    """
    Get the path to a pretrained model file.
    
    Args:
        model_name: Name of the model (e.g., 'random_forest_estimator')
        format_type: File format ('joblib' or 'pkl')
        
    Returns:
        Path to the pretrained model file, or None if not found
    """
    artifact_path = ensure_model_artifact(model_name)
    if artifact_path:
        return str(artifact_path)

    # Fallback to legacy on-disk locations to preserve backward compatibility.
    legacy_path = Path(f"models/{model_name}.{format_type}")
    if legacy_path.exists():
        logger.warning(
            "Using legacy model path at %s; please migrate to the new asset cache.",
            legacy_path,
        )
        return str(legacy_path)

    return None

def get_neural_network_model_path(model_name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Get the path to a pretrained neural network model file.
    
    Args:
        model_name: Name of the neural network model
        
    Returns:
        Tuple of (model_path, config_path) or (None, None) if not found
    """
    model_artifact = ensure_model_artifact(model_name)
    config_filename_options = [
        f"{model_name}_neural_network_config.json",
        f"{model_name}_config.json",
        f"{model_name}.json",
    ]
    config_path = None
    for filename in config_filename_options:
        candidate = get_model_config_path(filename)
        if candidate:
            config_path = str(candidate)
            break

    if model_artifact:
        return str(model_artifact), config_path

    # Legacy fallback to repository-relative directories
    legacy_model = Path(f"models/{model_name}_neural_network.pth")
    if legacy_model.exists():
        logger.warning(
            "Using legacy neural-network model from %s; migrate to the asset cache.",
            legacy_model,
        )
        return str(legacy_model), config_path

    return None, config_path

# Modern metadata handling
try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("lrdbenchmark")
except (PackageNotFoundError, ImportError):
    # Fallback for older Python versions or if package not installed
    try:
        import pkg_resources
        __version__ = pkg_resources.get_distribution("lrdbenchmark").version
    except Exception:
        __version__ = "unknown"