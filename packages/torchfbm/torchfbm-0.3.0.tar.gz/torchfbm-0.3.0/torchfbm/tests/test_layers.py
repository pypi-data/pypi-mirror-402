"""
Comprehensive tests for torchfbm neural network layers module.

Tests cover:
- Compilation and imports
- Layer construction
- Forward pass shapes
- Training/eval mode behavior
- Gradient flow
- Seed reproducibility
"""
import pytest
import torch
import torch.nn as nn
from torchfbm import (
    FBMNoisyLinear,
    FractionalPositionalEmbedding,
    FractionalKernel,
    fractional_init_,
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
    """Test that all layers import correctly."""

    def test_import_noisy_linear(self):
        from torchfbm import FBMNoisyLinear
        assert FBMNoisyLinear is not None

    def test_import_positional_embedding(self):
        from torchfbm import FractionalPositionalEmbedding
        assert FractionalPositionalEmbedding is not None

    def test_import_fractional_kernel(self):
        from torchfbm import FractionalKernel
        assert FractionalKernel is not None

    def test_import_fractional_init(self):
        from torchfbm import fractional_init_
        assert callable(fractional_init_)


# =============================================================================
# FBMNoisyLinear Tests
# =============================================================================

class TestFBMNoisyLinear:
    """Test FBMNoisyLinear layer."""

    def test_construction(self, method):
        """Layer should construct without error."""
        layer = FBMNoisyLinear(64, 32, H=0.5, method=method)
        assert layer is not None

    def test_forward_shape(self, method):
        """Forward pass should produce correct shape."""
        layer = FBMNoisyLinear(64, 32, H=0.5, method=method)
        x = torch.randn(10, 64)
        out = layer(x)
        assert out.shape == (10, 32)

    def test_forward_batched(self, method):
        """Forward pass with batch dimension should work."""
        layer = FBMNoisyLinear(64, 32, H=0.5, method=method)
        x = torch.randn(16, 64)
        out = layer(x)
        assert out.shape == (16, 32)

    def test_train_mode_stochastic(self, method):
        """In train mode, output should be stochastic."""
        layer = FBMNoisyLinear(64, 32, H=0.5, method=method)
        layer.train()
        x = torch.randn(5, 64)
        out1 = layer(x)
        layer.sample_noise()  # Force new noise sample
        out2 = layer(x)
        # Outputs should differ due to noise
        assert not torch.allclose(out1, out2, atol=1e-6)

    def test_eval_mode_deterministic(self, method):
        """In eval mode, output should be deterministic (frozen noise)."""
        layer = FBMNoisyLinear(64, 32, H=0.5, method=method)
        layer.eval()
        x = torch.randn(5, 64)
        out1 = layer(x)
        out2 = layer(x)
        torch.testing.assert_close(out1, out2)

    def test_gradient_flow(self, method):
        """Gradients should flow through the layer."""
        layer = FBMNoisyLinear(64, 32, H=0.5, method=method)
        x = torch.randn(5, 64, requires_grad=True)
        out = layer(x)
        loss = out.sum()
        loss.backward()
        
        assert x.grad is not None
        assert layer.weight_mu.grad is not None
        assert layer.bias_mu.grad is not None

    def test_parameters_exist(self, method):
        """Layer should have expected parameters."""
        layer = FBMNoisyLinear(64, 32, H=0.5, method=method)
        param_names = [name for name, _ in layer.named_parameters()]
        assert "weight_mu" in param_names
        assert "weight_sigma" in param_names
        assert "bias_mu" in param_names
        assert "bias_sigma" in param_names

    def test_rank_full(self):
        """rank='full' should work."""
        layer = FBMNoisyLinear(32, 16, H=0.5, rank="full")
        x = torch.randn(5, 32)
        out = layer(x)
        assert out.shape == (5, 16)

    def test_rank_integer(self):
        """Integer rank should work."""
        layer = FBMNoisyLinear(64, 32, H=0.5, rank=4)
        x = torch.randn(5, 64)
        out = layer(x)
        assert out.shape == (5, 32)

    def test_seed_reproducibility(self, method):
        """Same seed should give reproducible initialization."""
        layer1 = FBMNoisyLinear(32, 16, H=0.5, method=method, seed=42)
        layer2 = FBMNoisyLinear(32, 16, H=0.5, method=method, seed=42)
        # Initial noise should be the same
        torch.testing.assert_close(layer1.noise_bias, layer2.noise_bias)


# =============================================================================
# FractionalPositionalEmbedding Tests
# =============================================================================

class TestFractionalPositionalEmbedding:
    """Test FractionalPositionalEmbedding layer."""

    def test_construction(self):
        """Layer should construct without error."""
        emb = FractionalPositionalEmbedding(max_len=512, d_model=64)
        assert emb is not None

    def test_forward_shape(self):
        """Forward pass should produce correct shape."""
        emb = FractionalPositionalEmbedding(max_len=512, d_model=64)
        x = torch.randn(8, 100, 64)  # (batch, seq_len, d_model)
        out = emb(x)
        assert out.shape == (8, 100, 64)

    def test_adds_positional_info(self):
        """Output should differ from input."""
        emb = FractionalPositionalEmbedding(max_len=512, d_model=64)
        x = torch.zeros(2, 50, 64)
        out = emb(x)
        assert not torch.allclose(out, x)

    def test_hurst_range_parameter(self):
        """Different H_range values should produce different embeddings."""
        emb1 = FractionalPositionalEmbedding(max_len=512, d_model=64, H_range=(0.1, 0.3))
        emb2 = FractionalPositionalEmbedding(max_len=512, d_model=64, H_range=(0.7, 0.9))
        x = torch.randn(2, 50, 64)
        out1 = emb1(x)
        out2 = emb2(x)
        assert not torch.allclose(out1, out2)


# =============================================================================
# FractionalKernel Tests
# =============================================================================

class TestFractionalKernel:
    """Test FractionalKernel layer (covariance kernel, not convolution)."""

    def test_construction(self):
        """Layer should construct without error."""
        kernel = FractionalKernel(H=0.5, length_scale=1.0)
        assert kernel is not None

    def test_forward_shape(self):
        """Forward pass should produce correct pairwise kernel shape."""
        kernel = FractionalKernel(H=0.5, length_scale=1.0)
        # x1: (batch, n_points, features), x2: (batch, m_points, features)
        x1 = torch.randn(4, 10, 8)
        x2 = torch.randn(4, 15, 8)
        out = kernel(x1, x2)
        # Output is pairwise kernel matrix: (batch, n_points, m_points)
        assert out.shape == (4, 10, 15)

    def test_self_kernel_shape(self):
        """Self-kernel (K(X, X)) should work."""
        kernel = FractionalKernel(H=0.5)
        x = torch.randn(4, 20, 8)
        out = kernel(x, x)
        assert out.shape == (4, 20, 20)

    def test_diagonal_is_one(self):
        """Self-kernel diagonal should be 1 (distance=0 -> exp(0)=1)."""
        kernel = FractionalKernel(H=0.5)
        x = torch.randn(2, 10, 8)
        out = kernel(x, x)
        # Diagonal entries: distance is 0, so exp(0) = 1
        for i in range(10):
            assert abs(out[0, i, i].item() - 1.0) < 1e-5

    def test_symmetric(self):
        """Self-kernel should be symmetric."""
        kernel = FractionalKernel(H=0.5)
        x = torch.randn(2, 10, 8)
        out = kernel(x, x)
        torch.testing.assert_close(out, out.transpose(-1, -2))

    def test_hurst_affects_output(self):
        """Different H values should produce different kernels."""
        kernel1 = FractionalKernel(H=0.2)
        kernel2 = FractionalKernel(H=0.8)
        x = torch.randn(2, 10, 8)
        out1 = kernel1(x, x)
        out2 = kernel2(x, x)
        assert not torch.allclose(out1, out2)


# =============================================================================
# fractional_init_ Tests
# =============================================================================

class TestFractionalInit:
    """Test fractional_init_ function."""

    def test_init_modifies_tensor(self):
        """Should modify tensor values in-place."""
        tensor = torch.randn(64, 32)
        original = tensor.clone()
        fractional_init_(tensor, H=0.7)
        # Tensor should change
        assert not torch.allclose(tensor, original)

    def test_init_2d_tensor(self):
        """Should work with 2D tensor."""
        tensor = torch.randn(100, 50)
        fractional_init_(tensor, H=0.7, std=0.02)
        assert tensor.shape == (100, 50)
        assert not torch.isnan(tensor).any()

    def test_hurst_affects_distribution(self):
        """Different H values should produce different patterns."""
        tensor1 = torch.randn(100, 100)
        tensor2 = torch.randn(100, 100)
        
        fractional_init_(tensor1, H=0.2, std=0.02)
        fractional_init_(tensor2, H=0.8, std=0.02)
        
        # Different H should give different weight patterns
        assert not torch.allclose(tensor1, tensor2)

    def test_std_affects_scale(self):
        """Different std values should affect variance."""
        tensor1 = torch.randn(100, 100)
        tensor2 = tensor1.clone()
        
        fractional_init_(tensor1, H=0.5, std=0.01)
        fractional_init_(tensor2, H=0.5, std=0.1)
        
        # Larger std should give larger variance
        assert tensor2.std() > tensor1.std() * 2


# =============================================================================
# Device Compatibility Tests
# =============================================================================

class TestDeviceCompatibility:
    """Test GPU/CPU device handling."""

    def test_noisy_linear_cpu(self):
        """NoisyLinear on CPU should work."""
        layer = FBMNoisyLinear(32, 16, device="cpu")
        x = torch.randn(5, 32)
        out = layer(x)
        assert out.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_noisy_linear_cuda(self):
        """NoisyLinear on CUDA should work."""
        layer = FBMNoisyLinear(32, 16, device="cuda")
        x = torch.randn(5, 32, device="cuda")
        out = layer(x)
        assert out.device.type == "cuda"

    def test_positional_embedding_cpu(self):
        """PositionalEmbedding on CPU should work."""
        emb = FractionalPositionalEmbedding(max_len=100, d_model=64, device="cpu")
        x = torch.randn(2, 50, 64)
        out = emb(x)
        assert out.device.type == "cpu"
