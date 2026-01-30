#!/usr/bin/env python3
"""
Tests for StructuralBreakDetector in diagnostics module.
"""

import pytest
import numpy as np
from lrdbenchmark.analysis.diagnostics import StructuralBreakDetector


class TestStructuralBreakDetector:
    """Tests for StructuralBreakDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return StructuralBreakDetector(significance_level=0.05, min_segment_length=50)
    
    @pytest.fixture
    def stationary_data(self):
        """Generate stationary data without breaks."""
        np.random.seed(42)
        return np.random.randn(500)
    
    @pytest.fixture
    def mean_break_data(self):
        """Generate data with a mean shift."""
        np.random.seed(42)
        data = np.random.randn(500)
        data[250:] += 3.0  # Large mean shift at midpoint
        return data
    
    @pytest.fixture
    def variance_break_data(self):
        """Generate data with a variance change."""
        np.random.seed(42)
        data1 = np.random.randn(250)
        data2 = np.random.randn(250) * 3.0  # 3x larger std
        return np.concatenate([data1, data2])


class TestCUSUMTest(TestStructuralBreakDetector):
    """Tests for CUSUM test."""
    
    def test_stationary_no_break(self, detector, stationary_data):
        """Test that stationary data shows no break."""
        result = detector.cusum_test(stationary_data)
        
        assert result['status'] == 'ok'
        assert result['test_name'] == 'CUSUM'
        # Stationary data should usually not trigger detection
        # (though random chance can cause false positives)
    
    def test_mean_shift_detected(self, detector, mean_break_data):
        """Test that mean shift is detected."""
        result = detector.cusum_test(mean_break_data)
        
        assert result['status'] == 'ok'
        assert result['break_detected'] == True
        # Break should be detected near the actual break point
        assert result['break_index'] is not None
        assert 200 < result['break_index'] < 300
    
    def test_short_data(self, detector):
        """Test handling of too-short data."""
        short_data = np.random.randn(50)
        result = detector.cusum_test(short_data)
        
        assert result['status'] == 'insufficient_data'
    
    def test_cusum_path_returned(self, detector, stationary_data):
        """Test that CUSUM path is returned."""
        result = detector.cusum_test(stationary_data)
        
        assert 'cusum_path' in result
        assert len(result['cusum_path']) == len(stationary_data)


class TestRecursiveCUSUM(TestStructuralBreakDetector):
    """Tests for recursive CUSUM."""
    
    def test_stationary_no_break(self, detector, stationary_data):
        """Test stationary data."""
        result = detector.recursive_cusum(stationary_data)
        
        assert result['status'] == 'ok'
        assert result['test_name'] == 'Recursive CUSUM'
    
    def test_mean_shift_detected(self, detector, mean_break_data):
        """Test mean shift detection."""
        result = detector.recursive_cusum(mean_break_data)
        
        assert result['status'] == 'ok'
        assert result['breaks_detected'] == True
        assert result['n_breaks'] >= 1
    
    def test_custom_window_size(self, detector, stationary_data):
        """Test with custom window size."""
        result = detector.recursive_cusum(stationary_data, window_size=50)
        
        assert result['status'] == 'ok'


class TestChowTest(TestStructuralBreakDetector):
    """Tests for Chow test."""
    
    def test_known_break_point(self, detector, mean_break_data):
        """Test with known break point."""
        result = detector.chow_test(mean_break_data, break_index=250)
        
        assert result['status'] == 'ok'
        assert result['test_name'] == 'Chow Test'
        assert result['break_detected'] == True
        assert result['p_value'] < 0.05
    
    def test_wrong_break_point(self, detector, mean_break_data):
        """Test with wrong break point (should still detect difference)."""
        result = detector.chow_test(mean_break_data, break_index=100)
        
        assert result['status'] == 'ok'
        # May or may not detect depending on where we split
    
    def test_stationary_no_break(self, detector, stationary_data):
        """Test stationary data at midpoint."""
        result = detector.chow_test(stationary_data)
        
        assert result['status'] == 'ok'
        # Should usually not detect a break
    
    def test_boundary_break_point(self, detector, stationary_data):
        """Test break point too close to boundary."""
        result = detector.chow_test(stationary_data, break_index=10)
        
        assert result['status'] == 'invalid_break_point'
    
    def test_mean_difference_reported(self, detector, mean_break_data):
        """Test that mean difference is reported."""
        result = detector.chow_test(mean_break_data, break_index=250)
        
        assert 'mean_before' in result
        assert 'mean_after' in result
        assert 'mean_difference' in result
        assert abs(result['mean_difference']) > 2.0  # Should be ~3


class TestICSSAlgorithm(TestStructuralBreakDetector):
    """Tests for ICSS algorithm."""
    
    def test_variance_change_detected(self, detector, variance_break_data):
        """Test variance change detection."""
        result = detector.icss_algorithm(variance_break_data)
        
        assert result['status'] == 'ok'
        assert result['test_name'] == 'ICSS'
        assert result['break_detected'] == True
    
    def test_stationary_no_break(self, detector, stationary_data):
        """Test stationary data."""
        result = detector.icss_algorithm(stationary_data)
        
        assert result['status'] == 'ok'
        # May or may not detect depending on random sample
    
    def test_d_k_path_returned(self, detector, stationary_data):
        """Test that D_k path is returned."""
        result = detector.icss_algorithm(stationary_data)
        
        assert 'd_k_path' in result
        assert len(result['d_k_path']) == len(stationary_data)


class TestDetectAll(TestStructuralBreakDetector):
    """Tests for comprehensive detection."""
    
    def test_all_tests_run(self, detector, stationary_data):
        """Test that all tests are run."""
        result = detector.detect_all(stationary_data)
        
        assert result['status'] == 'ok'
        assert 'cusum' in result
        assert 'recursive_cusum' in result
        assert 'chow' in result
        assert 'icss' in result
    
    def test_break_detected_flag(self, detector, mean_break_data):
        """Test any_break_detected flag."""
        result = detector.detect_all(mean_break_data)
        
        assert result['any_break_detected'] == True
        assert result['stationarity_valid'] == False
    
    def test_warnings_generated(self, detector, mean_break_data):
        """Test that warnings are generated."""
        result = detector.detect_all(mean_break_data)
        
        assert len(result['warnings']) > 0
        assert 'STATIONARITY WARNING' in result['warnings'][0]
    
    def test_recommendation_provided(self, detector, mean_break_data):
        """Test that recommendation is provided."""
        result = detector.detect_all(mean_break_data)
        
        assert 'recommendation' in result
        assert 'segmented' in result['recommendation'].lower()
    
    def test_paths_excluded_by_default(self, detector, stationary_data):
        """Test that paths are excluded by default."""
        result = detector.detect_all(stationary_data, include_paths=False)
        
        assert 'cusum_path' not in result['cusum']
        assert 'd_k_path' not in result['icss']
    
    def test_paths_included_when_requested(self, detector, stationary_data):
        """Test that paths are included when requested."""
        result = detector.detect_all(stationary_data, include_paths=True)
        
        assert 'cusum_path' in result['cusum']
        assert 'd_k_path' in result['icss']


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_constant_data(self):
        """Test with constant data."""
        detector = StructuralBreakDetector()
        data = np.ones(200)
        
        # Should handle gracefully
        result = detector.detect_all(data)
        assert result['status'] == 'ok'
    
    def test_trending_data(self):
        """Test with trending data."""
        detector = StructuralBreakDetector()
        data = np.linspace(0, 10, 500) + np.random.randn(500) * 0.1
        
        result = detector.detect_all(data)
        # Trend may or may not be detected as break
        assert result['status'] == 'ok'
    
    def test_multiple_breaks(self):
        """Test with multiple breaks."""
        detector = StructuralBreakDetector()
        np.random.seed(42)
        data = np.concatenate([
            np.random.randn(200),
            np.random.randn(200) + 3,
            np.random.randn(200) - 2
        ])
        
        result = detector.detect_all(data)
        assert result['any_break_detected'] == True
    
    def test_different_significance_levels(self):
        """Test with different significance levels."""
        np.random.seed(42)
        data = np.random.randn(500)
        data[250:] += 1.5  # Moderate break
        
        detector_strict = StructuralBreakDetector(significance_level=0.01)
        detector_lenient = StructuralBreakDetector(significance_level=0.10)
        
        result_strict = detector_strict.detect_all(data)
        result_lenient = detector_lenient.detect_all(data)
        
        # Both should run successfully
        assert result_strict['status'] == 'ok'
        assert result_lenient['status'] == 'ok'
