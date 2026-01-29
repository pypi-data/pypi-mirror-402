"""Hurst parameter schedules for diffusion models.

This module provides annealing schedules for the Hurst parameter,
useful in fractional diffusion models where the roughness of the
noise varies across sampling steps.

Inspired by noise scheduling in denoising diffusion models
(Ho, Jain & Abbeel, 2020).

Example:
    >>> from torchfbm.schedulers import get_hurst_schedule
    >>> # Smooth start, rough end
    >>> schedule = get_hurst_schedule(100, start_H=0.7, end_H=0.3, type='cosine')
"""

import torch


def get_hurst_schedule(
    n_steps: int, start_H: float = 0.3, end_H: float = 0.7, type="linear"
):
    """Generate a schedule of Hurst parameters for diffusion sampling.

    Creates an annealing schedule that varies the Hurst parameter across
    diffusion time steps. This allows for adaptive noise roughness during
    the generation process.

    Schedule Types:
        - **linear**: Uniform interpolation between start and end values

            $$H_t = start_H + \\frac{t}{T}(end_H - start_H)$$

        - **cosine**: Smooth cosine annealing (slower changes at endpoints)

            $$H_t = end_H + \\frac{1}{2}(start_H - end_H)(1 + \\cos(\\frac{\\pi t}{T}))$$

    Applications:
        - **Diffusion models**: Varying noise roughness during denoising
        - **Curriculum learning**: Gradually changing correlation structure
        - **Annealing**: Smooth transition between memory regimes

    Args:
        n_steps: Total number of steps in the schedule.
        start_H: Initial Hurst parameter value.
        end_H: Final Hurst parameter value.
        type: Schedule type, either 'linear' or 'cosine'.

    Returns:
        Tensor of shape ``(n_steps,)`` with Hurst values.

    Example:
        >>> # Linear schedule from rough to smooth
        >>> h_linear = get_hurst_schedule(100, start_H=0.3, end_H=0.7, type='linear')
        >>> h_linear[0], h_linear[-1]  # 0.3, 0.7

        >>> # Cosine schedule (slower at endpoints)
        >>> h_cosine = get_hurst_schedule(100, start_H=0.3, end_H=0.7, type='cosine')
    """
    if type == "linear":
        return torch.linspace(start_H, end_H, n_steps)
    elif type == "cosine":
        steps = torch.arange(n_steps)
        return end_H + 0.5 * (start_H - end_H) * (
            1 + torch.cos(steps / n_steps * torch.pi)
        )
