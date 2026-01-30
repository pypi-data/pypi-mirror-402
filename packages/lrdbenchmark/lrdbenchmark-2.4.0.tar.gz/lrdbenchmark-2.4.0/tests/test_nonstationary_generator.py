#!/usr/bin/env python3
"""
Tests for nonstationary time series generators.

These tests verify that the nonstationary generators produce signals with
the expected time-varying Hurst parameter characteristics.
"""

import pytest
import numpy as np
from lrdbenchmark.generation.nonstationary_generator import (
    RegimeSwitchingProcess,
    ContinuousDriftProcess,
    StructuralBreakProcess,
    EnsembleTimeAverageProcess,
    DriftType,
    create_nonstationary_process
)


class TestRegimeSwitchingProcess:
    """Tests for RegimeSwitchingProcess."""
    
    def test_basic_generation(self):
        """Test basic signal generation."""
        gen = RegimeSwitchingProcess(
            h_regimes=[0.3, 0.8],
            change_points=[0.5],
            random_state=42
        )
        result = gen.generate(1000)
        
        assert 'signal' in result
        assert 'h_trajectory' in result
        assert 'metadata' in result
        assert len(result['signal']) == 1000
        assert len(result['h_trajectory']) == 1000
    
    def test_h_trajectory_values(self):
        """Test that H trajectory has correct values in each regime."""
        gen = RegimeSwitchingProcess(
            h_regimes=[0.3, 0.8],
            change_points=[0.5],
            random_state=42
        )
        result = gen.generate(1000)
        
        h_traj = result['h_trajectory']
        
        # First half should be 0.3
        assert np.allclose(h_traj[:500], 0.3)
        # Second half should be 0.8
        assert np.allclose(h_traj[500:], 0.8)
    
    def test_multiple_regimes(self):
        """Test generation with multiple regimes."""
        gen = RegimeSwitchingProcess(
            h_regimes=[0.3, 0.5, 0.8],
            change_points=[0.33, 0.66],
            random_state=42
        )
        result = gen.generate(900)
        
        assert result['metadata']['n_regimes'] == 3
    
    def test_reproducibility(self):
        """Test that same seed produces same output."""
        gen1 = RegimeSwitchingProcess(h_regimes=[0.3, 0.8], random_state=42)
        gen2 = RegimeSwitchingProcess(h_regimes=[0.3, 0.8], random_state=42)
        
        result1 = gen1.generate(500, seed=123)
        result2 = gen2.generate(500, seed=123)
        
        np.testing.assert_array_equal(result1['signal'], result2['signal'])
    
    def test_invalid_change_points(self):
        """Test error handling for invalid change points."""
        with pytest.raises(ValueError):
            RegimeSwitchingProcess(
                h_regimes=[0.3, 0.5, 0.8],
                change_points=[0.5]  # Need 2 change points for 3 regimes
            )


class TestContinuousDriftProcess:
    """Tests for ContinuousDriftProcess."""
    
    def test_linear_drift(self):
        """Test linear H drift."""
        gen = ContinuousDriftProcess(
            h_start=0.3, h_end=0.8,
            drift_type='linear',
            random_state=42
        )
        result = gen.generate(1000)
        
        h_traj = result['h_trajectory']
        
        # Check start and end values
        assert np.isclose(h_traj[0], 0.3, atol=0.01)
        assert np.isclose(h_traj[-1], 0.8, atol=0.01)
        
        # Check monotonicity for linear drift
        assert np.all(np.diff(h_traj) >= 0)
    
    def test_sinusoidal_drift(self):
        """Test sinusoidal H drift."""
        gen = ContinuousDriftProcess(
            h_start=0.3, h_end=0.8,
            drift_type='sinusoidal',
            drift_params={'frequency': 2.0},
            random_state=42
        )
        result = gen.generate(1000)
        
        h_traj = result['h_trajectory']
        
        # Sinusoidal should oscillate
        assert h_traj.min() < 0.6  # Below mean
        assert h_traj.max() > 0.5  # Above mean
    
    def test_logistic_drift(self):
        """Test logistic (S-curve) H drift."""
        gen = ContinuousDriftProcess(
            h_start=0.3, h_end=0.8,
            drift_type='logistic',
            drift_params={'steepness': 10.0},
            random_state=42
        )
        result = gen.generate(1000)
        
        h_traj = result['h_trajectory']
        
        # Should have S-curve shape: slow at start/end, fast in middle
        assert np.isclose(h_traj[0], 0.3, atol=0.05)
        assert np.isclose(h_traj[-1], 0.8, atol=0.05)
    
    def test_drift_type_enum(self):
        """Test using DriftType enum."""
        gen = ContinuousDriftProcess(
            h_start=0.3, h_end=0.8,
            drift_type=DriftType.EXPONENTIAL,
            random_state=42
        )
        result = gen.generate(500)
        
        assert result['metadata']['drift_type'] == 'exponential'


class TestStructuralBreakProcess:
    """Tests for StructuralBreakProcess."""
    
    def test_single_break(self):
        """Test single structural break."""
        gen = StructuralBreakProcess(
            h_before=0.7, h_after=0.4,
            break_position=0.5,
            random_state=42
        )
        result = gen.generate(1000)
        
        assert 'break_indices' in result
        assert len(result['break_indices']) == 1
        assert result['break_indices'][0] == 500
    
    def test_multiple_breaks(self):
        """Test multiple structural breaks."""
        gen = StructuralBreakProcess(
            h_before=0.7, h_after=0.4,
            n_breaks=3,
            random_state=42
        )
        result = gen.generate(1000)
        
        assert len(result['break_indices']) == 3
    
    def test_level_shift(self):
        """Test that level shift is applied."""
        gen = StructuralBreakProcess(
            h_before=0.7, h_after=0.7,  # Same H
            break_severity=2.0,  # Strong level shift
            break_position=0.5,
            random_state=42
        )
        result = gen.generate(1000)
        
        signal = result['signal']
        
        # Mean before and after should differ
        mean_before = np.mean(signal[:500])
        mean_after = np.mean(signal[500:])
        assert abs(mean_after - mean_before) > 0.5
    
    def test_variance_change(self):
        """Test that variance change is applied."""
        gen = StructuralBreakProcess(
            h_before=0.7, h_after=0.7,
            variance_change=4.0,  # Double std after break
            break_position=0.5,
            random_state=42
        )
        result = gen.generate(1000)
        
        signal = result['signal']
        
        var_before = np.var(signal[:500])
        var_after = np.var(signal[500:])
        
        # Variance ratio should be approximately 4
        assert var_after / var_before > 2.0


class TestEnsembleTimeAverageProcess:
    """Tests for EnsembleTimeAverageProcess."""
    
    def test_basic_generation(self):
        """Test basic signal generation."""
        gen = EnsembleTimeAverageProcess(
            H=0.7,
            aging_exponent=0.5,
            random_state=42
        )
        result = gen.generate(500)
        
        assert len(result['signal']) == 500
        assert result['metadata']['ergodic'] == False
    
    def test_ensemble_generation(self):
        """Test ensemble generation for ergodicity testing."""
        gen = EnsembleTimeAverageProcess(
            H=0.7,
            aging_exponent=0.3,
            random_state=42
        )
        result = gen.generate_ensemble(
            n_realizations=10,
            length=500,
            seed=42
        )
        
        assert result['ensemble'].shape == (10, 500)
        assert len(result['ensemble_mean']) == 500
        assert len(result['time_mean']) == 10
    
    def test_aging_types(self):
        """Test different aging types."""
        for aging_type in ['power_law', 'logarithmic', 'exponential']:
            gen = EnsembleTimeAverageProcess(
                H=0.7,
                aging_exponent=0.5,
                aging_type=aging_type,
                random_state=42
            )
            result = gen.generate(500)
            
            assert result['metadata']['aging_type'] == aging_type


class TestFactoryFunction:
    """Tests for create_nonstationary_process factory."""
    
    def test_create_regime_switching(self):
        """Test factory creates regime switching process."""
        gen = create_nonstationary_process(
            'regime_switching',
            h_regimes=[0.3, 0.8],
            random_state=42
        )
        assert isinstance(gen, RegimeSwitchingProcess)
    
    def test_create_continuous_drift(self):
        """Test factory creates continuous drift process."""
        gen = create_nonstationary_process(
            'continuous_drift',
            h_start=0.3,
            h_end=0.8,
            random_state=42
        )
        assert isinstance(gen, ContinuousDriftProcess)
    
    def test_create_structural_break(self):
        """Test factory creates structural break process."""
        gen = create_nonstationary_process(
            'structural_break',
            h_before=0.7,
            h_after=0.4,
            random_state=42
        )
        assert isinstance(gen, StructuralBreakProcess)
    
    def test_create_ensemble_time_average(self):
        """Test factory creates ensemble time average process."""
        gen = create_nonstationary_process(
            'ensemble_time_average',
            H=0.7,
            random_state=42
        )
        assert isinstance(gen, EnsembleTimeAverageProcess)
    
    def test_invalid_process_type(self):
        """Test error for invalid process type."""
        with pytest.raises(ValueError):
            create_nonstationary_process('invalid_type')


class TestNumericalStability:
    """Tests for numerical stability at edge cases."""
    
    def test_extreme_h_values(self):
        """Test generation with extreme H values."""
        gen = RegimeSwitchingProcess(
            h_regimes=[0.05, 0.95],  # Near boundaries
            random_state=42
        )
        result = gen.generate(500)
        
        # Should not have NaN or Inf
        assert np.all(np.isfinite(result['signal']))
    
    def test_short_series(self):
        """Test generation of short series."""
        gen = ContinuousDriftProcess(h_start=0.3, h_end=0.8, random_state=42)
        result = gen.generate(50)  # Very short
        
        assert len(result['signal']) == 50
        assert np.all(np.isfinite(result['signal']))
    
    def test_long_series(self):
        """Test generation of long series."""
        gen = StructuralBreakProcess(h_before=0.7, h_after=0.4, random_state=42)
        result = gen.generate(10000)
        
        assert len(result['signal']) == 10000
        assert np.all(np.isfinite(result['signal']))
