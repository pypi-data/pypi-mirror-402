try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def get_device():
    """Identify the best available device (CUDA, MPS, or CPU)."""
    if not HAS_TORCH:
        return "cpu"
    
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"

DEVICE = get_device()
