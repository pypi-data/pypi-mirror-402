"""Fractional calculus transforms for time series.

This module provides fractional differentiation and integration operators,
which generalize classical calculus to non-integer orders.

Based on Grünwald-Letnikov fractional derivatives, implemented via FFT
for computational efficiency.

Example:
    >>> from torchfbm.transforms import fractional_diff, fractional_integrate
    >>> x = torch.randn(100)
    >>> x_diff = fractional_diff(x, d=0.5)  # Half-derivative
    >>> x_int = fractional_integrate(x, d=0.5)  # Half-integral
"""

import torch
import torch.fft


def fractional_diff(
    x: torch.Tensor, d: float, dim: int = -1, return_numpy: bool = False
) -> torch.Tensor:
    """Compute the fractional derivative (or integral) of a time series.

    Based on the Grünwald-Letnikov definition, implemented via FFT.

    The fractional derivative of order $d$ is computed in the frequency domain
    using the transfer function:

    $$H(\\omega) = (1 - e^{-i\\omega})^d$$

    This generalizes the standard difference operator:
    - $d = 0$: Identity (no change)
    - $d = 1$: First difference $\\Delta x_t = x_t - x_{t-1}$
    - $d = 0.5$: Half-derivative (between identity and first difference)
    - $d < 0$: Fractional integration (smoothing)

    Applications:
        - **Finance**: Fractionally differenced series for ARFIMA models
        - **Memory preservation**: Unlike integer differencing, fractional
          differencing preserves long-range dependence while achieving
          stationarity.

    Note:
        Uses circular (periodic) boundary conditions due to FFT. Edge effects
        may occur at the boundaries.

    Args:
        x: Input tensor. Differentiation applied along `dim`.
        d: Fractional order. Positive for differentiation, negative for integration.
        dim: Dimension along which to apply the transform. Default is last dim.
        return_numpy: If True, returns NumPy array instead of torch.Tensor.

    Returns:
        Fractionally differentiated tensor with same shape as input.

    Raises:
        ValueError: If dimension is invalid or empty.
        TypeError: If input dtype is not a float type.

    Example:
        >>> x = torch.cumsum(torch.randn(1000), dim=0)  # Random walk
        >>> x_stationary = fractional_diff(x, d=0.4)  # Make stationary
        >>> # x_stationary should have lower autocorrelation
    """
    dim = dim if dim >= 0 else x.dim() + dim
    if dim < 0 or dim >= x.dim():
        raise ValueError(f"Invalid dim {dim} for input with {x.dim()} dims")

    n = x.shape[dim]
    device = x.device

    if n == 0:
        raise ValueError(
            "Cannot compute fractional difference along an empty dimension"
        )

    real_dtype = x.real.dtype if torch.is_complex(x) else x.dtype
    if real_dtype not in (torch.float16, torch.float32, torch.float64, torch.bfloat16):
        raise TypeError(f"Unsupported dtype {real_dtype} for fractional_diff")

    # Frequency domain transfer function: (1 - e^(-i*omega))^d
    freq_dtype = torch.promote_types(real_dtype, torch.float32)
    k = torch.arange(n, device=device, dtype=freq_dtype)
    omega = 2 * torch.tensor(torch.pi, device=device, dtype=freq_dtype) * k / n
    transfer = (1 - torch.exp(-1j * omega)) ** d

    if d < 0:
        transfer = transfer.clone()
        transfer[0] = torch.tensor(1.0, device=device, dtype=transfer.dtype)

    view_shape = [1] * x.dim()
    view_shape[dim] = n
    transfer = transfer.reshape(view_shape)

    # Apply via FFT convolution
    x_fft = torch.fft.fft(x, dim=dim)
    transfer = transfer.to(device=device, dtype=x_fft.dtype)
    diff_fft = x_fft * transfer
    x_diff = torch.fft.ifft(diff_fft, dim=dim).real

    return x_diff.cpu().numpy() if return_numpy else x_diff


def fractional_integrate(
    x: torch.Tensor, d: float, dim: int = -1, return_numpy: bool = False
) -> torch.Tensor:
    """Compute the fractional integral of a time series.

    This is the inverse operation of fractional differentiation:

    $$I^d[x] = D^{-d}[x]$$

    Fractional integration "smooths" the series by accumulating past values
    with power-law decaying weights.

    Args:
        x: Input tensor. Integration applied along `dim`.
        d: Fractional order of integration (positive values).
        dim: Dimension along which to apply the transform.
        return_numpy: If True, returns NumPy array instead of torch.Tensor.

    Returns:
        Fractionally integrated tensor with same shape as input.

    Example:
        >>> noise = torch.randn(1000)
        >>> smooth = fractional_integrate(noise, d=0.5)
        >>> # smooth has longer memory than noise
    """
    return fractional_diff(x, -d, dim=dim, return_numpy=return_numpy)
