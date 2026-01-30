#!/usr/bin/env python3
"""
Comprehensive Stratified Report Generator
Produces rich, regime-specific breakdowns of benchmark results
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json


class StratifiedReportGenerator:
    """
    Generate comprehensive stratified reports breaking out results by:
    - True H bands (for synthetic data)
    - Estimated H bands (for all data)
    - Tail index classes
    - Sample length regimes
    - Contamination type and level
    - Estimator families and individual methods
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise stratified report generator.
        
        Parameters
        ----------
        config : dict, optional
            Protocol configuration with stratification settings
        """
        self.config = config or {}
        self.stratification_config = self.config.get("stratification", {})
        
        # Load band definitions from config
        self._load_band_definitions()
    
    def _load_band_definitions(self):
        """Load stratification band definitions from config."""
        # Hurst bands
        hurst_cfg = self.stratification_config.get("hurst_bands", {})
        if hurst_cfg.get("enabled", True):
            self.hurst_bands = hurst_cfg.get("bands", self._default_hurst_bands())
        else:
            self.hurst_bands = []
        
        # Length bands
        length_cfg = self.stratification_config.get("length_bands", {})
        if length_cfg.get("enabled", True):
            self.length_bands = length_cfg.get("bands", self._default_length_bands())
        else:
            self.length_bands = []
        
        # Tail classes
        tail_cfg = self.stratification_config.get("tail_classes", {})
        if tail_cfg.get("enabled", True):
            self.tail_classes = tail_cfg.get("classes", self._default_tail_classes())
        else:
            self.tail_classes = {}
    
    def _default_hurst_bands(self) -> List[Dict[str, Any]]:
        """Default Hurst band definitions."""
        return [
            {"name": "anti-persistent (H<0.3)", "min": 0.0, "max": 0.3},
            {"name": "short-range (0.3≤H<0.5)", "min": 0.3, "max": 0.5},
            {"name": "borderline (0.5≤H<0.55)", "min": 0.5, "max": 0.55},
            {"name": "moderate persistence (0.55≤H<0.7)", "min": 0.55, "max": 0.7},
            {"name": "persistent (0.7≤H<0.85)", "min": 0.7, "max": 0.85},
            {"name": "ultra-persistent (H≥0.85)", "min": 0.85, "max": 1.0}
        ]
    
    def _default_length_bands(self) -> List[Dict[str, Any]]:
        """Default length band definitions."""
        return [
            {"name": "very short (≤256)", "min": 0, "max": 256},
            {"name": "short (257-512)", "min": 257, "max": 512},
            {"name": "medium (513-2048)", "min": 513, "max": 2048},
            {"name": "long (2049-8192)", "min": 2049, "max": 8192},
            {"name": "ultra-long (>8192)", "min": 8193, "max": 1000000}
        ]
    
    def _default_tail_classes(self) -> Dict[str, List[str]]:
        """Default tail class mappings."""
        return {
            "gaussian": ["fBm", "fGn"],
            "linear-LRD": ["ARFIMAModel"],
            "multifractal-heavy-tail": ["MRW"],
            "alpha-stable": ["AlphaStable"],
            "neural-fSDE": ["NeuralFSDE"]
        }
    
    def generate_report(
        self,
        results: Dict[str, Any],
        output_dir: Optional[Path] = None,
        formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive stratified report.
        
        Parameters
        ----------
        results : dict
            Benchmark results dictionary
        output_dir : Path, optional
            Directory to save reports
        formats : list of str, optional
            Output formats: 'markdown', 'json', 'csv', 'html'
            
        Returns
        -------
        dict
            Stratified report data
        """
        if formats is None:
            formats = ['markdown', 'json']
        
        # Extract results data
        all_results = results.get("results", {})
        benchmark_metadata = {
            "timestamp": results.get("timestamp"),
            "benchmark_type": results.get("benchmark_type"),
            "data_length": results.get("data_length"),
            "contamination_type": results.get("contamination_type"),
            "contamination_level": results.get("contamination_level"),
            "total_tests": results.get("total_tests"),
            "successful_tests": results.get("successful_tests")
        }
        
        # Generate all stratifications
        stratified_data = {
            "metadata": benchmark_metadata,
            "true_h_stratification": self._stratify_by_true_h(all_results),
            "estimated_h_stratification": self._stratify_by_estimated_h(all_results),
            "tail_class_stratification": self._stratify_by_tail_class(all_results),
            "length_stratification": self._stratify_by_length(
                all_results, results.get("data_length")
            ),
            "contamination_stratification": self._stratify_by_contamination(
                all_results, 
                results.get("contamination_type"),
                results.get("contamination_level")
            ),
            "estimator_family_stratification": self._stratify_by_estimator_family(all_results),
            "cross_stratifications": self._generate_cross_stratifications(all_results, results)
        }
        
        # Save in requested formats
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True, parents=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if 'json' in formats:
                json_path = output_dir / f"stratified_report_{timestamp}.json"
                with open(json_path, 'w') as f:
                    json.dump(stratified_data, f, indent=2, default=str)
            
            if 'markdown' in formats:
                md_path = output_dir / f"stratified_report_{timestamp}.md"
                self._save_markdown_report(stratified_data, md_path)
            
            if 'csv' in formats:
                self._save_csv_reports(stratified_data, output_dir, timestamp)
            
            if 'html' in formats:
                html_path = output_dir / f"stratified_report_{timestamp}.html"
                self._save_html_report(stratified_data, html_path)
        
        return stratified_data
    
    def _stratify_by_true_h(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Stratify results by true Hurst parameter bands."""
        bands_data = {}
        
        for model_name, model_data in results.items():
            estimator_results = model_data.get("estimator_results", [])
            data_params = model_data.get("data_params", {})
            
            true_h = data_params.get("H") or data_params.get("d")
            
            for est_result in estimator_results:
                if not est_result.get("success"):
                    continue
                
                error = est_result.get("error")
                if error is None or not np.isfinite(error):
                    continue
                
                # Determine band
                band_name = self._categorise_into_band(true_h, self.hurst_bands)
                
                if band_name not in bands_data:
                    bands_data[band_name] = self._init_band_bucket()
                
                self._update_band_bucket(
                    bands_data[band_name],
                    est_result,
                    model_name,
                    true_h
                )
        
        return {
            "bands": self._summarise_bands(bands_data),
            "total_observations": sum(b["count"] for b in bands_data.values())
        }
    
    def _stratify_by_estimated_h(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Stratify results by estimated Hurst parameter bands."""
        bands_data = {}
        
        for model_name, model_data in results.items():
            estimator_results = model_data.get("estimator_results", [])
            
            for est_result in estimator_results:
                if not est_result.get("success"):
                    continue
                
                error = est_result.get("error")
                estimated_h = est_result.get("estimated_hurst")
                
                if error is None or not np.isfinite(error):
                    continue
                if estimated_h is None or not np.isfinite(estimated_h):
                    continue
                
                # Determine band based on estimate
                band_name = self._categorise_into_band(estimated_h, self.hurst_bands)
                
                if band_name not in bands_data:
                    bands_data[band_name] = self._init_band_bucket()
                
                self._update_band_bucket(
                    bands_data[band_name],
                    est_result,
                    model_name,
                    est_result.get("true_hurst")
                )
        
        return {
            "bands": self._summarise_bands(bands_data),
            "total_observations": sum(b["count"] for b in bands_data.values()),
            "interpretation": "Stratification by estimated H shows where estimators place the data, revealing regime-dependent biases"
        }
    
    def _stratify_by_tail_class(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Stratify by tail/heaviness class."""
        class_data = {}
        
        # Reverse mapping for lookup
        model_to_class = {}
        for class_name, models in self.tail_classes.items():
            for model in models:
                model_to_class[model] = class_name
        
        for model_name, model_data in results.items():
            tail_class = model_to_class.get(model_name, "unknown")
            
            estimator_results = model_data.get("estimator_results", [])
            data_params = model_data.get("data_params", {})
            true_h = data_params.get("H") or data_params.get("d")
            
            for est_result in estimator_results:
                if not est_result.get("success"):
                    continue
                
                error = est_result.get("error")
                if error is None or not np.isfinite(error):
                    continue
                
                if tail_class not in class_data:
                    class_data[tail_class] = self._init_band_bucket()
                
                self._update_band_bucket(
                    class_data[tail_class],
                    est_result,
                    model_name,
                    true_h
                )
        
        return {
            "classes": self._summarise_bands(class_data),
            "total_observations": sum(b["count"] for b in class_data.values())
        }
    
    def _stratify_by_length(
        self, 
        results: Dict[str, Any],
        data_length: Optional[int]
    ) -> Dict[str, Any]:
        """Stratify by data length bands."""
        if data_length is None:
            return {"status": "unavailable", "reason": "Data length not provided"}
        
        length_band = self._categorise_into_band(data_length, self.length_bands)
        
        band_data = {length_band: self._init_band_bucket()}
        
        for model_name, model_data in results.items():
            estimator_results = model_data.get("estimator_results", [])
            data_params = model_data.get("data_params", {})
            true_h = data_params.get("H") or data_params.get("d")
            
            for est_result in estimator_results:
                if not est_result.get("success"):
                    continue
                
                error = est_result.get("error")
                if error is None or not np.isfinite(error):
                    continue
                
                self._update_band_bucket(
                    band_data[length_band],
                    est_result,
                    model_name,
                    true_h
                )
        
        return {
            "bands": self._summarise_bands(band_data),
            "data_length": data_length,
            "total_observations": sum(b["count"] for b in band_data.values())
        }
    
    def _stratify_by_contamination(
        self,
        results: Dict[str, Any],
        contamination_type: Optional[str],
        contamination_level: Optional[float]
    ) -> Dict[str, Any]:
        """Stratify by contamination type and level."""
        contam_key = "clean" if contamination_type is None else f"{contamination_type} (level={contamination_level})"
        
        contam_data = {contam_key: self._init_band_bucket()}
        
        for model_name, model_data in results.items():
            estimator_results = model_data.get("estimator_results", [])
            data_params = model_data.get("data_params", {})
            true_h = data_params.get("H") or data_params.get("d")
            
            for est_result in estimator_results:
                if not est_result.get("success"):
                    continue
                
                error = est_result.get("error")
                if error is None or not np.isfinite(error):
                    continue
                
                self._update_band_bucket(
                    contam_data[contam_key],
                    est_result,
                    model_name,
                    true_h
                )
        
        return {
            "scenarios": self._summarise_bands(contam_data),
            "contamination_type": contamination_type,
            "contamination_level": contamination_level,
            "total_observations": sum(b["count"] for b in contam_data.values())
        }
    
    def _stratify_by_estimator_family(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Stratify by estimator family (classical, ML, neural)."""
        # Determine families from estimator names
        family_keywords = {
            "classical": ["GPH", "Whittle", "Periodogram", "DFA", "DMA", "R/S", "Higuchi",
                         "CWT", "WaveletVar", "WaveletLogVar", "WaveletWhittle",
                         "MFDFA", "WaveletLeaders"],
            "ML": ["RandomForest", "GradientBoosting", "SVR", "XGBoost", "LightGBM"],
            "neural": ["CNN", "LSTM", "GRU", "Transformer", "ResNet"]
        }
        
        family_data = {}
        
        for model_name, model_data in results.items():
            estimator_results = model_data.get("estimator_results", [])
            data_params = model_data.get("data_params", {})
            true_h = data_params.get("H") or data_params.get("d")
            
            for est_result in estimator_results:
                if not est_result.get("success"):
                    continue
                
                error = est_result.get("error")
                if error is None or not np.isfinite(error):
                    continue
                
                estimator_name = est_result.get("estimator", "")
                
                # Determine family
                family = "other"
                for fam_name, keywords in family_keywords.items():
                    if any(kw in estimator_name for kw in keywords):
                        family = fam_name
                        break
                
                if family not in family_data:
                    family_data[family] = self._init_band_bucket()
                
                self._update_band_bucket(
                    family_data[family],
                    est_result,
                    model_name,
                    true_h
                )
        
        return {
            "families": self._summarise_bands(family_data),
            "total_observations": sum(b["count"] for b in family_data.values())
        }
    
    def _generate_cross_stratifications(
        self, 
        results: Dict[str, Any],
        full_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate cross-tabulations (e.g., H band × tail class)."""
        cross_tabs = {}
        
        # H band × tail class
        h_tail_cross = {}
        
        # Reverse mapping for tail classes
        model_to_class = {}
        for class_name, models in self.tail_classes.items():
            for model in models:
                model_to_class[model] = class_name
        
        for model_name, model_data in results.items():
            tail_class = model_to_class.get(model_name, "unknown")
            estimator_results = model_data.get("estimator_results", [])
            data_params = model_data.get("data_params", {})
            true_h = data_params.get("H") or data_params.get("d")
            
            h_band = self._categorise_into_band(true_h, self.hurst_bands)
            
            cross_key = f"{h_band} × {tail_class}"
            
            for est_result in estimator_results:
                if not est_result.get("success"):
                    continue
                
                error = est_result.get("error")
                if error is None or not np.isfinite(error):
                    continue
                
                if cross_key not in h_tail_cross:
                    h_tail_cross[cross_key] = self._init_band_bucket()
                
                self._update_band_bucket(
                    h_tail_cross[cross_key],
                    est_result,
                    model_name,
                    true_h
                )
        
        cross_tabs["h_band_x_tail_class"] = {
            "cross_tabulation": self._summarise_bands(h_tail_cross),
            "total_observations": sum(b["count"] for b in h_tail_cross.values())
        }
        
        return cross_tabs
    
    def _categorise_into_band(
        self, 
        value: Optional[float], 
        bands: List[Dict[str, Any]]
    ) -> str:
        """Categorise a value into the appropriate band."""
        if value is None or not np.isfinite(value):
            return "unknown"
        
        for band in bands:
            if band["min"] <= value < band["max"]:
                return band["name"]
        
        # Handle edge case for maximum value
        if bands and value >= bands[-1]["min"]:
            return bands[-1]["name"]
        
        return "unknown"
    
    def _init_band_bucket(self) -> Dict[str, Any]:
        """Initialise an empty band bucket."""
        return {
            "count": 0,
            "success": 0,
            "errors": [],
            "ci_widths": [],
            "coverage": [],
            "estimated_values": [],
            "true_values": [],
            "data_models": set(),
            "estimators": set(),
            "execution_times": [],
            "r_squared_values": [],
            "convergence_rates": [],
            "bias_percentages": []
        }
    
    def _update_band_bucket(
        self,
        bucket: Dict[str, Any],
        est_result: Dict[str, Any],
        model_name: str,
        true_h: Optional[float]
    ):
        """Update a band bucket with a new result."""
        bucket["count"] += 1
        
        if est_result.get("success"):
            bucket["success"] += 1
        
        error = est_result.get("error")
        if error is not None and np.isfinite(error):
            bucket["errors"].append(float(error))
        
        estimated_h = est_result.get("estimated_hurst")
        if estimated_h is not None and np.isfinite(estimated_h):
            bucket["estimated_values"].append(float(estimated_h))
        
        if true_h is not None and np.isfinite(true_h):
            bucket["true_values"].append(float(true_h))
        
        bucket["data_models"].add(model_name)
        bucket["estimators"].add(est_result.get("estimator"))
        
        exec_time = est_result.get("execution_time")
        if exec_time is not None:
            bucket["execution_times"].append(float(exec_time))
        
        r_squared = est_result.get("r_squared")
        if r_squared is not None and np.isfinite(r_squared):
            bucket["r_squared_values"].append(float(r_squared))
        
        # Advanced metrics
        advanced_metrics = est_result.get("advanced_metrics", {})
        
        convergence_rate = advanced_metrics.get("convergence_rate")
        if convergence_rate is not None and np.isfinite(convergence_rate):
            bucket["convergence_rates"].append(float(convergence_rate))
        
        bias_pct = advanced_metrics.get("bias_percentage")
        if bias_pct is not None and np.isfinite(bias_pct):
            bucket["bias_percentages"].append(float(bias_pct))
        
        # Confidence interval
        ci = est_result.get("confidence_interval")
        if isinstance(ci, (list, tuple)) and len(ci) == 2:
            if ci[0] is not None and ci[1] is not None:
                try:
                    width = float(ci[1]) - float(ci[0])
                    if np.isfinite(width):
                        bucket["ci_widths"].append(width)
                except (TypeError, ValueError):
                    pass
        
        # Coverage
        uncertainty = est_result.get("uncertainty", {})
        if isinstance(uncertainty, dict):
            coverage_data = uncertainty.get("coverage", {})
            if isinstance(coverage_data, dict):
                for cov_value in coverage_data.values():
                    if cov_value is not None:
                        bucket["coverage"].append(bool(cov_value))
                        break
    
    def _summarise_bands(self, bands_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Summarise band data into statistics."""
        summary = {}
        
        for band_name, bucket in bands_data.items():
            count = bucket["count"]
            success = bucket["success"]
            errors = bucket["errors"]
            ci_widths = bucket["ci_widths"]
            coverage = bucket["coverage"]
            estimates = bucket["estimated_values"]
            true_values = bucket["true_values"]
            exec_times = bucket["execution_times"]
            r_squared_vals = bucket["r_squared_values"]
            convergence_rates = bucket["convergence_rates"]
            bias_percentages = bucket["bias_percentages"]
            
            if count == 0:
                continue
            
            summary[band_name] = {
                "n": int(count),
                "success_rate": float(success / count) if count else 0.0,
                "mean_error": float(np.mean(errors)) if errors else None,
                "median_error": float(np.median(errors)) if errors else None,
                "std_error": float(np.std(errors)) if len(errors) > 1 else 0.0,
                "min_error": float(np.min(errors)) if errors else None,
                "max_error": float(np.max(errors)) if errors else None,
                "mean_ci_width": float(np.mean(ci_widths)) if ci_widths else None,
                "coverage_rate": float(np.mean(coverage)) if coverage else None,
                "mean_estimated_h": float(np.mean(estimates)) if estimates else None,
                "std_estimated_h": float(np.std(estimates)) if len(estimates) > 1 else None,
                "mean_true_h": float(np.mean(true_values)) if true_values else None,
                "mean_execution_time": float(np.mean(exec_times)) if exec_times else None,
                "mean_r_squared": float(np.mean(r_squared_vals)) if r_squared_vals else None,
                "mean_convergence_rate": float(np.mean(convergence_rates)) if convergence_rates else None,
                "mean_bias_percentage": float(np.mean(bias_percentages)) if bias_percentages else None,
                "data_models": sorted(bucket["data_models"]),
                "estimators": sorted(est for est in bucket["estimators"] if est is not None),
                "n_estimators": len([est for est in bucket["estimators"] if est is not None])
            }
        
        return summary
    
    def _save_markdown_report(self, data: Dict[str, Any], output_path: Path):
        """Save stratified report as Markdown."""
        lines = []
        
        lines.append("# Comprehensive Stratified Benchmark Report")
        lines.append("")
        
        metadata = data.get("metadata", {})
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Benchmark Type:** {metadata.get('benchmark_type', 'unknown')}")
        lines.append(f"**Data Length:** {metadata.get('data_length', 'unknown')}")
        if metadata.get("contamination_type"):
            lines.append(f"**Contamination:** {metadata['contamination_type']} (level={metadata.get('contamination_level', 0)})")
        lines.append(f"**Total Tests:** {metadata.get('total_tests', 0)} (Successful: {metadata.get('successful_tests', 0)})")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # True H stratification
        lines.append("## Stratification by True Hurst Parameter")
        lines.append("")
        self._add_stratification_table(
            lines, 
            data.get("true_h_stratification", {}).get("bands", {})
        )
        lines.append("")
        
        # Estimated H stratification
        lines.append("## Stratification by Estimated Hurst Parameter")
        lines.append("")
        est_h_data = data.get("estimated_h_stratification", {})
        if est_h_data.get("interpretation"):
            lines.append(f"*{est_h_data['interpretation']}*")
            lines.append("")
        self._add_stratification_table(
            lines,
            est_h_data.get("bands", {})
        )
        lines.append("")
        
        # Tail class stratification
        lines.append("## Stratification by Tail Class")
        lines.append("")
        self._add_stratification_table(
            lines,
            data.get("tail_class_stratification", {}).get("classes", {})
        )
        lines.append("")
        
        # Length stratification
        lines.append("## Stratification by Data Length")
        lines.append("")
        self._add_stratification_table(
            lines,
            data.get("length_stratification", {}).get("bands", {})
        )
        lines.append("")
        
        # Contamination stratification
        lines.append("## Stratification by Contamination")
        lines.append("")
        self._add_stratification_table(
            lines,
            data.get("contamination_stratification", {}).get("scenarios", {})
        )
        lines.append("")
        
        # Estimator family stratification
        lines.append("## Stratification by Estimator Family")
        lines.append("")
        self._add_stratification_table(
            lines,
            data.get("estimator_family_stratification", {}).get("families", {})
        )
        lines.append("")
        
        # Cross-stratifications
        lines.append("## Cross-Stratifications")
        lines.append("")
        cross_strat = data.get("cross_stratifications", {})
        h_tail = cross_strat.get("h_band_x_tail_class", {})
        if h_tail:
            lines.append("### Hurst Band × Tail Class")
            lines.append("")
            self._add_stratification_table(
                lines,
                h_tail.get("cross_tabulation", {})
            )
            lines.append("")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
    
    def _add_stratification_table(
        self, 
        lines: List[str], 
        bands: Dict[str, Any]
    ):
        """Add a stratification table to the report."""
        if not bands:
            lines.append("*No data available*")
            return
        
        # Table header
        lines.append("| Band | n | Success | Mean Error | Median Error | Std Error | Mean CI Width | Coverage | Mean Ĥ | Mean R² | Data Models |")
        lines.append("|------|---|---------|------------|--------------|-----------|---------------|----------|--------|---------|-------------|")
        
        # Sort bands by mean error
        sorted_bands = sorted(
            bands.items(),
            key=lambda x: (x[1].get("mean_error") is None, x[1].get("mean_error", 0.0))
        )
        
        for band_name, metrics in sorted_bands:
            n = metrics.get("n", 0)
            success_rate = metrics.get("success_rate", 0.0)
            mean_error = metrics.get("mean_error")
            median_error = metrics.get("median_error")
            std_error = metrics.get("std_error")
            mean_ci = metrics.get("mean_ci_width")
            coverage = metrics.get("coverage_rate")
            mean_h = metrics.get("mean_estimated_h")
            mean_r2 = metrics.get("mean_r_squared")
            models = metrics.get("data_models", [])
            
            lines.append(
                f"| {band_name} | {n} | {success_rate:.1%} | "
                f"{mean_error:.4f if mean_error is not None else 'N/A'} | "
                f"{median_error:.4f if median_error is not None else 'N/A'} | "
                f"{std_error:.4f if std_error is not None else 'N/A'} | "
                f"{mean_ci:.4f if mean_ci is not None else 'N/A'} | "
                f"{coverage:.1%if coverage is not None else 'N/A'} | "
                f"{mean_h:.4f if mean_h is not None else 'N/A'} | "
                f"{mean_r2:.3f if mean_r2 is not None else 'N/A'} | "
                f"{', '.join(models[:3]) + ('...' if len(models) > 3 else '')} |"
            )
    
    def _save_csv_reports(
        self, 
        data: Dict[str, Any], 
        output_dir: Path, 
        timestamp: str
    ):
        """Save stratified data as CSV files."""
        # Save each stratification as a separate CSV
        stratifications = [
            ("true_h", data.get("true_h_stratification", {}).get("bands", {})),
            ("estimated_h", data.get("estimated_h_stratification", {}).get("bands", {})),
            ("tail_class", data.get("tail_class_stratification", {}).get("classes", {})),
            ("length", data.get("length_stratification", {}).get("bands", {})),
            ("contamination", data.get("contamination_stratification", {}).get("scenarios", {})),
            ("estimator_family", data.get("estimator_family_stratification", {}).get("families", {}))
        ]
        
        for name, bands_data in stratifications:
            if not bands_data:
                continue
            
            csv_data = []
            for band_name, metrics in bands_data.items():
                row = {"band": band_name}
                row.update(metrics)
                # Convert sets to strings
                if "data_models" in row:
                    row["data_models"] = ", ".join(row["data_models"])
                if "estimators" in row:
                    row["estimators"] = ", ".join(row["estimators"])
                csv_data.append(row)
            
            if csv_data:
                df = pd.DataFrame(csv_data)
                csv_path = output_dir / f"stratified_{name}_{timestamp}.csv"
                df.to_csv(csv_path, index=False)
    
    def _save_html_report(self, data: Dict[str, Any], output_path: Path):
        """Save stratified report as HTML."""
        # Basic HTML template
        html = ["<!DOCTYPE html>", "<html>", "<head>"]
        html.append("<title>Stratified Benchmark Report</title>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("table { border-collapse: collapse; width: 100%; margin: 20px 0; }")
        html.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("th { background-color: #4CAF50; color: white; }")
        html.append("tr:nth-child(even) { background-color: #f2f2f2; }")
        html.append("h1, h2, h3 { color: #333; }")
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        html.append("<h1>Comprehensive Stratified Benchmark Report</h1>")
        
        metadata = data.get("metadata", {})
        html.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html.append(f"<p><strong>Benchmark Type:</strong> {metadata.get('benchmark_type', 'unknown')}</p>")
        
        # Add tables (simplified version)
        html.append("<h2>Summary</h2>")
        html.append("<p>Full HTML rendering not yet implemented. Please refer to JSON or Markdown outputs.</p>")
        
        html.append("</body>")
        html.append("</html>")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(html))

