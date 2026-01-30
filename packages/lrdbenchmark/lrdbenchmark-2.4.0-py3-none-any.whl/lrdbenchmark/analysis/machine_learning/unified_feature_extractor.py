"""
Unified Feature Extractor for Machine Learning Estimators

This module provides a unified feature extraction pipeline that extracts
76 features from time series data for machine learning-based Hurst parameter estimation.
"""

import numpy as np
from scipy import stats
from scipy.signal import welch
from typing import Dict, Any, List, Optional

class UnifiedFeatureExtractor:
    """
    Unified feature extractor that provides a standardized set of features
    for machine learning-based Hurst parameter estimation.
    """
    
    @staticmethod
    def extract_features_76(data: np.ndarray) -> np.ndarray:
        """
        Extract 76 features from time series data.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series data
            
        Returns
        -------
        np.ndarray
            Array of 76 features
        """
        if len(data) < 10:
            # Return zeros for very short series
            return np.zeros(76)
        
        features = []
        mean_val = np.mean(data)
        std_val = np.std(data)
        var_val = np.var(data)
        min_val = np.min(data)
        max_val = np.max(data)
        median_val = np.median(data)
        tol = np.finfo(float).eps

        if std_val <= tol:
            skew_val = 0.0
            kurtosis_val = 0.0
        else:
            skew_val = stats.skew(data)
            kurtosis_val = stats.kurtosis(data)
        
        # Basic statistical features (10)
        features.extend([
            mean_val,
            std_val,
            var_val,
            min_val,
            max_val,
            median_val,
            skew_val,
            kurtosis_val,
            np.percentile(data, 25),
            np.percentile(data, 75)
        ])
        
        # Autocorrelation features (10)
        max_lag = min(10, len(data) // 4)
        if max_lag > 0 and std_val > tol:
            for lag in range(1, max_lag + 1):
                if lag < len(data):
                    corr = np.corrcoef(data[:-lag], data[lag:])[0, 1]
                    features.append(corr if not np.isnan(corr) else 0.0)
                else:
                    features.append(0.0)
        else:
            features.extend([0.0] * max_lag)
        
        # Fill remaining autocorrelation features with zeros if needed
        while len(features) < 20:
            features.append(0.0)
        
        # Spectral features (10)
        try:
            freqs, psd = welch(data, nperseg=min(256, len(data)//4))
            psd_sum = np.sum(psd)
            peak_frequency = np.argmax(psd) / len(psd) if len(psd) > 0 else 0.0
            if psd_sum > 0:
                mean_frequency = np.sum(psd * freqs) / psd_sum
                second_moment = np.sum(psd * freqs**2) / psd_sum
                low_freq_power = np.sum(psd[:len(psd)//4]) / psd_sum
                high_freq_power = np.sum(psd[len(psd)//2:]) / psd_sum
            else:
                mean_frequency = 0.0
                second_moment = 0.0
                low_freq_power = 0.0
                high_freq_power = 0.0

            features.extend([
                np.mean(psd),
                np.std(psd),
                np.max(psd),
                peak_frequency,
                psd_sum,
                mean_frequency,
                second_moment,
                low_freq_power,
                high_freq_power,
                len(psd)  # Number of frequency bins
            ])
        except:
            features.extend([0.0] * 10)
        
        # Wavelet-like features (10)
        try:
            # Simple wavelet decomposition using differences
            d1 = np.diff(data)
            d2 = np.diff(d1)
            d3 = np.diff(d2)
            
            features.extend([
                np.mean(np.abs(d1)),
                np.std(d1),
                np.mean(np.abs(d2)),
                np.std(d2),
                np.mean(np.abs(d3)),
                np.std(d3),
                np.sum(np.abs(d1)),
                np.sum(np.abs(d2)),
                np.sum(np.abs(d3)),
                len(d1) / len(data)  # Normalized length
            ])
        except:
            features.extend([0.0] * 10)
        
        # Fractal-like features (10)
        try:
            # Detrended fluctuation analysis approximation
            n = len(data)
            scales = [4, 8, 16, 32, 64]
            dfa_features = []
            
            for scale in scales:
                if scale < n:
                    # Simple DFA approximation
                    segments = n // scale
                    if segments > 0:
                        fluctuations = []
                        for i in range(segments):
                            segment = data[i*scale:(i+1)*scale]
                            if len(segment) > 1:
                                # Linear detrending
                                x = np.arange(len(segment))
                                coeffs = np.polyfit(x, segment, 1)
                                trend = np.polyval(coeffs, x)
                                detrended = segment - trend
                                fluctuations.append(np.sqrt(np.mean(detrended**2)))
                        
                        if fluctuations:
                            dfa_features.append(np.mean(fluctuations))
                        else:
                            dfa_features.append(0.0)
                    else:
                        dfa_features.append(0.0)
                else:
                    dfa_features.append(0.0)
            
            # Pad to 10 features
            while len(dfa_features) < 10:
                dfa_features.append(0.0)
            
            features.extend(dfa_features[:10])
        except:
            features.extend([0.0] * 10)
        
        # Entropy and complexity features (10)
        try:
            # Sample entropy approximation
            def sample_entropy(data, m=2, r=0.2):
                N = len(data)
                if N < m + 1:
                    return 0.0
                
                def _maxdist(xi, xj, m):
                    return max([abs(ua - va) for ua, va in zip(xi, xj)])
                
                def _get_matches(data, m):
                    N = len(data)
                    patterns = np.array([data[i:i + m] for i in range(N - m + 1)])
                    return patterns
            
            patterns_m = _get_matches(data, 2)
            patterns_m1 = _get_matches(data, 3)
            
            # Simplified entropy calculation
            if len(patterns_m) > 0 and len(patterns_m1) > 0:
                r = 0.2 * np.std(data)
                matches_m = 0
                matches_m1 = 0
                
                for i in range(len(patterns_m)):
                    for j in range(len(patterns_m)):
                        if i != j and np.max(np.abs(patterns_m[i] - patterns_m[j])) <= r:
                            matches_m += 1
                
                for i in range(len(patterns_m1)):
                    for j in range(len(patterns_m1)):
                        if i != j and np.max(np.abs(patterns_m1[i] - patterns_m1[j])) <= r:
                            matches_m1 += 1
                
                if matches_m > 0 and matches_m1 > 0:
                    entropy = -np.log(matches_m1 / matches_m)
                else:
                    entropy = 0.0
            else:
                entropy = 0.0
            
            # Additional complexity features
            features.extend([
                entropy,
                np.sum(np.diff(data) != 0) / len(data),  # Zero crossing rate
                np.sum(np.abs(np.diff(data))),  # Total variation
                np.sum(np.diff(data)**2),  # Energy
                np.mean(np.abs(data)),  # Mean absolute value
                np.std(np.abs(data)),  # Std of absolute values
                np.sum(data > np.mean(data)) / len(data),  # Fraction above mean
                np.sum(data < np.mean(data)) / len(data),  # Fraction below mean
                np.sum(np.diff(data) > 0) / len(data),  # Fraction of increases
                np.sum(np.diff(data) < 0) / len(data)   # Fraction of decreases
            ])
        except:
            features.extend([0.0] * 10)
        
        # Additional features to reach 76 (6 more)
        try:
            features.extend([
                len(data),  # Series length
                np.sum(data),  # Sum
                np.prod(np.sign(data)),  # Sign product
                np.sum(data**2),  # Sum of squares
                np.sum(data**3),  # Sum of cubes
                np.sum(data**4)   # Sum of fourth powers
            ])
        except:
            features.extend([0.0] * 6)
        
        # Ensure exactly 76 features
        while len(features) < 76:
            features.append(0.0)
        
        return np.array(features[:76])
    
    @staticmethod
    def extract_features_54(data: np.ndarray) -> np.ndarray:
        """
        Extract 54 features (subset of 76) for Gradient Boosting.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series data
            
        Returns
        -------
        np.ndarray
            Array of 54 features
        """
        features_76 = UnifiedFeatureExtractor.extract_features_76(data)
        # Return first 54 features
        return features_76[:54]
    
    @staticmethod
    def extract_features_29(data: np.ndarray) -> np.ndarray:
        """
        Extract 29 features (subset of 76) for SVR.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series data
            
        Returns
        -------
        np.ndarray
            Array of 29 features
        """
        features_76 = UnifiedFeatureExtractor.extract_features_76(data)
        # Return first 29 features
        return features_76[:29]

    @staticmethod
    def extract_features_8(data: np.ndarray) -> np.ndarray:
        """
        Extract 8 core statistical features used by lightweight pretrained models.

        Parameters
        ----------
        data : np.ndarray
            Input time series data

        Returns
        -------
        np.ndarray
            Array of 8 features
        """
        if np.any(np.isnan(data)):
            data = data[~np.isnan(data)]

        if len(data) < 10:
            return np.zeros(8)

        diff_data = np.diff(data)
        abs_data = np.abs(data)
        diff_abs = np.diff(data) ** 2

        features = [
            np.mean(data),
            np.std(data),
            np.mean(diff_data),
            np.std(diff_data),
            np.mean(abs_data),
            np.std(abs_data),
            np.mean(diff_abs),
            np.std(diff_abs),
        ]

        return np.array(features)
    
    @staticmethod
    def get_feature_names_76() -> List[str]:
        """
        Get names of the 76 features.
        
        Returns
        -------
        List[str]
            List of feature names
        """
        names = []
        
        # Basic statistical features
        names.extend([
            'mean', 'std', 'var', 'min', 'max', 'median', 'skew', 'kurtosis',
            'q25', 'q75'
        ])
        
        # Autocorrelation features
        for i in range(10):
            names.append(f'autocorr_lag_{i+1}')
        
        # Spectral features
        names.extend([
            'psd_mean', 'psd_std', 'psd_max', 'psd_peak_freq', 'psd_sum',
            'psd_mean_freq', 'psd_second_moment', 'psd_low_freq_power',
            'psd_high_freq_power', 'psd_n_bins'
        ])
        
        # Wavelet features
        names.extend([
            'wavelet_d1_mean', 'wavelet_d1_std', 'wavelet_d2_mean', 'wavelet_d2_std',
            'wavelet_d3_mean', 'wavelet_d3_std', 'wavelet_d1_sum', 'wavelet_d2_sum',
            'wavelet_d3_sum', 'wavelet_norm_length'
        ])
        
        # Fractal features
        for i in range(10):
            names.append(f'dfa_scale_{i+1}')
        
        # Entropy features
        names.extend([
            'sample_entropy', 'zero_crossing_rate', 'total_variation', 'energy',
            'mean_abs', 'std_abs', 'frac_above_mean', 'frac_below_mean',
            'frac_increases', 'frac_decreases'
        ])
        
        # Additional features
        names.extend([
            'length', 'sum', 'sign_product', 'sum_squares', 'sum_cubes', 'sum_fourth_powers'
        ])
        
        return names[:76]
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """Alias for get_feature_names_76() for backward compatibility."""
        return UnifiedFeatureExtractor.get_feature_names_76()
    
    @staticmethod
    def get_feature_names_29() -> List[str]:
        """Get names of the first 29 features."""
        return UnifiedFeatureExtractor.get_feature_names_76()[:29]
    
    @staticmethod
    def get_feature_names_54() -> List[str]:
        """Get names of the first 54 features."""
        return UnifiedFeatureExtractor.get_feature_names_76()[:54]

    @staticmethod
    def get_feature_names_8() -> List[str]:
        """Feature names for the 8-core statistical features."""
        return [
            "mean",
            "std",
            "diff_mean",
            "diff_std",
            "abs_mean",
            "abs_std",
            "diff_sq_mean",
            "diff_sq_std",
        ]
