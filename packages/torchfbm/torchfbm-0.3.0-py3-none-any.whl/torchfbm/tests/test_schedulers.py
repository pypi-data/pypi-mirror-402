"""
Comprehensive tests for torchfbm schedulers module.

Tests cover:
- Hurst schedule creation and interpolation
- Boundary conditions
- Various interpolation modes
- Edge cases
"""
import pytest
import torch
import numpy as np
from torchfbm import get_hurst_schedule


# =============================================================================
# Import Tests
# =============================================================================

class TestImports:
    """Test that scheduler components import correctly."""

    def test_import_get_hurst_schedule(self):
        from torchfbm import get_hurst_schedule
        assert callable(get_hurst_schedule)


# =============================================================================
# Basic Functionality Tests
# =============================================================================

class TestBasicFunctionality:
    """Test basic scheduler functionality."""

    def test_returns_tensor(self):
        """Schedule should return a tensor."""
        schedule = get_hurst_schedule(n_steps=100, start_H=0.3, end_H=0.7)
        assert isinstance(schedule, torch.Tensor)

    def test_correct_length(self):
        """Schedule should have correct number of steps."""
        n_steps = 50
        schedule = get_hurst_schedule(n_steps=n_steps, start_H=0.3, end_H=0.7)
        assert len(schedule) == n_steps

    @pytest.mark.parametrize("n_steps", [1, 10, 100, 1000])
    def test_various_lengths(self, n_steps):
        """Various schedule lengths should work."""
        schedule = get_hurst_schedule(n_steps=n_steps, start_H=0.3, end_H=0.7)
        assert len(schedule) == n_steps


# =============================================================================
# Boundary Condition Tests
# =============================================================================

class TestBoundaryConditions:
    """Test boundary conditions of schedules."""

    def test_starts_at_start_h(self):
        """Schedule should start at start_H."""
        start_H = 0.3
        schedule = get_hurst_schedule(n_steps=100, start_H=start_H, end_H=0.7)
        assert abs(schedule[0].item() - start_H) < 1e-5

    def test_ends_at_end_h(self):
        """Schedule should end at end_H."""
        end_H = 0.8
        schedule = get_hurst_schedule(n_steps=100, start_H=0.3, end_H=end_H)
        assert abs(schedule[-1].item() - end_H) < 1e-5

    def test_constant_schedule(self):
        """start_H == end_H should give constant schedule."""
        h_value = 0.5
        schedule = get_hurst_schedule(n_steps=100, start_H=h_value, end_H=h_value)
        assert torch.allclose(schedule, torch.full((100,), h_value))


# =============================================================================
# Interpolation Mode Tests
# =============================================================================

class TestInterpolationModes:
    """Test different interpolation modes."""

    def test_linear_mode(self):
        """Linear mode should produce linear interpolation."""
        schedule = get_hurst_schedule(
            n_steps=100, start_H=0.2, end_H=0.8, type="linear"
        )
        # Check linearity: differences should be constant
        diffs = schedule[1:] - schedule[:-1]
        assert torch.allclose(diffs, diffs[0].expand_as(diffs), atol=1e-5)

    def test_cosine_mode(self):
        """Cosine mode should produce smooth transitions."""
        schedule = get_hurst_schedule(
            n_steps=100, start_H=0.2, end_H=0.8, type="cosine"
        )
        # Cosine schedule: starts at start_H, approaches but may not exactly reach end_H
        # Formula: end_H + 0.5*(start_H - end_H)*(1 + cos(k/n * pi))
        # At k=0: end_H + 0.5*(start_H - end_H)*(1 + 1) = start_H  ✓
        # At k=n-1: close to but not exactly end_H due to discrete steps
        assert abs(schedule[0].item() - 0.2) < 1e-5  # Should start at start_H exactly
        # End value depends on n_steps discretization, just check it's moving toward end_H
        assert schedule[-1].item() > schedule[0].item()  # Should be increasing
        # Cosine has slower start/end, faster middle
        # First diff should be smaller than middle diff
        first_diff = (schedule[1] - schedule[0]).abs().item()
        mid_diff = (schedule[50] - schedule[49]).abs().item()
        assert first_diff < mid_diff


# =============================================================================
# Value Range Tests
# =============================================================================

class TestValueRange:
    """Test that schedule values stay within valid ranges."""

    def test_values_in_valid_range(self):
        """All schedule values should be in [0, 1]."""
        schedule = get_hurst_schedule(n_steps=100, start_H=0.1, end_H=0.9)
        assert (schedule >= 0).all()
        assert (schedule <= 1).all()

    def test_increasing_schedule(self):
        """start_H < end_H should give increasing schedule (linear mode)."""
        schedule = get_hurst_schedule(
            n_steps=100, start_H=0.2, end_H=0.8, type="linear"
        )
        # Should be monotonically non-decreasing
        diffs = schedule[1:] - schedule[:-1]
        assert (diffs >= -1e-6).all()  # Allow tiny numerical error

    def test_decreasing_schedule(self):
        """start_H > end_H should give decreasing schedule (linear mode)."""
        schedule = get_hurst_schedule(
            n_steps=100, start_H=0.8, end_H=0.2, type="linear"
        )
        # Should be monotonically non-increasing
        diffs = schedule[1:] - schedule[:-1]
        assert (diffs <= 1e-6).all()


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_step(self):
        """n_steps=1 should work."""
        schedule = get_hurst_schedule(n_steps=1, start_H=0.3, end_H=0.7)
        assert len(schedule) == 1
        # Single step could be either start or end; just check it's valid
        assert 0 <= schedule[0].item() <= 1

    def test_two_steps(self):
        """n_steps=2 should give exactly [start_H, end_H]."""
        schedule = get_hurst_schedule(n_steps=2, start_H=0.3, end_H=0.7, type="linear")
        assert len(schedule) == 2
        assert abs(schedule[0].item() - 0.3) < 1e-5
        assert abs(schedule[-1].item() - 0.7) < 1e-5

    def test_extreme_hurst_values(self):
        """Extreme but valid Hurst values should work."""
        schedule = get_hurst_schedule(n_steps=100, start_H=0.01, end_H=0.99)
        assert (schedule >= 0).all()
        assert (schedule <= 1).all()

    def test_no_nan_values(self):
        """Schedule should never contain NaN."""
        for mode in ["linear", "cosine"]:
            schedule = get_hurst_schedule(
                n_steps=100, start_H=0.3, end_H=0.7, type=mode
            )
            assert not torch.isnan(schedule).any()

    def test_no_inf_values(self):
        """Schedule should never contain Inf."""
        for mode in ["linear", "cosine"]:
            schedule = get_hurst_schedule(
                n_steps=100, start_H=0.3, end_H=0.7, type=mode
            )
            assert not torch.isinf(schedule).any()


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Test integration with other torchfbm components."""

    def test_use_with_fbm_generation(self):
        """Schedule values should be usable as Hurst parameters."""
        from torchfbm import fbm
        
        schedule = get_hurst_schedule(n_steps=10, start_H=0.3, end_H=0.7)
        
        # Each schedule value should work as a Hurst parameter
        for h in schedule:
            # fbm(n, H, size) returns shape (*size, n+1) due to prepended zero
            path = fbm(n=100, H=h.item(), size=(1,))
            assert path.shape == (1, 101)  # n+1 points for cumsum path
            assert not torch.isnan(path).any()
