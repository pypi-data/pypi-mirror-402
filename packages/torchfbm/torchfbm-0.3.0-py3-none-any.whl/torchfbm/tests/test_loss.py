"""
Comprehensive tests for torchfbm loss functions module.

Tests cover:
- Compilation and imports
- Forward pass shapes
- Gradient flow
- Mathematical properties
"""
import pytest
import torch
import torch.nn as nn
from torchfbm import HurstRegularizationLoss, SpectralConsistencyLoss, fbm


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(params=[0.3, 0.5, 0.7])
def target_hurst(request):
    return request.param


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test that loss functions import correctly."""

    def test_import_hurst_loss(self):
        from torchfbm import HurstRegularizationLoss
        assert HurstRegularizationLoss is not None

    def test_import_spectral_loss(self):
        from torchfbm import SpectralConsistencyLoss
        assert SpectralConsistencyLoss is not None


# =============================================================================
# HurstRegularizationLoss Tests
# =============================================================================

class TestHurstRegularizationLoss:
    """Test HurstRegularizationLoss."""

    def test_construction(self, target_hurst):
        """Loss should construct without error."""
        loss_fn = HurstRegularizationLoss(target_H=target_hurst)
        assert loss_fn is not None
        assert loss_fn.target_H == target_hurst

    def test_forward_returns_scalar(self):
        """Forward should return a scalar tensor."""
        loss_fn = HurstRegularizationLoss(target_H=0.5)
        x = fbm(500, H=0.5, size=(10,))
        loss = loss_fn(x)
        assert loss.dim() == 0  # Scalar

    def test_loss_is_non_negative(self, target_hurst):
        """Loss should be non-negative."""
        loss_fn = HurstRegularizationLoss(target_H=target_hurst)
        x = fbm(500, H=0.5, size=(10,))
        loss = loss_fn(x)
        assert loss.item() >= 0

    def test_loss_zero_at_target(self, target_hurst):
        """Loss should be small when H matches target."""
        loss_fn = HurstRegularizationLoss(target_H=target_hurst)
        x = fbm(2000, H=target_hurst, size=(20,))
        loss = loss_fn(x)
        # Due to estimation noise, won't be exactly zero
        assert loss.item() < 0.1

    def test_loss_increases_with_mismatch(self):
        """Loss should increase when H differs from target."""
        loss_fn = HurstRegularizationLoss(target_H=0.5)
        
        x_match = fbm(2000, H=0.5, size=(20,))
        x_mismatch = fbm(2000, H=0.8, size=(20,))
        
        loss_match = loss_fn(x_match)
        loss_mismatch = loss_fn(x_mismatch)
        
        assert loss_mismatch.item() > loss_match.item()

    def test_gradient_flow(self):
        """Gradients should flow through the loss."""
        loss_fn = HurstRegularizationLoss(target_H=0.5)
        x = torch.randn(10, 500, requires_grad=True)
        loss = loss_fn(x)
        loss.backward()
        assert x.grad is not None

    def test_is_nn_module(self):
        """Should be an nn.Module."""
        loss_fn = HurstRegularizationLoss(target_H=0.5)
        assert isinstance(loss_fn, nn.Module)


# =============================================================================
# SpectralConsistencyLoss Tests
# =============================================================================

class TestSpectralConsistencyLoss:
    """Test SpectralConsistencyLoss."""

    def test_construction(self):
        """Loss should construct without error."""
        loss_fn = SpectralConsistencyLoss(target_beta=2.0)
        assert loss_fn is not None
        assert loss_fn.target_beta == 2.0

    def test_forward_returns_scalar(self):
        """Forward should return a scalar tensor."""
        loss_fn = SpectralConsistencyLoss(target_beta=2.0)
        x = torch.randn(10, 500)
        loss = loss_fn(x)
        assert loss.dim() == 0  # Scalar

    def test_loss_is_non_negative(self):
        """Loss should be non-negative."""
        loss_fn = SpectralConsistencyLoss(target_beta=2.0)
        x = torch.randn(10, 500)
        loss = loss_fn(x)
        assert loss.item() >= 0

    def test_gradient_flow(self):
        """Gradients should flow through the loss."""
        loss_fn = SpectralConsistencyLoss(target_beta=2.0)
        x = torch.randn(10, 500, requires_grad=True)
        loss = loss_fn(x)
        loss.backward()
        assert x.grad is not None

    def test_is_nn_module(self):
        """Should be an nn.Module."""
        loss_fn = SpectralConsistencyLoss(target_beta=2.0)
        assert isinstance(loss_fn, nn.Module)

    def test_beta_relationship_to_hurst(self):
        """beta = 2H + 1 for fBm."""
        # For H=0.5, beta should be 2.0
        H = 0.7
        target_beta = 2 * H + 1  # = 2.4
        loss_fn = SpectralConsistencyLoss(target_beta=target_beta)
        
        x = fbm(2000, H=H, size=(20,))
        increments = x[:, 1:] - x[:, :-1]  # fGn for spectral analysis
        loss = loss_fn(increments)
        
        # Loss should be relatively small for matching H
        assert loss.item() < 5.0  # Allow tolerance for spectral estimation

    def test_different_beta_values(self):
        """Different target_beta should give different losses."""
        x = torch.randn(10, 500)
        
        loss_fn1 = SpectralConsistencyLoss(target_beta=1.5)
        loss_fn2 = SpectralConsistencyLoss(target_beta=2.5)
        
        loss1 = loss_fn1(x)
        loss2 = loss_fn2(x)
        
        # Losses should differ
        assert not torch.isclose(loss1, loss2)

    def test_freq_cutoff_parameters(self):
        """Frequency cutoff parameters should work."""
        loss_fn = SpectralConsistencyLoss(
            target_beta=2.0,
            low_freq_cutoff=0.05,
            high_freq_cutoff=0.8
        )
        x = torch.randn(10, 500)
        loss = loss_fn(x)
        assert not torch.isnan(loss)

    def test_smooth_kernel_parameter(self):
        """Smooth kernel parameter should work."""
        loss_fn = SpectralConsistencyLoss(target_beta=2.0, smooth_kernel=7)
        x = torch.randn(10, 500)
        loss = loss_fn(x)
        assert not torch.isnan(loss)


# =============================================================================
# Integration Tests
# =============================================================================

class TestLossIntegration:
    """Test loss functions in training scenarios."""

    def test_combined_loss(self):
        """Losses can be combined with other losses."""
        hurst_loss = HurstRegularizationLoss(target_H=0.5)
        spectral_loss = SpectralConsistencyLoss(target_beta=2.0)
        
        x = torch.randn(10, 500, requires_grad=True)
        
        mse = (x ** 2).mean()
        h_loss = hurst_loss(x)
        s_loss = spectral_loss(x)
        
        total_loss = mse + 0.1 * h_loss + 0.1 * s_loss
        total_loss.backward()
        
        assert x.grad is not None

    def test_in_training_loop(self):
        """Losses should work in a simple training loop."""
        # Simple model
        model = nn.Linear(100, 500)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        hurst_loss = HurstRegularizationLoss(target_H=0.5)
        
        for _ in range(3):
            x = torch.randn(8, 100)
            out = model(x)
            loss = hurst_loss(out)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        # Should complete without error
        assert True


# =============================================================================
# Device Compatibility Tests
# =============================================================================

class TestDeviceCompatibility:
    """Test GPU/CPU device handling."""

    def test_hurst_loss_cpu(self):
        """HurstRegularizationLoss on CPU should work."""
        loss_fn = HurstRegularizationLoss(target_H=0.5)
        x = torch.randn(10, 500, device="cpu")
        loss = loss_fn(x)
        assert loss.device.type == "cpu"

    def test_spectral_loss_cpu(self):
        """SpectralConsistencyLoss on CPU should work."""
        loss_fn = SpectralConsistencyLoss(target_beta=2.0)
        x = torch.randn(10, 500, device="cpu")
        loss = loss_fn(x)
        assert loss.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_hurst_loss_cuda(self):
        """HurstRegularizationLoss on CUDA should work."""
        loss_fn = HurstRegularizationLoss(target_H=0.5)
        x = torch.randn(10, 500, device="cuda")
        loss = loss_fn(x)
        assert loss.device.type == "cuda"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_spectral_loss_cuda(self):
        """SpectralConsistencyLoss on CUDA should work."""
        loss_fn = SpectralConsistencyLoss(target_beta=2.0)
        x = torch.randn(10, 500, device="cuda")
        loss = loss_fn(x)
        assert loss.device.type == "cuda"
