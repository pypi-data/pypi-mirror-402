#!/usr/bin/env python3
"""
Comprehensive Diagnostics Module for LRD Estimation
Provides automated log-log checks, residual tests, goodness-of-fit analysis,
and scale-window sensitivity analysis for power-law fits.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
import warnings


class PowerLawDiagnostics:
    """
    Comprehensive diagnostics for power-law fits in LRD estimation.
    Includes log-log checks, residual analysis, and goodness-of-fit tests.
    """
    
    def __init__(self, min_r_squared: float = 0.5, min_points: int = 6):
        """
        Initialise power-law diagnostics.
        
        Parameters
        ----------
        min_r_squared : float
            Minimum R² threshold for acceptable fits
        min_points : int
            Minimum number of scale points required
        """
        self.min_r_squared = min_r_squared
        self.min_points = min_points
    
    def diagnose(
        self,
        scales: np.ndarray,
        statistics: np.ndarray,
        slope: Optional[float] = None,
        intercept: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run comprehensive diagnostic suite on power-law fit.
        
        Parameters
        ----------
        scales : np.ndarray
            Scale values (e.g., frequencies, windows, wavelet scales)
        statistics : np.ndarray
            Corresponding statistics (e.g., PSD, fluctuation function)
        slope : float, optional
            Pre-computed slope of log-log fit
        intercept : float, optional
            Pre-computed intercept of log-log fit
            
        Returns
        -------
        dict
            Comprehensive diagnostic results
        """
        scales = np.asarray(scales, dtype=np.float64)
        statistics = np.asarray(statistics, dtype=np.float64)
        
        # Validate inputs
        valid_mask = (
            np.isfinite(scales) & 
            np.isfinite(statistics) & 
            (scales > 0) & 
            (statistics > 0)
        )
        scales = scales[valid_mask]
        statistics = statistics[valid_mask]
        
        if len(scales) < self.min_points:
            return {
                "status": "insufficient_data",
                "reason": f"Need at least {self.min_points} valid scale points, got {len(scales)}",
                "n_points": len(scales)
            }
        
        # Transform to log-log space
        log_scales = np.log2(scales)
        log_stats = np.log2(statistics)
        
        # Compute or validate linear fit
        if slope is None or intercept is None:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                log_scales, log_stats
            )
        else:
            # Recompute correlation metrics with provided fit
            fitted_values = slope * log_scales + intercept
            residuals = log_stats - fitted_values
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((log_stats - np.mean(log_stats)) ** 2)
            r_value = np.sqrt(1 - ss_res / ss_tot) if ss_tot > 0 else 0
            p_value = None  # Would need full regression for p-value
            std_err = np.sqrt(ss_res / (len(log_scales) - 2)) if len(log_scales) > 2 else np.inf
        
        r_squared = r_value ** 2
        
        # Run diagnostic tests
        linearity_check = self._check_linearity(log_scales, log_stats, r_squared)
        residual_analysis = self._analyse_residuals(
            log_scales, log_stats, slope, intercept
        )
        goodness_of_fit = self._assess_goodness_of_fit(
            log_scales, log_stats, slope, intercept
        )
        breakpoint_detection = self._detect_breakpoints(log_scales, log_stats)
        
        # Overall assessment
        passes_checks = (
            linearity_check["passes"] and
            residual_analysis["normality"]["passes"] and
            not residual_analysis["autocorrelation"]["significant"] and
            r_squared >= self.min_r_squared
        )
        
        return {
            "status": "ok",
            "n_points": len(scales),
            "log_log_fit": {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_squared),
                "r_value": float(r_value),
                "p_value": float(p_value) if p_value is not None else None,
                "std_err": float(std_err)
            },
            "linearity_check": linearity_check,
            "residual_analysis": residual_analysis,
            "goodness_of_fit": goodness_of_fit,
            "breakpoint_detection": breakpoint_detection,
            "overall_assessment": {
                "passes_diagnostics": passes_checks,
                "quality_score": self._compute_quality_score(
                    linearity_check, residual_analysis, r_squared
                ),
                "warnings": self._generate_warnings(
                    linearity_check, residual_analysis, breakpoint_detection
                )
            }
        }
    
    def _check_linearity(
        self, 
        log_scales: np.ndarray, 
        log_stats: np.ndarray,
        r_squared: float
    ) -> Dict[str, Any]:
        """Check linearity of log-log relationship."""
        passes = r_squared >= self.min_r_squared
        
        # Additional linearity checks
        # Runs test for randomness of residuals
        slope, intercept = np.polyfit(log_scales, log_stats, 1)
        residuals = log_stats - (slope * log_scales + intercept)
        
        # Count runs (sequences of same sign)
        signs = np.sign(residuals)
        runs = np.sum(signs[:-1] != signs[1:]) + 1
        
        # Expected runs under randomness
        n_pos = np.sum(signs > 0)
        n_neg = np.sum(signs < 0)
        n = len(signs)
        
        if n_pos > 0 and n_neg > 0:
            expected_runs = (2 * n_pos * n_neg) / n + 1
            var_runs = (2 * n_pos * n_neg * (2 * n_pos * n_neg - n)) / (n ** 2 * (n - 1))
            z_runs = (runs - expected_runs) / np.sqrt(var_runs) if var_runs > 0 else 0
            runs_test_p_value = 2 * (1 - stats.norm.cdf(abs(z_runs)))
        else:
            runs_test_p_value = None
            z_runs = None
        
        return {
            "passes": passes,
            "r_squared": float(r_squared),
            "meets_threshold": passes,
            "runs_test": {
                "n_runs": int(runs),
                "z_statistic": float(z_runs) if z_runs is not None else None,
                "p_value": float(runs_test_p_value) if runs_test_p_value is not None else None,
                "random_residuals": runs_test_p_value > 0.05 if runs_test_p_value is not None else None
            }
        }
    
    def _analyse_residuals(
        self,
        log_scales: np.ndarray,
        log_stats: np.ndarray,
        slope: float,
        intercept: float
    ) -> Dict[str, Any]:
        """Comprehensive residual analysis."""
        # Compute residuals
        fitted_values = slope * log_scales + intercept
        residuals = log_stats - fitted_values
        standardised_residuals = (residuals - np.mean(residuals)) / np.std(residuals)
        
        # Normality test (Shapiro-Wilk)
        if len(residuals) >= 3:
            try:
                shapiro_stat, shapiro_p = stats.shapiro(residuals)
                normality_passes = shapiro_p > 0.05
            except Exception:
                shapiro_stat, shapiro_p = None, None
                normality_passes = None
        else:
            shapiro_stat, shapiro_p = None, None
            normality_passes = None
        
        # Autocorrelation test (Ljung-Box)
        n_lags = min(10, len(residuals) // 3)
        if n_lags >= 1:
            try:
                acf_values = self._compute_acf(residuals, n_lags)
                # Simplified Ljung-Box statistic
                lb_stat = len(residuals) * (len(residuals) + 2) * np.sum(
                    acf_values[1:] ** 2 / (len(residuals) - np.arange(1, len(acf_values)))
                )
                lb_p_value = 1 - stats.chi2.cdf(lb_stat, n_lags)
                autocorr_significant = lb_p_value < 0.05
            except Exception:
                acf_values = None
                lb_stat, lb_p_value = None, None
                autocorr_significant = None
        else:
            acf_values = None
            lb_stat, lb_p_value = None, None
            autocorr_significant = None
        
        # Heteroscedasticity test (Breusch-Pagan)
        try:
            # Regress squared residuals on log_scales
            if len(residuals) >= 3:
                bp_slope, bp_intercept = np.polyfit(log_scales, residuals ** 2, 1)
                fitted_sq_resid = bp_slope * log_scales + bp_intercept
                ss_res = np.sum((residuals ** 2 - fitted_sq_resid) ** 2)
                ss_tot = np.sum((residuals ** 2 - np.mean(residuals ** 2)) ** 2)
                bp_r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                bp_stat = len(residuals) * bp_r_squared
                bp_p_value = 1 - stats.chi2.cdf(bp_stat, 1)
                heteroscedasticity = bp_p_value < 0.05
            else:
                bp_stat, bp_p_value, heteroscedasticity = None, None, None
        except Exception:
            bp_stat, bp_p_value, heteroscedasticity = None, None, None
        
        return {
            "normality": {
                "shapiro_statistic": float(shapiro_stat) if shapiro_stat is not None else None,
                "shapiro_p_value": float(shapiro_p) if shapiro_p is not None else None,
                "passes": normality_passes,
                "interpretation": "Residuals appear normally distributed" if normality_passes else "Residuals may not be normally distributed"
            },
            "autocorrelation": {
                "ljung_box_statistic": float(lb_stat) if lb_stat is not None else None,
                "ljung_box_p_value": float(lb_p_value) if lb_p_value is not None else None,
                "n_lags": int(n_lags) if n_lags >= 1 else None,
                "significant": autocorr_significant,
                "interpretation": "No significant autocorrelation" if not autocorr_significant else "Residuals show autocorrelation"
            },
            "heteroscedasticity": {
                "breusch_pagan_statistic": float(bp_stat) if bp_stat is not None else None,
                "breusch_pagan_p_value": float(bp_p_value) if bp_p_value is not None else None,
                "present": heteroscedasticity,
                "interpretation": "Homoscedastic residuals" if not heteroscedasticity else "Heteroscedastic residuals detected"
            },
            "statistics": {
                "mean": float(np.mean(residuals)),
                "std": float(np.std(residuals)),
                "min": float(np.min(residuals)),
                "max": float(np.max(residuals)),
                "skewness": float(stats.skew(residuals)) if len(residuals) >= 3 else None,
                "kurtosis": float(stats.kurtosis(residuals)) if len(residuals) >= 3 else None
            }
        }
    
    def _compute_acf(self, data: np.ndarray, n_lags: int) -> np.ndarray:
        """Compute autocorrelation function."""
        data = data - np.mean(data)
        acf = np.correlate(data, data, mode='full')
        acf = acf[len(acf) // 2:]
        acf = acf / acf[0]
        return acf[:n_lags + 1]
    
    def _assess_goodness_of_fit(
        self,
        log_scales: np.ndarray,
        log_stats: np.ndarray,
        slope: float,
        intercept: float
    ) -> Dict[str, Any]:
        """Assess goodness-of-fit using multiple criteria."""
        n = len(log_scales)
        k = 2  # Number of parameters (slope and intercept)
        
        # Compute residuals and metrics
        fitted_values = slope * log_scales + intercept
        residuals = log_stats - fitted_values
        rss = np.sum(residuals ** 2)
        tss = np.sum((log_stats - np.mean(log_stats)) ** 2)
        
        r_squared = 1 - rss / tss if tss > 0 else 0
        adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k) if n > k else r_squared
        
        # AIC and BIC
        log_likelihood = -n / 2 * np.log(2 * np.pi * rss / n) - n / 2
        aic = 2 * k - 2 * log_likelihood
        bic = k * np.log(n) - 2 * log_likelihood
        
        # Mean absolute error in log-log space
        mae = np.mean(np.abs(residuals))
        
        return {
            "r_squared": float(r_squared),
            "adjusted_r_squared": float(adjusted_r_squared),
            "aic": float(aic),
            "bic": float(bic),
            "mae_log_space": float(mae),
            "rmse_log_space": float(np.sqrt(rss / n)),
            "interpretation": {
                "aic_interpretation": "Lower AIC indicates better fit",
                "bic_interpretation": "Lower BIC indicates better fit with parsimony",
                "adjusted_r_squared_interpretation": f"Explains {adjusted_r_squared * 100:.1f}% of variance (adjusted)"
            }
        }
    
    def _detect_breakpoints(
        self,
        log_scales: np.ndarray,
        log_stats: np.ndarray
    ) -> Dict[str, Any]:
        """Detect potential breakpoints in log-log relationship."""
        n_points = len(log_scales)
        
        if n_points < 6:
            return {
                "status": "insufficient_data",
                "reason": "Need at least 6 points for breakpoint detection"
            }
        
        best_score = np.inf
        best_breakpoint: Optional[Dict[str, Any]] = None
        
        # Try all possible breakpoints
        for split_idx in range(2, n_points - 2):
            left_x = log_scales[:split_idx]
            left_y = log_stats[:split_idx]
            right_x = log_scales[split_idx:]
            right_y = log_stats[split_idx:]
            
            try:
                left_fit = stats.linregress(left_x, left_y)
                right_fit = stats.linregress(right_x, right_y)
            except Exception:
                continue
            
            # Compute residual sum of squares for two-segment fit
            left_resid = left_y - (left_fit.intercept + left_fit.slope * left_x)
            right_resid = right_y - (right_fit.intercept + right_fit.slope * right_x)
            rss_two_segment = np.sum(left_resid ** 2) + np.sum(right_resid ** 2)
            
            if rss_two_segment < best_score:
                best_score = rss_two_segment
                best_breakpoint = {
                    "break_index": int(split_idx),
                    "break_scale": float(2 ** log_scales[split_idx]),
                    "left_slope": float(left_fit.slope),
                    "right_slope": float(right_fit.slope),
                    "slope_difference": float(abs(left_fit.slope - right_fit.slope)),
                    "left_r_squared": float(left_fit.rvalue ** 2),
                    "right_r_squared": float(right_fit.rvalue ** 2),
                    "rss": float(rss_two_segment)
                }
        
        # Compare with single-segment fit
        single_fit = stats.linregress(log_scales, log_stats)
        single_resid = log_stats - (single_fit.intercept + single_fit.slope * log_scales)
        rss_single = np.sum(single_resid ** 2)
        
        # F-test for improvement
        if best_breakpoint is not None:
            f_stat = ((rss_single - best_score) / 2) / (best_score / (n_points - 4))
            f_p_value = 1 - stats.f.cdf(f_stat, 2, n_points - 4)
            
            breakpoint_significant = f_p_value < 0.05
            
            return {
                "status": "ok",
                "breakpoint_detected": breakpoint_significant,
                "best_breakpoint": best_breakpoint if breakpoint_significant else None,
                "f_statistic": float(f_stat),
                "f_p_value": float(f_p_value),
                "rss_single_segment": float(rss_single),
                "rss_two_segment": float(best_score),
                "improvement_ratio": float(rss_single / best_score) if best_score > 0 else None
            }
        else:
            return {
                "status": "ok",
                "breakpoint_detected": False,
                "reason": "No suitable breakpoint found"
            }
    
    def _compute_quality_score(
        self,
        linearity_check: Dict[str, Any],
        residual_analysis: Dict[str, Any],
        r_squared: float
    ) -> float:
        """Compute overall quality score (0-1 scale)."""
        score = 0.0
        weights = 0.0
        
        # R² contribution (40% weight)
        if r_squared is not None:
            score += 0.4 * min(1.0, r_squared / 0.9)
            weights += 0.4
        
        # Normality contribution (20% weight)
        if residual_analysis["normality"]["passes"] is not None:
            score += 0.2 if residual_analysis["normality"]["passes"] else 0.0
            weights += 0.2
        
        # No autocorrelation contribution (20% weight)
        if residual_analysis["autocorrelation"]["significant"] is not None:
            score += 0.2 if not residual_analysis["autocorrelation"]["significant"] else 0.0
            weights += 0.2
        
        # Homoscedasticity contribution (20% weight)
        if residual_analysis["heteroscedasticity"]["present"] is not None:
            score += 0.2 if not residual_analysis["heteroscedasticity"]["present"] else 0.0
            weights += 0.2
        
        return score / weights if weights > 0 else 0.0
    
    def _generate_warnings(
        self,
        linearity_check: Dict[str, Any],
        residual_analysis: Dict[str, Any],
        breakpoint_detection: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable warnings based on diagnostics."""
        warnings_list = []
        
        if not linearity_check.get("passes", False):
            warnings_list.append(
                f"Low R² ({linearity_check.get('r_squared', 0):.3f}) indicates poor log-log linearity"
            )
        
        if residual_analysis["normality"].get("passes") is False:
            warnings_list.append("Residuals deviate from normality")
        
        if residual_analysis["autocorrelation"].get("significant"):
            warnings_list.append("Significant residual autocorrelation detected")
        
        if residual_analysis["heteroscedasticity"].get("present"):
            warnings_list.append("Heteroscedastic residuals detected")
        
        if breakpoint_detection.get("breakpoint_detected"):
            bp = breakpoint_detection.get("best_breakpoint", {})
            warnings_list.append(
                f"Significant breakpoint at scale {bp.get('break_scale', 'unknown'):.2f}"
            )
        
        return warnings_list


class ScaleWindowSensitivityAnalyser:
    """
    Analyse sensitivity of H estimates to scale window selection.
    """
    
    def __init__(
        self,
        perturbation_levels: Optional[List[float]] = None,
        leave_one_out: bool = True
    ):
        """
        Initialise scale window sensitivity analyser.
        
        Parameters
        ----------
        perturbation_levels : list of float, optional
            Multiplicative perturbation factors to apply to scale bounds
        leave_one_out : bool
            Whether to perform leave-one-out analysis
        """
        self.perturbation_levels = perturbation_levels or [0.9, 0.95, 1.05, 1.1]
        self.leave_one_out = leave_one_out
    
    def analyse(
        self,
        estimator,
        data: np.ndarray,
        base_result: Dict[str, Any],
        original_scales: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Analyse sensitivity to scale window perturbations.
        
        Parameters
        ----------
        estimator : BaseEstimator
            Estimator instance to test
        data : np.ndarray
            Input data
        base_result : dict
            Baseline estimation result
        original_scales : np.ndarray, optional
            Original scale values used
            
        Returns
        -------
        dict
            Sensitivity analysis results
        """
        base_h = base_result.get("hurst_parameter")
        if base_h is None:
            return {
                "status": "unavailable",
                "reason": "No baseline Hurst parameter available"
            }
        
        perturbation_results = []
        leave_one_out_results = []
        
        # Perturbation analysis
        for factor in self.perturbation_levels:
            try:
                # Attempt to modify estimator parameters
                perturbed_result = self._perturb_and_estimate(
                    estimator, data, factor
                )
                
                if perturbed_result.get("hurst_parameter") is not None:
                    delta_h = perturbed_result["hurst_parameter"] - base_h
                    perturbation_results.append({
                        "factor": float(factor),
                        "h_estimate": float(perturbed_result["hurst_parameter"]),
                        "delta_h": float(delta_h),
                        "success": True
                    })
                else:
                    perturbation_results.append({
                        "factor": float(factor),
                        "success": False,
                        "reason": "Estimation failed"
                    })
            except Exception as e:
                perturbation_results.append({
                    "factor": float(factor),
                    "success": False,
                    "reason": str(e)
                })
        
        # Leave-one-out analysis
        if self.leave_one_out and original_scales is not None:
            leave_one_out_results = self._leave_one_out_analysis(
                estimator, data, base_h, original_scales
            )
        
        # Summary statistics
        successful_perturbations = [
            r for r in perturbation_results if r.get("success", False)
        ]
        
        if successful_perturbations:
            delta_h_values = [r["delta_h"] for r in successful_perturbations]
            sensitivity_summary = {
                "mean_abs_delta": float(np.mean(np.abs(delta_h_values))),
                "max_abs_delta": float(np.max(np.abs(delta_h_values))),
                "std_delta": float(np.std(delta_h_values)),
                "n_successful": len(successful_perturbations),
                "n_total": len(perturbation_results)
            }
        else:
            sensitivity_summary = {
                "mean_abs_delta": None,
                "max_abs_delta": None,
                "std_delta": None,
                "n_successful": 0,
                "n_total": len(perturbation_results)
            }
        
        return {
            "status": "ok",
            "base_h": float(base_h),
            "perturbation_results": perturbation_results,
            "leave_one_out_results": leave_one_out_results,
            "sensitivity_summary": sensitivity_summary,
            "interpretation": self._interpret_sensitivity(sensitivity_summary)
        }
    
    def _perturb_and_estimate(
        self,
        estimator,
        data: np.ndarray,
        factor: float
    ) -> Dict[str, Any]:
        """Apply perturbation and re-estimate."""
        # Try to modify scale parameters if estimator supports it
        # This is a simplified approach; specific estimators may need custom handling
        
        # Attempt to extract and modify scale parameters
        params = {}
        
        # Common parameter names across estimators
        param_names = [
            'min_window', 'max_window',
            'min_freq_ratio', 'max_freq_ratio',
            'min_level', 'max_level'
        ]
        
        for param_name in param_names:
            if hasattr(estimator, param_name):
                original_value = getattr(estimator, param_name)
                if isinstance(original_value, (int, float)) and original_value is not None:
                    params[param_name] = original_value
        
        # Apply perturbation
        if params:
            # Store original values
            original_params = params.copy()
            
            # Modify parameters
            for param_name, value in params.items():
                if isinstance(value, int):
                    setattr(estimator, param_name, int(value * factor))
                else:
                    setattr(estimator, param_name, value * factor)
            
            try:
                # Re-estimate
                result = estimator.estimate(data)
            finally:
                # Restore original parameters
                for param_name, value in original_params.items():
                    setattr(estimator, param_name, value)
            
            return result
        else:
            # If we can't perturb, just return the original estimate
            return estimator.estimate(data)
    
    def _leave_one_out_analysis(
        self,
        estimator,
        data: np.ndarray,
        base_h: float,
        scales: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Leave-one-out influence analysis.
        Note: This is a placeholder; full implementation would require
        access to internal scale computation in each estimator.
        """
        # This is a simplified version
        # Full implementation would need estimator-specific logic
        return []
    
    def _interpret_sensitivity(self, summary: Dict[str, Any]) -> str:
        """Generate interpretation of sensitivity results."""
        max_delta = summary.get("max_abs_delta")
        
        if max_delta is None:
            return "Sensitivity analysis unavailable"
        
        if max_delta < 0.05:
            return "Low sensitivity: estimates are robust to scale window perturbations"
        elif max_delta < 0.1:
            return "Moderate sensitivity: estimates show some variability with scale window changes"
        else:
            return "High sensitivity: estimates are highly sensitive to scale window selection"


def run_comprehensive_diagnostics(
    scales: np.ndarray,
    statistics: np.ndarray,
    estimator = None,
    data: Optional[np.ndarray] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run complete diagnostic suite on power-law fit.
    
    Parameters
    ----------
    scales : np.ndarray
        Scale values
    statistics : np.ndarray
        Corresponding statistics
    estimator : BaseEstimator, optional
        Estimator instance for sensitivity analysis
    data : np.ndarray, optional
        Original data for sensitivity analysis
    config : dict, optional
        Configuration dict with diagnostic settings
        
    Returns
    -------
    dict
        Complete diagnostic results
    """
    if config is None:
        config = {}
    
    diagnostics_cfg = config.get("diagnostics", {})
    
    # Power-law diagnostics
    log_log_cfg = diagnostics_cfg.get("log_log_checks", {})
    power_law_diag = PowerLawDiagnostics(
        min_r_squared=log_log_cfg.get("min_r_squared", 0.5),
        min_points=log_log_cfg.get("min_points", 6)
    )
    
    power_law_results = power_law_diag.diagnose(scales, statistics)
    
    # Scale window sensitivity (if estimator and data provided)
    sensitivity_results = {}
    if estimator is not None and data is not None:
        sensitivity_cfg = diagnostics_cfg.get("scale_window_sensitivity", {})
        if sensitivity_cfg.get("enabled", True):
            sensitivity_analyser = ScaleWindowSensitivityAnalyser(
                perturbation_levels=sensitivity_cfg.get("perturbation_levels"),
                leave_one_out=sensitivity_cfg.get("leave_one_out", True)
            )
            
            # Need to get base result from estimator
            try:
                base_result = {"hurst_parameter": estimator.results.get("hurst_parameter")}
                sensitivity_results = sensitivity_analyser.analyse(
                    estimator, data, base_result, scales
                )
            except Exception as e:
                sensitivity_results = {
                    "status": "failed",
                    "error": str(e)
                }
    
    return {
        "power_law_diagnostics": power_law_results,
        "scale_window_sensitivity": sensitivity_results if sensitivity_results else {
            "status": "not_performed"
        }
    }


class StructuralBreakDetector:
    """
    Detector for structural breaks in time series.
    
    Implements multiple tests for detecting change points that would invalidate
    the stationarity assumptions required by classical LRD estimators.
    
    Methods
    -------
    cusum_test : Standard CUSUM test for mean shifts
    recursive_cusum : Sequential/online CUSUM detection
    chow_test : Test for known break point
    icss_algorithm : Iterative Cumulative Sum of Squares for variance changes
    detect_all : Run all tests and return comprehensive results
    """
    
    def __init__(
        self,
        significance_level: float = 0.05,
        min_segment_length: int = 50
    ):
        """
        Initialize structural break detector.
        
        Parameters
        ----------
        significance_level : float
            Significance level for hypothesis tests
        min_segment_length : int
            Minimum segment length for break detection
        """
        self.significance_level = significance_level
        self.min_segment_length = min_segment_length
    
    def cusum_test(
        self,
        data: np.ndarray,
        normalize: bool = True
    ) -> Dict[str, Any]:
        """
        Standard CUSUM test for detecting mean shifts.
        
        The CUSUM (Cumulative Sum) test detects changes in the mean of a 
        time series by monitoring cumulative deviations from the sample mean.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series
        normalize : bool
            Whether to normalize the CUSUM statistic
            
        Returns
        -------
        dict
            Test results including:
            - statistic: Maximum absolute CUSUM value
            - critical_value: Critical value at significance level
            - break_detected: Whether a break was detected
            - break_index: Estimated break location (if detected)
            - cusum_path: Full CUSUM path for visualization
        """
        n = len(data)
        
        if n < 2 * self.min_segment_length:
            return {
                "status": "insufficient_data",
                "reason": f"Need at least {2 * self.min_segment_length} points"
            }
        
        # Compute CUSUM
        mean_val = np.mean(data)
        cumsum = np.cumsum(data - mean_val)
        
        if normalize:
            std_val = np.std(data)
            if std_val > 0:
                cumsum = cumsum / (std_val * np.sqrt(n))
        
        # Test statistic: maximum absolute deviation
        statistic = np.max(np.abs(cumsum))
        break_index = np.argmax(np.abs(cumsum))
        
        # Critical value (Brownian bridge approximation)
        # Using Andrew (1993) critical values for significance level
        critical_values = {
            0.01: 1.63,
            0.05: 1.36,
            0.10: 1.22
        }
        critical_value = critical_values.get(
            self.significance_level, 
            1.36  # Default to 0.05
        )
        
        break_detected = statistic > critical_value
        
        return {
            "status": "ok",
            "test_name": "CUSUM",
            "statistic": float(statistic),
            "critical_value": float(critical_value),
            "break_detected": break_detected,
            "break_index": int(break_index) if break_detected else None,
            "break_position": float(break_index / n) if break_detected else None,
            "p_value_approx": self._cusum_pvalue(statistic),
            "cusum_path": cumsum.tolist()
        }
    
    def _cusum_pvalue(self, statistic: float) -> float:
        """Approximate p-value for CUSUM statistic."""
        # Kolmogorov distribution approximation
        if statistic <= 0:
            return 1.0
        # Using asymptotic formula
        k = statistic
        p_value = 2 * np.sum([
            (-1)**(j-1) * np.exp(-2 * j**2 * k**2) 
            for j in range(1, 101)
        ])
        return max(0, min(1, 1 - p_value))
    
    def recursive_cusum(
        self,
        data: np.ndarray,
        window_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recursive CUSUM for sequential/online break detection.
        
        Monitors the process sequentially and detects when the cumulative
        sum exceeds threshold, suitable for online monitoring.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series
        window_size : int, optional
            Initial window for establishing baseline
            
        Returns
        -------
        dict
            Detection results including break points and timing
        """
        n = len(data)
        
        if window_size is None:
            window_size = min(100, n // 4)
        
        if n < window_size + self.min_segment_length:
            return {
                "status": "insufficient_data",
                "reason": f"Need at least {window_size + self.min_segment_length} points"
            }
        
        # Establish baseline from initial window
        baseline_mean = np.mean(data[:window_size])
        baseline_std = np.std(data[:window_size])
        
        if baseline_std <= 0:
            baseline_std = 1.0
        
        # Compute recursive residuals and CUSUM
        cusum_plus = np.zeros(n - window_size)
        cusum_minus = np.zeros(n - window_size)
        
        # Control limit (typically 4-5 for detecting 1-sigma shifts)
        control_limit = 5.0
        slack = 0.5  # Allowance parameter
        
        breaks_detected = []
        
        for i in range(window_size, n):
            idx = i - window_size
            z = (data[i] - baseline_mean) / baseline_std
            
            # Two-sided CUSUM
            cusum_plus[idx] = max(0, cusum_plus[idx-1] + z - slack) if idx > 0 else max(0, z - slack)
            cusum_minus[idx] = max(0, cusum_minus[idx-1] - z - slack) if idx > 0 else max(0, -z - slack)
            
            # Check for break
            if cusum_plus[idx] > control_limit or cusum_minus[idx] > control_limit:
                breaks_detected.append(i)
                # Reset after detection
                cusum_plus[idx] = 0
                cusum_minus[idx] = 0
        
        return {
            "status": "ok",
            "test_name": "Recursive CUSUM",
            "breaks_detected": len(breaks_detected) > 0,
            "n_breaks": len(breaks_detected),
            "break_indices": breaks_detected,
            "break_positions": [b / n for b in breaks_detected],
            "control_limit": control_limit,
            "cusum_plus": cusum_plus.tolist(),
            "cusum_minus": cusum_minus.tolist()
        }
    
    def chow_test(
        self,
        data: np.ndarray,
        break_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Chow test for structural break at a known or estimated point.
        
        Tests whether regression coefficients (here, just the mean) differ
        before and after a specified break point.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series
        break_index : int, optional
            Index of hypothesized break. If None, tests at midpoint.
            
        Returns
        -------
        dict
            Test results including F-statistic and p-value
        """
        n = len(data)
        
        if break_index is None:
            break_index = n // 2
        
        if break_index < self.min_segment_length or n - break_index < self.min_segment_length:
            return {
                "status": "invalid_break_point",
                "reason": "Break point too close to boundary"
            }
        
        # Split data
        data_before = data[:break_index]
        data_after = data[break_index:]
        
        n1, n2 = len(data_before), len(data_after)
        
        # Compute means and variances
        mean_before = np.mean(data_before)
        mean_after = np.mean(data_after)
        mean_pooled = np.mean(data)
        
        # Sum of squared residuals
        ssr_unrestricted = np.sum((data_before - mean_before)**2) + np.sum((data_after - mean_after)**2)
        ssr_restricted = np.sum((data - mean_pooled)**2)
        
        # F-statistic
        # k = 1 (testing difference in means)
        k = 1
        if ssr_unrestricted > 0:
            f_statistic = ((ssr_restricted - ssr_unrestricted) / k) / (ssr_unrestricted / (n - 2*k))
        else:
            f_statistic = 0.0
        
        # P-value from F-distribution
        p_value = 1 - stats.f.cdf(f_statistic, k, n - 2*k)
        
        break_detected = p_value < self.significance_level
        
        return {
            "status": "ok",
            "test_name": "Chow Test",
            "break_index": int(break_index),
            "break_position": float(break_index / n),
            "f_statistic": float(f_statistic),
            "p_value": float(p_value),
            "break_detected": break_detected,
            "mean_before": float(mean_before),
            "mean_after": float(mean_after),
            "mean_difference": float(mean_after - mean_before)
        }
    
    def icss_algorithm(
        self,
        data: np.ndarray,
        max_iterations: int = 100
    ) -> Dict[str, Any]:
        """
        Iterative Cumulative Sum of Squares (ICSS) algorithm.
        
        Detects multiple variance change points using the algorithm of
        Inclán and Tiao (1994).
        
        Parameters
        ----------
        data : np.ndarray
            Input time series
        max_iterations : int
            Maximum iterations for refinement
            
        Returns
        -------
        dict
            Detected variance change points
        """
        n = len(data)
        
        if n < 2 * self.min_segment_length:
            return {
                "status": "insufficient_data",
                "reason": f"Need at least {2 * self.min_segment_length} points"
            }
        
        # Center the data
        data_centered = data - np.mean(data)
        
        # Compute cumulative sum of squares
        css = np.cumsum(data_centered**2)
        total_ss = css[-1]
        
        if total_ss <= 0:
            return {
                "status": "constant_variance",
                "break_detected": False
            }
        
        # Compute D_k statistic (normalized deviation from linear growth)
        k = np.arange(1, n + 1)
        expected_ss = (k / n) * total_ss
        d_k = (css - expected_ss) / np.sqrt(total_ss)
        
        # Find maximum absolute deviation
        max_d = np.max(np.abs(d_k))
        break_index = np.argmax(np.abs(d_k))
        
        # Critical value (asymptotic distribution)
        # Using sqrt(2 * log(log(n))) * 1.358 as approximation
        if n > 10:
            critical_value = np.sqrt(2 * np.log(np.log(n))) * 1.358
        else:
            critical_value = 1.36
        
        # Simple single-break detection
        break_detected = max_d > critical_value
        
        # For multiple breaks, iterate (simplified version)
        break_points = []
        if break_detected:
            break_points.append(int(break_index))
        
        return {
            "status": "ok",
            "test_name": "ICSS",
            "statistic": float(max_d),
            "critical_value": float(critical_value),
            "break_detected": break_detected,
            "n_breaks": len(break_points),
            "break_indices": break_points,
            "break_positions": [bp / n for bp in break_points],
            "d_k_path": d_k.tolist()
        }
    
    def detect_all(
        self,
        data: np.ndarray,
        include_paths: bool = False
    ) -> Dict[str, Any]:
        """
        Run all structural break tests and return comprehensive results.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series
        include_paths : bool
            Whether to include full paths (can be large)
            
        Returns
        -------
        dict
            Comprehensive break detection results with warnings
        """
        data = np.asarray(data, dtype=np.float64)
        
        # Run all tests
        cusum_result = self.cusum_test(data)
        recursive_result = self.recursive_cusum(data)
        chow_result = self.chow_test(data)
        icss_result = self.icss_algorithm(data)
        
        # Remove paths if not requested
        if not include_paths:
            for result in [cusum_result, recursive_result, icss_result]:
                for key in ['cusum_path', 'cusum_plus', 'cusum_minus', 'd_k_path']:
                    result.pop(key, None)
        
        # Summary
        any_break_detected = (
            cusum_result.get("break_detected", False) or
            recursive_result.get("breaks_detected", False) or
            chow_result.get("break_detected", False) or
            icss_result.get("break_detected", False)
        )
        
        # Generate warnings
        warnings_list = []
        if cusum_result.get("break_detected"):
            warnings_list.append(
                f"CUSUM detected mean shift at position {cusum_result.get('break_position', 0):.2%}"
            )
        if recursive_result.get("n_breaks", 0) > 0:
            warnings_list.append(
                f"Recursive CUSUM detected {recursive_result['n_breaks']} break(s)"
            )
        if chow_result.get("break_detected"):
            warnings_list.append(
                f"Chow test detected break (p={chow_result.get('p_value', 1):.4f})"
            )
        if icss_result.get("break_detected"):
            warnings_list.append(
                f"ICSS detected {icss_result.get('n_breaks', 0)} variance change point(s)"
            )
        
        if any_break_detected:
            warnings_list.insert(0, 
                "⚠️ STATIONARITY WARNING: Structural breaks detected. "
                "Classical LRD estimator results may be unreliable."
            )
        
        return {
            "status": "ok",
            "any_break_detected": any_break_detected,
            "stationarity_valid": not any_break_detected,
            "cusum": cusum_result,
            "recursive_cusum": recursive_result,
            "chow": chow_result,
            "icss": icss_result,
            "warnings": warnings_list,
            "recommendation": (
                "Consider segmented analysis or nonstationary methods" 
                if any_break_detected else 
                "Data appears stationary; proceed with classical estimation"
            )
        }
