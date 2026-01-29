"""Neural network layers with fractional Brownian motion integration.

This module provides PyTorch layers that incorporate fractional Brownian motion
and fractional Gaussian noise for exploration, regularization, and feature
extraction in deep learning.

Layers Included:
    - :class:`FBMNoisyLinear`: NoisyNet-style linear layer with fBm noise
    - :class:`FractionalPositionalEmbedding`: Positional encoding using fBm paths
    - :class:`FractionalKernel`: Power-law covariance kernel for attention/GPs
    - :func:`fractional_init_`: Weight initialization with correlated noise

Example:
    >>> from torchfbm.layers import FBMNoisyLinear, FractionalPositionalEmbedding
    >>> layer = FBMNoisyLinear(64, 32, H=0.7)
    >>> pos_embed = FractionalPositionalEmbedding(max_len=512, d_model=256)
"""

import torch
from typing import Optional
import torch.nn as nn
import torch.nn.functional as F
from .generators import generate_davies_harte, generate_cholesky


import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Union
from .generators import generate_davies_harte, generate_cholesky


class FBMNoisyLinear(nn.Module):
    """Linear layer with parametric fractional Brownian motion noise.

    Based on Fortunato, Azar, Piot et al. (2017) NoisyNets, extended with
    fractional Gaussian noise for temporally correlated exploration.

    Standard NoisyNets use independent Gaussian noise, which provides
    memoryless exploration. This layer uses fGn instead, allowing:
    - **H > 0.5**: Persistent exploration (smooth, trending noise)
    - **H = 0.5**: Standard NoisyNet behavior (independent noise)
    - **H < 0.5**: Anti-persistent exploration (rough, oscillating noise)

    The noisy weights are computed as:

    $$W = \\mu_W + \\sigma_W \\odot \\epsilon_W$$

    $$b = \\mu_b + \\sigma_b \\odot \\epsilon_b$$

    where $\\epsilon_W$ and $\\epsilon_b$ are sampled from correlated
    fGn streams.

    Memory Optimization:
        For large layers, full-rank noise requires $O(n_{out} \\times n_{in})$
        storage. The ``rank`` parameter enables low-rank factorization:
        - ``rank='full'``: Independent noise per weight (expensive)
        - ``rank=k``: Uses $k$ rank-1 outer products (efficient)

    Args:
        in_features: Number of input features.
        out_features: Number of output features.
        H: Hurst parameter for fBm noise (0 < H < 1).
        sigma_init: Initial scale for learnable noise parameters.
        rank: Noise rank ('full' for independent, or integer for low-rank).
        buffer_size: Number of pre-generated noise samples.
        method: Generation method ('davies_harte' or 'cholesky').
        device: Device to store parameters and buffers.
        dtype: Data type for parameters and buffers.
        seed: Random seed for reproducibility.

    Example:
        >>> # Replace standard linear in DQN for exploration
        >>> layer = FBMNoisyLinear(64, 32, H=0.7, rank=4)
        >>> layer.train()  # Noisy weights during training
        >>> output = layer(input)
        >>> layer.eval()   # Mean weights during inference
        >>> output = layer(input)
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        H: float = 0.5,
        sigma_init: float = 0.5,
        rank: Union[int, str] = 1,  # 1, 10, or "full"
        buffer_size: int = 1000,
        method: str = "davies_harte",
        device: str = "cpu",
        dtype: torch.dtype = torch.float32,
        seed: Optional[int] = None,
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.H = H
        self.rank = rank
        self.buffer_size = buffer_size
        self.method = method
        self.step_counter = 0
        self._device = torch.device(device)
        self._dtype = dtype
        self._seed = seed

        # --- Learnable Parameters ---
        self.weight_mu = nn.Parameter(
            torch.empty(out_features, in_features, device=self._device, dtype=self._dtype)
        )
        self.weight_sigma = nn.Parameter(
            torch.empty(out_features, in_features, device=self._device, dtype=self._dtype)
        )
        self.bias_mu = nn.Parameter(
            torch.empty(out_features, device=self._device, dtype=self._dtype)
        )
        self.bias_sigma = nn.Parameter(
            torch.empty(out_features, device=self._device, dtype=self._dtype)
        )

        # --- Output Buffers (for sampled noise) ---
        self.register_buffer(
            "weight_epsilon", 
            torch.empty(out_features, in_features, device=self._device, dtype=self._dtype)
        )
        self.register_buffer(
            "bias_epsilon", 
            torch.empty(out_features, device=self._device, dtype=self._dtype)
        )

        # --- Stream Buffers (The reservoir of random numbers) ---
        # 1. Bias is ALWAYS independent (Full Rank) because it's cheap (O(N))
        self.register_buffer(
            "noise_bias", 
            torch.empty(out_features, buffer_size, device=self._device, dtype=self._dtype)
        )

        # 2. Weight Noise Allocation
        if self.rank == "full":
            # Independent: O(N_out * N_in) - Expensive
            self.register_buffer(
                "noise_weight_source", 
                torch.empty(out_features, in_features, buffer_size, device=self._device, dtype=self._dtype)
            )
            if (in_features * out_features) > 1e9:
                print(
                    f"Warning: Using full-rank noise for weights with size "
                    f"({out_features}, {in_features}) may consume significant memory. Consider setting rank to a smaller integer."
                )
        else:
            # Low-Rank: O(Rank * (N_out + N_in)) memory - Efficient
            r = int(self.rank)
            self.register_buffer(
                "noise_in", 
                torch.empty(r, in_features, buffer_size, device=self._device, dtype=self._dtype)
            )
            self.register_buffer(
                "noise_out", 
                torch.empty(r, out_features, buffer_size, device=self._device, dtype=self._dtype)
            )

        self.reset_parameters(sigma_init)
        self.refresh_noise_stream()

    def reset_parameters(self, sigma_init):
        """Initialize layer parameters.

        Uses uniform initialization for mean parameters and constant
        initialization for sigma parameters.

        Args:
            sigma_init: Initial value for noise scaling parameters.
        """
        mu_range = 1 / self.in_features**0.5
        self.weight_mu.data.uniform_(-mu_range, mu_range)
        self.weight_sigma.data.fill_(sigma_init / self.in_features**0.5)
        self.bias_mu.data.uniform_(-mu_range, mu_range)
        self.bias_sigma.data.fill_(sigma_init / self.out_features**0.5)

    def refresh_noise_stream(self):
        """Regenerate the fGn noise buffers.

        Called automatically when the buffer is exhausted during forward passes.
        Uses different seeds for weight and bias noise to ensure independence.
        """
        gen_func = generate_cholesky if self.method == "cholesky" else generate_davies_harte
        
        # --- Seed Management ---
        # We ensure distinct seeds for every component to prevent correlation
        s_bias = self._seed
        s_in = self._seed + 1 if self._seed is not None else None
        s_out = self._seed + 2 if self._seed is not None else None
        s_full = self._seed + 3 if self._seed is not None else None

        # 1. Generate Bias Noise (Always Independent)
        self.noise_bias = gen_func(
            self.buffer_size, self.H, (self.out_features,), 
            self._device, self._dtype, seed=s_bias
        )

        # 2. Generate Weight Noise
        if self.rank == "full":
            # Flatten, generate, reshape
            total = self.out_features * self.in_features
            raw = gen_func(
                self.buffer_size, self.H, (total,), 
                self._device, self._dtype, seed=s_full
            )
            self.noise_weight_source = raw.view(self.out_features, self.in_features, self.buffer_size)
        
        else:
            r = int(self.rank)
            
            # Input Factors (Rank, In)
            noise_in_flat = gen_func(
                self.buffer_size, self.H, (r * self.in_features,), 
                self._device, self._dtype, seed=s_in
            )
            self.noise_in = noise_in_flat.view(r, self.in_features, self.buffer_size)
            
            # Output Factors (Rank, Out)
            noise_out_flat = gen_func(
                self.buffer_size, self.H, (r * self.out_features,), 
                self._device, self._dtype, seed=s_out
            )
            self.noise_out = noise_out_flat.view(r, self.out_features, self.buffer_size)

        self.step_counter = 0

    def sample_noise(self):
        """Sample noise for current forward pass.

        Reads from pre-generated buffers and constructs weight/bias noise.
        For low-rank mode, synthesizes full noise matrix from rank-k factors.
        """
        if self.step_counter >= self.buffer_size:
            self.refresh_noise_stream()

        # Bias is always simple lookup
        self.bias_epsilon = self.noise_bias[..., self.step_counter]

        if self.rank == "full":
            self.weight_epsilon = self.noise_weight_source[..., self.step_counter]
        
        else:
            # Low-Rank Synthesis
            u = self.noise_in[..., self.step_counter]   # (Rank, In)
            v = self.noise_out[..., self.step_counter]  # (Rank, Out)

            # Apply Factorized NoisyNet transform: f(x) = sign(x) * sqrt(abs(x))
            # This preserves the magnitude distribution when multiplying two Gaussians
            def f(x): return x.sign().mul(x.abs().sqrt())
            u_hat = f(u)
            v_hat = f(v)

            # Sum of Outer Products: W = (1/sqrt(K)) * Sum(v_k (x) u_k)
            # einsum: rank(r), out(o), in(i) -> out(o), in(i)
            matrix_noise = torch.einsum('ro, ri -> oi', v_hat, u_hat)
            
            # Scale to maintain unit variance
            scale = 1.0 / (int(self.rank) ** 0.5)
            self.weight_epsilon = matrix_noise * scale

        self.step_counter += 1

    def forward(self, input):
        """Forward pass with optional noise injection.

        During training: Uses noisy weights $\\mu + \\sigma \\odot \\epsilon$
        During eval: Uses only mean weights $\\mu$

        Args:
            input: Input tensor of shape ``(batch, in_features)``.

        Returns:
            Output tensor of shape ``(batch, out_features)``.
        """
        if self.training:
            self.sample_noise()
            return F.linear(
                input,
                self.weight_mu + self.weight_sigma * self.weight_epsilon,
                self.bias_mu + self.bias_sigma * self.bias_epsilon,
            )
        return F.linear(input, self.weight_mu, self.bias_mu)

from .generators import fbm  


class FractionalPositionalEmbedding(nn.Module):
    """Positional embedding using frozen fractional Brownian motion paths.

    Uses diverse fBm paths with varying Hurst parameters to create
    positional encodings that capture multi-scale fractal structure.

    Unlike sinusoidal embeddings which encode position at fixed frequencies,
    fBm embeddings encode position at varying levels of roughness:
    - Low H channels: High-frequency, local position information
    - High H channels: Low-frequency, global position trends

    The embedding is computed once during initialization and frozen
    (non-learnable), similar to standard positional encodings.

    Algorithm:
        1. Generate ``d_model`` fBm paths with Hurst parameters
           linearly spaced in ``H_range``
        2. Normalize each path to zero mean and unit variance
        3. Store as frozen buffer

    Args:
        max_len: Maximum sequence length supported.
        d_model: Embedding dimension (number of fBm paths).
        H_range: Tuple of (H_min, H_max) for diverse roughness levels.
        method: Generation method ('davies_harte' or 'cholesky').
        device: Device to store embeddings.
        dtype: Data type for embeddings.
        seed: Random seed for reproducibility.

    Example:
        >>> embed = FractionalPositionalEmbedding(
        ...     max_len=512, d_model=256, H_range=(0.1, 0.9)
        ... )
        >>> x = torch.randn(32, 100, 256)  # (batch, seq, dim)
        >>> x_with_pos = embed(x)  # Adds positional encoding
    """

    def __init__(
        self,
        max_len,
        d_model,
        H_range=(0.1, 0.9),
        method="davies_harte",
        device="cpu",
        dtype=torch.float32,
        seed: Optional[int] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.method = method
        self._device = torch.device(device)
        self._dtype = dtype
        self._seed = seed

        # 1. Create H values from H_range[0] to H_range[1]
        # We ensure they are within safe bounds [0.01, 0.99]
        h_min = max(0.01, H_range[0])
        h_max = min(0.99, H_range[1])
        Hs = torch.linspace(
            h_min, h_max, d_model, device=self._device, dtype=self._dtype
        )

        embeddings = []
        for i in range(d_model):
            # Generate path using selected method
            # We generate on CPU initially to save GPU memory for weights,
            # then register as buffer moves it to device automatically.
            path = fbm(
                max_len,
                H=Hs[i].item(),
                size=(1,),
                method=self.method,
                device=self._device,
                dtype=self._dtype,
                seed=self._seed,
            ).squeeze()

            # Normalization (Critical for Embeddings to preserve gradient scale)
            path = (path - path.mean()) / (path.std() + 1e-6)
            embeddings.append(path)

        # Shape: (max_len, d_model)
        # We assume the fbm path length (max_len+1) needs to be trimmed or matched
        # fbm() returns n+1 points, take 1 to max_len+1
        pe_tensor = torch.stack(embeddings, dim=1)

        # Crop if fbm generated n+1 and we want max_len
        pe_tensor = pe_tensor[:max_len, :]

        self.register_buffer("pe", pe_tensor.to(self._device, self._dtype))

    def forward(self, x):
        """Add positional encoding to input.

        Args:
            x: Input tensor of shape ``(batch, seq_len, d_model)``.

        Returns:
            Tensor with positional encoding added, same shape as input.

        Raises:
            ValueError: If sequence length exceeds ``max_len``.
        """
        seq_len = x.size(1)
        if seq_len > self.pe.size(0):
            raise ValueError(
                f"Sequence length {seq_len} exceeds max_len {self.pe.size(0)}"
            )

        return x + self.pe[:seq_len, :].unsqueeze(0)


def fractional_init_(tensor: torch.Tensor, H: float = 0.7, std: float = 0.02):
    """Initialize tensor weights using fractional Gaussian noise (in-place).

    Fills the tensor with correlated fGn values, inducing long-range
    spatial correlations in the weight matrix. May be useful for:
    - CNN kernels where adjacent weights should be correlated
    - Inducing smoothness priors in weight space
    - Experimental architectures with structured initialization

    The fGn is normalized to zero mean and scaled to the target standard
    deviation.

    Args:
        tensor: Tensor to initialize (modified in-place).
        H: Hurst parameter controlling spatial correlation.
        std: Target standard deviation of initialized weights.

    Example:
        >>> linear = nn.Linear(64, 32)
        >>> fractional_init_(linear.weight, H=0.7, std=0.02)
    """
    with torch.no_grad():
        rows, cols = tensor.shape
        total_elements = rows * cols

        # Generate a long correlated stream
        fgn = generate_davies_harte(total_elements, H, device=tensor.device)

        # Normalize and Scale
        fgn = (fgn - fgn.mean()) / (fgn.std() + 1e-8)
        fgn = fgn * std

        tensor.copy_(fgn.view(rows, cols))


class FractionalKernel(nn.Module):
    """Power-law covariance kernel based on fractional distance.

    Computes similarity based on the fractional Brownian motion covariance
    structure, where correlation decays as a power law with distance.

    The kernel is defined as:

    $$K(x, y) = \\exp\\left(-\\left(\\frac{\\|x - y\\|}{\\ell}\\right)^{2H}\\right)$$

    where:
    - $\\|x - y\\|$ is the Euclidean distance
    - $\\ell$ is the length scale
    - $H$ is the Hurst parameter

    Properties:
        - **H = 0.5**: Standard squared exponential (RBF) kernel
        - **H < 0.5**: Rougher kernel (faster decay)
        - **H > 0.5**: Smoother kernel (slower decay)

    Applications:
        - **Attention mechanisms**: Fractal-aware attention patterns
        - **Gaussian Processes**: Long-memory covariance functions
        - **Kernel methods**: SVMs with power-law similarity

    Args:
        H: Hurst parameter controlling decay rate.
        length_scale: Characteristic length scale $\\ell$.

    Example:
        >>> kernel = FractionalKernel(H=0.7, length_scale=1.0)
        >>> x1 = torch.randn(32, 10, 64)  # (batch, n_points, dim)
        >>> x2 = torch.randn(32, 20, 64)  # (batch, m_points, dim)
        >>> K = kernel(x1, x2)  # (32, 10, 20) similarity matrix
    """

    def __init__(self, H: float = 0.5, length_scale: float = 1.0):
        super().__init__()
        self.H = H
        self.length_scale = length_scale

    def forward(self, x1, x2):
        """Compute pairwise kernel values.

        Args:
            x1: First set of points, shape ``(batch, n, dim)``.
            x2: Second set of points, shape ``(batch, m, dim)``.

        Returns:
            Kernel matrix of shape ``(batch, n, m)``.
        """
        # x1: (B, N, D)
        # x2: (B, M, D)
        # Compute pairwise distances
        dist = torch.cdist(x1, x2, p=2)  # Euclidean dist

        # Fractional similarity
        # We invert it so closer = higher similarity
        # Kernel = exp( - (dist / length_scale)^(2H) )
        return torch.exp(-torch.pow(dist / self.length_scale, 2 * self.H))