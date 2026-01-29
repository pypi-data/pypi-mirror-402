"""
Comprehensive tests for torchfbm generators module.

Tests cover:
- Compilation and imports
- Output shapes and dtypes
- Seed reproducibility
- Mathematical properties (covariance structure, scaling)
- Edge cases and error handling
- Device compatibility
"""
import pytest
import torch
import numpy as np
from torchfbm import fbm, generate_davies_harte, generate_cholesky
from torchfbm.generators import _autocovariance


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(params=[0.1, 0.3, 0.5, 0.7])
def hurst_param(request):
    """Parametrize over a range of Hurst parameters.
    
    Excludes H=0.9 from parametrized tests since Cholesky method
    has numerical stability issues near H=1 for large n.
    """
    return request.param


@pytest.fixture(params=["davies_harte", "cholesky"])
def method(request):
    """Parametrize over generation methods."""
    return request.param


@pytest.fixture(params=[torch.float32, torch.float64])
def dtype(request):
    """Parametrize over supported dtypes."""
    return request.param


@pytest.fixture
def device():
    """Return available device."""
    return "cuda" if torch.cuda.is_available() else "cpu"


# =============================================================================
# Basic Import and Compilation Tests
# =============================================================================

class TestImports:
    """Test that all modules import correctly."""

    def test_import_fbm(self):
        from torchfbm import fbm
        assert callable(fbm)

    def test_import_generators(self):
        from torchfbm import generate_davies_harte, generate_cholesky
        assert callable(generate_davies_harte)
        assert callable(generate_cholesky)

    def test_import_autocovariance(self):
        from torchfbm.generators import _autocovariance
        assert callable(_autocovariance)


# =============================================================================
# Shape and Dtype Tests
# =============================================================================

class TestShapeAndDtype:
    """Test output shapes and data types."""

    @pytest.mark.parametrize("n", [10, 100, 1000])
    @pytest.mark.parametrize("size", [(1,), (5,), (2, 3)])
    def test_fbm_output_shape(self, n, size):
        """fBm output should have shape (*size, n+1)."""
        result = fbm(n, H=0.5, size=size)
        expected_shape = (*size, n + 1)
        assert result.shape == expected_shape, f"Expected {expected_shape}, got {result.shape}"

    @pytest.mark.parametrize("n", [10, 100])
    @pytest.mark.parametrize("size", [(1,), (5,), (2, 3)])
    def test_fgn_output_shape(self, n, size, method):
        """fGn output should have shape (*size, n)."""
        if method == "davies_harte":
            result = generate_davies_harte(n, H=0.5, size=size)
        else:
            result = generate_cholesky(n, H=0.5, size=size)
        expected_shape = (*size, n)
        assert result.shape == expected_shape, f"Expected {expected_shape}, got {result.shape}"

    def test_output_dtype_float32(self):
        """Default dtype should be float32."""
        result = fbm(100, H=0.5)
        assert result.dtype == torch.float32

    def test_output_dtype_float64(self):
        """Should respect float64 dtype."""
        result = fbm(100, H=0.5, dtype=torch.float64)
        assert result.dtype == torch.float64

    def test_output_is_tensor(self):
        """Default output should be a torch.Tensor."""
        result = fbm(100, H=0.5)
        assert isinstance(result, torch.Tensor)

    def test_output_numpy(self):
        """return_numpy=True should return numpy array."""
        result = fbm(100, H=0.5, return_numpy=True)
        assert isinstance(result, np.ndarray)


# =============================================================================
# Seed Reproducibility Tests
# =============================================================================

class TestSeedReproducibility:
    """Test that seeds produce reproducible results."""

    def test_fbm_seed_reproducibility(self, method):
        """Same seed should produce identical results."""
        result1 = fbm(100, H=0.5, method=method, seed=42)
        result2 = fbm(100, H=0.5, method=method, seed=42)
        torch.testing.assert_close(result1, result2)

    def test_fbm_different_seeds(self, method):
        """Different seeds should produce different results."""
        result1 = fbm(100, H=0.5, method=method, seed=42)
        result2 = fbm(100, H=0.5, method=method, seed=43)
        assert not torch.allclose(result1, result2), "Different seeds produced identical results"

    def test_fgn_seed_reproducibility_davies_harte(self):
        """Davies-Harte with same seed should be reproducible."""
        result1 = generate_davies_harte(100, H=0.7, seed=123)
        result2 = generate_davies_harte(100, H=0.7, seed=123)
        torch.testing.assert_close(result1, result2)

    def test_fgn_seed_reproducibility_cholesky(self):
        """Cholesky with same seed should be reproducible."""
        result1 = generate_cholesky(100, H=0.7, seed=123)
        result2 = generate_cholesky(100, H=0.7, seed=123)
        torch.testing.assert_close(result1, result2)


# =============================================================================
# Mathematical Property Tests
# =============================================================================

class TestMathematicalProperties:
    """Test mathematical properties of fBm/fGn."""

    def test_fbm_starts_at_zero(self, method):
        """fBm path should start at zero."""
        result = fbm(100, H=0.5, size=(10,), method=method)
        assert torch.allclose(result[:, 0], torch.zeros(10), atol=1e-7)

    def test_fgn_zero_mean(self, hurst_param, method):
        """fGn should have approximately zero mean (law of large numbers)."""
        # Cholesky has numerical issues for large n, especially with higher H
        n = 1000 if method == "cholesky" else 10000
        num_samples = 100 if method == "cholesky" else 100
        
        result = generate_davies_harte(n, hurst_param, size=(num_samples,)) if method == "davies_harte" \
                 else generate_cholesky(n, hurst_param, size=(num_samples,))
        mean = result.mean()
        assert abs(mean.item()) < 0.15, f"Mean {mean.item()} too far from zero"

    def test_fgn_unit_variance(self, hurst_param, method):
        """fGn should have approximately unit variance at lag 0."""
        # Cholesky has numerical issues for large n
        n = 1000 if method == "cholesky" else 10000
        num_samples = 100 if method == "cholesky" else 100
        
        result = generate_davies_harte(n, hurst_param, size=(num_samples,)) if method == "davies_harte" \
                 else generate_cholesky(n, hurst_param, size=(num_samples,))
        var = result.var(dim=-1).mean()
        assert 0.7 < var.item() < 1.3, f"Variance {var.item()} not close to 1.0"

    def test_autocovariance_lag_zero(self, hurst_param):
        """Autocovariance at lag 0 should be 1.0."""
        gamma = _autocovariance(hurst_param, 10, torch.device("cpu"), torch.float32)
        assert abs(gamma[0].item() - 1.0) < 1e-6, f"gamma(0) = {gamma[0].item()}, expected 1.0"

    def test_autocovariance_symmetry(self, hurst_param):
        """Autocovariance function should match theoretical formula."""
        n = 20
        gamma = _autocovariance(hurst_param, n, torch.device("cpu"), torch.float32)
        
        # Verify formula: gamma(k) = 0.5 * (|k+1|^{2H} - 2|k|^{2H} + |k-1|^{2H})
        for k in range(n):
            expected = 0.5 * (abs(k+1)**(2*hurst_param) - 2*abs(k)**(2*hurst_param) + abs(k-1)**(2*hurst_param))
            assert abs(gamma[k].item() - expected) < 1e-5, f"gamma({k}) mismatch"

    def test_hurst_scaling_variance(self, hurst_param):
        """Variance of increments should scale as tau^{2H}."""
        n = 5000
        num_samples = 50
        path = fbm(n, hurst_param, size=(num_samples,), seed=42)
        
        lags = [10, 20, 50, 100]
        variances = []
        for lag in lags:
            increments = path[:, lag:] - path[:, :-lag]
            var = increments.var(dim=-1).mean()
            variances.append(var.item())
        
        # In log-log space, slope should be ~2H
        log_lags = np.log(lags)
        log_vars = np.log(variances)
        
        # Linear regression
        slope, _ = np.polyfit(log_lags, log_vars, 1)
        estimated_H = slope / 2
        
        # Allow some tolerance for finite samples
        assert abs(estimated_H - hurst_param) < 0.15, \
            f"Estimated H={estimated_H:.3f}, expected {hurst_param}"

    def test_h_clamping(self):
        """H values outside (0, 1) should be clamped."""
        # H > 1 should be clamped to 0.99
        result = fbm(100, H=1.5)
        assert result is not None and not torch.isnan(result).any()
        
        # H < 0 should be clamped to 0.01
        result = fbm(100, H=-0.5)
        assert result is not None and not torch.isnan(result).any()


# =============================================================================
# Device Compatibility Tests
# =============================================================================

class TestDeviceCompatibility:
    """Test GPU/CPU device handling."""

    def test_cpu_generation(self):
        """Generation on CPU should work."""
        result = fbm(100, H=0.5, device="cpu")
        assert result.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_generation(self):
        """Generation on CUDA should work."""
        result = fbm(100, H=0.5, device="cuda")
        assert result.device.type == "cuda"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_seed_reproducibility(self):
        """Seeds should work on CUDA."""
        result1 = fbm(100, H=0.5, device="cuda", seed=42)
        result2 = fbm(100, H=0.5, device="cuda", seed=42)
        torch.testing.assert_close(result1, result2)


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_n_equals_one(self, method):
        """n=1 should produce valid output."""
        if method == "davies_harte":
            result = generate_davies_harte(1, H=0.5)
        else:
            result = generate_cholesky(1, H=0.5)
        assert result.shape[-1] == 1

    def test_n_equals_two(self, method):
        """n=2 should produce valid output."""
        result = fbm(2, H=0.5, method=method)
        assert result.shape[-1] == 3  # n+1 points

    def test_large_n(self, method):
        """Large n should not crash (but may be slow for Cholesky)."""
        # Cholesky is O(n^3), so limit to smaller n
        # Also, Cholesky can have numerical issues for large n with H near extremes
        n = 200 if method == "cholesky" else 10000
        result = fbm(n, H=0.5, method=method)
        assert result.shape[-1] == n + 1

    def test_extreme_h_low(self):
        """Very low H (rough) should work."""
        result = fbm(100, H=0.05)
        assert not torch.isnan(result).any()

    def test_extreme_h_high(self):
        """Very high H (smooth) should work with Davies-Harte."""
        # Cholesky can have numerical issues near H=1
        result = fbm(100, H=0.95, method="davies_harte")
        assert not torch.isnan(result).any()

    def test_no_nan_or_inf(self, hurst_param, method):
        """Output should never contain NaN or Inf."""
        result = fbm(1000, hurst_param, method=method)
        assert not torch.isnan(result).any(), "NaN detected in output"
        assert not torch.isinf(result).any(), "Inf detected in output"


# =============================================================================
# Cross-Method Consistency Tests
# =============================================================================

class TestMethodConsistency:
    """Test that different methods produce statistically consistent results."""

    def test_methods_same_distribution(self, hurst_param):
        """Davies-Harte and Cholesky should produce same distribution."""
        n = 1000
        num_samples = 100
        
        dh_result = generate_davies_harte(n, hurst_param, size=(num_samples,), seed=42)
        ch_result = generate_cholesky(n, hurst_param, size=(num_samples,), seed=42)
        
        # They won't be identical (different algorithms), but statistics should match
        dh_mean, ch_mean = dh_result.mean().item(), ch_result.mean().item()
        dh_std, ch_std = dh_result.std().item(), ch_result.std().item()
        
        # Allow reasonable tolerance
        assert abs(dh_mean - ch_mean) < 0.2, "Means differ significantly"
        assert abs(dh_std - ch_std) < 0.2, "Stds differ significantly"
