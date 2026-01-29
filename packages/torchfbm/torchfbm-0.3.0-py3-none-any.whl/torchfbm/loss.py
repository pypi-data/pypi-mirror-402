"""Loss functions for enforcing fractional properties.

This module provides regularization losses that encourage neural network
outputs to exhibit specific fractional Brownian motion properties.

These losses are useful for:
    - Generative models that should produce fractal-like outputs
    - Time series forecasting with memory preservation
    - Physics-informed neural networks with scaling constraints

Example:
    >>> from torchfbm.loss import HurstRegularizationLoss, SpectralConsistencyLoss
    >>> hurst_loss = HurstRegularizationLoss(target_H=0.7)
    >>> spectral_loss = SpectralConsistencyLoss(target_beta=2.4)  # beta = 2H + 1
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from .estimators import estimate_hurst


class HurstRegularizationLoss(torch.nn.Module):
    """Regularization loss penalizing deviation from target Hurst exponent.

    Encourages generated time series to have a specific Hurst parameter
    by adding a penalty term to the training objective.

    The loss is computed as:

    $$\\mathcal{L}_{Hurst} = \\lambda (\\hat{H}(x) - H_{target})^2$$

    where $\\hat{H}(x)$ is the estimated Hurst exponent of the input.

    Usage in Training:
        Combine with task loss for multi-objective optimization:

        >>> total_loss = mse_loss(pred, target) + 0.1 * hurst_reg(pred)

    Note:
        The Hurst estimation uses R/S analysis, which may not be fully
        differentiable. Consider using :class:`SpectralConsistencyLoss`
        for smoother gradients.

    Args:
        target_H: Target Hurst exponent to encourage. Typically in (0, 1).

    Example:
        >>> reg = HurstRegularizationLoss(target_H=0.7)
        >>> x = torch.randn(32, 100)  # Batch of sequences
        >>> loss = reg(x)  # Penalty for deviation from H=0.7
    """

    def __init__(self, target_H: float = 0.5):
        super().__init__()
        self.target_H = target_H

    def forward(self, x):
        """Compute Hurst regularization loss.

        Args:
            x: Input tensor of shape ``(batch, time)`` or ``(time,)``.

        Returns:
            Scalar loss tensor.
        """
        h_est = estimate_hurst(x)
        #Use spectral consistency for more stable differentiation
        return torch.mean((h_est - self.target_H) ** 2)


class SpectralConsistencyLoss(nn.Module):
    """Spectral loss for enforcing power-law scaling.

    Penalizes deviations from the target spectral exponent $\\beta$,
    where the power spectral density follows:

    $$S(f) \\propto \\frac{1}{f^\\beta}$$

    For fractional Brownian motion, $\\beta = 2H + 1$, so:
    - $H = 0.5$ (Brownian): $\\beta = 2.0$
    - $H = 0.7$ (Persistent): $\\beta = 2.4$
    - $H = 0.3$ (Anti-persistent): $\\beta = 1.6$

    Features:
        - **PSD smoothing**: Reduces variance in spectral estimate
        - **Frequency masking**: Ignores DC and Nyquist components
        - **Windowing**: Hann window reduces spectral leakage
        - **Differentiable**: Gradients flow through regression

    Algorithm:
        1. Apply Hann window and compute FFT
        2. Estimate power spectral density
        3. Smooth PSD with average pooling
        4. Mask to relevant frequency range
        5. Linear regression in log-log space to estimate $\\beta$
        6. MSE loss against target $\\beta$

    Args:
        target_beta: Target spectral exponent. For fBm: $\\beta = 2H + 1$.
        low_freq_cutoff: Normalized frequency below which to ignore (avoids DC).
        high_freq_cutoff: Normalized frequency above which to ignore (avoids noise).
        smooth_kernel: Kernel size for PSD smoothing.

    Example:
        >>> loss_fn = SpectralConsistencyLoss(target_beta=2.4)  # H=0.7
        >>> x = fbm(1000, H=0.7, size=(32,))
        >>> loss = loss_fn(x)  # Should be small for correct H
    """

    def __init__(
        self, 
        target_beta: float, 
        low_freq_cutoff: float = 0.02, 
        high_freq_cutoff: float = 0.9, 
        smooth_kernel: int = 5
    ):
        super().__init__()
        self.target_beta = target_beta
        self.low_freq_cutoff = low_freq_cutoff
        self.high_freq_cutoff = high_freq_cutoff
        self.smooth_kernel = smooth_kernel

    def forward(self, x: torch.Tensor):
        """Compute spectral consistency loss.

        Args:
            x: Input tensor of shape ``(batch, channels, time)`` or ``(batch, time)``.

        Returns:
            Scalar MSE loss between estimated and target beta.
        """
        # x shape: (Batch, Channels, Time) or (Batch, Time)
        n = x.shape[-1]
        device = x.device

        # 1. Compute PSD with Windowing (to reduce leakage)
        # Hann window prevents the "cliff-edge" effect at the ends of the sequence
        window = torch.hann_window(n, periodic=True, device=device)
        fft = torch.fft.rfft(x * window, dim=-1)
        psd = torch.abs(fft) ** 2

        # 2. Smooth the PSD
        # Raw periodograms are too noisy for stable gradients. 
        # We apply a 1D average pool to smooth the spectral estimate.
        if self.smooth_kernel > 1:
            psd = F.avg_pool1d(
                psd.view(-1, 1, psd.shape[-1]), 
                kernel_size=self.smooth_kernel, 
                stride=1, 
                padding=self.smooth_kernel // 2
            ).view(psd.shape)

        # 3. Frequency setup
        freqs = torch.fft.rfftfreq(n, d=1.0, device=device)
        
        # 4. Create Mask
        # Skip DC component and extreme high-frequency noise
        mask = (freqs > self.low_freq_cutoff) & (freqs < self.high_freq_cutoff)
        # Ensure at least some bins remain
        if not mask.any():
            return torch.tensor(0.0, device=device, requires_grad=True)

        log_f = torch.log(freqs[mask])
        log_psd = torch.log(psd[..., mask] + 1e-10)

        # 5. Batch Regression
        # We solve: log_psd = -beta * log_f + intercept
        # Formula for slope: beta = - Cov(log_f, log_psd) / Var(log_f)
        mean_f = log_f.mean()
        mean_psd = log_psd.mean(dim=-1, keepdim=True)

        diff_f = log_f - mean_f
        diff_psd = log_psd - mean_psd

        num = (diff_f * diff_psd).sum(dim=-1)
        den = (diff_f ** 2).sum()

        estimated_beta = -num / (den + 1e-8)

        # 6. Penalize deviations from target
        return F.mse_loss(estimated_beta, torch.full_like(estimated_beta, self.target_beta))

