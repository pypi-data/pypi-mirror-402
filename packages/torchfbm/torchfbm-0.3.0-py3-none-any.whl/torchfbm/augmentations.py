"""Data augmentation with fractional Gaussian noise.

This module provides augmentation techniques that add correlated noise
to training data, helping models become robust to specific correlation
structures in input data.

Example:
    >>> from torchfbm.augmentations import FractionalNoiseAugmentation
    >>> augment = FractionalNoiseAugmentation(H=0.7, sigma=0.01)
    >>> x_augmented = augment(x)
"""

import torch
from .generators import generate_davies_harte


class FractionalNoiseAugmentation(torch.nn.Module):
    """Data augmentation by adding fractional Gaussian noise.

    Adds fGn with specified Hurst parameter to training samples,
    helping models become robust to different correlation structures.

    The augmentation adds noise scaled by sigma:

    $$x_{aug} = x + \\sigma \\cdot fGn(H)$$

    Use Cases:
        - **H > 0.5 (persistent)**: Robustness to trending patterns
        - **H < 0.5 (anti-persistent)**: Robustness to mean-reverting noise
        - **H = 0.5**: Equivalent to standard Gaussian noise augmentation

    The augmentation is only applied during training with probability ``p``.

    Args:
        H: Hurst parameter for the fGn. Controls correlation structure.
        sigma: Noise amplitude scaling factor.
        p: Probability of applying the augmentation (per sample).

    Example:
        >>> # Make model robust to trending noise
        >>> augment = FractionalNoiseAugmentation(H=0.7, sigma=0.01, p=0.5)
        >>> model = nn.Sequential(augment, nn.Linear(100, 10))
        >>> 
        >>> # During training, 50% of samples get fGn added
        >>> model.train()
        >>> y = model(x)  # Augmentation active
        >>> 
        >>> # During eval, no augmentation
        >>> model.eval()
        >>> y = model(x)  # No noise added
    """

    def __init__(self, H: float = 0.5, sigma: float = 0.01, p: float = 0.5):
        super().__init__()
        self.H = H
        self.sigma = sigma
        self.p = p

    def forward(self, x):
        """Apply fractional noise augmentation.

        Args:
            x: Input tensor. Noise is added along the last dimension.

        Returns:
            Augmented tensor (during training with probability p),
            or unchanged input (during eval or with probability 1-p).
        """
        if self.training and torch.rand(1) < self.p:
            noise = generate_davies_harte(
                x.shape[-1], self.H, size=x.shape[:-1], device=x.device
            )
            return x + self.sigma * noise
        return x
