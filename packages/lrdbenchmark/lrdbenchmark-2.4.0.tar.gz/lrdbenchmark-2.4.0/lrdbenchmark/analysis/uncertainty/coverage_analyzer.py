#!/usr/bin/env python3
"""
Coverage Probability Analyzer for LRDBenchmark.

Provides Monte Carlo estimation of confidence interval coverage probabilities
to assess the reliability of uncertainty quantification methods.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass
import warnings


@dataclass
class CoverageResult:
    """Results from coverage probability analysis."""
    method: str
    nominal_level: float
    empirical_coverage: float
    n_trials: int
    n_covered: int
    coverage_error: float
    standard_error: float
    calibrated: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'method': self.method,
            'nominal_level': self.nominal_level,
            'empirical_coverage': self.empirical_coverage,
            'n_trials': self.n_trials,
            'n_covered': self.n_covered,
            'coverage_error': self.coverage_error,
            'standard_error': self.standard_error,
            'calibrated': self.calibrated
        }


class CoverageAnalyzer:
    """
    Monte Carlo analyzer for confidence interval coverage probabilities.
    
    Assesses whether UQ methods produce calibrated confidence intervals
    by measuring how often the true value falls within the reported CI.
    
    Example
    -------
    >>> analyzer = CoverageAnalyzer(n_trials=200)
    >>> results = analyzer.analyze_estimator_coverage(
    ...     estimator_cls=DFAEstimator,
    ...     data_model_cls=FBMModel,
    ...     true_H=0.7,
    ...     length=1000
    ... )
    >>> print(f"Coverage: {results['block_bootstrap'].empirical_coverage:.2%}")
    """
    
    def __init__(
        self,
        n_trials: int = 100,
        confidence_level: float = 0.95,
        tolerance: float = 0.05,
        random_state: Optional[int] = None
    ):
        """
        Initialize coverage analyzer.
        
        Parameters
        ----------
        n_trials : int
            Number of Monte Carlo trials
        confidence_level : float
            Nominal confidence level
        tolerance : float
            Acceptable deviation from nominal coverage (for calibration check)
        random_state : int, optional
            Random seed
        """
        self.n_trials = n_trials
        self.confidence_level = confidence_level
        self.tolerance = tolerance
        self.rng = np.random.default_rng(random_state)
    
    def analyze_estimator_coverage(
        self,
        estimator_cls: Type,
        data_model_cls: Type,
        true_H: float,
        length: int,
        estimator_params: Optional[Dict[str, Any]] = None,
        data_model_params: Optional[Dict[str, Any]] = None,
        uq_methods: Optional[List[str]] = None,
        n_bootstrap: int = 64
    ) -> Dict[str, CoverageResult]:
        """
        Analyze coverage probability for an estimator-model combination.
        
        Parameters
        ----------
        estimator_cls : Type
            Estimator class (e.g., DFAEstimator)
        data_model_cls : Type
            Data generation model class (e.g., FBMModel)
        true_H : float
            True Hurst parameter
        length : int
            Length of generated time series
        estimator_params : dict, optional
            Parameters for estimator
        data_model_params : dict, optional
            Additional parameters for data model
        uq_methods : list of str, optional
            UQ methods to test: 'block_bootstrap', 'percentile', 'studentized'
        n_bootstrap : int
            Number of bootstrap samples per trial
        
        Returns
        -------
        dict
            Coverage results for each UQ method
        """
        estimator_params = estimator_params or {}
        data_model_params = data_model_params or {}
        uq_methods = uq_methods or ['block_bootstrap', 'percentile']
        
        # Track coverage for each method
        coverage_counts = {method: 0 for method in uq_methods}
        successful_trials = {method: 0 for method in uq_methods}
        
        for trial in range(self.n_trials):
            # Generate data
            seed = int(self.rng.integers(0, 2**32))
            try:
                model = data_model_cls(H=true_H, **data_model_params)
                data = model.generate(length=length, seed=seed)
            except Exception as e:
                warnings.warn(f"Data generation failed: {e}")
                continue
            
            # Create estimator and get point estimate
            try:
                estimator = estimator_cls(**estimator_params)
                result = estimator.estimate(data)
                point_estimate = result.get('hurst_parameter')
                
                if point_estimate is None or not np.isfinite(point_estimate):
                    continue
            except Exception as e:
                continue
            
            # Compute confidence intervals for each method
            for method in uq_methods:
                try:
                    ci = self._compute_ci(
                        estimator_cls, estimator_params,
                        data, method, n_bootstrap, seed
                    )
                    
                    if ci is not None:
                        lower, upper = ci
                        if lower <= true_H <= upper:
                            coverage_counts[method] += 1
                        successful_trials[method] += 1
                except Exception:
                    continue
        
        # Compute coverage statistics
        results = {}
        for method in uq_methods:
            n_successful = successful_trials[method]
            n_covered = coverage_counts[method]
            
            if n_successful > 0:
                empirical_coverage = n_covered / n_successful
                coverage_error = empirical_coverage - self.confidence_level
                # Standard error of proportion
                se = np.sqrt(empirical_coverage * (1 - empirical_coverage) / n_successful)
                calibrated = abs(coverage_error) <= self.tolerance
            else:
                empirical_coverage = 0.0
                coverage_error = -self.confidence_level
                se = 0.0
                calibrated = False
            
            results[method] = CoverageResult(
                method=method,
                nominal_level=self.confidence_level,
                empirical_coverage=empirical_coverage,
                n_trials=n_successful,
                n_covered=n_covered,
                coverage_error=coverage_error,
                standard_error=se,
                calibrated=calibrated
            )
        
        return results
    
    def _compute_ci(
        self,
        estimator_cls: Type,
        estimator_params: Dict[str, Any],
        data: np.ndarray,
        method: str,
        n_bootstrap: int,
        seed: int
    ) -> Optional[tuple]:
        """Compute confidence interval using specified method."""
        rng = np.random.default_rng(seed + hash(method) % 2**16)
        n = len(data)
        
        if n < 32:
            return None
        
        # Block bootstrap
        block_size = max(8, int(np.sqrt(n)))
        n_blocks = int(np.ceil(n / block_size))
        
        estimates = []
        for _ in range(n_bootstrap):
            # Resample blocks
            starts = rng.integers(0, n - block_size + 1, size=n_blocks)
            blocks = [data[s:s+block_size] for s in starts]
            resampled = np.concatenate(blocks)[:n]
            
            try:
                estimator = estimator_cls(**estimator_params)
                result = estimator.estimate(resampled)
                h_est = result.get('hurst_parameter')
                if h_est is not None and np.isfinite(h_est):
                    estimates.append(h_est)
            except Exception:
                continue
        
        if len(estimates) < 10:
            return None
        
        estimates = np.array(estimates)
        
        if method == 'block_bootstrap' or method == 'percentile':
            # Percentile method
            alpha = 1 - self.confidence_level
            lower = np.percentile(estimates, alpha/2 * 100)
            upper = np.percentile(estimates, (1 - alpha/2) * 100)
            return (lower, upper)
        
        elif method == 'studentized':
            # Studentized bootstrap (bias-corrected and accelerated)
            point_est = np.mean(estimates)
            se = np.std(estimates, ddof=1)
            
            # Use t-distribution critical value
            from scipy import stats
            df = len(estimates) - 1
            t_crit = stats.t.ppf((1 + self.confidence_level) / 2, df)
            
            lower = point_est - t_crit * se
            upper = point_est + t_crit * se
            return (lower, upper)
        
        return None
    
    def generate_coverage_report(
        self,
        results: Dict[str, CoverageResult]
    ) -> Dict[str, Any]:
        """
        Generate a summary report from coverage results.
        
        Returns
        -------
        dict
            Summary with calibration status and recommendations
        """
        report = {
            'methods': {},
            'best_method': None,
            'all_calibrated': True,
            'recommendations': []
        }
        
        best_error = float('inf')
        
        for method, result in results.items():
            report['methods'][method] = result.to_dict()
            
            if not result.calibrated:
                report['all_calibrated'] = False
                if result.coverage_error < 0:
                    report['recommendations'].append(
                        f"{method}: Coverage too low ({result.empirical_coverage:.1%} vs "
                        f"{self.confidence_level:.1%}). CIs are too narrow."
                    )
                else:
                    report['recommendations'].append(
                        f"{method}: Coverage too high ({result.empirical_coverage:.1%} vs "
                        f"{self.confidence_level:.1%}). CIs are too wide."
                    )
            
            if abs(result.coverage_error) < best_error:
                best_error = abs(result.coverage_error)
                report['best_method'] = method
        
        if report['all_calibrated']:
            report['recommendations'].append(
                "All methods are well-calibrated for this estimator-model combination."
            )
        
        return report


def run_comprehensive_coverage_analysis(
    estimator_cls: Type,
    data_model_cls: Type,
    H_values: List[float],
    length: int = 1000,
    n_trials: int = 100,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run coverage analysis across multiple H values.
    
    Parameters
    ----------
    estimator_cls : Type
        Estimator class
    data_model_cls : Type
        Data model class
    H_values : list of float
        H values to test
    length : int
        Series length
    n_trials : int
        Trials per H value
    seed : int
        Random seed
    
    Returns
    -------
    dict
        Comprehensive coverage results
    """
    analyzer = CoverageAnalyzer(n_trials=n_trials, random_state=seed)
    
    all_results = {}
    
    for H in H_values:
        results = analyzer.analyze_estimator_coverage(
            estimator_cls=estimator_cls,
            data_model_cls=data_model_cls,
            true_H=H,
            length=length
        )
        all_results[H] = {
            method: result.to_dict() for method, result in results.items()
        }
    
    # Summary statistics
    summary = {
        'H_values': H_values,
        'results_by_H': all_results,
        'mean_coverage': {},
        'overall_calibrated': True
    }
    
    methods = list(all_results[H_values[0]].keys())
    for method in methods:
        coverages = [all_results[H][method]['empirical_coverage'] for H in H_values]
        summary['mean_coverage'][method] = np.mean(coverages)
        
        # Check if all H values are calibrated
        for H in H_values:
            if not all_results[H][method]['calibrated']:
                summary['overall_calibrated'] = False
    
    return summary
