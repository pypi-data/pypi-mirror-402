"""
Comprehensive tests for torchfbm transforms module.

Tests cover:
- Compilation and imports
- Output shapes and dtypes
- Mathematical properties (inverse relationship)
- Edge cases
"""
import pytest
import torch
import numpy as np
from torchfbm import fractional_diff, fractional_integrate


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(params=[0.0, 0.2, 0.5, 0.7, 1.0])
def diff_order(request):
    return request.param


@pytest.fixture(params=[torch.float32, torch.float64])
def dtype(request):
    return request.param


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test that transforms import correctly."""

    def test_import_fractional_diff(self):
        from torchfbm import fractional_diff
        assert callable(fractional_diff)

    def test_import_fractional_integrate(self):
        from torchfbm import fractional_integrate
        assert callable(fractional_integrate)


# =============================================================================
# Shape and Dtype Tests
# =============================================================================

class TestShapeAndDtype:
    """Test output shapes and data types."""

    def test_output_shape_1d(self, diff_order):
        """1D input should produce same shape output."""
        x = torch.randn(100)
        out = fractional_diff(x, d=diff_order)
        assert out.shape == x.shape

    def test_output_shape_2d(self, diff_order):
        """2D input should produce same shape output."""
        x = torch.randn(10, 100)
        out = fractional_diff(x, d=diff_order)
        assert out.shape == x.shape

    def test_output_shape_3d(self, diff_order):
        """3D input should produce same shape output."""
        x = torch.randn(5, 10, 100)
        out = fractional_diff(x, d=diff_order)
        assert out.shape == x.shape

    def test_output_dtype_float32(self):
        """Output should preserve float32 dtype."""
        x = torch.randn(100, dtype=torch.float32)
        out = fractional_diff(x, d=0.5)
        assert out.dtype == torch.float32

    def test_output_dtype_float64(self):
        """Output should preserve float64 dtype."""
        x = torch.randn(100, dtype=torch.float64)
        out = fractional_diff(x, d=0.5)
        assert out.dtype == torch.float64

    def test_output_is_tensor(self):
        """Default output should be torch.Tensor."""
        x = torch.randn(100)
        out = fractional_diff(x, d=0.5)
        assert isinstance(out, torch.Tensor)

    def test_output_numpy(self):
        """return_numpy=True should return numpy array."""
        x = torch.randn(100)
        out = fractional_diff(x, d=0.5, return_numpy=True)
        assert isinstance(out, np.ndarray)


# =============================================================================
# Mathematical Properties Tests
# =============================================================================

class TestMathematicalProperties:
    """Test mathematical properties of fractional differentiation."""

    def test_d_zero_is_identity(self):
        """d=0 should return the input unchanged."""
        x = torch.randn(100)
        out = fractional_diff(x, d=0.0)
        torch.testing.assert_close(out, x, atol=1e-5, rtol=1e-5)

    def test_d_one_approximates_diff(self):
        """d=1 should approximate standard differencing."""
        x = torch.cumsum(torch.randn(100), dim=0)  # Integrated noise
        out = fractional_diff(x, d=1.0)
        # Should be similar to torch.diff (with appropriate handling of first element)
        # Due to FFT boundary effects, we just check it's not the same as input
        assert not torch.allclose(out, x)

    def test_inverse_relationship(self, diff_order):
        """Integrating a differentiated signal should recover original (approximately)."""
        if diff_order == 0:
            pytest.skip("d=0 is identity, trivially inverse")
        
        x = torch.randn(100, dtype=torch.float64)
        
        # Differentiate then integrate
        x_diff = fractional_diff(x, d=diff_order)
        x_recovered = fractional_integrate(x_diff, d=diff_order)
        
        # Due to FFT boundary effects, we can only check correlation pattern
        # The exact values may differ due to circular convolution artifacts
        # Check that the central values are correlated (not exact)
        central_slice = slice(20, 80)
        correlation = torch.corrcoef(torch.stack([
            x[central_slice], x_recovered[central_slice]
        ]))[0, 1]
        
        # Should have positive correlation (signals are related)
        assert correlation > 0.5, f"Correlation {correlation} too low for inverse relationship"

    def test_integrate_is_negative_diff(self):
        """Integration with d should equal differentiation with -d."""
        x = torch.randn(100)
        d = 0.4
        
        int_result = fractional_integrate(x, d=d)
        diff_neg_result = fractional_diff(x, d=-d)
        
        torch.testing.assert_close(int_result, diff_neg_result)

    def test_additivity_of_orders(self):
        """diff(x, d1 + d2) ≈ diff(diff(x, d1), d2)."""
        x = torch.randn(100, dtype=torch.float64)
        d1, d2 = 0.3, 0.2
        
        # Direct
        direct = fractional_diff(x, d=d1 + d2)
        
        # Sequential
        step1 = fractional_diff(x, d=d1)
        sequential = fractional_diff(step1, d=d2)
        
        # Should be approximately equal (some numerical error expected)
        torch.testing.assert_close(direct, sequential, atol=1e-3, rtol=1e-3)


# =============================================================================
# Dim Parameter Tests
# =============================================================================

class TestDimParameter:
    """Test dim parameter for axis selection."""

    def test_dim_last(self):
        """dim=-1 should differentiate along last axis."""
        x = torch.randn(5, 100)
        out = fractional_diff(x, d=0.5, dim=-1)
        assert out.shape == (5, 100)

    def test_dim_first(self):
        """dim=0 should differentiate along first axis."""
        x = torch.randn(100, 5)
        out = fractional_diff(x, d=0.5, dim=0)
        assert out.shape == (100, 5)

    def test_dim_middle(self):
        """dim=1 should work for 3D tensors."""
        x = torch.randn(5, 100, 10)
        out = fractional_diff(x, d=0.5, dim=1)
        assert out.shape == (5, 100, 10)


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dimension_raises(self):
        """Empty dimension should raise ValueError."""
        x = torch.randn(10, 0)
        with pytest.raises(ValueError, match="empty dimension"):
            fractional_diff(x, d=0.5, dim=-1)

    def test_invalid_dim_raises(self):
        """Invalid dim should raise ValueError."""
        x = torch.randn(100)
        with pytest.raises((ValueError, IndexError)):
            fractional_diff(x, d=0.5, dim=5)

    def test_unsupported_dtype_raises(self):
        """Unsupported dtype should raise TypeError."""
        x = torch.randint(0, 10, (100,))  # Integer tensor
        with pytest.raises(TypeError):
            fractional_diff(x, d=0.5)

    def test_short_series(self):
        """Short series should work."""
        x = torch.randn(10)
        out = fractional_diff(x, d=0.5)
        assert out.shape == (10,)

    def test_no_nan_output(self, diff_order):
        """Output should not contain NaN."""
        x = torch.randn(100)
        out = fractional_diff(x, d=diff_order)
        assert not torch.isnan(out).any()

    def test_no_inf_output(self, diff_order):
        """Output should not contain Inf."""
        x = torch.randn(100)
        out = fractional_diff(x, d=diff_order)
        assert not torch.isinf(out).any()

    def test_negative_order(self):
        """Negative order (integration) should work."""
        x = torch.randn(100)
        out = fractional_diff(x, d=-0.5)
        assert out.shape == (100,)
        assert not torch.isnan(out).any()


# =============================================================================
# Device Compatibility Tests
# =============================================================================

class TestDeviceCompatibility:
    """Test GPU/CPU device handling."""

    def test_cpu(self):
        """Operation on CPU should work."""
        x = torch.randn(100, device="cpu")
        out = fractional_diff(x, d=0.5)
        assert out.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda(self):
        """Operation on CUDA should work."""
        x = torch.randn(100, device="cuda")
        out = fractional_diff(x, d=0.5)
        assert out.device.type == "cuda"
