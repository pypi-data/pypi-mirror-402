"""
Terso - Egocentric manipulation video datasets for physical AI.

Install with full dependencies for local dataset loading:
    pip install terso[full]

Basic usage (API only):
    from terso import Client
    
    client = Client(api_key="your-key")
    client.upload("video.mp4", task="pour_latte")

Full usage (with datasets):
    from terso import load_dataset
    
    dataset = load_dataset("kitchen-v1")
    for sample in dataset:
        print(sample.hand_poses.shape)
"""

__version__ = "0.1.0rc"
__all__ = [
    # Core
    "Client",
    "upload",
    "download",
    # Datasets (require terso[full])
    "load_dataset",
    "list_datasets",
    # Config
    "set_api_key",
    "get_api_key",
]

from terso.client import Client, upload, download
from terso.config import set_api_key, get_api_key, list_datasets


def load_dataset(name: str, split: str = "train", **kwargs):
    """
    Load a Terso dataset.
    
    Requires: pip install terso[full]
    
    Args:
        name: Dataset name (e.g., "kitchen-v1")
        split: Which split to load ("train", "val", "test")
        **kwargs: Additional arguments passed to ManipulationDataset
        
    Returns:
        ManipulationDataset instance
        
    Example:
        dataset = load_dataset("kitchen-v1", split="train")
        for sample in dataset:
            print(sample.frames.shape)  # (T, H, W, 3)
    """
    try:
        from terso.datasets import ManipulationDataset
    except ImportError as e:
        raise ImportError(
            "Dataset loading requires additional dependencies. "
            "Install with: pip install terso[full]"
        ) from e
    
    from terso.config import get_dataset_path
    
    path = get_dataset_path(name)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset '{name}' not found at {path}. "
            f"Download it first with: terso download {name}"
        )
    
    return ManipulationDataset(root=path, split=split, **kwargs)
