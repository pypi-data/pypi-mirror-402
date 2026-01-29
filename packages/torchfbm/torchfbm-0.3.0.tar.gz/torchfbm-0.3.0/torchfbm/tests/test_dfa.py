"""
Comprehensive tests for torchfbm DFA (Detrended Fluctuation Analysis) module.

Tests cover:
- Compilation and imports
- Output shapes and dtypes
- Mathematical properties (scaling exponent accuracy)
- Edge cases
"""
import pytest
import torch
import numpy as np
from torchfbm import fbm, dfa


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(params=[0.3, 0.5, 0.7])
def hurst_param(request):
    return request.param


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test that DFA imports correctly."""

    def test_import_dfa(self):
        from torchfbm import dfa
        assert callable(dfa)


# =============================================================================
# Shape and Dtype Tests
# =============================================================================

class TestShapeAndDtype:
    """Test output shapes and data types."""

    def test_output_shape_1d_input(self):
        """1D input should return scalar."""
        x = torch.randn(1000)
        alpha = dfa(x)
        assert alpha.shape == (1,)

    def test_output_shape_2d_input(self):
        """2D input (Batch, Time) should return (Batch,)."""
        x = torch.randn(10, 1000)
        alpha = dfa(x)
        assert alpha.shape == (10,)

    def test_output_is_tensor(self):
        """Default output should be torch.Tensor."""
        x = torch.randn(1000)
        alpha = dfa(x)
        assert isinstance(alpha, torch.Tensor)

    def test_return_fluctuations(self):
        """return_alpha=False should return (F, scales)."""
        x = torch.randn(1000)
        F, scales = dfa(x, return_alpha=False)
        assert isinstance(F, torch.Tensor)
        assert isinstance(scales, np.ndarray)


# =============================================================================
# Mathematical Properties Tests
# =============================================================================

class TestMathematicalProperties:
    """Test mathematical properties of DFA."""

    def test_alpha_estimate_accuracy(self, hurst_param):
        """DFA alpha should approximate H for long fBm paths."""
        n = 5000
        num_samples = 10
        path = fbm(n, hurst_param, size=(num_samples,), seed=42)
        
        # DFA on fBm increments (fGn)
        increments = path[:, 1:] - path[:, :-1]
        alpha = dfa(increments)
        
        # For fGn, alpha ≈ H
        mean_alpha = alpha.mean().item()
        assert abs(mean_alpha - hurst_param) < 0.2, \
            f"DFA alpha={mean_alpha:.3f}, expected ~{hurst_param}"

    def test_alpha_in_reasonable_range(self, hurst_param):
        """Alpha should be in a reasonable range (0, 2)."""
        path = fbm(2000, hurst_param, size=(10,))
        increments = path[:, 1:] - path[:, :-1]
        alpha = dfa(increments)
        
        assert (alpha > 0).all(), "Alpha <= 0"
        assert (alpha < 2).all(), "Alpha >= 2"

    def test_fluctuation_increases_with_scale(self):
        """F(s) should generally increase with scale for fBm."""
        path = fbm(2000, H=0.7)
        increments = path[:, 1:] - path[:, :-1]
        F, scales = dfa(increments, return_alpha=False)
        
        # F should be monotonically increasing (approximately)
        F_np = F.squeeze().numpy()
        # Allow some non-monotonicity due to noise
        increases = np.sum(np.diff(F_np) > 0)
        assert increases > len(F_np) * 0.7, "F(s) not increasing with scale"


# =============================================================================
# Parameter Tests
# =============================================================================

class TestParameters:
    """Test DFA parameters."""

    def test_custom_scales(self):
        """Custom scales should work."""
        x = torch.randn(1000)
        scales = [10, 20, 50, 100, 200]
        alpha = dfa(x, scales=scales)
        assert not torch.isnan(alpha).any()

    def test_order_1(self):
        """order=1 (DFA1) should work."""
        x = torch.randn(1000)
        alpha = dfa(x, order=1)
        assert not torch.isnan(alpha).any()

    def test_order_2(self):
        """order=2 (DFA2) should work."""
        x = torch.randn(1000)
        alpha = dfa(x, order=2)
        assert not torch.isnan(alpha).any()

    def test_order_3(self):
        """order=3 (DFA3) should work."""
        x = torch.randn(2000)
        alpha = dfa(x, order=3)
        assert not torch.isnan(alpha).any()


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases."""

    def test_short_series(self):
        """Short series should still work (with fewer scales)."""
        x = torch.randn(100)
        alpha = dfa(x)
        assert not torch.isnan(alpha).any()

    def test_very_short_series(self):
        """Very short series should not crash."""
        x = torch.randn(50)
        alpha = dfa(x)
        # May be inaccurate but should not crash
        assert alpha.shape == (1,)

    def test_no_nan_output(self, hurst_param):
        """Output should never contain NaN."""
        path = fbm(1000, hurst_param, size=(10,))
        increments = path[:, 1:] - path[:, :-1]
        alpha = dfa(increments)
        assert not torch.isnan(alpha).any()

    def test_no_inf_output(self, hurst_param):
        """Output should never contain Inf."""
        path = fbm(1000, hurst_param, size=(10,))
        increments = path[:, 1:] - path[:, :-1]
        alpha = dfa(increments)
        assert not torch.isinf(alpha).any()


# =============================================================================
# Device Compatibility Tests
# =============================================================================

class TestDeviceCompatibility:
    """Test GPU/CPU device handling."""

    def test_cpu(self):
        """DFA on CPU should work."""
        x = torch.randn(1000, device="cpu")
        alpha = dfa(x)
        assert alpha.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda(self):
        """DFA on CUDA should work."""
        x = torch.randn(1000, device="cuda")
        alpha = dfa(x)
        assert alpha.device.type == "cuda"
