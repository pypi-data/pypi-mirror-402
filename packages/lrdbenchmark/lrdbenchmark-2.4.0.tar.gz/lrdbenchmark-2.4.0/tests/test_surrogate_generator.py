#!/usr/bin/env python3
"""
Tests for surrogate data generators.
"""

import pytest
import numpy as np
from lrdbenchmark.generation.surrogate_generator import (
    IAFFTSurrogate,
    PhaseRandomizedSurrogate,
    ARSurrogate,
    create_surrogate_generator
)


class TestIAFFTSurrogate:
    """Tests for IAAFT surrogate generator."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample data for testing."""
        np.random.seed(42)
        return np.random.randn(256)
    
    def test_basic_generation(self, sample_data):
        """Test basic surrogate generation."""
        gen = IAFFTSurrogate(random_state=42)
        result = gen.generate(sample_data)
        
        assert 'surrogates' in result
        assert len(result['surrogates']) == len(sample_data)
        assert np.all(np.isfinite(result['surrogates']))
    
    def test_multiple_surrogates(self, sample_data):
        """Test generating multiple surrogates."""
        gen = IAFFTSurrogate(random_state=42)
        result = gen.generate(sample_data, n_surrogates=5)
        
        assert result['surrogates'].shape == (5, len(sample_data))
    
    def test_amplitude_preservation(self, sample_data):
        """Test that amplitude distribution is roughly preserved."""
        gen = IAFFTSurrogate(max_iterations=50, random_state=42)
        result = gen.generate(sample_data)
        
        original_sorted = np.sort(sample_data)
        surrogate_sorted = np.sort(result['surrogates'])
        
        # Amplitudes should be very similar
        np.testing.assert_array_almost_equal(original_sorted, surrogate_sorted, decimal=5)
    
    def test_convergence_info(self, sample_data):
        """Test that convergence info is returned."""
        gen = IAFFTSurrogate(random_state=42)
        result = gen.generate(sample_data)
        
        assert 'metadata' in result
        assert 'convergence_info' in result['metadata']
        assert len(result['metadata']['convergence_info']) == 1


class TestPhaseRandomizedSurrogate:
    """Tests for phase randomization surrogate."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample data."""
        np.random.seed(42)
        return np.random.randn(256)
    
    def test_basic_generation(self, sample_data):
        """Test basic generation."""
        gen = PhaseRandomizedSurrogate(random_state=42)
        result = gen.generate(sample_data)
        
        assert 'surrogates' in result
        assert len(result['surrogates']) == len(sample_data)
        assert np.all(np.isfinite(result['surrogates']))
    
    def test_power_spectrum_preservation(self, sample_data):
        """Test that power spectrum is preserved."""
        gen = PhaseRandomizedSurrogate(random_state=42)
        result = gen.generate(sample_data)
        
        from scipy.fft import fft
        
        original_power = np.abs(fft(sample_data))**2
        surrogate_power = np.abs(fft(result['surrogates']))**2
        
        # Power spectra should be identical
        np.testing.assert_array_almost_equal(original_power, surrogate_power, decimal=10)
    
    def test_multiple_surrogates(self, sample_data):
        """Test multiple surrogates."""
        gen = PhaseRandomizedSurrogate(random_state=42)
        result = gen.generate(sample_data, n_surrogates=3)
        
        assert result['surrogates'].shape == (3, len(sample_data))


class TestARSurrogate:
    """Tests for AR surrogate generator."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample AR-like data."""
        np.random.seed(42)
        n = 500
        data = np.zeros(n)
        for i in range(2, n):
            data[i] = 0.5 * data[i-1] + 0.3 * data[i-2] + np.random.randn()
        return data
    
    def test_basic_generation(self, sample_data):
        """Test basic generation."""
        gen = ARSurrogate(order=5, random_state=42)
        result = gen.generate(sample_data)
        
        assert 'surrogates' in result
        assert len(result['surrogates']) == len(sample_data)
        assert np.all(np.isfinite(result['surrogates']))
    
    def test_ar_coefficients_returned(self, sample_data):
        """Test that AR coefficients are returned."""
        gen = ARSurrogate(order=5, random_state=42)
        result = gen.generate(sample_data)
        
        assert 'ar_coefficients' in result
        assert len(result['ar_coefficients']) == 5
    
    def test_multiple_surrogates(self, sample_data):
        """Test multiple surrogates."""
        gen = ARSurrogate(order=3, random_state=42)
        result = gen.generate(sample_data, n_surrogates=4)
        
        assert result['surrogates'].shape == (4, len(sample_data))
    
    def test_different_orders(self, sample_data):
        """Test different AR orders."""
        for order in [1, 5, 10, 20]:
            gen = ARSurrogate(order=order, random_state=42)
            result = gen.generate(sample_data)
            assert len(result['ar_coefficients']) == order


class TestFactoryFunction:
    """Tests for create_surrogate_generator factory."""
    
    def test_create_iaaft(self):
        """Test creating IAAFT generator."""
        gen = create_surrogate_generator('iaaft', random_state=42)
        assert isinstance(gen, IAFFTSurrogate)
    
    def test_create_phase(self):
        """Test creating phase randomization generator."""
        gen = create_surrogate_generator('phase_randomization', random_state=42)
        assert isinstance(gen, PhaseRandomizedSurrogate)
    
    def test_create_ar(self):
        """Test creating AR generator."""
        gen = create_surrogate_generator('ar', order=5, random_state=42)
        assert isinstance(gen, ARSurrogate)
    
    def test_invalid_method(self):
        """Test error for invalid method."""
        with pytest.raises(ValueError):
            create_surrogate_generator('invalid')


class TestReproducibility:
    """Tests for reproducibility."""
    
    def test_iaaft_reproducibility(self):
        """Test IAAFT reproducibility."""
        np.random.seed(42)
        data = np.random.randn(128)
        
        gen1 = IAFFTSurrogate(random_state=42)
        gen2 = IAFFTSurrogate(random_state=42)
        
        result1 = gen1.generate(data, seed=123)
        result2 = gen2.generate(data, seed=123)
        
        np.testing.assert_array_equal(result1['surrogates'], result2['surrogates'])
    
    def test_phase_reproducibility(self):
        """Test phase randomization reproducibility."""
        np.random.seed(42)
        data = np.random.randn(128)
        
        gen1 = PhaseRandomizedSurrogate(random_state=42)
        gen2 = PhaseRandomizedSurrogate(random_state=42)
        
        result1 = gen1.generate(data, seed=123)
        result2 = gen2.generate(data, seed=123)
        
        np.testing.assert_array_equal(result1['surrogates'], result2['surrogates'])
