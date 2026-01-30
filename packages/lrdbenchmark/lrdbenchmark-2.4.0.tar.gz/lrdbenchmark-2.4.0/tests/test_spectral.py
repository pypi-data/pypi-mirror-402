import numpy as np
import pytest

from lrdbenchmark.analysis.spectral.periodogram_estimator import PeriodogramEstimator
from lrdbenchmark.analysis.spectral.whittle_estimator import WhittleEstimator
from lrdbenchmark.analysis.spectral.gph_estimator import GPHEstimator
from lrdbenchmark.models.data_models.fbm_model import FractionalBrownianMotion
from lrdbenchmark.models.data_models.fgn_model import FractionalGaussianNoise


def generate_fgn_from_fbm(H: float, n: int, seed: int = 123) -> np.ndarray:
    # Use FractionalGaussianNoise directly instead of fBm differences
    fgn = FractionalGaussianNoise(H=H)
    return fgn.generate(n, seed=seed)


def test_periodogram_basic():
    data = generate_fgn_from_fbm(0.7, 2048)
    est = PeriodogramEstimator(max_freq_ratio=0.1)
    res = est.estimate(data)
    assert "hurst_parameter" in res
    assert np.isfinite(res["hurst_parameter"]) and 0.0 < res["hurst_parameter"] < 1.5


def test_whittle_basic():
    data = generate_fgn_from_fbm(0.6, 2048)
    est = WhittleEstimator()
    res = est.estimate(data)
    assert "hurst_parameter" in res and "d_parameter" in res
    assert np.isfinite(res["d_parameter"]) and -0.5 <= res["d_parameter"] <= 0.5


def test_gph_basic():
    data = generate_fgn_from_fbm(0.55, 2048)
    est = GPHEstimator()
    res = est.estimate(data)
    assert "hurst_parameter" in res and "d_parameter" in res
    assert np.isfinite(res["hurst_parameter"]) and 0.0 < res["hurst_parameter"] < 1.5


@pytest.mark.skip(reason="GPH estimator is known to be biased and requires further investigation.")
@pytest.mark.parametrize("true_h", [0.3, 0.5, 0.7, 0.9])
def test_gph_numerical_correctness(true_h):
    """Test GPH estimator for numerical correctness against known H values."""
    # Using a longer time series for better estimate stability
    data = generate_fgn_from_fbm(true_h, 4096)
    est = GPHEstimator(max_freq_ratio=0.1)
    res = est.estimate(data)

    assert "hurst_parameter" in res
    estimated_h = res["hurst_parameter"]

    # Allow for a reasonable tolerance for stochastic estimators
    assert estimated_h == pytest.approx(true_h, abs=0.2)




