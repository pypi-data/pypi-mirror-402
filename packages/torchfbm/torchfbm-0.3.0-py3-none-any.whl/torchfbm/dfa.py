"""Detrended Fluctuation Analysis (DFA) for scaling exponent estimation.

This module provides GPU-accelerated DFA for measuring long-range correlations
in time series. DFA is particularly useful for non-stationary signals.

Based on Peng et al. (1994).

Example:
    >>> from torchfbm import fbm
    >>> from torchfbm.dfa import dfa
    >>> path = fbm(n=10000, H=0.7, size=(10,))
    >>> alpha = dfa(path)
    >>> print(f"DFA exponent: {alpha.mean():.3f}")  # Should be ~0.7
"""

import torch
import numpy as np


def dfa(
    x: torch.Tensor,
    scales: list = None,
    order: int = 1,
    return_alpha: bool = True,
) -> torch.Tensor:
    """Compute Detrended Fluctuation Analysis scaling exponent.

    Based on Peng et al. (1994).

    DFA measures the scaling behavior of the fluctuation function $F(s)$:

    $$F(s) \\sim s^{\\alpha}$$

    where $s$ is the scale (window size) and $\\alpha$ is the scaling exponent.

    For fBm, $\\alpha = H$ (the Hurst exponent). The relationship between DFA
    exponent and correlation structure:

    - $\\alpha < 0.5$: Anti-correlated (mean-reverting)
    - $\\alpha = 0.5$: Uncorrelated (white noise)
    - $0.5 < \\alpha < 1$: Long-range correlated
    - $\\alpha = 1$: $1/f$ noise (pink noise)
    - $\\alpha > 1$: Non-stationary, unbounded

    Algorithm:
        1. Compute profile: $y(k) = \\sum_{i=1}^{k}(x_i - \\bar{x})$
        2. Divide into segments of size $s$
        3. Fit polynomial trend in each segment
        4. Compute RMS of detrended fluctuations: $F(s)$
        5. Regress $\\log F(s)$ vs $\\log s$ to get $\\alpha$

    Args:
        x: Time series tensor of shape `(batch, time)` or `(time,)`.
        scales: List of window sizes. If None, uses 20 log-spaced scales.
        order: Polynomial order for detrending:
            - 1: Linear (DFA1, removes linear trends)
            - 2: Quadratic (DFA2, removes parabolic trends)
            - 3: Cubic (DFA3)
        return_alpha: If True, returns scaling exponent $\\alpha$.
            If False, returns tuple `(F, scales)` with raw fluctuation function.

    Returns:
        If `return_alpha=True`: Scaling exponent(s) of shape `(batch,)`.
        If `return_alpha=False`: Tuple of (fluctuation tensor, scales array).

    Example:
        >>> path = fbm(n=10000, H=0.8, size=(20,), seed=42)
        >>> alpha = dfa(path, order=2)
        >>> assert abs(alpha.mean() - 0.8) < 0.1
    """
    # Handle 1D input
    if x.dim() == 1:
        x = x.unsqueeze(0)

    device = x.device
    N = x.shape[1]

    # Compute profile: y(k) = cumsum(x - mean)
    y = torch.cumsum(x - x.mean(dim=1, keepdim=True), dim=1)

    # Default: 20 logarithmically-spaced scales
    if scales is None:
        min_scale = order + 2
        max_scale = N // 4
        scales = np.unique(
            np.logspace(np.log10(min_scale), np.log10(max_scale), num=20).astype(int)
        )

    fluctuations = []

    for s in scales:
        # Segment profile into non-overlapping windows
        n_segments = N // s
        limit = n_segments * s
        y_truncated = y[:, :limit]
        y_segmented = y_truncated.view(x.shape[0], n_segments, s)

        # Batched polynomial detrending via pseudo-inverse
        t = torch.arange(s, device=device, dtype=x.dtype)
        X = torch.stack([t**k for k in range(order + 1)], dim=1)

        try:
            coeffs_op = torch.linalg.pinv(X)
        except:
            coeffs_op = torch.linalg.inv(X.T @ X) @ X.T

        beta = torch.matmul(y_segmented, coeffs_op.t())
        trend = torch.matmul(beta, X.t())

        # RMS of detrended fluctuations
        rms = torch.sqrt(torch.mean((y_segmented - trend) ** 2, dim=2))
        F_s = torch.mean(rms, dim=1)
        fluctuations.append(F_s)

    # Stack fluctuations: (Batch, Num_Scales)
    F = torch.stack(fluctuations, dim=1)

    if not return_alpha:
        return F, scales

    # Log-log regression: log(F) = alpha * log(s) + C
    log_F = torch.log(F)
    log_scales = torch.log(torch.tensor(scales, device=device, dtype=x.dtype))
    S_xx = torch.var(log_scales, unbiased=False)
    mean_x = torch.mean(log_scales)
    mean_y = torch.mean(log_F, dim=1, keepdim=True)

    # Broadcast subtraction
    S_xy = torch.mean((log_scales - mean_x) * (log_F - mean_y), dim=1)

    alpha = S_xy / S_xx
    return alpha
