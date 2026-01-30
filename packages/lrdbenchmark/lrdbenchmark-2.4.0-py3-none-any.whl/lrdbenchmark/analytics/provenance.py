#!/usr/bin/env python3
"""
Comprehensive Provenance Tracking System
Captures and packages all protocol-critical settings, environment info,
and execution metadata for full reproducibility
"""

import numpy as np
import platform
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import subprocess


class ProvenanceTracker:
    """
    Tracks and packages comprehensive provenance information for benchmark runs.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise provenance tracker.
        
        Parameters
        ----------
        config : dict, optional
            Protocol configuration
        """
        self.config = config or {}
        self.provenance_config = self.config.get("provenance", {})
    
    def capture_provenance(
        self,
        benchmark_metadata: Dict[str, Any],
        estimators_tested: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Capture comprehensive provenance bundle.
        
        Parameters
        ----------
        benchmark_metadata : dict
            Metadata about the benchmark run
        estimators_tested : dict, optional
            Dictionary of estimator categories and names tested
            
        Returns
        -------
        dict
            Complete provenance bundle
        """
        provenance_bundle = {
            "provenance_version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "benchmark_metadata": benchmark_metadata
        }
        
        # Protocol configuration
        provenance_bundle["protocol"] = self._capture_protocol_config()
        
        # Environment information
        if self.provenance_config.get("track_environment", True):
            provenance_bundle["environment"] = self._capture_environment()
        
        # Package versions
        if self.provenance_config.get("track_package_versions", True):
            provenance_bundle["package_versions"] = self._capture_package_versions()
        
        # Hardware information
        if self.provenance_config.get("track_hardware", True):
            provenance_bundle["hardware"] = self._capture_hardware()
        
        # Runtime information
        if self.provenance_config.get("track_runtime", True):
            provenance_bundle["runtime"] = self._capture_runtime(benchmark_metadata)
        
        # Estimators tested
        if estimators_tested:
            provenance_bundle["estimators_tested"] = estimators_tested
        
        # Git commit info (if available)
        provenance_bundle["git_info"] = self._capture_git_info()
        
        return provenance_bundle
    
    def _capture_protocol_config(self) -> Dict[str, Any]:
        """Capture full protocol configuration."""
        protocol_data = {
            "version": self.config.get("version", "unknown"),
            "protocol_metadata": self.config.get("protocol_metadata", {}),
        }
        
        # Preprocessing settings
        preprocessing = self.config.get("preprocessing", {})
        protocol_data["preprocessing"] = {
            "detrend": preprocessing.get("detrend", {}),
            "tapering": preprocessing.get("tapering", {}),
            "outlier_removal": preprocessing.get("outlier_removal", {}),
            "winsorize": preprocessing.get("winsorize", {}),
            "filtering": preprocessing.get("filtering", {})
        }
        
        # Scale selection heuristics
        scale_selection = self.config.get("scale_selection", {})
        protocol_data["scale_selection"] = {
            "spectral": {
                "method": scale_selection.get("spectral", {}).get("method"),
                "min_freq_ratio": scale_selection.get("spectral", {}).get("min_freq_ratio"),
                "max_freq_ratio": scale_selection.get("spectral", {}).get("max_freq_ratio"),
                "low_freq_trim": scale_selection.get("spectral", {}).get("low_freq_trim"),
                "high_freq_trim": scale_selection.get("spectral", {}).get("high_freq_trim"),
                "trimming_method": scale_selection.get("spectral", {}).get("trimming_method"),
                "options": scale_selection.get("spectral", {}).get("options", {})
            },
            "temporal": {
                "method": scale_selection.get("temporal", {}).get("method"),
                "min_window": scale_selection.get("temporal", {}).get("min_window"),
                "max_window": scale_selection.get("temporal", {}).get("max_window"),
                "window_density": scale_selection.get("temporal", {}).get("window_density"),
                "step_type": scale_selection.get("temporal", {}).get("step_type"),
                "options": scale_selection.get("temporal", {}).get("options", {})
            },
            "wavelet": {
                "method": scale_selection.get("wavelet", {}).get("method"),
                "min_level": scale_selection.get("wavelet", {}).get("min_level"),
                "max_level": scale_selection.get("wavelet", {}).get("max_level"),
                "wavelet": scale_selection.get("wavelet", {}).get("wavelet"),
                "boundary": scale_selection.get("wavelet", {}).get("boundary"),
                "options": scale_selection.get("wavelet", {}).get("options", {})
            }
        }
        
        # Diagnostics settings
        diagnostics = self.config.get("diagnostics", {})
        protocol_data["diagnostics"] = {
            "log_log_checks": diagnostics.get("log_log_checks", {}),
            "residual_tests": diagnostics.get("residual_tests", {}),
            "goodness_of_fit": diagnostics.get("goodness_of_fit", {}),
            "scale_window_sensitivity": diagnostics.get("scale_window_sensitivity", {})
        }
        
        # Stratification settings
        stratification = self.config.get("stratification", {})
        protocol_data["stratification"] = {
            "hurst_bands": stratification.get("hurst_bands", {}),
            "length_bands": stratification.get("length_bands", {}),
            "tail_classes": stratification.get("tail_classes", {}),
            "contamination_types": stratification.get("contamination_types", {})
        }
        
        # Data model defaults
        protocol_data["data_models"] = self.config.get("data_models", {})
        
        # Estimator overrides
        protocol_data["estimator_overrides"] = self.config.get("estimator_overrides", {})
        
        # Benchmark settings
        benchmark_cfg = self.config.get("benchmark", {})
        protocol_data["benchmark"] = {
            "confidence_level": benchmark_cfg.get("confidence_level"),
            "uncertainty": benchmark_cfg.get("uncertainty", {}),
            "monte_carlo": benchmark_cfg.get("monte_carlo", {})
        }
        
        return protocol_data
    
    def _capture_environment(self) -> Dict[str, Any]:
        """Capture Python and system environment."""
        return {
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
            "python_compiler": platform.python_compiler(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0]
        }
    
    def _capture_package_versions(self) -> Dict[str, Any]:
        """Capture versions of key packages."""
        versions = {}
        
        packages = [
            "numpy", "scipy", "pandas", "matplotlib", 
            "sklearn", "pywt", "statsmodels"
        ]
        
        for package in packages:
            try:
                mod = __import__(package)
                versions[package] = getattr(mod, "__version__", "unknown")
            except ImportError:
                versions[package] = "not installed"
        
        # Check for optional acceleration packages
        optional_packages = ["jax", "numba", "torch", "tensorflow"]
        for package in optional_packages:
            try:
                mod = __import__(package)
                versions[package] = getattr(mod, "__version__", "unknown")
            except ImportError:
                versions[package] = "not installed"
        
        return versions
    
    def _capture_hardware(self) -> Dict[str, Any]:
        """Capture hardware information."""
        hardware_info = {
            "cpu_count": self._get_cpu_count(),
            "total_memory_gb": self._get_total_memory()
        }
        
        # Try to get GPU information
        gpu_info = self._get_gpu_info()
        if gpu_info:
            hardware_info["gpu"] = gpu_info
        
        return hardware_info
    
    def _get_cpu_count(self) -> Optional[int]:
        """Get CPU count."""
        try:
            import os
            return os.cpu_count()
        except Exception:
            return None
    
    def _get_total_memory(self) -> Optional[float]:
        """Get total system memory in GB."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return round(mem.total / (1024 ** 3), 2)
        except ImportError:
            return None
        except Exception:
            return None
    
    def _get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """Get GPU information if available."""
        gpu_info = {}
        
        # Try CUDA/PyTorch
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info["cuda_available"] = True
                gpu_info["cuda_version"] = torch.version.cuda
                gpu_info["device_count"] = torch.cuda.device_count()
                gpu_info["devices"] = [
                    torch.cuda.get_device_name(i) 
                    for i in range(torch.cuda.device_count())
                ]
                return gpu_info
        except ImportError:
            pass
        
        # Try JAX
        try:
            import jax
            devices = jax.devices()
            if any(d.platform == "gpu" for d in devices):
                gpu_info["jax_available"] = True
                gpu_info["devices"] = [str(d) for d in devices if d.platform == "gpu"]
                return gpu_info
        except ImportError:
            pass
        
        return None if not gpu_info else gpu_info
    
    def _capture_runtime(self, benchmark_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Capture runtime information."""
        return {
            "total_tests": benchmark_metadata.get("total_tests"),
            "successful_tests": benchmark_metadata.get("successful_tests"),
            "success_rate": benchmark_metadata.get("success_rate"),
            "benchmark_type": benchmark_metadata.get("benchmark_type"),
            "data_length": benchmark_metadata.get("data_length"),
            "contamination_type": benchmark_metadata.get("contamination_type"),
            "contamination_level": benchmark_metadata.get("contamination_level"),
            "data_models_tested": benchmark_metadata.get("data_models_tested"),
            "estimators_tested": benchmark_metadata.get("estimators_tested")
        }
    
    def _capture_git_info(self) -> Dict[str, Any]:
        """Capture git repository information if available."""
        git_info = {}
        
        try:
            # Get git commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["commit_hash"] = result.stdout.strip()
            
            # Get git branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()
            
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["has_uncommitted_changes"] = bool(result.stdout.strip())
            
            # Get remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["remote_url"] = result.stdout.strip()
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            git_info["status"] = "git information unavailable"
        
        return git_info if git_info else {"status": "not a git repository"}
    
    def save_provenance(
        self, 
        provenance_bundle: Dict[str, Any], 
        output_path: Path
    ):
        """
        Save provenance bundle to file.
        
        Parameters
        ----------
        provenance_bundle : dict
            Complete provenance data
        output_path : Path
            Path to save the provenance file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(output_path, 'w') as f:
            json.dump(provenance_bundle, f, indent=2, default=str)
    
    def verify_reproducibility(
        self,
        provenance_bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify that the current environment matches the provenance bundle.
        
        Parameters
        ----------
        provenance_bundle : dict
            Provenance bundle to verify against
            
        Returns
        -------
        dict
            Verification results with warnings and mismatches
        """
        warnings_list = []
        mismatches = []
        
        # Check Python version
        current_python = sys.version
        recorded_python = provenance_bundle.get("environment", {}).get("python_version")
        if recorded_python and current_python != recorded_python:
            mismatches.append({
                "category": "environment",
                "field": "python_version",
                "recorded": recorded_python,
                "current": current_python
            })
        
        # Check package versions
        current_versions = self._capture_package_versions()
        recorded_versions = provenance_bundle.get("package_versions", {})
        
        for package, recorded_version in recorded_versions.items():
            current_version = current_versions.get(package)
            if current_version and current_version != recorded_version:
                mismatches.append({
                    "category": "package_version",
                    "package": package,
                    "recorded": recorded_version,
                    "current": current_version
                })
        
        # Check protocol version
        current_protocol_version = self.config.get("version")
        recorded_protocol_version = provenance_bundle.get("protocol", {}).get("version")
        if recorded_protocol_version and current_protocol_version != recorded_protocol_version:
            warnings_list.append(
                f"Protocol version mismatch: recorded={recorded_protocol_version}, "
                f"current={current_protocol_version}"
            )
        
        # Assess reproducibility
        if not mismatches and not warnings_list:
            status = "fully_reproducible"
            message = "Environment matches provenance bundle exactly"
        elif mismatches and not any(m["category"] == "package_version" for m in mismatches):
            status = "likely_reproducible"
            message = "Minor differences detected, results should be reproducible"
        else:
            status = "possibly_not_reproducible"
            message = "Significant differences detected, results may differ"
        
        return {
            "status": status,
            "message": message,
            "warnings": warnings_list,
            "mismatches": mismatches,
            "n_mismatches": len(mismatches)
        }


def create_provenance_bundle(
    benchmark_results: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to create a provenance bundle from benchmark results.
    
    Parameters
    ----------
    benchmark_results : dict
        Complete benchmark results
    config : dict, optional
        Protocol configuration
        
    Returns
    -------
    dict
        Provenance bundle
    """
    tracker = ProvenanceTracker(config)
    
    benchmark_metadata = {
        "timestamp": benchmark_results.get("timestamp"),
        "benchmark_type": benchmark_results.get("benchmark_type"),
        "data_length": benchmark_results.get("data_length"),
        "contamination_type": benchmark_results.get("contamination_type"),
        "contamination_level": benchmark_results.get("contamination_level"),
        "total_tests": benchmark_results.get("total_tests"),
        "successful_tests": benchmark_results.get("successful_tests"),
        "success_rate": benchmark_results.get("success_rate"),
        "data_models_tested": benchmark_results.get("data_models_tested"),
        "estimators_tested": benchmark_results.get("estimators_tested")
    }
    
    return tracker.capture_provenance(benchmark_metadata)


def verify_provenance(
    provenance_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Verify a provenance bundle against current environment.
    
    Parameters
    ----------
    provenance_path : Path
        Path to provenance bundle JSON file
    config : dict, optional
        Current protocol configuration
        
    Returns
    -------
    dict
        Verification results
    """
    with open(provenance_path, 'r') as f:
        provenance_bundle = json.load(f)
    
    tracker = ProvenanceTracker(config)
    return tracker.verify_reproducibility(provenance_bundle)

