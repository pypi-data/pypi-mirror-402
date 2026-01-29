"""Fractional noise for reinforcement learning exploration.

This module provides action noise generators using fractional Gaussian noise,
enabling correlated exploration strategies in RL algorithms.

The use of fGn instead of white noise allows for:
    - Smoother exploration trajectories (H > 0.5)
    - More thorough local exploration (H < 0.5)
    - Tunable temporal correlation in action perturbations

Compatible with Stable Baselines3 and similar RL frameworks.

Example:
    >>> from torchfbm.rl import FBMActionNoise
    >>> noise = FBMActionNoise(mean=0, sigma=0.1, H=0.7)
    >>> action = policy(state) + noise()
"""

import numpy as np
import torch
from .generators import generate_davies_harte, generate_cholesky


class FBMActionNoise:
    """Fractional Gaussian noise for RL action space exploration.

    Generates temporally correlated noise for action exploration, providing
    smoother or rougher perturbations depending on the Hurst parameter.

    Inspired by Ornstein-Uhlenbeck noise commonly used in DDPG, but with
    controllable long-range dependence.

    Properties by Hurst Parameter:
        - **H > 0.5 (persistent)**: Smooth, trending exploration. Actions
          tend to continue in the same direction, good for momentum-based tasks.
        - **H = 0.5**: Standard Gaussian noise (memoryless).
        - **H < 0.5 (anti-persistent)**: Rough, oscillating exploration.
          Actions frequently reverse, good for thorough local search.

    Implementation:
        Pre-generates a buffer of fGn samples for efficiency. When the buffer
        is exhausted, a new batch is generated automatically.

    Compatibility:
        - **return_numpy=True**: Compatible with Stable Baselines3
        - **return_numpy=False**: Returns PyTorch tensors (for custom implementations)

    Args:
        mean: Mean of the noise distribution.
        sigma: Standard deviation scaling factor.
        H: Hurst parameter in (0, 1). Controls temporal correlation.
        size: Shape of noise samples (action dimensions).
        buffer_size: Number of pre-generated samples.
        method: Generation method ('davies_harte' or 'cholesky').
        device: Computation device for tensor generation.
        return_numpy: If True, returns NumPy arrays (SB3 compatible).

    Example:
        >>> # For Stable Baselines3
        >>> noise = FBMActionNoise(
        ...     mean=np.zeros(action_dim),
        ...     sigma=0.1,
        ...     H=0.7,
        ...     return_numpy=True
        ... )
        >>> model = DDPG("MlpPolicy", env, action_noise=noise)

        >>> # For custom PyTorch RL
        >>> noise = FBMActionNoise(
        ...     mean=0, sigma=0.1, H=0.6, device='cuda'
        ... )
        >>> action = policy(state) + noise()
    """

    def __init__(
        self,
        mean,
        sigma,
        H=0.5,
        size=(1,),
        buffer_size=10000,
        method="davies_harte",
        device="cpu",
        return_numpy=False,
    ):
        self._mu = mean
        self._sigma = sigma
        self._H = H
        self._size = size
        self._buffer_size = buffer_size
        self._method = method
        self._device = device
        self._return_numpy = return_numpy

        self.reset()

    def reset(self):
        """Pre-generate a buffer of fGn samples.

        Called automatically during initialization and when the
        buffer is exhausted during sampling.
        """
        if self._method == "cholesky":
            gen_func = generate_cholesky
        else:
            gen_func = generate_davies_harte

        fgn = gen_func(self._buffer_size, self._H, size=self._size, device=self._device)

        if self._return_numpy:
            try:
                self._noise_buffer = (
                    fgn.detach().cpu().numpy()
                )  # Convert to NumPy on CPU
            except RuntimeError as e:
                if "Numpy is not available" in str(e):
                    raise ImportError(
                        "NumPy conversion requested but NumPy is not properly installed or has compatibility issues. "
                        "Please install/upgrade numpy: pip install -U numpy"
                    ) from e
                raise
        else:
            self._noise_buffer = fgn  # Keep as Tensor on Device

        self._step = 0

    def __call__(self):
        """Sample noise for the current step.

        Returns:
            Noise sample, either as NumPy array (if return_numpy=True)
            or PyTorch tensor.
        """
        if self._step >= self._buffer_size:
            self.reset()

        noise = self._noise_buffer[..., self._step]
        self._step += 1
        val = self._mu + self._sigma * noise

        if self._return_numpy:
            if isinstance(val, torch.Tensor):
                try:
                    return val.detach().cpu().numpy()
                except RuntimeError as e:
                    if "Numpy is not available" in str(e):
                        raise ImportError(
                            "NumPy conversion requested but NumPy is not properly installed or has compatibility issues. "
                            "Please install/upgrade numpy: pip install -U numpy"
                        ) from e
                    raise
            return np.asarray(val)
        else:
            # If val is somehow numpy/float, cast to tensor
            if not isinstance(val, torch.Tensor):
                val = torch.tensor(val, device=self._device)
            return val

    def __repr__(self) -> str:
        return f"FBMActionNoise(mu={self._mu}, sigma={self._sigma}, H={self._H}, numpy={self._return_numpy})"
