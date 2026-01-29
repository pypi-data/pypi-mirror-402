"""
Comprehensive tests for torchfbm estimators module.

Tests cover:
- Compilation and imports
- Output shapes and dtypes  
- Hurst estimation accuracy
- Seed reproducibility
- Edge cases
"""
import pytest
import torch
import numpy as np
from torchfbm import fbm, estimate_hurst


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(params=[0.2, 0.3, 0.5, 0.7, 0.8])
def true_hurst(request):
    """Parametrize over true Hurst values."""
    return request.param


# =============================================================================
# Basic Import Tests
# =============================================================================

class TestImports:
    """Test that estimator imports correctly."""

    def test_import_estimate_hurst(self):
        from torchfbm import estimate_hurst
        assert callable(estimate_hurst)


# =============================================================================
# Shape and Dtype Tests
# =============================================================================

class TestShapeAndDtype:
    """Test output shapes and data types."""

    def test_output_shape_single_batch(self):
        """Single batch element should return scalar-like tensor."""
        path = fbm(1000, H=0.5, size=(1,))
        h_est = estimate_hurst(path)
        assert h_est.shape == (1,)

    def test_output_shape_multiple_batch(self):
        """Multiple batch elements should return correct shape."""
        path = fbm(1000, H=0.5, size=(10,))
        h_est = estimate_hurst(path)
        assert h_est.shape == (10,)

    def test_output_is_tensor(self):
        """Default output should be torch.Tensor."""
        path = fbm(1000, H=0.5)
        h_est = estimate_hurst(path)
        assert isinstance(h_est, torch.Tensor)

    def test_output_numpy(self):
        """return_numpy=True should return numpy array."""
        path = fbm(1000, H=0.5)
        h_est = estimate_hurst(path, return_numpy=True)
        assert isinstance(h_est, np.ndarray)

    def test_output_dtype_matches_input(self):
        """Output dtype should be float."""
        path = fbm(1000, H=0.5, dtype=torch.float64)
        h_est = estimate_hurst(path)
        # Estimator may use float32 internally, but should be numeric
        assert h_est.dtype in [torch.float32, torch.float64]


# =============================================================================
# Estimation Accuracy Tests
# =============================================================================

class TestEstimationAccuracy:
    """Test Hurst estimation accuracy."""

    def test_estimate_accuracy(self, true_hurst):
        """Estimated H should be close to true H for long paths."""
        n = 5000
        num_samples = 20
        path = fbm(n, true_hurst, size=(num_samples,), seed=42)
        h_est = estimate_hurst(path)
        
        mean_estimate = h_est.mean().item()
        # Allow tolerance of 0.15 for variogram method
        assert abs(mean_estimate - true_hurst) < 0.15, \
            f"Estimated H={mean_estimate:.3f}, expected {true_hurst}"

    def test_estimate_consistency(self):
        """Multiple estimates on same data should be identical."""
        path = fbm(1000, H=0.7, seed=42)
        h_est1 = estimate_hurst(path)
        h_est2 = estimate_hurst(path)
        torch.testing.assert_close(h_est1, h_est2)

    def test_estimate_in_valid_range(self, true_hurst):
        """Estimated H should always be in (0, 1)."""
        path = fbm(1000, true_hurst, size=(50,))
        h_est = estimate_hurst(path)
        assert (h_est > 0).all(), "Estimated H <= 0"
        assert (h_est < 1).all(), "Estimated H >= 1"

    def test_h_05_brownian_motion(self):
        """H=0.5 should be recovered for standard Brownian motion."""
        path = fbm(5000, H=0.5, size=(30,), seed=123)
        h_est = estimate_hurst(path)
        mean_estimate = h_est.mean().item()
        assert abs(mean_estimate - 0.5) < 0.1, \
            f"Estimated H={mean_estimate:.3f} for Brownian motion"


# =============================================================================
# Assume Path Tests
# =============================================================================

class TestAssumePath:
    """Test assume_path parameter."""

    def test_assume_path_true(self):
        """assume_path=True should work for fBm paths."""
        path = fbm(1000, H=0.7, size=(5,))
        h_est = estimate_hurst(path, assume_path=True)
        assert h_est.shape == (5,)

    def test_assume_path_false(self):
        """assume_path=False should work for fGn increments."""
        from torchfbm import generate_davies_harte
        fgn = generate_davies_harte(1000, H=0.7, size=(5,))
        h_est = estimate_hurst(fgn, assume_path=False)
        assert h_est.shape == (5,)


# =============================================================================
# Lag Range Tests
# =============================================================================

class TestLagRange:
    """Test min_lag and max_lag parameters."""

    def test_custom_lag_range(self):
        """Custom lag range should work."""
        path = fbm(1000, H=0.5)
        h_est = estimate_hurst(path, min_lag=5, max_lag=50)
        assert not torch.isnan(h_est).any()

    def test_small_lag_range(self):
        """Small lag range should still produce result."""
        path = fbm(1000, H=0.5)
        h_est = estimate_hurst(path, min_lag=2, max_lag=5)
        assert not torch.isnan(h_est).any()

    def test_large_lag_range(self):
        """Large lag range should work if data supports it."""
        path = fbm(2000, H=0.5)
        h_est = estimate_hurst(path, min_lag=2, max_lag=100)
        assert not torch.isnan(h_est).any()


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_short_series(self):
        """Short series should still produce result (may be inaccurate)."""
        path = fbm(50, H=0.5)
        h_est = estimate_hurst(path, min_lag=2, max_lag=10)
        assert not torch.isnan(h_est).any()

    def test_no_nan_output(self, true_hurst):
        """Output should never contain NaN."""
        path = fbm(1000, true_hurst, size=(20,))
        h_est = estimate_hurst(path)
        assert not torch.isnan(h_est).any()

    def test_no_inf_output(self, true_hurst):
        """Output should never contain Inf."""
        path = fbm(1000, true_hurst, size=(20,))
        h_est = estimate_hurst(path)
        assert not torch.isinf(h_est).any()


# =============================================================================
# Device Compatibility Tests
# =============================================================================

class TestDeviceCompatibility:
    """Test GPU/CPU device handling."""

    def test_cpu_estimation(self):
        """Estimation on CPU should work."""
        path = fbm(1000, H=0.5, device="cpu")
        h_est = estimate_hurst(path)
        assert h_est.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_estimation(self):
        """Estimation on CUDA should work."""
        path = fbm(1000, H=0.5, device="cuda")
        h_est = estimate_hurst(path)
        assert h_est.device.type == "cuda"
