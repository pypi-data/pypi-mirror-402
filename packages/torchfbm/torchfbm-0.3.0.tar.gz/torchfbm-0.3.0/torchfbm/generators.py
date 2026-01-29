"""Fractional Brownian Motion and Fractional Gaussian Noise generators.

This module provides efficient algorithms for generating fBm paths and fGn samples,
including both exact (Cholesky) and approximate (Davies-Harte) methods.

The core mathematical foundation is based on Mandelbrot & Van Ness (1968), with
generation algorithms from Davies & Harte (1987) and Asmussen & Glynn (2007).

Example:
    >>> from torchfbm import fbm, generate_davies_harte
    >>> # Generate fBm path with H=0.7
    >>> path = fbm(n=1000, H=0.7, size=(10,))
    >>> # Generate fGn increments
    >>> noise = generate_davies_harte(n=1000, H=0.7, size=(10,))
"""

import torch
import numpy
import warnings


def _autocovariance(
    H: float, n: int, device: torch.device, dtype: torch.dtype
) -> torch.Tensor:
    """Compute the autocovariance function of fractional Gaussian noise.

    Based on Mandelbrot & Van Ness (1968).

    The autocovariance function $\\gamma(k)$ for fGn is given by:

    $$\\gamma(k) = \\frac{1}{2}\\left(|k+1|^{2H} - 2|k|^{2H} + |k-1|^{2H}\\right)$$

    Key properties:
        - $\\gamma(0) = 1$ (unit variance at lag 0)
        - For $H > 0.5$: $\\gamma(k) > 0$ (persistent, positive correlations)
        - For $H < 0.5$: $\\gamma(k) < 0$ for $k \\geq 1$ (anti-persistent)
        - For $H = 0.5$: $\\gamma(k) = 0$ for $k \\geq 1$ (white noise)

    Args:
        H: Hurst exponent in $(0, 1)$.
        n: Number of lags to compute (0 to n-1).
        device: Torch device for computation.
        dtype: Data type for the output tensor.

    Returns:
        Tensor of autocovariance values $[\\gamma(0), \\gamma(1), ..., \\gamma(n-1)]$.
    """
    k = torch.arange(0, n, device=device, dtype=dtype)
    return 0.5 * (
        torch.abs(k + 1) ** (2 * H)
        - 2 * torch.abs(k) ** (2 * H)
        + torch.abs(k - 1) ** (2 * H)
    )


def generate_cholesky(
    n: int,
    H: float,
    size: tuple = (1,),
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
    seed: int = None,
    return_numpy: bool = False,
) -> torch.Tensor:
    """Generate fractional Gaussian noise using Cholesky decomposition.

    Exact method based on Asmussen & Glynn (2007).

    This method constructs the full covariance matrix $\\Sigma$ and decomposes it as
    $\\Sigma = LL^T$ where $L$ is lower triangular. The fGn samples are then:

    $$X = L \\cdot Z \\quad \\text{where } Z \\sim \\mathcal{N}(0, I)$$

    Complexity:
        - Time: $O(n^3)$ for Cholesky decomposition
        - Space: $O(n^2)$ for covariance matrix storage

    Note:
        Exact but computationally expensive for large $n$. Use Davies-Harte method
        for $n > 1000$. May encounter numerical instability for $H$ close to 0 or 1
        with large $n$.

    Args:
        n: Number of samples to generate (length of fGn sequence).
        H: Hurst exponent in $(0, 1)$.
        size: Batch dimensions. Output shape will be `(*size, n)`.
        device: Torch device ('cpu' or 'cuda').
        dtype: Data type (torch.float32 or torch.float64).
        seed: Random seed for reproducibility.
        return_numpy: If True, returns NumPy array instead of torch.Tensor.

    Returns:
        Fractional Gaussian noise samples with shape `(*size, n)`.

    Example:
        >>> fgn = generate_cholesky(n=100, H=0.7, size=(5,), seed=42)
        >>> assert fgn.shape == (5, 100)
    """
    device = torch.device(device)
    generator = torch.Generator(device=device)
    if seed is not None:
        generator.manual_seed(seed)

    gamma = _autocovariance(H, n, device, dtype)
    idx = torch.arange(n, device=device)
    lhs = idx.unsqueeze(0)
    rhs = idx.unsqueeze(1)
    distance_matrix = torch.abs(lhs - rhs)
    Sigma = gamma[distance_matrix]

    jitter = 1e-6 * torch.eye(n, device=device, dtype=dtype)
    try:
        L = torch.linalg.cholesky(Sigma + jitter)
    except RuntimeError:
        L = torch.linalg.cholesky(Sigma + jitter * 10)

    noise = torch.randn(*size, n, device=device, dtype=dtype, generator=generator)
    result = torch.matmul(noise, L.t())
    return result.cpu().numpy() if return_numpy else result


def generate_davies_harte(
    n: int,
    H: float,
    size: tuple = (1,),
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
    seed: int = None,
    return_numpy: bool = False,
) -> torch.Tensor:
    """Generate fractional Gaussian noise using the Davies-Harte method.

    Based on Davies & Harte (1987).

    This FFT-based method embeds the Toeplitz covariance matrix into a circulant
    matrix, enabling efficient spectral factorization. The algorithm:

    1. Construct circulant embedding: $c = [\\gamma_0, ..., \\gamma_{n-1}, \\gamma_{n-2}, ..., \\gamma_1]$
    2. Compute eigenvalues via FFT: $\\lambda = \\text{FFT}(c)$
    3. Generate complex noise: $W \\sim \\mathcal{CN}(0, I)$
    4. Apply spectral factorization: $X = \\text{IFFT}(\\sqrt{\\lambda} \\cdot W)$

    Complexity:
        - Time: $O(n \\log n)$ via FFT
        - Space: $O(n)$

    Warning:
        For some combinations of $H$ and $n$, the circulant embedding may have
        negative eigenvalues. These are clamped to zero with a warning. For exact
        results in such cases, use the Cholesky method.

    Args:
        n: Number of samples to generate (length of fGn sequence).
        H: Hurst exponent in $(0, 1)$.
        size: Batch dimensions. Output shape will be `(*size, n)`.
        device: Torch device ('cpu' or 'cuda').
        dtype: Data type (torch.float32 or torch.float64).
        seed: Random seed for reproducibility.
        return_numpy: If True, returns NumPy array instead of torch.Tensor.

    Returns:
        Fractional Gaussian noise samples with shape `(*size, n)`.

    Example:
        >>> fgn = generate_davies_harte(n=10000, H=0.7, size=(100,), seed=42)
        >>> assert fgn.shape == (100, 10000)
    """
    device = torch.device(device)
    generator = torch.Generator(device=device)
    if seed is not None:
        generator.manual_seed(seed)

    gamma = _autocovariance(H, n, device, dtype)

    # Circulant embedding: [gamma_0, ..., gamma_{n-1}, gamma_{n-2}, ..., gamma_1]
    row = torch.cat([gamma, gamma[1:-1].flip(0)])
    M = row.shape[0]

    # FFT (Real to Complex)
    lambdas = torch.fft.fft(row).real
    if torch.any(lambdas < 0):
        warnings.warn(
            "Negative eigenvalues encountered in Davies-Harte method, but zeroed out. "
            "Results may be inaccurate. Consider using 'cholesky' method for exact results."
        )
        lambdas = torch.clamp(lambdas, min=0.0)

    # Generate Complex White Noise with specific generator/dtype
    rng_real = torch.randn(*size, M, device=device, dtype=dtype, generator=generator)
    rng_imag = torch.randn(*size, M, device=device, dtype=dtype, generator=generator)
    complex_noise = torch.complex(rng_real, rng_imag)

    scale = torch.sqrt(lambdas / M)
    fft_noise = complex_noise * scale

    simulation = torch.fft.ifft(fft_noise) * M
    result = simulation.real[..., :n]
    return result.cpu().numpy() if return_numpy else result


def fbm(
    n: int,
    H: float,
    size: tuple = (1,),
    method: str = "davies_harte",
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
    seed: int = None,
    return_numpy: bool = False,
) -> torch.Tensor:
    """Generate Fractional Brownian Motion paths.

    Based on Mandelbrot & Van Ness (1968).

    Fractional Brownian Motion $B_H(t)$ is a continuous-time Gaussian process with:

    - $B_H(0) = 0$
    - $\\mathbb{E}[B_H(t)] = 0$
    - $\\text{Cov}(B_H(s), B_H(t)) = \\frac{1}{2}(|s|^{2H} + |t|^{2H} - |t-s|^{2H})$

    The Hurst exponent $H \\in (0, 1)$ controls the path regularity:

    - $H < 0.5$: Rough paths, anti-persistent (mean-reverting)
    - $H = 0.5$: Standard Brownian motion
    - $H > 0.5$: Smooth paths, persistent (trending)

    The fBm path is constructed by cumulative summation of fGn:

    $$B_H(t_k) = \\sum_{i=1}^{k} X_i \\quad \\text{where } X \\sim \\text{fGn}(H)$$

    Args:
        n: Number of increments. Output path has $n+1$ points (includes $B_H(0)=0$).
        H: Hurst exponent in $(0, 1)$. Automatically clamped to $[0.01, 0.99]$.
        size: Batch dimensions. Output shape will be `(*size, n+1)`.
        method: Generation method:
            - 'davies_harte': Fast FFT-based, $O(n \\log n)$ (default)
            - 'cholesky': Exact but slow, $O(n^3)$
        device: Torch device ('cpu' or 'cuda').
        dtype: Data type (torch.float32 or torch.float64).
        seed: Random seed for reproducibility.
        return_numpy: If True, returns NumPy array instead of torch.Tensor.

    Returns:
        fBm paths with shape `(*size, n+1)`. First element is always 0.

    Example:
        >>> path = fbm(n=1000, H=0.7, size=(10,), seed=42)
        >>> assert path.shape == (10, 1001)
        >>> assert (path[:, 0] == 0).all()  # Starts at zero
    """
    H = max(0.01, min(H, 0.99))

    if method == "cholesky":
        func = generate_cholesky
    else:
        func = generate_davies_harte

    fgn = func(n, H, size, device=device, dtype=dtype, seed=seed, return_numpy=False)

    zeros = torch.zeros(*size, 1, device=device, dtype=dtype)
    result = torch.cat([zeros, torch.cumsum(fgn, dim=-1)], dim=-1)
    return result.cpu().numpy() if return_numpy else result
