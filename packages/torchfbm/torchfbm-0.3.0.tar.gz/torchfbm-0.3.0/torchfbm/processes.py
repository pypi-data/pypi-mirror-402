"""Stochastic processes driven by fractional Brownian motion.

This module provides implementations of various stochastic processes that
incorporate fractional Brownian motion as the driving noise, enabling
simulation of systems with long-range dependence and anomalous diffusion.

Processes Included:
    - **Fractional Ornstein-Uhlenbeck**: Mean-reverting process with memory
    - **Geometric fBm**: Asset price model with long-range dependence
    - **Reflected fBm**: Bounded fBm with reflection barriers
    - **Fractional Brownian Bridge**: fBm conditioned on endpoint
    - **Multifractal Random Walk**: Volatility clustering model

Example:
    >>> from torchfbm.processes import fractional_ou_process, geometric_fbm
    >>> # Mean-reverting process with memory
    >>> ou = fractional_ou_process(1000, H=0.7, theta=0.5, mu=0.0)
    >>> # Asset prices with long-range dependence
    >>> prices = geometric_fbm(252, H=0.6, mu=0.05, sigma=0.2, s0=100)
"""

import torch
from .generators import generate_davies_harte, generate_cholesky, fbm


def fractional_ou_process(
    n: int,
    H: float,
    theta: float = 0.5,
    mu: float = 0.0,
    sigma: float = 1.0,
    dt: float = 0.01,
    size: tuple = (1,),
    method: str = "davies_harte",
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
    return_numpy: bool = False,
):
    """Simulate a Fractional Ornstein-Uhlenbeck (fOU) process.

    Based on Cheridito, Kawaguchi & Maejima (2003).

    The fOU process is defined by the stochastic differential equation:

    $$dX_t = \\theta(\\mu - X_t)dt + \\sigma dB^H_t$$

    where:
    - $\\theta$ is the mean-reversion speed
    - $\\mu$ is the long-term mean
    - $\\sigma$ is the volatility
    - $B^H_t$ is fractional Brownian motion with Hurst parameter $H$

    Properties:
        - **H > 0.5**: Persistent memory, slower mean-reversion than standard OU
        - **H = 0.5**: Reduces to standard OU process
        - **H < 0.5**: Anti-persistent, faster mean-reversion

    The process is stationary and mean-reverting, but unlike standard OU,
    it exhibits long-range dependence when $H \\neq 0.5$.

    Args:
        n: Number of time steps.
        H: Hurst parameter in (0, 1). Controls memory persistence.
        theta: Mean-reversion speed. Higher values = faster reversion.
        mu: Long-term mean level.
        sigma: Volatility coefficient.
        dt: Time step size.
        size: Batch dimensions for multiple sample paths.
        method: Generation method, either 'davies_harte' (fast) or 'cholesky' (exact).
        device: Computation device ('cpu' or 'cuda').
        dtype: Data type for tensors.
        return_numpy: If True, returns NumPy array.

    Returns:
        Tensor of shape ``(*size, n+1)`` containing the simulated paths.

    Example:
        >>> # Simulate interest rate with memory
        >>> rates = fractional_ou_process(
        ...     n=1000, H=0.7, theta=0.1, mu=0.05, sigma=0.01
        ... )
    """
    # Clamp H to valid range (0, 1)
    H = max(0.01, min(H, 0.99))

    if method == "cholesky":
        gen_func = generate_cholesky
    else:
        gen_func = generate_davies_harte

    # Generate fGn and scale by dt^H
    fgn = gen_func(n, H, size, device=device, dtype=dtype, return_numpy=False)
    noise_term = sigma * fgn * (dt**H)

    # Euler-Maruyama integration
    x = torch.zeros(*size, n + 1, device=device, dtype=dtype)
    x[..., 0] = mu  # Start at mean

    drift_factor = 1 - theta * dt
    drift_constant = theta * mu * dt

    for t in range(n):
        x[..., t + 1] = x[..., t] * drift_factor + drift_constant + noise_term[..., t]

    return x.cpu().numpy() if return_numpy else x


def geometric_fbm(
    n: int,
    H: float,
    mu: float = 0.05,
    sigma: float = 0.2,
    t_max: float = 1.0,
    s0: float = 100.0,
    size: tuple = (1,),
    method: str = "davies_harte",
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
    return_numpy: bool = False,
):
    """Simulate Geometric Fractional Brownian Motion (GFBm).

    Generalization of Geometric Brownian Motion with long-range dependence.
    Based on the framework described in Rogers (1997).

    The price follows:

    $$S_t = S_0 \\exp\\left((\\mu - \\frac{1}{2}\\sigma^2)t + \\sigma B^H_t\\right)$$

    where:
    - $S_0$ is the initial price
    - $\\mu$ is the drift (expected return)
    - $\\sigma$ is the volatility
    - $B^H_t$ is fractional Brownian motion

    Note:
        Unlike standard GBM, GFBm with $H \\neq 0.5$ admits arbitrage in
        continuous time. However, it remains useful for modeling observed
        market properties like volatility clustering and trend persistence.

    Applications:
        - **Finance**: Modeling assets with trending behavior ($H > 0.5$)
        - **Volatility modeling**: Capturing long-memory in volatility
        - **Risk analysis**: Fat-tailed return distributions

    Args:
        n: Number of time steps.
        H: Hurst parameter in (0, 1).
        mu: Drift coefficient (annualized return).
        sigma: Volatility coefficient (annualized).
        t_max: Total time horizon.
        s0: Initial price.
        size: Batch dimensions for multiple paths.
        method: Generation method ('davies_harte' or 'cholesky').
        device: Computation device.
        dtype: Data type for tensors.
        return_numpy: If True, returns NumPy array.

    Returns:
        Tensor of shape ``(*size, n+1)`` containing price paths.

    Raises:
        ValueError: If n <= 0.

    Example:
        >>> # Simulate 1 year of daily prices
        >>> prices = geometric_fbm(
        ...     n=252, H=0.6, mu=0.08, sigma=0.20, s0=100.0
        ... )
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")

    device = torch.device(device)

    t = torch.linspace(0, t_max, n + 1, device=device, dtype=dtype).expand(*size, n + 1)

    # Generate fBm path and scale to time horizon t_max
    fbm_path = fbm(
        n, H, size=size, method=method, device=device, dtype=dtype, return_numpy=False
    )
    scale_factor = (t_max / n) ** H
    fbm_path = fbm_path * scale_factor

    # Apply exponential transformation
    drift = (mu - 0.5 * sigma**2) * t
    diffusion = sigma * fbm_path

    log_returns = drift + diffusion

    result = s0 * torch.exp(log_returns)
    return result.cpu().numpy() if return_numpy else result


import torch
from .generators import fbm  # Ensure fbm is imported


@torch.jit.script
def _apply_reflection(
    path: torch.Tensor, increments: torch.Tensor, lower: float, upper: float
) -> torch.Tensor:
    """Apply reflection boundaries via Skorokhod reflection map.

    JIT-compiled loop for efficient boundary enforcement. When the process
    exceeds a boundary, it reflects back into the domain.

    Reflection rules:
        - If $X_{t+1} > upper$: $X_{t+1} \\leftarrow 2 \\cdot upper - X_{t+1}$
        - If $X_{t+1} < lower$: $X_{t+1} \\leftarrow 2 \\cdot lower - X_{t+1}$

    Args:
        path: Output tensor of shape ``(..., T+1)``, modified in-place.
        increments: Increment tensor of shape ``(..., T)``.
        lower: Lower reflection boundary.
        upper: Upper reflection boundary.

    Returns:
        Modified path tensor with reflections applied.
    """
    # Create output tensor
    # increments shape: (..., T)
    # path shape: (..., T+1)

    # Iterate through time
    # Note: We assume the first point is already set (usually 0 or S0)
    T = increments.shape[-1]

    # We flatten batch dims for the loop to make it simple, then reshape back?
    # JIT handles arbitrary shapes fairly well, but simple loops are safest.
    # Let's just iterate over time dimension T

    for t in range(T):
        # Propose next step
        dx = increments[..., t]
        current_x = path[..., t]
        next_x = current_x + dx

        # Check Upper Bound
        # If next_x > upper: overshoot is (next_x - upper)
        # reflected = upper - overshoot = upper - (next_x - upper) = 2*upper - next_x

        # We use torch.where to handle batch logic without python branching
        over_upper = next_x > upper
        next_x = torch.where(over_upper, 2 * upper - next_x, next_x)

        # Check Lower Bound
        # If next_x < lower: undershoot is (lower - next_x)
        # reflected = lower + undershoot = lower + (lower - next_x) = 2*lower - next_x
        under_lower = next_x < lower
        next_x = torch.where(under_lower, 2 * lower - next_x, next_x)

        # Store
        path[..., t + 1] = next_x

    return path


def reflected_fbm(
    n: int,
    H: float,
    lower: float = -1.0,
    upper: float = 1.0,
    mu: float = 0.0,
    sigma: float = 1.0,
    t_max: float = 1.0,
    start_val: float = 0.0,
    size: tuple = (1,),
    method: str = "davies_harte",
    device: str = "cpu",
    return_numpy: bool = False,
):
    """Simulate Reflected Fractional Brownian Motion with barriers.

    Based on the Skorokhod reflection map applied to fBm increments.

    The process is constrained to the interval $[lower, upper]$ using
    instantaneous reflection at the boundaries. This is a continuous-path
    approximation of bounded diffusion.

    Applications:
        - **Target zone models**: Exchange rates within currency bands
          (Krugman, 1991)
        - **Physical systems**: Particles confined in a box
        - **Finance**: Assets with hard support/resistance levels
        - **Queueing theory**: Buffer capacities

    Algorithm:
        1. Generate free fBm increments
        2. Apply reflection at each time step using the Skorokhod map
        3. Use JIT compilation for efficiency

    Args:
        n: Number of time steps.
        H: Hurst parameter in (0, 1).
        lower: Lower reflection barrier.
        upper: Upper reflection barrier.
        mu: Drift coefficient.
        sigma: Volatility coefficient.
        t_max: Total time horizon.
        start_val: Initial value (must be in [lower, upper]).
        size: Batch dimensions.
        method: Generation method ('davies_harte' or 'cholesky').
        device: Computation device.
        return_numpy: If True, returns NumPy array.

    Returns:
        Tensor of shape ``(*size, n+1)`` with paths bounded in [lower, upper].

    Raises:
        ValueError: If n <= 0.

    Example:
        >>> # Exchange rate in a target zone
        >>> rate = reflected_fbm(
        ...     n=1000, H=0.7, lower=1.0, upper=1.5, start_val=1.25
        ... )
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")

    device = torch.device(device)
    # 1. Generate fGn (Increments)
    # We use fbm() to handle method/clamping, but we need the *steps*, not the path.
    # So we call the generator directly or diff the fbm path.
    # Let's diff the fbm path for consistency with the geometric_fbm scaling logic.

    # Generate unbounded path first to get correctly scaled increments
    unbounded_path = fbm(n, H, size, method=method, device=device, return_numpy=False)

    # Scale to t_max and sigma
    scale_factor = sigma * (t_max / n) ** H
    unbounded_path = unbounded_path * scale_factor

    # Add drift (mu * dt)
    dt = t_max / n
    t_grid = torch.linspace(0, t_max, n + 1, device=device).expand(*size, n + 1)
    drift = mu * t_grid

    # Combine to get the proposed increments with drift
    total_unbounded = unbounded_path + drift

    # Calculate increments (dX)
    increments = total_unbounded[..., 1:] - total_unbounded[..., :-1]

    # 2. Prepare container
    reflected_path = torch.zeros_like(total_unbounded)
    reflected_path[..., 0] = start_val

    # 3. Run JIT Reflection
    # Ensure bounds are floats for JIT
    reflected_path = _apply_reflection(
        reflected_path, increments, float(lower), float(upper)
    )

    return reflected_path.cpu().numpy() if return_numpy else reflected_path


def fractional_brownian_bridge(
    n: int,
    H: float,
    start_val: float = 0.0,
    end_val: float = 0.0,
    t_max: float = 1.0,
    sigma: float = 1.0,
    size: tuple = (1,),
    method: str = "davies_harte",
    device: str = "cpu",
    return_numpy: bool = False,
):
    """Simulate a Fractional Brownian Bridge.

    Generates fBm conditioned on fixed start and end values.
    Based on the pinning method described in Norros, Valkeila & Virtamo (1999).

    The bridge is constructed using linear correction of a free fBm path:

    $$B^{H,bridge}_t = B^H_t - \\frac{t}{T}(B^H_T - (end - start)) + start$$

    This produces a "rough" path (for $H < 0.5$) or "smooth" path (for $H > 0.5$)
    that is pinned to specific boundary values.

    Applications:
        - **Finance**: Modeling prices with known future values (options at expiry)
        - **Simulation**: Conditioning on observed endpoints
        - **Interpolation**: Rough path interpolation between data points
        - **Testing**: Generating paths with known boundary conditions

    Args:
        n: Number of time steps.
        H: Hurst parameter in (0, 1).
        start_val: Starting value $B^{H,bridge}_0$.
        end_val: Ending value $B^{H,bridge}_T$.
        t_max: Total time horizon $T$.
        sigma: Volatility scaling.
        size: Batch dimensions.
        method: Generation method ('davies_harte' or 'cholesky').
        device: Computation device.
        return_numpy: If True, returns NumPy array.

    Returns:
        Tensor of shape ``(*size, n+1)`` with bridge paths.

    Example:
        >>> # Bridge from 0 to 1 with rough texture
        >>> bridge = fractional_brownian_bridge(
        ...     n=1000, H=0.3, start_val=0.0, end_val=1.0
        ... )
        >>> print(bridge[0, 0], bridge[0, -1])  # ~0.0, ~1.0
    """
    device = torch.device(device)

    # 1. Generate a FREE unconditioned path starting at 0
    # We use fbm() to handle H-clamping and method selection
    # shape: (..., n+1)
    free_path = fbm(n, H, size=size, method=method, device=device, return_numpy=False)

    # 2. Scale the free path to physical time/sigma
    # Scale factor for variance over time T is T^(2H)
    # The generator gives us unit step variance.
    scale_factor = sigma * (t_max / n) ** H
    free_path = free_path * scale_factor

    # 3. Create the Time Grid
    # Shape: (1, ..., n+1) to broadcast correctly
    t_grid = torch.linspace(0, t_max, n + 1, device=device)
    # Reshape for broadcasting against 'size'
    # If size=(Batch, ), free_path is (Batch, n+1).
    # We need t_grid to be (1, n+1) compatible.
    for _ in range(len(size)):
        t_grid = t_grid.unsqueeze(0)

    # 4. Calculate the Bridge "Drift"
    # We need to subtract the error at the end.
    # The free path ends at X_T. We want it to end at (end_val - start_val).
    # Current endpoint error = free_path[..., -1]

    current_end = free_path[..., -1:]  # Keep dims for broadcast
    target_displacement = end_val - start_val

    # The correction term is linear interpolation of the error
    # Correction(t) = (t / T) * (current_end - target_displacement)
    correction = (t_grid / t_max) * (current_end - target_displacement)

    # 5. Apply correction and shift start
    bridge = free_path - correction + start_val

    return bridge.cpu().numpy() if return_numpy else bridge


def multifractal_random_walk(n, H, lambda_sq=0.02, device="cpu"):
    """Simulate a Multifractal Random Walk (MRW).

    Based on Bacry, Delour & Muzy (2001).

    The MRW combines fractional noise with stochastic volatility to produce
    multifractal scaling:

    $$X_t = \\sum_{i=1}^{t} \\sigma_i \\epsilon_i$$

    where the volatility is:

    $$\\sigma_t = \\exp(\\lambda^2 \\omega_t)$$

    and $\\omega_t$ is fGn with Hurst parameter $H$, $\\epsilon_t$ is Gaussian noise.

    The intermittency parameter $\\lambda^2$ controls the strength of
    volatility clustering:
    - $\\lambda^2 \\approx 0$: Nearly Gaussian returns
    - $\\lambda^2 > 0$: Fat tails and volatility clustering
    - Higher $\\lambda^2$: More extreme events ("flash crashes")

    Properties:
        - Multifractal spectrum depends on both $H$ and $\\lambda^2$
        - Captures stylized facts of financial returns
        - Long-memory in squared/absolute returns

    Args:
        n: Number of time steps.
        H: Hurst parameter for the volatility process.
        lambda_sq: Intermittency coefficient (controls tail fatness).
        device: Computation device.

    Returns:
        Tensor of shape ``(n,)`` containing the MRW path.

    Example:
        >>> # Simulate returns with volatility clustering
        >>> mrw = multifractal_random_walk(1000, H=0.7, lambda_sq=0.02)
    """
    # 1. Generate fGn for the volatility cone (omega)
    # The correlation of omega is logarithmic
    # This is complex to do perfectly, but a proxy is:
    omega = generate_davies_harte(n, H, device=device)

    # 2. Stochastic Volatility
    sigma = torch.exp(lambda_sq * omega)

    # 3. The Walk
    noise = torch.randn(n, device=device)
    mrw = torch.cumsum(sigma * noise, dim=-1)
    return mrw
