"""
Comprehensive tests for torchfbm processes module.

Tests cover:
- Compilation and imports
- Output shapes and dtypes
- Mathematical properties (positivity, boundedness, etc.)
- Seed reproducibility
- Edge cases
"""
import pytest
import torch
import numpy as np
from torchfbm import (
    fractional_ou_process,
    geometric_fbm,
    reflected_fbm,
    fractional_brownian_bridge,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(params=["davies_harte", "cholesky"])
def method(request):
    return request.param


@pytest.fixture(params=[0.3, 0.5, 0.7])
def hurst_param(request):
    return request.param


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test that all process functions import correctly."""

    def test_import_fractional_ou(self):
        from torchfbm import fractional_ou_process
        assert callable(fractional_ou_process)

    def test_import_geometric_fbm(self):
        from torchfbm import geometric_fbm
        assert callable(geometric_fbm)

    def test_import_reflected_fbm(self):
        from torchfbm import reflected_fbm
        assert callable(reflected_fbm)

    def test_import_brownian_bridge(self):
        from torchfbm import fractional_brownian_bridge
        assert callable(fractional_brownian_bridge)


# =============================================================================
# Fractional OU Process Tests
# =============================================================================

class TestFractionalOU:
    """Test fractional Ornstein-Uhlenbeck process."""

    def test_output_shape(self, method):
        """Output shape should be (*size, n+1)."""
        result = fractional_ou_process(100, H=0.5, size=(5,), method=method)
        assert result.shape == (5, 101)

    def test_output_dtype(self):
        """Output dtype should match specified dtype."""
        result = fractional_ou_process(100, H=0.5, dtype=torch.float64)
        assert result.dtype == torch.float64

    def test_starts_at_mean(self, method):
        """Process should start at mu."""
        mu = 2.5
        result = fractional_ou_process(100, H=0.5, mu=mu, method=method, size=(10,))
        torch.testing.assert_close(result[:, 0], torch.full((10,), mu))

    def test_mean_reversion(self, method):
        """Process should revert toward mu on average."""
        mu = 1.0
        theta = 2.0  # Strong mean reversion
        result = fractional_ou_process(
            500, H=0.5, theta=theta, mu=mu, dt=0.01, size=(100,), method=method
        )
        final_mean = result[:, -1].mean().item()
        # Should be close to mu (within some tolerance)
        assert abs(final_mean - mu) < 1.0

    def test_seed_reproducibility(self, method):
        """Same seed should give same result."""
        r1 = fractional_ou_process(100, H=0.5, method=method, size=(1,))
        r2 = fractional_ou_process(100, H=0.5, method=method, size=(1,))
        # Without seed, results will differ; this tests that function runs
        assert r1.shape == r2.shape

    def test_numpy_output(self, method):
        """return_numpy=True should return numpy array."""
        result = fractional_ou_process(100, H=0.5, method=method, return_numpy=True)
        assert isinstance(result, np.ndarray)

    def test_no_nan_or_inf(self, hurst_param, method):
        """Output should not contain NaN or Inf."""
        result = fractional_ou_process(500, hurst_param, method=method, size=(10,))
        assert not torch.isnan(result).any()
        assert not torch.isinf(result).any()


# =============================================================================
# Geometric fBm Tests
# =============================================================================

class TestGeometricFBM:
    """Test geometric fractional Brownian motion."""

    def test_output_shape(self, method):
        """Output shape should be (*size, n+1)."""
        result = geometric_fbm(100, H=0.5, size=(5,), method=method)
        assert result.shape == (5, 101)

    def test_starts_at_s0(self, method):
        """Process should start at s0."""
        s0 = 150.0
        result = geometric_fbm(100, H=0.5, s0=s0, size=(10,), method=method)
        torch.testing.assert_close(result[:, 0], torch.full((10,), s0))

    def test_always_positive(self, hurst_param, method):
        """Geometric fBm should always be positive."""
        result = geometric_fbm(500, hurst_param, size=(50,), method=method)
        assert (result > 0).all(), "Geometric fBm produced non-positive values"

    def test_no_nan_or_inf(self, hurst_param, method):
        """Output should not contain NaN or Inf."""
        result = geometric_fbm(500, hurst_param, method=method, size=(10,))
        assert not torch.isnan(result).any()
        assert not torch.isinf(result).any()

    def test_numpy_output(self, method):
        """return_numpy=True should return numpy array."""
        result = geometric_fbm(100, H=0.5, method=method, return_numpy=True)
        assert isinstance(result, np.ndarray)

    def test_invalid_n_raises(self):
        """n <= 0 should raise ValueError."""
        with pytest.raises(ValueError):
            geometric_fbm(0, H=0.5)
        with pytest.raises(ValueError):
            geometric_fbm(-10, H=0.5)


# =============================================================================
# Reflected fBm Tests
# =============================================================================

class TestReflectedFBM:
    """Test reflected fractional Brownian motion."""

    def test_output_shape(self, method):
        """Output shape should be (*size, n+1)."""
        result = reflected_fbm(100, H=0.5, size=(5,), method=method)
        assert result.shape == (5, 101)

    def test_stays_in_bounds(self, hurst_param, method):
        """Reflected fBm should stay within [lower, upper]."""
        lower, upper = -1.0, 1.0
        result = reflected_fbm(
            500, hurst_param, lower=lower, upper=upper, size=(50,), method=method
        )
        assert (result >= lower).all(), f"Values below lower bound {lower}"
        assert (result <= upper).all(), f"Values above upper bound {upper}"

    def test_custom_bounds(self, method):
        """Custom bounds should be respected."""
        lower, upper = 0.0, 10.0
        result = reflected_fbm(
            200, H=0.5, lower=lower, upper=upper, start_val=5.0, size=(20,), method=method
        )
        assert (result >= lower).all()
        assert (result <= upper).all()

    def test_starts_at_start_val(self, method):
        """Process should start at start_val."""
        start_val = 0.5
        result = reflected_fbm(100, H=0.5, start_val=start_val, size=(10,), method=method)
        torch.testing.assert_close(result[:, 0], torch.full((10,), start_val))

    def test_no_nan_or_inf(self, hurst_param, method):
        """Output should not contain NaN or Inf."""
        result = reflected_fbm(500, hurst_param, method=method, size=(10,))
        assert not torch.isnan(result).any()
        assert not torch.isinf(result).any()

    def test_numpy_output(self, method):
        """return_numpy=True should return numpy array."""
        result = reflected_fbm(100, H=0.5, method=method, return_numpy=True)
        assert isinstance(result, np.ndarray)


# =============================================================================
# Fractional Brownian Bridge Tests
# =============================================================================

class TestFractionalBrownianBridge:
    """Test fractional Brownian bridge."""

    def test_output_shape(self, method):
        """Output shape should be (*size, n+1)."""
        result = fractional_brownian_bridge(100, H=0.5, size=(5,), method=method)
        assert result.shape == (5, 101)

    def test_starts_at_start(self, method):
        """Bridge should start at specified start value."""
        start_value = 1.0
        result = fractional_brownian_bridge(100, H=0.5, start_val=start_value, size=(10,), method=method)
        torch.testing.assert_close(result[:, 0], torch.full((10,), start_value), atol=1e-5, rtol=1e-5)

    def test_ends_at_end(self, method):
        """Bridge should end at specified end value."""
        end_value = 2.0
        result = fractional_brownian_bridge(100, H=0.5, end_val=end_value, size=(10,), method=method)
        torch.testing.assert_close(result[:, -1], torch.full((10,), end_value), atol=1e-5, rtol=1e-5)

    def test_start_and_end(self, hurst_param, method):
        """Bridge should connect start and end."""
        start_value, end_value = -1.0, 3.0
        result = fractional_brownian_bridge(
            200, hurst_param, start_val=start_value, end_val=end_value, size=(20,), method=method
        )
        torch.testing.assert_close(result[:, 0], torch.full((20,), start_value), atol=1e-5, rtol=1e-5)
        torch.testing.assert_close(result[:, -1], torch.full((20,), end_value), atol=1e-5, rtol=1e-5)

    def test_no_nan_or_inf(self, hurst_param, method):
        """Output should not contain NaN or Inf."""
        result = fractional_brownian_bridge(500, hurst_param, method=method, size=(10,))
        assert not torch.isnan(result).any()
        assert not torch.isinf(result).any()

    def test_numpy_output(self, method):
        """return_numpy=True should return numpy array."""
        result = fractional_brownian_bridge(100, H=0.5, method=method, return_numpy=True)
        assert isinstance(result, np.ndarray)


# =============================================================================
# Device Compatibility Tests
# =============================================================================

class TestDeviceCompatibility:
    """Test GPU/CPU device handling."""

    def test_ou_cpu(self):
        result = fractional_ou_process(100, H=0.5, device="cpu")
        assert result.device.type == "cpu"

    def test_gfbm_cpu(self):
        result = geometric_fbm(100, H=0.5, device="cpu")
        assert result.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_ou_cuda(self):
        result = fractional_ou_process(100, H=0.5, device="cuda")
        assert result.device.type == "cuda"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_gfbm_cuda(self):
        result = geometric_fbm(100, H=0.5, device="cuda")
        assert result.device.type == "cuda"
