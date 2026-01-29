"""Fractional stochastic differential equation solvers.

This module provides neural network modules for solving stochastic
differential equations driven by fractional Brownian motion.

Based on the theory of rough paths and fractional calculus for SDEs.

Example:
    >>> from torchfbm.sde import NeuralFSDE
    >>> drift = nn.Linear(2, 2)
    >>> diffusion = nn.Linear(2, 2)
    >>> fsde = NeuralFSDE(state_size=2, drift_net=drift, diffusion_net=diffusion)
    >>> x0 = torch.randn(32, 2)
    >>> trajectory = fsde(x0, n_steps=100)
"""

import torch
import torch.nn as nn
from .generators import generate_davies_harte


class NeuralFSDE(nn.Module):
    """Neural network solver for fractional stochastic differential equations.

    Solves SDEs of the form:

    $$dX_t = \\mu(X_t, t)dt + \\sigma(X_t, t)dB^H_t$$

    where:
    - $\\mu$ is the drift network
    - $\\sigma$ is the diffusion network
    - $B^H_t$ is fractional Brownian motion with Hurst parameter $H$

    Uses Euler-Maruyama discretization with fGn increments. The Hurst
    parameter can optionally be learned during training.

    Note:
        For $H < 0.5$ (rough regime), standard Euler-Maruyama may be unstable.
        This implementation raises an error for $H < 0.5$ until rough path
        integration methods are implemented.

    Algorithm:
        For each step $i$:

        $$X_{i+1} = X_i + \\mu(X_i) \\Delta t + \\sigma(X_i) \\cdot (\\Delta t)^H \\epsilon_i$$

        where $\\epsilon_i$ is fGn with the specified Hurst parameter.

    Args:
        state_size: Dimension of the state space.
        drift_net: Neural network for drift $\\mu(X_t)$. Input/output: ``state_size``.
        diffusion_net: Neural network for diffusion $\\sigma(X_t)$. Input/output: ``state_size``.
        H_init: Initial Hurst parameter value.
        learnable_H: If True, H is a learnable parameter.
        t_max: Total time horizon for integration.

    Example:
        >>> # Define drift and diffusion networks
        >>> drift = nn.Sequential(nn.Linear(2, 16), nn.Tanh(), nn.Linear(16, 2))
        >>> diffusion = nn.Sequential(nn.Linear(2, 16), nn.Tanh(), nn.Linear(16, 2))
        >>>
        >>> # Create fSDE with learnable Hurst parameter
        >>> fsde = NeuralFSDE(
        ...     state_size=2,
        ...     drift_net=drift,
        ...     diffusion_net=diffusion,
        ...     H_init=0.7,
        ...     learnable_H=True
        ... )
        >>>
        >>> # Integrate from initial conditions
        >>> x0 = torch.randn(32, 2)  # Batch of initial states
        >>> trajectory = fsde(x0, n_steps=100)  # (32, 101, 2)
    """

    def __init__(
        self,
        state_size,
        drift_net,
        diffusion_net,
        H_init=0.5,
        learnable_H=False,
        t_max=1.0,
    ):
        super().__init__()
        self.state_size = state_size
        self.drift_net = drift_net
        self.diffusion_net = diffusion_net
        self.t_max = t_max

        # Constraint: H must be in (0, 1)

        raw_h = torch.tensor(H_init, dtype=torch.float32).logit()
        
        if learnable_H:
            self.raw_h = nn.Parameter(raw_h)
        else:
            self.register_buffer("raw_h", raw_h)

    @property
    def H(self):
        """Current Hurst parameter value, constrained to (0.01, 0.99)."""
        return torch.sigmoid(self.raw_h) * 0.98 + 0.01

    def forward(self, x0, n_steps, method="davies_harte"):
        """Integrate the fSDE from initial conditions.

        Args:
            x0: Initial state tensor of shape ``(batch, state_size)``.
            n_steps: Number of integration steps.
            method: fGn generation method ('davies_harte' or 'cholesky').

        Returns:
            Trajectory tensor of shape ``(batch, n_steps+1, state_size)``.

        Raises:
            ValueError: If $H < 0.5$ (rough regime not yet supported).
        """
        # Validate H
        h_curr = self.H
        if h_curr < 0.5:
             # Euler-Maruyama unstable for H < 0.5
            raise ValueError(
                "Standard Euler-Maruyama solvers are mathematically unstable for H < 0.5 "
                "(Rough paths). Please use H >= 0.5 or wait for stable release (Rough Signatures)."
            )
            pass 

        batch_size = x0.shape[0]
        dt = self.t_max / n_steps
        device = x0.device

        # 2. Generate Noise
        # use Torch ops for H gradient to flow
        fgn = generate_davies_harte(
            n_steps, h_curr, size=(batch_size, self.state_size), device=device
        )
        
        # 3. Scale Noise: fGn ~ N(0, 1) -> N(0, dt^(2H))
        noise_increments = fgn * (dt ** h_curr)

        # 4. Integrate
        xt = x0
        trajectory = [x0]
        
        #eventual optimization: use jit or vectorized ops
        for i in range(n_steps):
            drift = self.drift_net(xt) * dt
            diffusion = self.diffusion_net(xt)

            # SDE: dX = mu*dt + sigma*dB
            # Using ito interpretation
            noise = diffusion * noise_increments[..., i]

            xt = xt + drift + noise
            trajectory.append(xt)

        return torch.stack(trajectory, dim=1)
