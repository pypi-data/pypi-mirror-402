"""Online (streaming) fractional Gaussian noise generation.

This module provides incremental generation of fGn samples, useful when
the sequence length is not known in advance or when memory constraints
prevent batch generation.

Based on the incremental Cholesky update approach from Dietrich & Newsam (1997).

Example:
    >>> from torchfbm.online import CachedFGNGenerator
    >>> gen = CachedFGNGenerator(H=0.7)
    >>> samples = [gen.step() for _ in range(100)]
"""

import torch
from .generators import _autocovariance


class CachedFGNGenerator:
    """Online fractional Gaussian noise generator with incremental Cholesky updates.

    Based on Dietrich & Newsam (1997).

    Generates exact fGn samples one at a time, maintaining the correct
    correlation structure by incrementally updating the Cholesky factorization.

    Algorithm:
        At step $n$, we have the covariance matrix $\\Sigma_n$ and its
        Cholesky factor $L_n$ such that $\\Sigma_n = L_n L_n^T$.

        To add a new sample:
        1. Compute the new covariance row $\\mathbf{v} = Cov(X_{n+1}, X_1, ..., X_n)$
        2. Solve $L_n \\mathbf{w} = \\mathbf{v}$ for $\\mathbf{w}$
        3. Compute $\\delta = \\sqrt{\\gamma(0) - \\|\\mathbf{w}\\|^2}$
        4. Generate $X_{n+1} = \\mathbf{w}^T \\mathbf{Z} + \\delta z_{new}$
        5. Extend $L_{n+1}$ with the new row

    Complexity:
        - Per step: $O(n)$ for solve and update
        - Total for $N$ steps: $O(N^2)$
        - Memory: $O(N^2)$ for Cholesky factor

    Note:
        For batch generation where the full length is known, use
        :func:`generate_cholesky` or :func:`generate_davies_harte` instead.

    Args:
        H: Hurst parameter in (0, 1).
        device: Computation device ('cpu' or 'cuda').
        dtype: Data type for tensors.

    Attributes:
        n: Current number of generated samples.
        H: Hurst parameter.

    Example:
        >>> gen = CachedFGNGenerator(H=0.7, device='cpu')
        >>> # Generate samples one at a time
        >>> for _ in range(100):
        ...     sample = gen.step()
        ...     process_sample(sample)
    """

    def __init__(self, H: float, device="cpu", dtype=torch.float32):
        self.H = H
        self.device = torch.device(device)
        self.dtype = dtype
        self.n = 0

        self.L = torch.zeros(0, 0, device=self.device, dtype=self.dtype)
        self.z_history = torch.zeros(0, device=self.device, dtype=self.dtype)

    def step(self) -> torch.Tensor:
        """Generate the next sample in the fGn sequence.

        Each call generates a single correlated sample that maintains
        the correct fGn covariance structure with all previous samples.

        Returns:
            Scalar tensor containing the next fGn value.

        Example:
            >>> gen = CachedFGNGenerator(H=0.7)
            >>> x1 = gen.step()  # First sample
            >>> x2 = gen.step()  # Second sample (correlated with x1)
        """
        new_idx = self.n
        z = torch.randn(1, device=self.device, dtype=self.dtype)

        if new_idx == 0:
            # Initialize first point
            self.L = torch.ones(1, 1, device=self.device, dtype=self.dtype)
            val = z
            self.z_history = torch.cat([self.z_history, z])

        else:
            # Incremental Cholesky update
            full_gamma = _autocovariance(self.H, new_idx + 1, self.device, self.dtype)
            v = full_gamma[1:].flip(0)
            c = full_gamma[0]

            # Solve L * w = v via forward substitution
            v = v.unsqueeze(1)
            w = torch.linalg.solve_triangular(self.L, v, upper=False)
            w_flat = w.flatten()
            w_norm_sq = torch.dot(w_flat, w_flat)

            delta_sq = c - w_norm_sq
            delta = torch.sqrt(torch.clamp(delta_sq, min=1e-8))

            # Generate correlated sample: X = w^T Z + delta * z_new
            val = torch.dot(w_flat, self.z_history) + delta * z
            self.z_history = torch.cat([self.z_history, z])

            # Extend Cholesky factor
            zeros_col = torch.zeros(self.n, 1, device=self.device, dtype=self.dtype)
            L_padded = torch.cat([self.L, zeros_col], dim=1)
            bottom_row = torch.cat([w_flat, delta.unsqueeze(0)])
            self.L = torch.vstack([L_padded, bottom_row.unsqueeze(0)])

        self.n += 1
        return val
