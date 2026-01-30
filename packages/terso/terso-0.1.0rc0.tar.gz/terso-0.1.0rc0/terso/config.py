"""
Terso configuration management.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Default API endpoint
DEFAULT_BASE_URL = "https://api.terso.ai"

# Config directory
CONFIG_DIR = Path.home() / ".terso"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> dict[str, Any]:
    """Load config from file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config: dict[str, Any]) -> None:
    """Save config to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_api_key() -> str | None:
    """
    Get API key from environment or config.
    
    Checks in order:
        1. TERSO_API_KEY environment variable
        2. ~/.terso/config.json
    """
    # Environment variable takes precedence
    api_key = os.environ.get("TERSO_API_KEY")
    if api_key:
        return api_key
    
    # Fall back to config file
    config = get_config()
    return config.get("api_key")


def set_api_key(api_key: str) -> None:
    """
    Save API key to config file.
    
    Args:
        api_key: Your API key from terso.ai
    """
    config = get_config()
    config["api_key"] = api_key
    save_config(config)
    print(f"API key saved to {CONFIG_FILE}")


def get_base_url() -> str:
    """Get API base URL."""
    return os.environ.get("TERSO_API_URL", DEFAULT_BASE_URL)


def get_dataset_path(name: str) -> Path:
    """Get local path for a dataset."""
    return CONFIG_DIR / "datasets" / name


# Dataset registry
DATASETS = {
    "kitchen-v1": {
        "name": "kitchen-v1",
        "description": "Kitchen manipulation tasks (cooking, prep, plating)",
        "tasks": ["crack_egg", "pour_liquid", "chop_vegetable", "stir_pot", "plate_food"],
        "status": "coming_soon",
    },
    "barista-v1": {
        "name": "barista-v1", 
        "description": "Barista tasks (espresso, latte art, pour-over)",
        "tasks": ["pull_espresso", "steam_milk", "pour_latte_art", "pour_over", "tamp_grounds"],
        "status": "coming_soon",
    },
}


def list_datasets() -> dict[str, dict]:
    """
    List available datasets.
    
    Returns:
        Dict of dataset name -> metadata
        
    Example:
        from terso import list_datasets
        for name, info in list_datasets().items():
            print(f"{name}: {info['description']}")
    """
    # Try to fetch from API
    try:
        import requests
        response = requests.get(
            f"{get_base_url()}/datasets",
            timeout=5,
            headers={"x-api-key": get_api_key()} if get_api_key() else {},
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return {d["name"]: d for d in data}
            return data
    except Exception:
        pass
    
    # Fall back to local registry
    return DATASETS
