#!/usr/bin/env python3
"""
Tests for critical regime generators.
"""

import pytest
import numpy as np
from lrdbenchmark.generation.critical_regime_generator import (
    OrnsteinUhlenbeckProcess,
    SubordinatedProcess,
    FractionalLevyMotion,
    SOCAvalancheModel,
    create_critical_regime_process
)


class TestOrnsteinUhlenbeckProcess:
    """Tests for OU process with time-varying friction."""
    
    def test_basic_generation(self):
        """Test basic signal generation."""
        gen = OrnsteinUhlenbeckProcess(
            theta_start=0.1, theta_end=1.0,
            random_state=42
        )
        result = gen.generate(500)
        
        assert 'signal' in result
        assert 'theta_trajectory' in result
        assert len(result['signal']) == 500
        assert np.all(np.isfinite(result['signal']))
    
    def test_theta_trajectory(self):
        """Test theta trajectory shapes."""
        gen = OrnsteinUhlenbeckProcess(
            theta_start=0.1, theta_end=1.0,
            transition_type='linear',
            random_state=42
        )
        result = gen.generate(500)
        
        theta = result['theta_trajectory']
        assert np.isclose(theta[0], 0.1, atol=0.01)
        assert np.isclose(theta[-1], 1.0, atol=0.01)
    
    def test_transition_types(self):
        """Test different transition types."""
        for trans_type in ['linear', 'exponential', 'step']:
            gen = OrnsteinUhlenbeckProcess(
                theta_start=0.1, theta_end=1.0,
                transition_type=trans_type,
                random_state=42
            )
            result = gen.generate(500)
            assert len(result['signal']) == 500
    
    def test_reproducibility(self):
        """Test reproducibility with same seed."""
        gen1 = OrnsteinUhlenbeckProcess(random_state=42)
        gen2 = OrnsteinUhlenbeckProcess(random_state=42)
        
        result1 = gen1.generate(200, seed=123)
        result2 = gen2.generate(200, seed=123)
        
        np.testing.assert_array_equal(result1['signal'], result2['signal'])


class TestSubordinatedProcess:
    """Tests for subordinated Brownian motion."""
    
    def test_basic_generation(self):
        """Test basic generation."""
        gen = SubordinatedProcess(alpha=0.7, random_state=42)
        result = gen.generate(500)
        
        assert 'signal' in result
        assert len(result['signal']) == 500
        assert np.all(np.isfinite(result['signal']))
    
    def test_alpha_range(self):
        """Test different alpha values."""
        for alpha in [0.3, 0.5, 0.7, 0.9]:
            gen = SubordinatedProcess(alpha=alpha, random_state=42)
            result = gen.generate(300)
            assert len(result['signal']) == 300
    
    def test_invalid_alpha(self):
        """Test error for invalid alpha."""
        with pytest.raises(ValueError):
            SubordinatedProcess(alpha=1.5)
        with pytest.raises(ValueError):
            SubordinatedProcess(alpha=0.0)
    
    def test_metadata(self):
        """Test metadata content."""
        gen = SubordinatedProcess(alpha=0.7, random_state=42)
        result = gen.generate(100)
        
        assert result['metadata']['subdiffusive'] == True
        assert result['metadata']['ergodic'] == False


class TestFractionalLevyMotion:
    """Tests for fractional Lévy motion."""
    
    def test_basic_generation(self):
        """Test basic generation."""
        gen = FractionalLevyMotion(H=0.7, alpha=1.5, random_state=42)
        result = gen.generate(500)
        
        assert 'signal' in result
        assert len(result['signal']) == 500
        assert np.all(np.isfinite(result['signal']))
    
    def test_gaussian_case(self):
        """Test alpha=2 (Gaussian) case."""
        gen = FractionalLevyMotion(H=0.7, alpha=2.0, random_state=42)
        result = gen.generate(500)
        
        assert len(result['signal']) == 500
        assert result['metadata']['heavy_tailed'] == False
    
    def test_heavy_tailed_case(self):
        """Test alpha<2 (heavy-tailed) case."""
        gen = FractionalLevyMotion(H=0.7, alpha=1.5, random_state=42)
        result = gen.generate(500)
        
        assert result['metadata']['heavy_tailed'] == True
        assert result['metadata']['infinite_variance'] == True
    
    def test_invalid_parameters(self):
        """Test error for invalid parameters."""
        with pytest.raises(ValueError):
            FractionalLevyMotion(H=1.5)  # Invalid H
        with pytest.raises(ValueError):
            FractionalLevyMotion(alpha=2.5)  # Invalid alpha
        with pytest.raises(ValueError):
            FractionalLevyMotion(beta=2.0)  # Invalid beta


class TestSOCAvalancheModel:
    """Tests for SOC sandpile model."""
    
    def test_basic_generation(self):
        """Test basic generation."""
        gen = SOCAvalancheModel(grid_size=16, random_state=42)
        result = gen.generate(200, warmup=100)
        
        assert 'signal' in result
        assert len(result['signal']) == 200
        assert np.all(np.isfinite(result['signal']))
    
    def test_raw_avalanche_sizes(self):
        """Test raw avalanche sizes are returned."""
        gen = SOCAvalancheModel(grid_size=16, random_state=42)
        result = gen.generate(100, warmup=50)
        
        assert 'raw_avalanche_sizes' in result
        assert len(result['raw_avalanche_sizes']) == 100
    
    def test_normalized_output(self):
        """Test that output is normalized."""
        gen = SOCAvalancheModel(grid_size=16, random_state=42)
        result = gen.generate(500, warmup=200)
        
        # Should be approximately zero mean, unit variance
        assert abs(np.mean(result['signal'])) < 0.5
        assert abs(np.std(result['signal']) - 1.0) < 0.5
    
    def test_metadata(self):
        """Test metadata content."""
        gen = SOCAvalancheModel(grid_size=32, random_state=42)
        result = gen.generate(100)
        
        assert result['metadata']['critical'] == True
        assert result['metadata']['power_law_distributed'] == True


class TestFactoryFunction:
    """Tests for create_critical_regime_process factory."""
    
    def test_create_ou(self):
        """Test creating OU process."""
        gen = create_critical_regime_process('ornstein_uhlenbeck', random_state=42)
        assert isinstance(gen, OrnsteinUhlenbeckProcess)
        
        gen = create_critical_regime_process('ou', random_state=42)
        assert isinstance(gen, OrnsteinUhlenbeckProcess)
    
    def test_create_subordinated(self):
        """Test creating subordinated process."""
        gen = create_critical_regime_process('subordinated', alpha=0.7, random_state=42)
        assert isinstance(gen, SubordinatedProcess)
    
    def test_create_levy(self):
        """Test creating fractional Lévy motion."""
        gen = create_critical_regime_process('fractional_levy', H=0.7, alpha=1.5, random_state=42)
        assert isinstance(gen, FractionalLevyMotion)
    
    def test_create_soc(self):
        """Test creating SOC model."""
        gen = create_critical_regime_process('soc_avalanche', grid_size=16, random_state=42)
        assert isinstance(gen, SOCAvalancheModel)
        
        gen = create_critical_regime_process('sandpile', grid_size=16, random_state=42)
        assert isinstance(gen, SOCAvalancheModel)
    
    def test_invalid_type(self):
        """Test error for invalid process type."""
        with pytest.raises(ValueError):
            create_critical_regime_process('invalid')


class TestNumericalStability:
    """Tests for numerical stability."""
    
    def test_long_ou_series(self):
        """Test long OU series generation."""
        gen = OrnsteinUhlenbeckProcess(random_state=42)
        result = gen.generate(5000)
        assert np.all(np.isfinite(result['signal']))
    
    def test_extreme_alpha_levy(self):
        """Test extreme alpha values in Lévy motion."""
        for alpha in [0.5, 1.0, 1.9]:
            gen = FractionalLevyMotion(H=0.7, alpha=alpha, random_state=42)
            result = gen.generate(300)
            # May have some extreme values but should complete
            assert len(result['signal']) == 300
    
    def test_small_grid_soc(self):
        """Test small grid SOC."""
        gen = SOCAvalancheModel(grid_size=8, random_state=42)
        result = gen.generate(100)
        assert len(result['signal']) == 100
