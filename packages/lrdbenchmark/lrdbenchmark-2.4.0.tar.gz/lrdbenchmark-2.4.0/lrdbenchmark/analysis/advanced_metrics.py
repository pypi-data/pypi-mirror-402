#!/usr/bin/env python3
"""
Advanced Metrics Module for LRDBench

This module provides advanced computational profiling and estimation evaluation
metrics including convergence rates and mean signed error calculations.
"""

import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from scipy import stats
from scipy.optimize import curve_fit
import warnings


class ConvergenceAnalyzer:
    """
    Analyzer for convergence rates and stability of estimators.
    
    This class provides methods to analyze how quickly estimators converge
    to stable estimates and how reliable their convergence is.
    """
    
    def __init__(self, convergence_threshold: float = 1e-6, max_iterations: int = 100):
        """
        Initialize the convergence analyzer.
        
        Parameters
        ----------
        convergence_threshold : float
            Threshold for considering convergence achieved
        max_iterations : int
            Maximum number of iterations to test
        """
        self.convergence_threshold = convergence_threshold
        self.max_iterations = max_iterations
    
    def analyze_convergence_rate(
        self, 
        estimator, 
        data: np.ndarray, 
        true_value: Optional[float] = None,
        data_subsets: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Analyze convergence rate of an estimator.
        
        Parameters
        ----------
        estimator : BaseEstimator
            Estimator instance to analyze
        data : np.ndarray
            Full dataset for analysis
        true_value : float, optional
            True parameter value for error calculation
        data_subsets : List[int], optional
            List of subset sizes to test. If None, uses geometric progression.
            
        Returns
        -------
        dict
            Convergence analysis results
        """
        if data_subsets is None:
            # Use geometric progression for subset sizes
            n = len(data)
            data_subsets = []
            # Start with larger minimum size to avoid spectral estimator issues
            current_size = max(100, n // 10)  # Start with at least 100 points or 10% of data
            while current_size <= n:
                data_subsets.append(current_size)
                current_size = int(current_size * 1.3)  # Slower progression
            data_subsets.append(n)  # Include full dataset
        
        estimates = []
        errors = []
        subset_sizes = []
        convergence_flags = []
        
        for subset_size in data_subsets:
            if subset_size > len(data):
                continue
                
            # Use first subset_size points
            subset_data = data[:subset_size]
            
            try:
                # Estimate parameter
                result = estimator.estimate(subset_data)
                estimate = result.get('hurst_parameter', None)
                
                if estimate is not None:
                    estimates.append(estimate)
                    subset_sizes.append(subset_size)
                    
                    # Calculate error if true value is provided
                    if true_value is not None:
                        error = abs(estimate - true_value)
                        errors.append(error)
                    else:
                        errors.append(None)
                    
                    # Check convergence
                    if len(estimates) > 1:
                        convergence = abs(estimates[-1] - estimates[-2]) < self.convergence_threshold
                        convergence_flags.append(convergence)
                    else:
                        convergence_flags.append(False)
                        
            except Exception as e:
                warnings.warn(f"Failed to estimate for subset size {subset_size}: {e}")
                continue
        
        if len(estimates) < 2:
            return {
                'convergence_rate': None,
                'convergence_achieved': False,
                'final_estimate': estimates[0] if estimates else None,
                'convergence_iteration': None,
                'stability_metric': None,
                'subset_sizes': subset_sizes,
                'estimates': estimates,
                'errors': errors
            }
        
        # Calculate convergence rate
        convergence_rate = self._calculate_convergence_rate(estimates, subset_sizes)
        
        # Find convergence point
        convergence_iteration = None
        for i, converged in enumerate(convergence_flags):
            if converged:
                convergence_iteration = i + 1
                break
        
        # Calculate stability metric
        stability_metric = self._calculate_stability_metric(estimates)
        
        return {
            'convergence_rate': convergence_rate,
            'convergence_achieved': convergence_iteration is not None,
            'convergence_iteration': convergence_iteration,
            'final_estimate': estimates[-1],
            'stability_metric': stability_metric,
            'subset_sizes': subset_sizes,
            'estimates': estimates,
            'errors': errors,
            'convergence_flags': convergence_flags
        }
    
    def _calculate_convergence_rate(self, estimates: List[float], subset_sizes: List[int]) -> float:
        """
        Calculate the rate of convergence.
        
        Parameters
        ----------
        estimates : List[float]
            List of estimates
        subset_sizes : List[int]
            List of corresponding subset sizes
            
        Returns
        -------
        float
            Convergence rate (negative value indicates convergence)
        """
        if len(estimates) < 3:
            return None
        
        # Use log-log regression to estimate convergence rate
        # log(error) = a * log(n) + b
        errors = np.abs(np.diff(estimates))
        n_values = np.array(subset_sizes[1:])
        
        # Remove zero errors to avoid log(0)
        valid_indices = errors > 0
        if np.sum(valid_indices) < 2:
            return None
        
        log_errors = np.log(errors[valid_indices])
        log_n = np.log(n_values[valid_indices])
        
        try:
            # Fit linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(log_n, log_errors)
            return slope
        except:
            return None
    
    def _calculate_stability_metric(self, estimates: List[float]) -> float:
        """
        Calculate stability metric based on variance of estimates.
        
        Parameters
        ----------
        estimates : List[float]
            List of estimates
            
        Returns
        -------
        float
            Stability metric (lower is more stable)
        """
        if len(estimates) < 2:
            return None
        
        # Use coefficient of variation as stability metric
        estimates_array = np.array(estimates)
        mean_estimate = np.mean(estimates_array)
        std_estimate = np.std(estimates_array)
        
        if mean_estimate == 0:
            return None
        
        return std_estimate / abs(mean_estimate)


class MeanSignedErrorAnalyzer:
    """
    Analyzer for mean signed error and bias assessment.
    
    This class provides methods to calculate mean signed error and
    assess systematic bias in estimators.
    """
    
    def __init__(self):
        """Initialize the mean signed error analyzer."""
        pass
    
    def calculate_mean_signed_error(
        self, 
        estimates: List[float], 
        true_values: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate mean signed error and related metrics.
        
        Parameters
        ----------
        estimates : List[float]
            List of estimated values
        true_values : List[float]
            List of true values
            
        Returns
        -------
        dict
            Mean signed error analysis results
        """
        if len(estimates) != len(true_values):
            raise ValueError("Estimates and true values must have the same length")
        
        estimates_array = np.array(estimates)
        true_values_array = np.array(true_values)
        
        # Calculate signed errors
        signed_errors = estimates_array - true_values_array
        
        # Calculate metrics
        mean_signed_error = np.mean(signed_errors)
        mean_absolute_error = np.mean(np.abs(signed_errors))
        root_mean_squared_error = np.sqrt(np.mean(signed_errors**2))
        
        # Calculate bias metrics
        bias_percentage = (mean_signed_error / np.mean(np.abs(true_values_array))) * 100
        
        # Test for significant bias
        t_stat, p_value = stats.ttest_1samp(signed_errors, 0)
        
        # Calculate confidence interval for bias
        std_error = np.std(signed_errors, ddof=1) / np.sqrt(len(signed_errors))
        confidence_interval = stats.t.interval(
            0.95, 
            len(signed_errors) - 1, 
            loc=mean_signed_error, 
            scale=std_error
        )
        
        return {
            'mean_signed_error': mean_signed_error,
            'mean_absolute_error': mean_absolute_error,
            'root_mean_squared_error': root_mean_squared_error,
            'bias_percentage': bias_percentage,
            't_statistic': t_stat,
            'p_value': p_value,
            'significant_bias': p_value < 0.05,
            'confidence_interval_95': confidence_interval,
            'std_error': std_error,
            'signed_errors': signed_errors.tolist(),
            'estimates': estimates,
            'true_values': true_values
        }
    
    def analyze_bias_pattern(
        self, 
        estimates: List[float], 
        true_values: List[float],
        additional_variables: Optional[Dict[str, List[float]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze bias patterns and relationships with other variables.
        
        Parameters
        ----------
        estimates : List[float]
            List of estimated values
        true_values : List[float]
            List of true values
        additional_variables : Dict[str, List[float]], optional
            Additional variables to analyze bias relationships with
            
        Returns
        -------
        dict
            Bias pattern analysis results
        """
        mse_results = self.calculate_mean_signed_error(estimates, true_values)
        signed_errors = mse_results['signed_errors']
        
        bias_patterns = {
            'overestimation_frequency': np.sum(np.array(signed_errors) > 0) / len(signed_errors),
            'underestimation_frequency': np.sum(np.array(signed_errors) < 0) / len(signed_errors),
            'zero_error_frequency': np.sum(np.array(signed_errors) == 0) / len(signed_errors),
            'error_range': (np.min(signed_errors), np.max(signed_errors)),
            'error_skewness': stats.skew(signed_errors) if len(signed_errors) > 2 else 0.0,
            'error_kurtosis': stats.kurtosis(signed_errors) if len(signed_errors) > 3 else 0.0
        }
        
        # Analyze relationships with additional variables
        variable_correlations = {}
        if additional_variables:
            for var_name, var_values in additional_variables.items():
                if len(var_values) == len(signed_errors):
                    try:
                        # Check for constant input
                        if np.std(var_values) == 0:
                            variable_correlations[var_name] = {
                                'correlation': None,
                                'p_value': None,
                                'significant': False
                            }
                        else:
                            correlation, p_value = stats.pearsonr(signed_errors, var_values)
                            variable_correlations[var_name] = {
                                'correlation': correlation,
                                'p_value': p_value,
                                'significant': p_value < 0.05
                            }
                    except:
                        variable_correlations[var_name] = {
                            'correlation': None,
                            'p_value': None,
                            'significant': False
                        }
        
        return {
            **mse_results,
            'bias_patterns': bias_patterns,
            'variable_correlations': variable_correlations
        }


class ScalingInfluenceAnalyzer:
    """
    Analyse log–log scaling diagnostics and window influence for LRD estimators.
    """

    def analyse(
        self,
        scales: np.ndarray,
        statistics: np.ndarray,
        min_points: int = 4,
    ) -> Dict[str, Any]:
        """
        Fit log–log relationships and compute influence diagnostics.
        """
        scales = np.asarray(scales, dtype=np.float64)
        statistics = np.asarray(statistics, dtype=np.float64)

        valid_mask = np.isfinite(scales) & np.isfinite(statistics) & (scales > 0) & (statistics > 0)
        scales = scales[valid_mask]
        statistics = statistics[valid_mask]

        if len(scales) < min_points:
            return {
                "status": "insufficient_data",
                "reason": f"Need at least {min_points} valid scale points.",
            }

        log_scales = np.log2(scales)
        log_stats = np.log2(statistics)

        slope, intercept, r_value, p_value, std_err = stats.linregress(log_scales, log_stats)

        influence = self._leave_one_out_influence(log_scales, log_stats)
        breakpoint = self._detect_breakpoint(log_scales, log_stats)

        return {
            "status": "ok",
            "slope": float(slope),
            "intercept": float(intercept),
            "r_value": float(r_value),
            "r_squared": float(r_value ** 2),
            "p_value": float(p_value),
            "std_err": float(std_err),
            "n_points": int(len(log_scales)),
            "leave_one_out": influence,
            "breakpoint": breakpoint,
        }

    def _leave_one_out_influence(
        self, log_scales: np.ndarray, log_stats: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Assess influence of individual scale windows."""
        influence_results: List[Dict[str, Any]] = []
        n_points = len(log_scales)
        if n_points <= 3:
            return influence_results

        full_slope, _, _, _, _ = stats.linregress(log_scales, log_stats)

        for idx in range(n_points):
            mask = np.ones(n_points, dtype=bool)
            mask[idx] = False
            try:
                slope, _, _, _, _ = stats.linregress(log_scales[mask], log_stats[mask])
                delta = slope - full_slope
                influence_results.append(
                    {
                        "index": int(idx),
                        "scale": float(2 ** log_scales[idx]),
                        "slope_without": float(slope),
                        "delta_slope": float(delta),
                    }
                )
            except Exception:
                continue

        influence_results.sort(key=lambda item: abs(item["delta_slope"]), reverse=True)
        return influence_results

    def _detect_breakpoint(
        self, log_scales: np.ndarray, log_stats: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """Detect simple slope breakpoints via two-segment regression."""
        n_points = len(log_scales)
        if n_points < 6:
            return None

        best_score = np.inf
        best_break: Optional[Dict[str, Any]] = None

        for split in range(2, n_points - 2):
            left_x, left_y = log_scales[:split], log_stats[:split]
            right_x, right_y = log_scales[split:], log_stats[split:]
            try:
                left_fit = stats.linregress(left_x, left_y)
                right_fit = stats.linregress(right_x, right_y)
            except Exception:
                continue

            left_resid = left_y - (left_fit.intercept + left_fit.slope * left_x)
            right_resid = right_y - (right_fit.intercept + right_fit.slope * right_x)
            rss = np.sum(left_resid ** 2) + np.sum(right_resid ** 2)

            if rss < best_score:
                best_score = rss
                best_break = {
                    "break_scale": float(2 ** log_scales[split]),
                    "left_slope": float(left_fit.slope),
                    "right_slope": float(right_fit.slope),
                    "rss": float(rss),
                }

        return best_break


class RobustnessStressTester:
    """
    Generate standard stress panels (missingness, regime shifts, bursts, oscillations) for estimators.
    
    Implements standard robustness stress tests including:
    - Missingness patterns: MCAR (Missing Completely At Random), MAR (Missing At Random), 
      MNAR (Missing Not At Random), and block missing
    - Regime shifts: sudden changes in mean/scale
    - Burst noise: intermittent high-magnitude noise
    - Oscillations: additive periodic components
    """

    def __init__(self, random_state: Optional[int] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize robustness stress tester.
        
        Parameters
        ----------
        random_state : int, optional
            Random seed for reproducibility
        config : dict, optional
            Configuration dictionary with scenario parameters:
            - missing_rate: float (default 0.1)
            - block_fraction: float (default 0.2)
            - regime_shift: float (default 0.5)
            - burst_rate: float (default 0.05)
            - burst_magnitude: float (default 3.0)
            - oscillation_amplitude: float (default 0.3)
            - oscillation_frequency: float (default 0.1)
        """
        self._rng = np.random.default_rng(random_state)
        self.config = config or {}
        self.missing_rate = self.config.get("missing_rate", 0.1)
        self.block_fraction = self.config.get("block_fraction", 0.2)
        self.regime_shift = self.config.get("regime_shift", 0.5)
        self.burst_rate = self.config.get("burst_rate", 0.05)
        self.burst_magnitude = self.config.get("burst_magnitude", 3.0)
        self.oscillation_amplitude = self.config.get("oscillation_amplitude", 0.3)
        self.oscillation_frequency = self.config.get("oscillation_frequency", 0.1)

    def run_panels(
        self,
        estimator,
        data: np.ndarray,
        baseline_result: Optional[Dict[str, Any]] = None,
        true_value: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute robustness scenarios and report estimator sensitivity.
        
        Returns before/after H comparisons for each scenario to quantify
        preprocessing-induced bias and variance.
        """
        if baseline_result is None:
            return None

        baseline_estimate = baseline_result.get("hurst_parameter")
        if baseline_estimate is None or not np.isfinite(baseline_estimate):
            return None

        scenarios = {
            "missing_mcar": lambda x: self._apply_missing_mcar(x, rate=self.missing_rate),
            "missing_mar": lambda x: self._apply_missing_mar(x, rate=self.missing_rate),
            "missing_mnar": lambda x: self._apply_missing_mnar(x, rate=self.missing_rate),
            "missing_block": lambda x: self._apply_block_missing(x, block_fraction=self.block_fraction),
            "regime_shift": lambda x: self._apply_regime_shift(x, shift=self.regime_shift),
            "burst_noise": lambda x: self._apply_burst_noise(x, rate=self.burst_rate, magnitude=self.burst_magnitude),
            "oscillation": lambda x: self._apply_oscillation(x, amplitude=self.oscillation_amplitude, frequency=self.oscillation_frequency),
        }

        scenario_results: Dict[str, Dict[str, Any]] = {}
        deltas: List[float] = []
        successes = 0

        for name, transformer in scenarios.items():
            transformed = transformer(np.asarray(data, dtype=np.float64).copy())
            transformed = transformed[np.isfinite(transformed)]
            if len(transformed) < 32:
                scenario_results[name] = {
                    "status": "insufficient_data",
                    "reason": "Transformed series too short after cleaning.",
                }
                continue

            cloned = self._clone_estimator(estimator)
            start_time = time.time()
            try:
                result = cloned.estimate(transformed)
            except Exception as exc:
                scenario_results[name] = {
                    "status": "failed",
                    "reason": str(exc),
                }
                continue

            success = True
            estimate = result.get("hurst_parameter")
            execution_time = time.time() - start_time

            if estimate is None or not np.isfinite(estimate):
                scenario_results[name] = {
                    "status": "failed",
                    "reason": "Estimator returned non-finite H.",
                    "execution_time": execution_time,
                }
                continue

            delta = float(estimate - baseline_estimate)
            abs_delta = abs(delta)
            deltas.append(abs_delta)
            successes += 1

            # Calculate relative change
            relative_delta = delta / baseline_estimate if baseline_estimate != 0 else None

            scenario_results[name] = {
                "status": "ok",
                "before_h": float(baseline_estimate),  # H before stress test
                "after_h": float(estimate),  # H after stress test
                "delta_h": delta,  # Absolute change
                "abs_delta_h": abs_delta,  # Absolute magnitude of change
                "relative_delta_h": relative_delta,  # Relative change (%)
                "execution_time": execution_time,
                "true_value": float(true_value) if true_value is not None else None,
                "bias": delta if true_value is not None else None,  # Bias relative to true value
            }

        if not scenario_results:
            return None

        summary = {
            "n_scenarios": len(scenario_results),
            "successful_scenarios": successes,
            "mean_abs_delta": float(np.mean(deltas)) if deltas else None,
            "max_abs_delta": float(np.max(deltas)) if deltas else None,
            "baseline_estimate": float(baseline_estimate),
        }

        return {
            "baseline_estimate": float(baseline_estimate),
            "scenarios": scenario_results,
            "summary": summary,
        }

    def _clone_estimator(self, estimator):
        estimator_cls = estimator.__class__
        params: Dict[str, Any] = {}
        if hasattr(estimator, "get_params"):
            try:
                params = dict(estimator.get_params())
            except Exception:
                params = getattr(estimator, "parameters", {}).copy()
        else:
            params = getattr(estimator, "parameters", {}).copy()
        try:
            return estimator_cls(**params)
        except Exception:
            return estimator_cls()

    def _apply_missing_mcar(self, data: np.ndarray, rate: float) -> np.ndarray:
        """
        Apply Missing Completely At Random (MCAR) pattern.
        Missingness is independent of observed and unobserved data.
        """
        mask = self._rng.random(len(data)) < rate
        data[mask] = np.nan
        return data

    def _apply_missing_mar(self, data: np.ndarray, rate: float) -> np.ndarray:
        """
        Apply Missing At Random (MAR) pattern.
        Missingness depends on observed values (e.g., higher values more likely to be missing).
        """
        # Normalize data to [0, 1] for probability calculation
        data_normalized = (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data) + 1e-10)
        # Higher values have higher probability of being missing
        prob_missing = rate * (0.5 + data_normalized)
        prob_missing = np.clip(prob_missing, 0, 1)
        mask = self._rng.random(len(data)) < prob_missing
        data[mask] = np.nan
        return data

    def _apply_missing_mnar(self, data: np.ndarray, rate: float) -> np.ndarray:
        """
        Apply Missing Not At Random (MNAR) pattern.
        Missingness depends on the unobserved values themselves (e.g., extreme values more likely missing).
        """
        # Use absolute values to identify extremes
        abs_data = np.abs(data)
        threshold = np.percentile(abs_data, 100 * (1 - rate))
        # Values above threshold more likely to be missing
        prob_missing = np.where(abs_data > threshold, rate * 2, rate * 0.5)
        prob_missing = np.clip(prob_missing, 0, 1)
        mask = self._rng.random(len(data)) < prob_missing
        data[mask] = np.nan
        return data

    def _apply_block_missing(self, data: np.ndarray, block_fraction: float) -> np.ndarray:
        """
        Apply block missing pattern (consecutive missing values).
        """
        n = len(data)
        block_size = max(1, int(n * block_fraction * 0.3))
        start_idx = self._rng.integers(0, max(1, n - block_size))
        data[start_idx:start_idx + block_size] = np.nan
        return data

    def _apply_regime_shift(self, data: np.ndarray, shift: float) -> np.ndarray:
        """
        Apply regime shift (sudden change in mean/scale).
        """
        n = len(data)
        halfway = n // 2
        data[halfway:] = data[halfway:] + shift
        return data

    def _apply_burst_noise(self, data: np.ndarray, rate: float, magnitude: float) -> np.ndarray:
        """
        Apply intermittent burst noise (high-magnitude noise at random points).
        """
        mask = self._rng.random(len(data)) < rate
        noise = self._rng.normal(0, magnitude, size=len(data))
        data[mask] = data[mask] + noise[mask]
        return data

    def _apply_oscillation(self, data: np.ndarray, amplitude: float, frequency: float) -> np.ndarray:
        """
        Apply additive oscillation (periodic component).
        
        Parameters
        ----------
        amplitude : float
            Amplitude of oscillation relative to data std
        frequency : float
            Frequency as fraction of Nyquist (0 to 0.5)
        """
        n = len(data)
        t = np.arange(n)
        # Convert frequency to period
        period = int(1.0 / frequency) if frequency > 0 else n // 4
        period = max(4, min(period, n // 2))  # Ensure reasonable period
        oscillation = amplitude * np.std(data) * np.sin(2 * np.pi * t / period)
        return data + oscillation


class AdvancedPerformanceProfiler:
    """
    Comprehensive performance profiler with convergence and bias analysis.
    
    This class combines convergence analysis and mean signed error analysis
    to provide comprehensive performance profiling for estimators.
    """
    
    def __init__(
        self,
        convergence_threshold: float = 1e-6,
        max_iterations: int = 100,
        random_state: Optional[int] = None,
    ):
        """
        Initialize the advanced performance profiler.
        
        Parameters
        ----------
        convergence_threshold : float
            Threshold for convergence detection
        max_iterations : int
            Maximum iterations for convergence analysis
        """
        self.convergence_analyzer = ConvergenceAnalyzer(convergence_threshold, max_iterations)
        self.mse_analyzer = MeanSignedErrorAnalyzer()
        self.scaling_analyzer = ScalingInfluenceAnalyzer()
        self.stress_tester = RobustnessStressTester(random_state=random_state)
        self._rng = np.random.default_rng(random_state)
    
    def profile_estimator_performance(
        self,
        estimator,
        data: np.ndarray,
        true_value: Optional[float] = None,
        n_monte_carlo: int = 100,
        data_subsets: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive performance profiling of an estimator.
        
        Parameters
        ----------
        estimator : BaseEstimator
            Estimator to profile
        data : np.ndarray
            Dataset for analysis
        true_value : float, optional
            True parameter value
        n_monte_carlo : int
            Number of Monte Carlo simulations for bias analysis
        data_subsets : List[int], optional
            Subset sizes for convergence analysis
            
        Returns
        -------
        dict
            Comprehensive performance profile
        """
        # Basic performance metrics
        start_time = time.time()
        try:
            result = estimator.estimate(data)
            execution_time = time.time() - start_time
            success = True
            error_message = None
        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            error_message = str(e)
            result = None
        
        # Convergence analysis
        convergence_results = None
        if success and true_value is not None:
            convergence_results = self.convergence_analyzer.analyze_convergence_rate(
                estimator, data, true_value, data_subsets
            )
        
        # Monte Carlo bias analysis
        bias_results = None
        if success and true_value is not None and n_monte_carlo > 0:
            bias_results = self._monte_carlo_bias_analysis(
                estimator, data, true_value, n_monte_carlo
            )

        scaling_diagnostics = None
        if success and isinstance(result, dict):
            scaling_payload = self._extract_scaling_payload(result, estimator)
            if scaling_payload:
                scaling_diagnostics = self.scaling_analyzer.analyse(
                    scaling_payload["scales"],
                    scaling_payload["statistics"],
                )

        robustness_panel = None
        if success and isinstance(result, dict):
            robustness_panel = self.stress_tester.run_panels(
                estimator=estimator,
                data=data,
                baseline_result=result,
                true_value=true_value,
            )
        
        return {
            'basic_performance': {
                'success': success,
                'execution_time': execution_time,
                'error_message': error_message,
                'result': result
            },
            'convergence_analysis': convergence_results,
            'bias_analysis': bias_results,
            'scaling_diagnostics': scaling_diagnostics,
            'robustness_panel': robustness_panel,
            'comprehensive_score': self._calculate_comprehensive_score(
                success, execution_time, convergence_results, bias_results
            )
        }
    
    def _monte_carlo_bias_analysis(
        self,
        estimator,
        data: np.ndarray,
        true_value: float,
        n_simulations: int
    ) -> Dict[str, Any]:
        """
        Perform Monte Carlo bias analysis.
        
        Parameters
        ----------
        estimator : BaseEstimator
            Estimator to analyze
        data : np.ndarray
            Original dataset
        true_value : float
            True parameter value
        n_simulations : int
            Number of Monte Carlo simulations
            
        Returns
        -------
        dict
            Monte Carlo bias analysis results
        """
        estimates = []
        execution_times = []
        
        for i in range(n_simulations):
            # Add small random noise to create variations
            noise_level = 0.01 * np.std(data)
            noisy_data = data + self._rng.normal(0, noise_level, len(data))
            
            start_time = time.time()
            try:
                result = estimator.estimate(noisy_data)
                estimate = result.get('hurst_parameter', None)
                if estimate is not None:
                    estimates.append(estimate)
                    execution_times.append(time.time() - start_time)
            except:
                continue
        
        if len(estimates) == 0:
            return None
        
        # Create true values list (all same value)
        true_values = [true_value] * len(estimates)
        
        # Calculate bias metrics
        bias_results = self.mse_analyzer.analyze_bias_pattern(
            estimates, true_values, 
            additional_variables={'execution_time': execution_times}
        )
        
        return bias_results
    
    def _calculate_comprehensive_score(
        self,
        success: bool,
        execution_time: float,
        convergence_results: Optional[Dict[str, Any]],
        bias_results: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate comprehensive performance score.
        
        Parameters
        ----------
        success : bool
            Whether estimation was successful
        execution_time : float
            Execution time
        convergence_results : dict, optional
            Convergence analysis results
        bias_results : dict, optional
            Bias analysis results
            
        Returns
        -------
        float
            Comprehensive performance score (0-1, higher is better)
        """
        if not success:
            return 0.0
        
        score = 1.0
        
        # Execution time penalty (normalize to reasonable range)
        if execution_time > 1.0:  # Penalize if takes more than 1 second
            score *= max(0.1, 1.0 / execution_time)
        
        # Convergence bonus
        if convergence_results and convergence_results.get('convergence_achieved'):
            score *= 1.2  # 20% bonus for convergence
        
        # Bias penalty
        if bias_results:
            mse = bias_results.get('mean_signed_error', 0)
            if abs(mse) > 0.1:  # Penalize significant bias
                score *= max(0.5, 1.0 - abs(mse))
        
        return min(1.0, max(0.0, score))

    def _extract_scaling_payload(
        self,
        result: Dict[str, Any],
        estimator,
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Attempt to extract scale/statistic arrays from estimator results.
        """
        if not isinstance(result, dict):
            return None

        candidates: List[Tuple[Any, Any]] = []

        scale_stats = result.get("scale_statistics")
        if isinstance(scale_stats, dict):
            candidates.append(
                (scale_stats.get("scales"), scale_stats.get("statistics") or scale_stats.get("values"))
            )

        candidates.append((result.get("scales"), result.get("values")))
        candidates.append((result.get("log_scales"), result.get("log_values")))

        for scales, stats in candidates:
            if scales is None or stats is None:
                continue
            try:
                return {
                    "scales": np.asarray(scales, dtype=np.float64),
                    "statistics": np.asarray(stats, dtype=np.float64),
                }
            except Exception:
                continue

        getter = getattr(estimator, "get_scaling_diagnostics", None)
        if callable(getter):
            try:
                payload = getter()
                if isinstance(payload, dict):
                    scales = payload.get("scales")
                    stats = payload.get("statistics") or payload.get("values")
                    if scales is not None and stats is not None:
                        return {
                            "scales": np.asarray(scales, dtype=np.float64),
                            "statistics": np.asarray(stats, dtype=np.float64),
                        }
            except Exception:
                return None

        return None


def calculate_convergence_rate(estimates: List[float], subset_sizes: List[int]) -> float:
    """
    Calculate convergence rate from estimates and subset sizes.
    
    Parameters
    ----------
    estimates : List[float]
        List of estimates
    subset_sizes : List[int]
        List of corresponding subset sizes
        
    Returns
    -------
    float
        Convergence rate
    """
    analyzer = ConvergenceAnalyzer()
    return analyzer._calculate_convergence_rate(estimates, subset_sizes)


def calculate_mean_signed_error(estimates: List[float], true_values: List[float]) -> Dict[str, Any]:
    """
    Calculate mean signed error and related metrics.
    
    Parameters
    ----------
    estimates : List[float]
        List of estimated values
    true_values : List[float]
        List of true values
        
    Returns
    -------
    dict
        Mean signed error analysis results
    """
    analyzer = MeanSignedErrorAnalyzer()
    return analyzer.calculate_mean_signed_error(estimates, true_values)


def profile_estimator_performance(
    estimator,
    data: np.ndarray,
    true_value: Optional[float] = None,
    n_monte_carlo: int = 100
) -> Dict[str, Any]:
    """
    Profile estimator performance with advanced metrics.
    
    Parameters
    ----------
    estimator : BaseEstimator
        Estimator to profile
    data : np.ndarray
        Dataset for analysis
    true_value : float, optional
        True parameter value
    n_monte_carlo : int
        Number of Monte Carlo simulations
        
    Returns
    -------
    dict
        Performance profile with convergence and bias analysis
    """
    profiler = AdvancedPerformanceProfiler()
    return profiler.profile_estimator_performance(
        estimator, data, true_value, n_monte_carlo
    )
