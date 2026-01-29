import torch

def get_fgn_autocovariance(
    n: int, 
    H: float, 
    device="cpu", 
    dtype=torch.float32
) -> torch.Tensor:
    """
    Computes the first row of the Toeplitz covariance matrix for fGN.
    gamma(k) = 0.5 * (|k+1|^2H - 2|k|^2H + |k-1|^2H)
    """
    k = torch.arange(n, device=device, dtype=dtype)
    return 0.5 * (torch.abs(k + 1)**(2 * H) - 2 * torch.abs(k)**(2 * H) + torch.abs(k - 1)**(2 * H))

def get_fgn_covariance_matrix(
    n: int, 
    H: float, 
    device="cpu", 
    dtype=torch.float32
) -> torch.Tensor:
    """
    Constructs the full symmetric Toeplitz Covariance Matrix for fGN.
    Shape: (n, n)
    """
    # 1. Get the first row (Autocovariance)
    gamma = get_fgn_autocovariance(n, H, device, dtype)
    
    # 2. Use the Broadcasting Trick (No Loops)
    # This creates the indices |i - j| efficiently
    idx = torch.arange(n, device=device)
    lhs = idx.unsqueeze(0)  # (1, n)
    rhs = idx.unsqueeze(1)  # (n, 1)
    
    # "distance_matrix" contains the lag k for every entry (i, j)
    distance_matrix = torch.abs(lhs - rhs)
    
    # 3. Map gamma values to the matrix
    # PyTorch advanced indexing handles this instantly
    return gamma[distance_matrix]

def get_cholesky_factor(
    n: int, 
    H: float, 
    device="cpu", 
    dtype=torch.float32,
    jitter: float = 1e-6
) -> torch.Tensor:
    """
    Returns the Lower Triangular Matrix L such that Sigma = L @ L.T.
    Useful for checking numerical stability or manual noise generation.
    """
    sigma = get_fgn_covariance_matrix(n, H, device, dtype)
    
    # Add jitter for numerical stability (Conditioning)
    eye = torch.eye(n, device=device, dtype=dtype)
    
    try:
        L = torch.linalg.cholesky(sigma + jitter * eye)
    except RuntimeError:
        # Fallback for higher jitter if matrix is nearly singular (common when H -> 1.0)
        L = torch.linalg.cholesky(sigma + jitter * 10 * eye)
        
    return L