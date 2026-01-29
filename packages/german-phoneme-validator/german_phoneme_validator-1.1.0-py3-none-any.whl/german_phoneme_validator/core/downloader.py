"""
Module for downloading model assets from Hugging Face Hub.

Provides functionality to download and cache phoneme validation models from
Hugging Face Hub, with automatic update checking via ETag.
"""

import warnings
from pathlib import Path
from typing import Optional

try:
    from huggingface_hub import snapshot_download
except ImportError:
    snapshot_download = None
    warnings.warn(
        "huggingface_hub is not installed. Model downloads from Hugging Face Hub will not work. "
        "Install it with: pip install huggingface_hub",
        ImportWarning
    )

# Default repository ID for phoneme models
DEFAULT_REPO_ID = "SergejKurtasch/german-phoneme-models"


def _phoneme_pair_to_folder_name(pair_name: str) -> str:
    """
    Converts original phoneme pair name to normalized folder name.
    
    This function mirrors the logic from validator.py to ensure consistency.
    
    Args:
        pair_name: Original pair name (e.g., 'x-k', 'aː-a')
        
    Returns:
        Normalized folder name (e.g., 'x-k_model', 'aaa-a_model')
    """
    # Import here to avoid circular dependencies
    from .validator import _phoneme_pair_to_folder_name as _normalize_pair
    return _normalize_pair(pair_name)


def get_model_assets(
    phoneme_pair: str,
    repo_id: str = DEFAULT_REPO_ID,
    local_files_only: bool = False
) -> Path:
    """
    Download or retrieve model assets for a specific phoneme pair from Hugging Face Hub.
    
    This function uses snapshot_download from huggingface_hub to download model files.
    With local_files_only=False (default), it checks for updates via ETag without
    re-downloading unchanged files.
    
    Args:
        phoneme_pair: Phoneme pair name (e.g., 'b-p', 'a-ɛ')
        repo_id: Hugging Face repository ID (default: "SergejKurtasch/german-phoneme-models")
        local_files_only: If True, only use cached files. If False, check for updates (default: False)
        
    Returns:
        Path to the local directory containing the model assets
        
    Raises:
        ImportError: If huggingface_hub is not installed
        FileNotFoundError: If the model folder is not found in the repository
        Exception: For other download/access errors
        
    Example:
        >>> model_dir = get_model_assets('b-p')
        >>> model_path = model_dir / 'best_model.pt'
    """
    if snapshot_download is None:
        raise ImportError(
            "huggingface_hub is required for downloading models. "
            "Install it with: pip install huggingface_hub"
        )
    
    # Normalize phoneme pair to folder name
    folder_name = _phoneme_pair_to_folder_name(phoneme_pair)
    
    try:
        # Download or retrieve cached model folder
        # allow_patterns ensures we only download the specific model folder
        cache_dir = snapshot_download(
            repo_id=repo_id,
            allow_patterns=f"{folder_name}/*",
            local_files_only=local_files_only,
            repo_type="model"
        )
        
        # Return path to the specific model folder
        model_dir = Path(cache_dir) / folder_name
        
        if not model_dir.exists():
            raise FileNotFoundError(
                f"Model folder '{folder_name}' not found in repository '{repo_id}' "
                f"or cache directory '{cache_dir}'"
            )
        
        return model_dir
        
    except Exception as e:
        error_msg = (
            f"Failed to download model assets for phoneme pair '{phoneme_pair}' "
            f"from repository '{repo_id}': {str(e)}"
        )
        
        if local_files_only:
            error_msg += (
                "\nHint: Set local_files_only=False to allow downloading from Hugging Face Hub."
            )
        
        raise Exception(error_msg) from e


def get_all_model_assets(
    repo_id: str = DEFAULT_REPO_ID,
    local_files_only: bool = False
) -> Path:
    """
    Download or retrieve all model assets from Hugging Face Hub.
    
    Args:
        repo_id: Hugging Face repository ID (default: "SergejKurtasch/german-phoneme-models")
        local_files_only: If True, only use cached files. If False, check for updates (default: False)
        
    Returns:
        Path to the local directory containing all model assets
        
    Raises:
        ImportError: If huggingface_hub is not installed
        Exception: For other download/access errors
    """
    if snapshot_download is None:
        raise ImportError(
            "huggingface_hub is required for downloading models. "
            "Install it with: pip install huggingface_hub"
        )
    
    try:
        # Download or retrieve cached repository
        cache_dir = snapshot_download(
            repo_id=repo_id,
            local_files_only=local_files_only,
            repo_type="model"
        )
        
        return Path(cache_dir)
        
    except Exception as e:
        error_msg = (
            f"Failed to download all model assets from repository '{repo_id}': {str(e)}"
        )
        
        if local_files_only:
            error_msg += (
                "\nHint: Set local_files_only=False to allow downloading from Hugging Face Hub."
            )
        
        raise Exception(error_msg) from e
