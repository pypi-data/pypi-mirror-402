"""Hurst exponent estimation methods.

This module provides differentiable estimators for the Hurst exponent,
enabling end-to-end training of models with fBm-related objectives.

Example:
    >>> from torchfbm import fbm, estimate_hurst
    >>> path = fbm(n=5000, H=0.7, size=(100,))
    >>> H_est = estimate_hurst(path)
    >>> print(f"Estimated H: {H_est.mean():.3f}")  # Should be ~0.7
"""

import torch


def estimate_hurst(
    x: torch.Tensor,
    min_lag: int = 2,
    max_lag: int = 20,
    assume_path: bool = True,
    return_numpy: bool = False,
) -> torch.Tensor:
    """Estimate the Hurst exponent using the variogram method.

    Based on Mandelbrot (1969) and the classical rescaled range analysis.

    This method exploits the self-similarity property of fBm. For increments
    at lag $\\tau$, the variance scales as:

    $$\\text{Var}(B_H(t+\\tau) - B_H(t)) \\propto \\tau^{2H}$$

    Taking logarithms:

    $$\\log(\\text{Var}(\\tau)) = 2H \\cdot \\log(\\tau) + C$$

    The Hurst exponent is estimated via linear regression in log-log space.

    Note:
        This estimator is differentiable and can be used in loss functions
        for training neural networks with Hurst-regularized outputs.

    Args:
        x: Input time series of shape `(batch, time)` or `(time,)`.
        min_lag: Minimum lag for variance estimation.
        max_lag: Maximum lag for variance estimation.
        assume_path: If True, treats `x` as fBm path (default).
            If False, treats `x` as fGn (increments) and integrates first.
        return_numpy: If True, returns NumPy array instead of torch.Tensor.

    Returns:
        Estimated Hurst exponent(s) clamped to $[0.01, 0.99]$.
        Shape is `(batch,)` or scalar for 1D input.

    Example:
        >>> path = fbm(n=5000, H=0.8, size=(50,), seed=42)
        >>> H_est = estimate_hurst(path, min_lag=2, max_lag=50)
        >>> assert abs(H_est.mean() - 0.8) < 0.1  # Should be close to 0.8
    """
    # Normalize to zero mean, unit variance for numerical stability
    x = (x - x.mean(dim=-1, keepdim=True)) / (x.std(dim=-1, keepdim=True) + 1e-6)

    # Integrate fGn to fBm path if needed
    if not assume_path:
        x = torch.cumsum(x, dim=-1)

    lags = torch.arange(min_lag, max_lag, device=x.device)
    variances = []

    for lag in lags:
        # Compute increment variance at each scale
        if x.size(-1) <= lag:
            break
        increments = x[..., lag:] - x[..., :-lag]
        var = increments.var(dim=-1)
        variances.append(var)

    # Stack variances: Shape (Num_Lags, Batch)
    variances = torch.stack(variances, dim=0)

    # Log-log regression: log(Var) = 2H * log(lag) + C
    y = torch.log(variances + 1e-8)
    X = (
        torch.log(lags[: variances.size(0)].float()).unsqueeze(1).expand(-1, x.shape[0])
    )  # (Num_Lags, Batch)

    # Least squares slope estimation
    X_mean = X.mean(dim=0)
    y_mean = y.mean(dim=0)

    numerator = ((X - X_mean) * (y - y_mean)).sum(dim=0)
    denominator = ((X - X_mean) ** 2).sum(dim=0)

    slope = numerator / (denominator + 1e-8)

    # Slope = 2H, so H = Slope / 2
    H_est = slope / 2.0

    result = torch.clamp(H_est, 0.01, 0.99)
    return result.cpu().numpy() if return_numpy else result
