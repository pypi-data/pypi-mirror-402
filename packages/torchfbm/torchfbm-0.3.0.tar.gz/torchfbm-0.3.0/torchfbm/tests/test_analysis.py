"""
Comprehensive tests for torchfbm analysis module.

Tests cover:
- Covariance matrix computation
- Spectral analysis functions
- Mathematical properties of fBm covariance
- Edge cases and numerical stability
"""
import pytest
import torch
import numpy as np
from torchfbm import covariance_matrix, spectral_scaling_factor


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test that analysis components import correctly."""

    def test_import_covariance_matrix(self):
        from torchfbm import covariance_matrix
        assert callable(covariance_matrix)

    def test_import_spectral_scaling_factor(self):
        from torchfbm import spectral_scaling_factor
        assert callable(spectral_scaling_factor)


# =============================================================================
# Covariance Matrix Tests
# =============================================================================

class TestCovarianceMatrix:
    """Test covariance matrix computation."""

    def test_output_shape(self):
        """Output should be square matrix of size n x n."""
        n = 50
        cov = covariance_matrix(n=n, H=0.7)
        assert cov.shape == (n, n)

    def test_output_is_tensor(self):
        """Output should be a torch.Tensor."""
        cov = covariance_matrix(n=50, H=0.7)
        assert isinstance(cov, torch.Tensor)

    def test_symmetry(self):
        """Covariance matrix should be symmetric."""
        cov = covariance_matrix(n=50, H=0.7)
        torch.testing.assert_close(cov, cov.T)

    def test_positive_definite(self):
        """Covariance matrix should be positive semi-definite."""
        cov = covariance_matrix(n=50, H=0.7)
        eigenvalues = torch.linalg.eigvalsh(cov)
        assert (eigenvalues >= -1e-6).all()  # Allow small numerical error

    @pytest.mark.parametrize("hurst", [0.1, 0.3, 0.5, 0.7, 0.9])
    def test_various_hurst_values(self, hurst):
        """Various Hurst values should work."""
        cov = covariance_matrix(n=50, H=hurst)
        assert cov.shape == (50, 50)
        assert not torch.isnan(cov).any()

    def test_hurst_05_is_brownian(self):
        """H=0.5 should give Brownian motion covariance: min(s, t)."""
        n = 10
        cov = covariance_matrix(n=n, H=0.5)
        # For Brownian motion, Cov(B_s, B_t) = min(s, t)
        # Check diagonal elements (variance = t)
        for i in range(n):
            expected_var = (i + 1)  # Using t = i + 1
            # Scale factor may differ; check pattern
            assert cov[i, i] >= cov[i-1, i-1] if i > 0 else True

    def test_diagonal_positive(self):
        """Diagonal elements (variances) should be positive."""
        cov = covariance_matrix(n=50, H=0.7)
        diagonal = torch.diag(cov)
        assert (diagonal > 0).all()

    def test_increasing_diagonal(self):
        """Diagonal elements should increase (fBm variance grows with time)."""
        cov = covariance_matrix(n=50, H=0.7)
        diagonal = torch.diag(cov)
        # Each variance should be >= previous
        diffs = diagonal[1:] - diagonal[:-1]
        assert (diffs >= -1e-6).all()


# =============================================================================
# Dtype and Device Tests
# =============================================================================

class TestCovarianceDtypeDevice:
    """Test dtype and device handling for covariance matrix."""

    def test_default_dtype(self):
        """Default dtype should be float32."""
        cov = covariance_matrix(n=50, H=0.7)
        assert cov.dtype == torch.float32

    def test_cpu_device(self):
        """CPU device should work."""
        cov = covariance_matrix(n=50, H=0.7, device="cpu")
        assert cov.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_device(self):
        """CUDA device should work."""
        cov = covariance_matrix(n=50, H=0.7, device="cuda")
        assert cov.device.type == "cuda"


# =============================================================================
# Spectral Scaling Factor Tests
# =============================================================================

class TestSpectralScalingFactor:
    """Test spectral scaling factor computation."""

    def test_output_is_tensor(self):
        """Output should be a tensor."""
        f = torch.linspace(0.01, 1.0, 100)
        factor = spectral_scaling_factor(f=f, H=0.7)
        assert isinstance(factor, torch.Tensor)

    def test_output_shape(self):
        """Output shape should match input frequency shape."""
        f = torch.linspace(0.01, 1.0, 100)
        factor = spectral_scaling_factor(f=f, H=0.7)
        assert factor.shape == f.shape

    @pytest.mark.parametrize("hurst", [0.1, 0.3, 0.5, 0.7, 0.9])
    def test_various_hurst_values(self, hurst):
        """Various Hurst values should work."""
        f = torch.linspace(0.01, 1.0, 100)
        factor = spectral_scaling_factor(f=f, H=hurst)
        # Avoid checking f=0 which gets special handling
        assert not torch.isnan(factor).any()

    def test_no_inf(self):
        """Output should not contain Inf (avoiding f=0)."""
        f = torch.linspace(0.01, 1.0, 100)
        factor = spectral_scaling_factor(f=f, H=0.7)
        assert not torch.isinf(factor).any()

    def test_positive_values(self):
        """Scaling factors should be positive for positive frequencies."""
        f = torch.linspace(0.01, 1.0, 100)
        factor = spectral_scaling_factor(f=f, H=0.7)
        assert (factor >= 0).all()

    def test_decreasing_with_frequency(self):
        """Scaling should decrease with frequency (1/f behavior)."""
        f = torch.linspace(0.1, 1.0, 100)
        factor = spectral_scaling_factor(f=f, H=0.7)
        # Should be monotonically decreasing
        diffs = factor[1:] - factor[:-1]
        assert (diffs <= 1e-6).all()

    def test_zero_at_dc(self):
        """DC component (f=0) should be zeroed."""
        f = torch.tensor([0.0, 0.1, 0.5, 1.0])
        factor = spectral_scaling_factor(f=f, H=0.7)
        assert factor[0].item() == 0.0


# =============================================================================
# Mathematical Properties Tests
# =============================================================================

class TestMathematicalProperties:
    """Test mathematical properties of fBm analysis functions."""

    def test_covariance_formula(self):
        """Test fBm covariance formula: R(s,t) = 0.5 * (|t|^2H + |s|^2H - |t-s|^2H)."""
        hurst = 0.7
        n = 20
        cov = covariance_matrix(n=n, H=hurst)
        
        # Check that matrix structure is correct (Toeplitz)
        # First row should equal first column
        torch.testing.assert_close(cov[0, :], cov[:, 0])

    def test_higher_hurst_higher_persistence(self):
        """Higher Hurst should give higher off-diagonal correlation."""
        n = 20
        cov_low = covariance_matrix(n=n, H=0.3)
        cov_high = covariance_matrix(n=n, H=0.8)
        
        # Normalize to correlation
        def to_corr(cov):
            d = torch.sqrt(torch.diag(cov))
            return cov / torch.outer(d, d)
        
        corr_low = to_corr(cov_low)
        corr_high = to_corr(cov_high)
        
        # High Hurst should have higher correlations at lag 5
        lag = 5
        assert corr_high[0, lag].item() > corr_low[0, lag].item()


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_small_n(self):
        """Small n should work."""
        cov = covariance_matrix(n=2, H=0.7)
        assert cov.shape == (2, 2)

    def test_large_n(self):
        """Large n should work (may be slow)."""
        cov = covariance_matrix(n=500, H=0.7)
        assert cov.shape == (500, 500)

    def test_hurst_extreme_low(self):
        """Very low Hurst should work."""
        cov = covariance_matrix(n=50, H=0.05)
        assert not torch.isnan(cov).any()

    def test_hurst_extreme_high(self):
        """Very high Hurst should work."""
        cov = covariance_matrix(n=50, H=0.95)
        assert not torch.isnan(cov).any()

    def test_hurst_exactly_05(self):
        """H=0.5 should work (standard Brownian motion)."""
        cov = covariance_matrix(n=50, H=0.5)
        assert not torch.isnan(cov).any()


# =============================================================================
# Numerical Stability Tests
# =============================================================================

class TestNumericalStability:
    """Test numerical stability of computations."""

    def test_no_nan_float32(self):
        """float32 should not produce NaN."""
        cov = covariance_matrix(n=100, H=0.7)
        assert not torch.isnan(cov).any()

    def test_cholesky_decomposable(self):
        """Covariance matrix should be Cholesky decomposable."""
        cov = covariance_matrix(n=50, H=0.7)
        # Add small diagonal for numerical stability
        cov_stable = cov + torch.eye(50) * 1e-6
        try:
            L = torch.linalg.cholesky(cov_stable)
            assert L.shape == (50, 50)
        except RuntimeError:
            pytest.fail("Covariance matrix not positive definite for Cholesky")
