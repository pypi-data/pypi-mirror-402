"""
Comprehensive tests for torchfbm online module.

Tests cover:
- CachedFGNGenerator functionality
- Incremental generation correctness
- Cholesky update behavior
- Reproducibility with seeds
"""
import pytest
import torch
import numpy as np
from torchfbm import CachedFGNGenerator


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test that online components import correctly."""

    def test_import_cached_generator(self):
        from torchfbm import CachedFGNGenerator
        assert CachedFGNGenerator is not None


# =============================================================================
# Initialization Tests
# =============================================================================

class TestInitialization:
    """Test CachedFGNGenerator initialization."""

    def test_basic_init(self):
        """Basic initialization should work."""
        gen = CachedFGNGenerator(H=0.7)
        assert gen is not None

    @pytest.mark.parametrize("hurst", [0.1, 0.3, 0.5, 0.7, 0.9])
    def test_valid_hurst_range(self, hurst):
        """Valid Hurst values should initialize successfully."""
        gen = CachedFGNGenerator(H=hurst)
        assert gen is not None

    def test_with_device(self):
        """Initialization with device should work."""
        gen = CachedFGNGenerator(H=0.7, device="cpu")
        assert gen.device.type == "cpu"

    def test_with_dtype(self):
        """Initialization with dtype should work."""
        gen = CachedFGNGenerator(H=0.7, dtype=torch.float64)
        assert gen.dtype == torch.float64


# =============================================================================
# Generation Tests
# =============================================================================

class TestGeneration:
    """Test incremental noise generation."""

    def test_step_returns_tensor(self):
        """step() should return a tensor."""
        gen = CachedFGNGenerator(H=0.7)
        sample = gen.step()
        assert isinstance(sample, torch.Tensor)

    def test_step_returns_single_value(self):
        """step() should return a single value."""
        gen = CachedFGNGenerator(H=0.7)
        sample = gen.step()
        # Should be a single value
        assert sample.numel() == 1

    def test_multiple_steps(self):
        """Multiple step() calls should work."""
        gen = CachedFGNGenerator(H=0.7)
        samples = []
        for _ in range(50):
            samples.append(gen.step())
        assert len(samples) == 50

    def test_increments_n(self):
        """Each step should increment the internal counter n."""
        gen = CachedFGNGenerator(H=0.7)
        assert gen.n == 0
        gen.step()
        assert gen.n == 1
        gen.step()
        assert gen.n == 2

    def test_output_finite(self):
        """Output should be finite (no NaN/Inf)."""
        gen = CachedFGNGenerator(H=0.7)
        for _ in range(100):
            sample = gen.step()
            assert not torch.isnan(sample).any()
            assert not torch.isinf(sample).any()


# =============================================================================
# Reproducibility Tests
# =============================================================================

class TestReproducibility:
    """Test seeded reproducibility."""

    def test_seed_reproducibility(self):
        """Same seed should produce same sequence."""
        torch.manual_seed(42)
        gen1 = CachedFGNGenerator(H=0.7)
        samples1 = [gen1.step().item() for _ in range(20)]
        
        torch.manual_seed(42)
        gen2 = CachedFGNGenerator(H=0.7)
        samples2 = [gen2.step().item() for _ in range(20)]
        
        assert samples1 == samples2

    def test_different_seeds_differ(self):
        """Different seeds should produce different sequences."""
        torch.manual_seed(42)
        gen1 = CachedFGNGenerator(H=0.7)
        samples1 = [gen1.step().item() for _ in range(20)]
        
        torch.manual_seed(99)
        gen2 = CachedFGNGenerator(H=0.7)
        samples2 = [gen2.step().item() for _ in range(20)]
        
        assert samples1 != samples2


# =============================================================================
# Statistical Properties Tests
# =============================================================================

class TestStatisticalProperties:
    """Test statistical properties of generated noise."""

    def test_zero_mean_approx(self):
        """Generated noise should have approximately zero mean."""
        gen = CachedFGNGenerator(H=0.7)
        samples = torch.tensor([gen.step().item() for _ in range(500)])
        mean = samples.mean().item()
        assert abs(mean) < 0.2  # Generous tolerance for finite samples


# =============================================================================
# Cholesky Factor Tests
# =============================================================================

class TestCholeskyFactor:
    """Test Cholesky factor properties."""

    def test_l_matrix_grows(self):
        """Cholesky factor L should grow with each step."""
        gen = CachedFGNGenerator(H=0.7)
        assert gen.L.shape == (0, 0)
        gen.step()
        assert gen.L.shape == (1, 1)
        gen.step()
        assert gen.L.shape == (2, 2)
        gen.step()
        assert gen.L.shape == (3, 3)

    def test_l_is_lower_triangular(self):
        """L should be lower triangular."""
        gen = CachedFGNGenerator(H=0.7)
        for _ in range(10):
            gen.step()
        
        L = gen.L
        # Check upper triangle is zero
        upper = torch.triu(L, diagonal=1)
        assert torch.allclose(upper, torch.zeros_like(upper))

    def test_l_positive_diagonal(self):
        """L should have positive diagonal (well-conditioned)."""
        gen = CachedFGNGenerator(H=0.7)
        for _ in range(10):
            gen.step()
        
        diagonal = torch.diag(gen.L)
        assert (diagonal > 0).all()


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extreme_hurst_low(self):
        """Low Hurst value should work."""
        gen = CachedFGNGenerator(H=0.1)
        for _ in range(20):
            sample = gen.step()
            assert not torch.isnan(sample).any()

    def test_extreme_hurst_high(self):
        """High Hurst value should work."""
        gen = CachedFGNGenerator(H=0.9)
        for _ in range(20):
            sample = gen.step()
            assert not torch.isnan(sample).any()

    def test_single_step(self):
        """Single step should work."""
        gen = CachedFGNGenerator(H=0.7)
        sample = gen.step()
        assert sample.numel() == 1


# =============================================================================
# Device Tests
# =============================================================================

class TestDeviceHandling:
    """Test device handling."""

    def test_cpu_device(self):
        """Generator on CPU should work."""
        gen = CachedFGNGenerator(H=0.7, device="cpu")
        sample = gen.step()
        assert sample.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_device(self):
        """Generator on CUDA should work."""
        gen = CachedFGNGenerator(H=0.7, device="cuda")
        sample = gen.step()
        assert sample.device.type == "cuda"


# =============================================================================
# Dtype Tests
# =============================================================================

class TestDtypeHandling:
    """Test dtype handling."""

    def test_float32_dtype(self):
        """float32 should work."""
        gen = CachedFGNGenerator(H=0.7, dtype=torch.float32)
        sample = gen.step()
        assert sample.dtype == torch.float32

    def test_float64_dtype(self):
        """float64 should work."""
        gen = CachedFGNGenerator(H=0.7, dtype=torch.float64)
        sample = gen.step()
        assert sample.dtype == torch.float64
