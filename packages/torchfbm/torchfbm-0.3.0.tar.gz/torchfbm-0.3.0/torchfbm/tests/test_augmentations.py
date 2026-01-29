"""
Comprehensive tests for torchfbm augmentations module.

Tests cover:
- FractionalNoiseAugmentation class
- Data shape preservation
- Training/eval mode behavior
- Parameter validation
"""
import pytest
import torch
import numpy as np
from torchfbm import FractionalNoiseAugmentation


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test that augmentation components import correctly."""

    def test_import_fractional_noise_augmentation(self):
        from torchfbm import FractionalNoiseAugmentation
        assert FractionalNoiseAugmentation is not None


# =============================================================================
# Initialization Tests
# =============================================================================

class TestInitialization:
    """Test FractionalNoiseAugmentation initialization."""

    def test_basic_init(self):
        """Basic initialization should work."""
        aug = FractionalNoiseAugmentation()
        assert aug is not None

    def test_init_with_hurst(self):
        """Initialization with custom Hurst should work."""
        aug = FractionalNoiseAugmentation(H=0.7)
        assert aug.H == 0.7

    def test_init_with_sigma(self):
        """Initialization with custom sigma should work."""
        aug = FractionalNoiseAugmentation(sigma=0.05)
        assert aug.sigma == 0.05

    def test_init_with_probability(self):
        """Initialization with custom probability should work."""
        aug = FractionalNoiseAugmentation(p=0.8)
        assert aug.p == 0.8

    @pytest.mark.parametrize("hurst", [0.1, 0.3, 0.5, 0.7, 0.9])
    def test_valid_hurst_values(self, hurst):
        """Various Hurst values should initialize successfully."""
        aug = FractionalNoiseAugmentation(H=hurst)
        assert aug.H == hurst

    def test_is_module(self):
        """FractionalNoiseAugmentation should be an nn.Module."""
        aug = FractionalNoiseAugmentation()
        assert isinstance(aug, torch.nn.Module)


# =============================================================================
# Forward Pass Tests
# =============================================================================

class TestForwardPass:
    """Test forward pass functionality."""

    def test_output_shape_preserved(self):
        """Output shape should match input shape."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(10, 100)
        out = aug(x)
        assert out.shape == x.shape

    def test_output_dtype_preserved(self):
        """Output dtype should match input dtype."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(100, dtype=torch.float64)
        out = aug(x)
        assert out.dtype == torch.float64

    def test_output_is_tensor(self):
        """Output should be a tensor."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        assert isinstance(out, torch.Tensor)

    def test_training_mode_applies_noise(self):
        """Training mode with p=1 should always modify input."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.5, p=1.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        # With sigma=0.5 and p=1.0, output should differ
        assert not torch.allclose(out, x)

    def test_eval_mode_no_noise(self):
        """Eval mode should return input unchanged."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.5, p=1.0)
        aug.eval()
        x = torch.randn(100)
        out = aug(x)
        torch.testing.assert_close(out, x)

    def test_zero_probability_no_change(self):
        """p=0 should never apply augmentation."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.5, p=0.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        torch.testing.assert_close(out, x)

    def test_zero_sigma_no_visible_change(self):
        """sigma=0 should produce no visible change."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.0, p=1.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        torch.testing.assert_close(out, x)


# =============================================================================
# Statistical Properties Tests
# =============================================================================

class TestStatisticalProperties:
    """Test statistical properties of augmentation."""

    def test_probability_applied_roughly_correct(self):
        """Augmentation should be applied roughly p fraction of the time."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=1.0, p=0.5)
        aug.train()
        x = torch.randn(100)
        
        n_different = 0
        n_trials = 100
        for _ in range(n_trials):
            out = aug(x)
            if not torch.allclose(out, x):
                n_different += 1
        
        # Should be roughly 50% with some variance
        ratio = n_different / n_trials
        assert 0.3 < ratio < 0.7  # Generous tolerance

    def test_noise_scale_proportional_to_sigma(self):
        """Larger sigma should produce larger differences from input."""
        x = torch.randn(1000)
        
        aug_small = FractionalNoiseAugmentation(H=0.7, sigma=0.01, p=1.0)
        aug_large = FractionalNoiseAugmentation(H=0.7, sigma=1.0, p=1.0)
        aug_small.train()
        aug_large.train()
        
        torch.manual_seed(42)
        diff_small = (aug_small(x) - x).abs().mean().item()
        
        torch.manual_seed(42)
        diff_large = (aug_large(x) - x).abs().mean().item()
        
        assert diff_large > diff_small


# =============================================================================
# Batch Processing Tests
# =============================================================================

class TestBatchProcessing:
    """Test batch processing capabilities."""

    def test_1d_input(self):
        """1D input should work."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        assert out.shape == (100,)

    def test_2d_batch(self):
        """2D batch should work."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(32, 100)
        out = aug(x)
        assert out.shape == (32, 100)

    def test_3d_batch(self):
        """3D batch should work."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(8, 4, 100)
        out = aug(x)
        assert out.shape == (8, 4, 100)


# =============================================================================
# Device Compatibility Tests
# =============================================================================

class TestDeviceCompatibility:
    """Test GPU/CPU device handling."""

    def test_cpu(self):
        """Operations on CPU should work."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(100, device="cpu")
        out = aug(x)
        assert out.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda(self):
        """Operations on CUDA should work."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(100, device="cuda")
        out = aug(x)
        assert out.device.type == "cuda"


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_short_sequence(self):
        """Short sequences should work."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(10)
        out = aug(x)
        assert out.shape == (10,)

    def test_extreme_hurst_low(self):
        """Very low Hurst should work."""
        aug = FractionalNoiseAugmentation(H=0.05, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        assert not torch.isnan(out).any()

    def test_extreme_hurst_high(self):
        """Very high Hurst should work."""
        aug = FractionalNoiseAugmentation(H=0.95, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        assert not torch.isnan(out).any()

    def test_no_nan_output(self):
        """Output should not contain NaN."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.5, p=1.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        assert not torch.isnan(out).any()

    def test_no_inf_output(self):
        """Output should not contain Inf."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.5, p=1.0)
        aug.train()
        x = torch.randn(100)
        out = aug(x)
        assert not torch.isinf(out).any()


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Test integration in neural network pipelines."""

    def test_in_sequential(self):
        """Should work in nn.Sequential."""
        model = torch.nn.Sequential(
            FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0),
            torch.nn.Linear(100, 50),
            torch.nn.ReLU(),
        )
        model.train()
        x = torch.randn(8, 100)
        out = model(x)
        assert out.shape == (8, 50)

    def test_gradient_flow(self):
        """Gradients should flow through the augmentation."""
        aug = FractionalNoiseAugmentation(H=0.7, sigma=0.1, p=1.0)
        aug.train()
        x = torch.randn(10, 100, requires_grad=True)
        out = aug(x)
        loss = out.sum()
        loss.backward()
        # Input gradient should exist
        assert x.grad is not None
