"""
Pytest configuration and shared fixtures for torchfbm tests.

This module provides common fixtures used across multiple test modules.
"""
import pytest
import torch
import numpy as np


# =============================================================================
# Random Seed Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def set_random_seeds():
    """Set random seeds for reproducibility in each test."""
    torch.manual_seed(42)
    np.random.seed(42)
    yield
    # Reset after test (optional)
    torch.manual_seed(torch.initial_seed())


# =============================================================================
# Device Fixtures
# =============================================================================

@pytest.fixture(params=["cpu"])
def device(request):
    """Provide device for testing (CPU only by default)."""
    return request.param


@pytest.fixture
def cuda_device():
    """Provide CUDA device if available, skip otherwise."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    return "cuda"


# =============================================================================
# Dtype Fixtures
# =============================================================================

@pytest.fixture(params=[torch.float32, torch.float64])
def dtype(request):
    """Provide dtype for testing."""
    return request.param


@pytest.fixture
def float64_dtype():
    """Provide float64 for high-precision tests."""
    return torch.float64


# =============================================================================
# Hurst Parameter Fixtures
# =============================================================================

@pytest.fixture(params=[0.1, 0.3, 0.5, 0.7, 0.9])
def hurst(request):
    """Provide representative Hurst values for testing."""
    return request.param


@pytest.fixture(params=[0.2, 0.5, 0.8])
def hurst_quick(request):
    """Provide fewer Hurst values for quick testing."""
    return request.param


@pytest.fixture
def low_hurst():
    """Provide low Hurst value (anti-persistent)."""
    return 0.2


@pytest.fixture
def high_hurst():
    """Provide high Hurst value (persistent)."""
    return 0.8


@pytest.fixture
def brownian_hurst():
    """Provide H=0.5 for standard Brownian motion."""
    return 0.5


# =============================================================================
# Sequence Length Fixtures
# =============================================================================

@pytest.fixture(params=[64, 256, 1024])
def n_samples(request):
    """Provide sequence lengths for testing."""
    return request.param


@pytest.fixture
def short_sequence():
    """Provide short sequence length."""
    return 64


@pytest.fixture
def medium_sequence():
    """Provide medium sequence length."""
    return 256


@pytest.fixture
def long_sequence():
    """Provide long sequence length."""
    return 1024


# =============================================================================
# Batch Size Fixtures
# =============================================================================

@pytest.fixture(params=[1, 8, 32])
def batch_size(request):
    """Provide batch sizes for testing."""
    return request.param


@pytest.fixture
def single_batch():
    """Provide single batch size."""
    return 1


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_1d_tensor():
    """Provide 1D sample tensor."""
    return torch.randn(256)


@pytest.fixture
def sample_2d_tensor():
    """Provide 2D sample tensor (batch, length)."""
    return torch.randn(8, 256)


@pytest.fixture
def sample_3d_tensor():
    """Provide 3D sample tensor (batch, channels, length)."""
    return torch.randn(8, 4, 256)


@pytest.fixture
def sample_fbm_path():
    """Provide a sample fBm path for testing estimators."""
    from torchfbm import fbm
    return fbm(hurst=0.7, n=1000, batch_size=1, seed=42)


# =============================================================================
# Network Fixtures (for SDE tests)
# =============================================================================

@pytest.fixture
def simple_drift_net():
    """Provide simple drift network."""
    import torch.nn as nn
    return nn.Linear(10, 10)


@pytest.fixture
def simple_diffusion_net():
    """Provide simple diffusion network."""
    import torch.nn as nn
    return nn.Linear(10, 10)


@pytest.fixture
def mlp_net():
    """Provide MLP network."""
    import torch.nn as nn
    return nn.Sequential(
        nn.Linear(10, 32),
        nn.ReLU(),
        nn.Linear(32, 10)
    )


# =============================================================================
# Tolerance Fixtures
# =============================================================================

@pytest.fixture
def strict_tolerance():
    """Provide strict numerical tolerance."""
    return {"atol": 1e-6, "rtol": 1e-6}


@pytest.fixture
def relaxed_tolerance():
    """Provide relaxed numerical tolerance for stochastic tests."""
    return {"atol": 1e-2, "rtol": 1e-2}


@pytest.fixture
def statistical_tolerance():
    """Provide tolerance for statistical property tests."""
    return {"atol": 0.1, "rtol": 0.1}


# =============================================================================
# Skip Markers
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "cuda: marks tests that require CUDA"
    )
    config.addinivalue_line(
        "markers", "statistical: marks tests for statistical properties"
    )
    config.addinivalue_line(
        "markers", "mathematical: marks tests for mathematical properties"
    )


# =============================================================================
# Utility Functions (available as fixtures)
# =============================================================================

@pytest.fixture
def assert_close():
    """Provide torch.testing.assert_close for convenience."""
    return torch.testing.assert_close


@pytest.fixture
def assert_no_nan():
    """Provide NaN assertion helper."""
    def _assert_no_nan(tensor, msg="Tensor contains NaN"):
        assert not torch.isnan(tensor).any(), msg
    return _assert_no_nan


@pytest.fixture
def assert_no_inf():
    """Provide Inf assertion helper."""
    def _assert_no_inf(tensor, msg="Tensor contains Inf"):
        assert not torch.isinf(tensor).any(), msg
    return _assert_no_inf


@pytest.fixture
def assert_finite():
    """Provide finiteness assertion helper."""
    def _assert_finite(tensor, msg="Tensor contains non-finite values"):
        assert torch.isfinite(tensor).all(), msg
    return _assert_finite
