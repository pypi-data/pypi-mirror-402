"""
Phoneme validation module using trained models.

Models are automatically downloaded from Hugging Face Hub on first use.
See core/downloader.py for download implementation details.

Adapted from gradio_modules/phoneme_validator.py for standalone use.
"""

import torch
import torch.nn as nn
import numpy as np
import librosa
import joblib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
import sys
import threading
import urllib.request
import urllib.error
import tarfile
import shutil
import os
warnings.filterwarnings('ignore')

# For finding artifacts in installed package
try:
    from importlib import resources
    # Python 3.9+ uses files() API
    if sys.version_info >= (3, 9):
        _has_files_api = True
    else:
        _has_files_api = False
except ImportError:
    _has_files_api = False

from .models import HybridCNNMLP_V4_3
from .feature_extraction import (
    extract_all_features,
    extract_spectrogram_window,
    SAMPLE_RATE,
    HOP_LENGTH,
    SPECTROGRAM_WINDOW_MS,
    N_MELS
)


# Class mapping for all phoneme pairs
# Based on LabelEncoder's lexicographic ordering used during training
# Format: {pair_name: {0: phoneme_class_0, 1: phoneme_class_1}}
CLASS_MAPPING = {
    'a-ɛ': {0: 'a', 1: 'ɛ'},
    'aː-a': {0: 'a', 1: 'aː'},  # Lexicographic: 'a' < 'aː'
    'aɪ̯-aː': {0: 'aː', 1: 'aɪ̯'},  # Lexicographic: 'aː' < 'aɪ̯'
    'aʊ̯-aː': {0: 'aː', 1: 'aʊ̯'},  # Lexicographic: 'aː' < 'aʊ̯'
    'b-p': {0: 'b', 1: 'p'},
    'd-t': {0: 'd', 1: 't'},
    'eː-ɛ': {0: 'ɛ', 1: 'eː'},  # Lexicographic: 'ɛ' < 'eː'
    'g-k': {0: 'g', 1: 'k'},  # Lexicographic: 'g' < 'k'
    'iː-ɪ': {0: 'ɪ', 1: 'iː'},  # Lexicographic: 'ɪ' < 'iː'
    'kʰ-g': {0: 'kʰ', 1: 'ɡ'},  # LabelEncoder: {'kʰ': 0, 'ɡ': 1} (note: 'g' in pair name, 'ɡ' in actual data)
    'oː-ɔ': {0: 'ɔ', 1: 'oː'},  # Lexicographic: 'ɔ' < 'oː'
    's-ʃ': {0: 's', 1: 'ʃ'},
    'ts-s': {0: 's', 1: 'ts'},  # Lexicographic: 's' < 'ts'
    'tʰ-d': {0: 'd', 1: 'tʰ'},  # Lexicographic: 'd' < 'tʰ'
    'uː-ʊ': {0: 'ʊ', 1: 'uː'},  # Lexicographic: 'ʊ' < 'uː'
    'x-k': {0: 'k', 1: 'x'},  # Lexicographic: 'k' < 'x' (CRITICAL: pair name is 'x-k' but class 0='k', class 1='x')
    'z-s': {0: 's', 1: 'z'},  # Lexicographic: 's' < 'z'
    'ç-x': {0: 'x', 1: 'ç'},  # Lexicographic: 'x' < 'ç'
    'ç-ʃ': {0: 'ç', 1: 'ʃ'},  # Lexicographic: 'ç' < 'ʃ'
    'ŋ-n': {0: 'n', 1: 'ŋ'},  # Lexicographic: 'n' < 'ŋ'
    'ə-ɛ': {0: 'ɛ', 1: 'ə'},  # Lexicographic: 'ɛ' < 'ə'
    'ʁ-ɐ': {0: 'ɐ', 1: 'ʁ'},  # Lexicographic: 'ɐ' < 'ʁ'
}

# Mapping for converting original phoneme pair name to normalized folder name
# Used for finding model folders after renaming
PHONEME_NORMALIZATION = {
    ':': 'aa',      # long vowel
    'ɪ̯': 'Ij',      # non-syllabic i
    'ʊ': 'U',       # near-close back vowel
    'ɐ': 'A',       # near-open central vowel
    'ʁ': 'R',       # voiced uvular fricative
    'ŋ': 'N',       # velar nasal
    'ə': 'schwa',   # schwa
    'ɛ': 'E',       # open-mid front vowel
    'ɔ': 'O',       # open-mid back vowel
    'ç': 'C',       # voiceless palatal fricative
    'ʃ': 'S',       # voiceless postalveolar fricative
    'ʰ': 'h',       # aspiration
    'a': 'a',
    'b': 'b',
    'd': 'd',
    'e': 'e',
    'g': 'g',
    'i': 'i',
    'k': 'k',
    'n': 'n',
    'o': 'o',
    'p': 'p',
    's': 's',
    't': 't',
    'u': 'u',
    'x': 'x',
    'z': 'z',
    'ɪ': 'I',
    'ː': 'aa',      # long vowel (additional replacement)
    '̯': '',         # non-syllabic marker - remove
}


def _normalize_phoneme_for_folder(phoneme: str) -> str:
    """
    Normalizes phoneme for use in folder name.
    Replaces IPA special characters with plain text without special characters.
    """
    result = []
    i = 0
    while i < len(phoneme):
        # Check multi-character sequences first
        found = False
        for multi_char in ['aɪ̯', 'aʊ̯', 'kʰ', 'tʰ', 'aː', 'eː', 'iː', 'oː', 'uː']:
            if phoneme[i:].startswith(multi_char):
                # Normalize each character
                for char in multi_char:
                    replacement = PHONEME_NORMALIZATION.get(char, char)
                    if replacement:  # Skip empty replacements (removed characters)
                        result.append(replacement)
                i += len(multi_char)
                found = True
                break
        
        if not found:
            char = phoneme[i]
            replacement = PHONEME_NORMALIZATION.get(char, char)
            if replacement:  # Skip empty replacements
                result.append(replacement)
            i += 1
    
    return ''.join(result)


def _phoneme_pair_to_folder_name(pair_name: str) -> str:
    """
    Converts original phoneme pair name to normalized folder name.
    
    Args:
        pair_name: Original pair name (e.g., 'x-k', 'aː-a')
        
    Returns:
        Normalized folder name (e.g., 'x-k_model', 'aaa-a_model')
    """
    parts = pair_name.split('-')
    if len(parts) != 2:
        return f"{pair_name}_model"
    
    normalized_parts = [_normalize_phoneme_for_folder(part) for part in parts]
    return f"{'-'.join(normalized_parts)}_model"


class PhonemeValidator:
    """Validator for phoneme pairs using trained models."""
    
    def __init__(self, artifacts_dir: Optional[Path] = None):
        """
        Initialize phoneme validator.
        
        Args:
            artifacts_dir: Path to artifacts directory. If None, uses default behavior:
            1. Tries to find local artifacts directory (for development)
            2. If not found, models are downloaded from Hugging Face Hub on-demand
               when _load_model() is called
        """
        if artifacts_dir is None:
            artifacts_dir = self._find_artifacts_dir()
        
        # artifacts_dir may not exist - models will be downloaded from HF Hub on-demand
        # If artifacts_dir was found (even if path doesn't exist), use it; otherwise None
        if artifacts_dir is not None:
            artifacts_dir_path = Path(artifacts_dir)
            # Only set if the path exists, otherwise set to None for HF Hub fallback
            self.artifacts_dir = artifacts_dir_path if artifacts_dir_path.exists() else None
        else:
            self.artifacts_dir = None
        self.models_cache = {}
        self.scalers_cache = {}
        self.feature_cols_cache = {}
        self.available_pairs = self._discover_phoneme_pairs()
        self.device = self._get_device()
        self.class_mapping = CLASS_MAPPING.copy()
    
    def _find_artifacts_dir(self) -> Path:
        """
        Find artifacts directory.
        
        Priority:
        1. Try to find artifacts in installed package using importlib.resources
        2. Fallback to relative paths for local development
        3. Try cache directory with downloaded artifacts (legacy GitHub Releases)
        
        Note: If no local artifacts directory is found, models will be downloaded
        from Hugging Face Hub on-demand in _load_model() via get_model_assets().
        This method is kept for backwards compatibility and local development.
        """
        # Try to find artifacts in installed package
        try:
            import german_phoneme_validator
            if _has_files_api:
                # Python 3.9+ - use files() API
                try:
                    artifacts_ref = resources.files('german_phoneme_validator') / 'artifacts'
                    if artifacts_ref.is_dir():
                        # Convert to Path object
                        artifacts_path = Path(str(artifacts_ref))
                        if artifacts_path.exists():
                            return artifacts_path
                except (ModuleNotFoundError, AttributeError, TypeError):
                    pass
            else:
                # Python < 3.9 - use path() API
                try:
                    with resources.path('german_phoneme_validator', 'artifacts') as artifacts_path:
                        artifacts_path_obj = Path(artifacts_path)
                        if artifacts_path_obj.exists():
                            return artifacts_path_obj
                except (ModuleNotFoundError, FileNotFoundError):
                    pass
        except ImportError:
            pass
        
        # Fallback: look for artifacts relative to source code (local development)
        current_dir = Path(__file__).parent.parent
        artifacts_dir = current_dir / 'artifacts'
        if artifacts_dir.exists():
            return artifacts_dir
        
        # Try parent directory
        artifacts_dir = current_dir.parent / 'artifacts'
        if artifacts_dir.exists():
            return artifacts_dir
        
        # If artifacts not found, try cache directory with downloaded artifacts
        cache_dir = self._get_cache_dir()
        cache_artifacts_dir = cache_dir / 'artifacts'
        
        if cache_artifacts_dir.exists() and any(cache_artifacts_dir.iterdir()):
            return cache_artifacts_dir
        
        # Attempt automatic download from GitHub Releases (legacy fallback)
        try:
            self._download_artifacts_from_github(cache_artifacts_dir)
            if cache_artifacts_dir.exists() and any(cache_artifacts_dir.iterdir()):
                return cache_artifacts_dir
        except Exception as e:
            # Silently fail - models will be downloaded from Hugging Face Hub on-demand
            pass
        
        # Return default path even if it doesn't exist
        # Models will be downloaded from Hugging Face Hub on-demand in _load_model()
        return current_dir / 'artifacts'
    
    def _get_cache_dir(self) -> Path:
        """Get cache directory for downloaded artifacts."""
        home = Path.home()
        cache_dir = home / '.cache' / 'german-phoneme-validator'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def _download_artifacts_from_github(self, target_dir: Path) -> None:
        """
        Download artifacts from GitHub Releases automatically.
        
        This function downloads the artifacts.tar.gz archive from the latest GitHub Release
        and extracts it to the target directory. The artifacts are cached for future use.
        
        Args:
            target_dir: Directory to extract artifacts to
        """
        # Get version to determine release tag
        try:
            import german_phoneme_validator
            version = german_phoneme_validator.__version__
        except (ImportError, AttributeError):
            version = "latest"
        
        github_repo = "SergejKurtasch/german-phoneme-validator"
        
        # Use version tag or 'latest' for GitHub Releases
        # Format: v1.0.1 -> v1.0.1, or use 'latest' for newest release
        release_tag = f"v{version}" if version != "latest" else "latest"
        
        # URL for artifacts archive in GitHub Releases
        # The archive should be named 'artifacts.tar.gz' in the release assets
        artifacts_url = (
            f"https://github.com/{github_repo}/releases/download/{release_tag}/artifacts.tar.gz"
        )
        
        print(f"Artifacts not found locally. Downloading from GitHub Releases...")
        print(f"Release: {release_tag}")
        print(f"URL: {artifacts_url}")
        
        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file for download
        temp_file = target_dir.parent / 'artifacts_temp.tar.gz'
        
        try:
            # Download archive with progress
            urllib.request.urlretrieve(
                artifacts_url, 
                temp_file, 
                reporthook=self._download_progress_hook
            )
            
            # Extract archive
            print(f"Extracting artifacts to {target_dir}...")
            with tarfile.open(temp_file, 'r:gz') as tar:
                tar.extractall(path=target_dir.parent)
            
            # Verify extraction (artifacts should be in target_dir after extraction)
            if not target_dir.exists() or not any(target_dir.iterdir()):
                # If extractall created artifacts in parent, move them
                potential_artifacts = target_dir.parent / 'artifacts'
                if potential_artifacts.exists() and potential_artifacts != target_dir:
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    potential_artifacts.rename(target_dir)
            
            print(f"Artifacts successfully downloaded and extracted to: {target_dir}")
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise FileNotFoundError(
                    f"Artifacts archive not found at {artifacts_url}. "
                    f"Please ensure artifacts.tar.gz is attached to release {release_tag}."
                )
            raise
        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
    
    def _download_progress_hook(self, count: int, block_size: int, total_size: int) -> None:
        """Progress hook for download (called by urllib.request.urlretrieve)."""
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            # Print progress every 5%
            if percent % 5 == 0:
                downloaded_mb = count * block_size / (1024 * 1024)
                total_mb = total_size / (1024 * 1024) if total_size > 0 else 0
                print(f"Download progress: {percent}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)")
    
    def _get_device(self) -> str:
        """Auto-detect device."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    
    def _discover_phoneme_pairs(self) -> List[str]:
        """
        Discover available phoneme pairs from artifacts directory.
        
        Searches for folders with format {normalized_pair}_model and restores
        original pair names from config.json or uses reverse mapping.
        
        If artifacts_dir is None or doesn't exist, returns empty list.
        Models will be discovered on-demand when loaded from Hugging Face Hub.
        """
        pairs = []
        if self.artifacts_dir is None or not self.artifacts_dir.exists():
            return pairs
        
        # Create reverse mapping: normalized name -> original name
        normalized_to_original = {}
        for original_pair in CLASS_MAPPING.keys():
            normalized_folder = _phoneme_pair_to_folder_name(original_pair)
            normalized_to_original[normalized_folder] = original_pair
        
        for item in self.artifacts_dir.iterdir():
            if item.is_dir() and item.name.endswith('_model'):
                # Try to find original name through reverse mapping
                original_pair = normalized_to_original.get(item.name)
                
                # If not found in mapping, try to restore from config.json (now in folder root)
                if original_pair is None:
                    config_path = item / 'config.json'
                    if config_path.exists():
                        try:
                            with open(config_path, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                                original_pair = config.get('phoneme_pair')
                        except (json.JSONDecodeError, IOError):
                            pass
                
                # If still not found, try to restore from folder name (fallback)
                if original_pair is None:
                    # This should not happen, but in case config.json is missing
                    continue
                
                # Check model presence (now in folder root)
                model_path = item / 'best_model.pt'
                if model_path.exists() and original_pair:
                    pairs.append(original_pair)
        
        return sorted(pairs)
    
    def _normalize_feature_vector(self, vector: np.ndarray, expected_size: int) -> np.ndarray:
        """
        Normalize feature vector to expected size (trim or pad as needed).
        
        Args:
            vector: Feature vector as numpy array
            expected_size: Expected size of the vector
            
        Returns:
            Normalized feature vector with exactly expected_size elements
        """
        if len(vector) > expected_size:
            return vector[:expected_size]
        elif len(vector) < expected_size:
            return np.pad(vector, (0, expected_size - len(vector)), 'constant')
        return vector
    
    def get_phoneme_pair(self, phoneme1: str, phoneme2: str) -> Optional[str]:
        """
        Determine phoneme pair from two phonemes.
        
        Args:
            phoneme1: First phoneme (expected)
            phoneme2: Second phoneme (recognized/suspected)
            
        Returns:
            Pair name (e.g., 'b-p') or None if not found
        """
        # Normalize phonemes
        p1 = phoneme1.strip().lower()
        p2 = phoneme2.strip().lower()
        
        # If phonemes are the same, check if phoneme is part of any available pair
        if p1 == p2:
            for pair in self.available_pairs:
                pair_phonemes = pair.split('-')
                if len(pair_phonemes) == 2:
                    pair_p1 = pair_phonemes[0].strip().lower()
                    pair_p2 = pair_phonemes[1].strip().lower()
                    if p1 == pair_p1 or p1 == pair_p2:
                        return pair
            return None
        
        # Try both orders
        pair1 = f"{p1}-{p2}"
        pair2 = f"{p2}-{p1}"
        
        if pair1 in self.available_pairs:
            return pair1
        elif pair2 in self.available_pairs:
            return pair2
        
        return None
    
    def _load_model(self, phoneme_pair: str) -> Optional[Tuple[nn.Module, Any, List[str]]]:
        """
        Load model, scaler, and feature columns for a phoneme pair.
        
        Priority:
        1. Check cache
        2. Try local artifacts_dir (if set and folder exists)
        3. Download from Hugging Face Hub via get_model_assets()
        
        Args:
            phoneme_pair: Phoneme pair name (e.g., 'b-p')
            
        Returns:
            Tuple of (model, scaler, feature_cols) or None if failed
        """
        if phoneme_pair in self.models_cache:
            return self.models_cache[phoneme_pair]
        
        # Convert original pair name to folder name
        folder_name = _phoneme_pair_to_folder_name(phoneme_pair)
        
        # Try local artifacts_dir first (for development/backwards compatibility)
        model_dir = None
        if self.artifacts_dir and (self.artifacts_dir / folder_name).exists():
            model_dir = self.artifacts_dir / folder_name
        else:
            # Fallback: download from Hugging Face Hub
            try:
                from .downloader import get_model_assets
                model_dir = get_model_assets(phoneme_pair)
            except Exception as e:
                warnings.warn(
                    f"Failed to load model from Hugging Face Hub for pair '{phoneme_pair}': {e}. "
                    f"Make sure huggingface_hub is installed and internet connection is available."
                )
                return None
        
        if model_dir is None or not model_dir.exists():
            return None
        
        try:
            # Load model (files are now directly in the model folder root)
            model_path = model_dir / 'best_model.pt'
            if not model_path.exists():
                return None
            
            checkpoint = torch.load(model_path, map_location=self.device)
            
            # Load config to get n_features (config.json is now in the model folder root)
            config_path = model_dir / 'config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    n_features = config.get('n_features', 129)
            else:
                n_features = 129  # Default
            
            # Create model
            model = HybridCNNMLP_V4_3(n_features=n_features, num_classes=2)
            model.load_state_dict(checkpoint['model_state_dict'])
            model.to(self.device)
            model.eval()
            
            # Load scaler
            scaler_path = model_dir / 'feature_scaler.joblib'
            scaler = None
            if scaler_path.exists():
                scaler = joblib.load(scaler_path)
            
            # Load feature columns
            feature_cols_path = model_dir / 'feature_cols.json'
            feature_cols = []
            if feature_cols_path.exists():
                with open(feature_cols_path, 'r') as f:
                    feature_cols = json.load(f)
            
            # Exclude metadata columns
            metadata_cols = ['phoneme_id', 'class', 'duration_ms', 'phoneme', 'utterance_id', 
                           'duration_ms_features', 'start_ms', 'end_ms', 'split', 'class_encoded']
            feature_cols = [col for col in feature_cols if col not in metadata_cols]
            
            # Trim to n_features if needed
            if len(feature_cols) > n_features:
                feature_cols = feature_cols[:n_features]
            
            result = (model, scaler, feature_cols)
            self.models_cache[phoneme_pair] = result
            return result
            
        except (FileNotFoundError, IOError) as e:
            print(f"File not found error loading model for {phoneme_pair}: {e}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing config/data for {phoneme_pair}: {e}")
            return None
        except (RuntimeError, ValueError) as e:
            print(f"Error loading model state for {phoneme_pair}: {e}")
            return None
        except Exception as e:
            import traceback
            print(f"Unexpected error loading model for {phoneme_pair}: {e}")
            print(traceback.format_exc())
            return None
    
    def _get_class_mapping(self, phoneme_pair: str) -> Dict[int, str]:
        """
        Get class-to-phoneme mapping for a phoneme pair.
        
        CRITICAL: This method ensures correct mapping between model output classes (0/1)
        and actual phonemes, preventing false phoneme substitution.
        
        The mapping is based on LabelEncoder's lexicographic ordering used during training.
        For example, for pair 'x-k', LabelEncoder gives {'k': 0, 'x': 1} (lexicographic: 'k' < 'x'),
        so class 0 = 'k', class 1 = 'x', regardless of pair name order.
        
        Args:
            phoneme_pair: Phoneme pair name (e.g., 'b-p' or 'x-k')
            
        Returns:
            Dictionary mapping class index (0 or 1) to phoneme string
        """
        # First, try to get from hardcoded mapping (extracted from training notebooks)
        if phoneme_pair in self.class_mapping:
            return self.class_mapping[phoneme_pair]
        
        # Fallback: use lexicographic ordering (same as LabelEncoder)
        # This handles any new pairs that might be added in the future
        phonemes = phoneme_pair.split('-')
        if len(phonemes) != 2:
            raise ValueError(f"Invalid phoneme pair format: {phoneme_pair}")
        
        # Sort lexicographically (same as LabelEncoder during training)
        sorted_phonemes = sorted(phonemes)
        
        # Create mapping: class 0 = first lexicographically, class 1 = second
        mapping = {0: sorted_phonemes[0], 1: sorted_phonemes[1]}
        
        # Cache it for future use
        self.class_mapping[phoneme_pair] = mapping
        
        return mapping
    
    def extract_audio_segment(
        self,
        audio: np.ndarray,
        start_ms: float,
        end_ms: float,
        sr: int = SAMPLE_RATE,
        context_ms: float = 100.0
    ) -> np.ndarray:
        """
        Extract audio segment with context.
        
        Args:
            audio: Full audio array
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds
            sr: Sample rate
            context_ms: Context to add before and after (milliseconds)
            
        Returns:
            Audio segment with context
        """
        start_sample = max(0, int((start_ms - context_ms) / 1000 * sr))
        end_sample = min(len(audio), int((end_ms + context_ms) / 1000 * sr))
        return audio[start_sample:end_sample]
    
    def validate_phoneme_segment(
        self,
        audio_segment: np.ndarray,
        phoneme_pair: str,
        expected_phoneme: str,
        suspected_phoneme: Optional[str] = None,
        sr: int = SAMPLE_RATE,
        is_missing: bool = False
    ) -> Dict[str, Any]:
        """
        Validate phoneme segment using trained model.
        
        Args:
            audio_segment: Audio segment (numpy array)
            phoneme_pair: Phoneme pair name (e.g., 'b-p')
            expected_phoneme: Expected correct phoneme
            suspected_phoneme: Suspected phoneme (if different from expected)
            sr: Sample rate
            is_missing: Whether the phoneme is marked as missing
            
        Returns:
            Dictionary with validation results
        """
        # Handle missing phonemes
        if is_missing:
            return {
                'expected_phoneme': expected_phoneme,
                'recognized_phoneme': suspected_phoneme,
                'is_correct': False,
                'confidence': 0.0,
                'predicted_phoneme': None,
                'probabilities': {},
                'is_missing': True
            }
        
        # Load model
        model_data = self._load_model(phoneme_pair)
        if model_data is None:
            return {
                'expected_phoneme': expected_phoneme,
                'recognized_phoneme': suspected_phoneme,
                'is_correct': None,
                'confidence': 0.0,
                'predicted_phoneme': None,
                'probabilities': {},
                'features': {},
                'error': f'Model not found for pair {phoneme_pair}'
            }
        
        model, scaler, feature_cols = model_data
        
        try:
            # Extract features directly from numpy array
            features_dict = extract_all_features(audio_segment, sr=sr, phoneme_type=phoneme_pair)
            
            # Extract spectrogram directly from numpy array
            spectrogram = extract_spectrogram_window(
                audio_segment,
                target_duration_ms=SPECTROGRAM_WINDOW_MS,
                sr=sr,
                n_mels=N_MELS,
                hop_length=HOP_LENGTH
            )
            
            if features_dict is None or spectrogram is None:
                return {
                    'is_correct': None,
                    'confidence': 0.0,
                    'predicted_phoneme': None,
                    'probabilities': {},
                    'features': {},
                    'error': 'Failed to extract features'
                }
            
            # Prepare features vector
            # First, flatten all array features in features_dict
            flattened_features = {}
            for key, val in features_dict.items():
                if isinstance(val, np.ndarray):
                    # Flatten array features and create multiple keys
                    for i, v in enumerate(val.flatten()):
                        # Only convert numeric values to float
                        if isinstance(v, (int, float, np.number)):
                            flattened_features[f"{key}_{i}"] = float(v)
                        else:
                            # Skip non-numeric values or convert to 0.0
                            flattened_features[f"{key}_{i}"] = 0.0
                else:
                    # Only convert numeric values to float
                    if isinstance(val, (int, float, np.number)):
                        flattened_features[key] = float(val)
                    else:
                        # Skip non-numeric values or convert to 0.0
                        flattened_features[key] = 0.0
            
            # Now build features_vector from feature_cols
            features_vector = []
            for col in feature_cols:
                if col in flattened_features:
                    features_vector.append(flattened_features[col])
                else:
                    features_vector.append(0.0)
            
            features_vector = np.array(features_vector, dtype=np.float32)
            
            # Prepare spectrogram
            if len(spectrogram.shape) == 2:
                spectrogram = np.expand_dims(spectrogram, axis=0)
            
            spectrogram = spectrogram.astype(np.float32)
            
            # Normalize features
            if scaler is not None:
                # Ensure features_vector matches scaler's expected input size
                if hasattr(scaler, 'n_features_in_'):
                    features_vector = self._normalize_feature_vector(features_vector, scaler.n_features_in_)
                
                features_vector = scaler.transform([features_vector])[0]
                
                # Ensure features_vector matches model's n_features
                if hasattr(model, 'n_features'):
                    features_vector = self._normalize_feature_vector(features_vector, model.n_features)
                
                features_vector = features_vector.astype(np.float32)
            
            # Convert to tensors
            spectrogram_tensor = torch.from_numpy(spectrogram).unsqueeze(0).to(self.device)
            features_tensor = torch.from_numpy(features_vector).unsqueeze(0).to(self.device)
            
            # Predict
            with torch.no_grad():
                logits = model((spectrogram_tensor, features_tensor))
                probabilities = torch.softmax(logits, dim=-1)[0]
                predicted_class = torch.argmax(logits, dim=-1)[0].item()
            
            # Get correct class-to-phoneme mapping (using lexicographic order like LabelEncoder)
            class_mapping = self._get_class_mapping(phoneme_pair)
            predicted_phoneme = class_mapping.get(predicted_class, None)
            
            # Normalize phonemes for comparison (handle 'g' vs 'ɡ' and other variations)
            def normalize_for_comparison(ph: str) -> str:
                """Normalize phoneme for comparison, handling common variations."""
                ph = ph.strip().lower()
                # Map common variations
                variations = {
                    'g': 'ɡ',  # Latin g -> IPA ɡ
                }
                return variations.get(ph, ph)
            
            # Check if correct (with normalization)
            expected_normalized = normalize_for_comparison(expected_phoneme) if expected_phoneme else None
            predicted_normalized = normalize_for_comparison(predicted_phoneme) if predicted_phoneme else None
            is_correct = (predicted_normalized == expected_normalized) if (predicted_normalized and expected_normalized) else None
            confidence = float(probabilities[predicted_class])
            
            # Get probabilities for both classes using correct mapping
            prob_dict = {}
            for class_idx, phoneme in class_mapping.items():
                if class_idx < len(probabilities):
                    prob_dict[phoneme] = float(probabilities[class_idx])
            
            result = {
                'expected_phoneme': expected_phoneme,
                'recognized_phoneme': suspected_phoneme,
                'is_correct': is_correct,
                'confidence': confidence,
                'predicted_phoneme': predicted_phoneme,
                'probabilities': prob_dict,
                'features': features_dict,
                'is_missing': False
            }
            
            return result
            
        except (ValueError, RuntimeError) as e:
            # Shape mismatches, tensor errors, etc.
            return {
                'expected_phoneme': expected_phoneme,
                'recognized_phoneme': suspected_phoneme,
                'is_correct': None,
                'confidence': 0.0,
                'predicted_phoneme': None,
                'probabilities': {},
                'features': {},
                'error': f'Model inference error: {str(e)}'
            }
        except Exception as e:
            import traceback
            return {
                'expected_phoneme': expected_phoneme,
                'recognized_phoneme': suspected_phoneme,
                'is_correct': None,
                'confidence': 0.0,
                'predicted_phoneme': None,
                'probabilities': {},
                'features': {},
                'error': f'Unexpected error: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def get_available_pairs(self) -> List[str]:
        """Get list of available phoneme pairs."""
        return self.available_pairs.copy()
    
    def has_trained_model(self, expected_phoneme: str, recognized_phoneme: str) -> bool:
        """
        Check if a trained model exists for a phoneme pair.
        
        Args:
            expected_phoneme: Expected phoneme (correct one)
            recognized_phoneme: Recognized phoneme (potentially incorrect)
            
        Returns:
            True if trained model exists for this pair, False otherwise
        """
        exp_ph = expected_phoneme.strip()
        rec_ph = recognized_phoneme.strip()
        
        if exp_ph == rec_ph:
            return False
        
        pair1 = f"{exp_ph}-{rec_ph}"
        pair2 = f"{rec_ph}-{exp_ph}"
        
        if pair1 in self.available_pairs or pair2 in self.available_pairs:
            return True
        
        return False
    
    def _normalize_phoneme_notation(self, phoneme: str) -> str:
        """
        Normalize IPA phoneme notation.
        Removes '/' brackets and converts to lowercase.
        
        Args:
            phoneme: Phoneme in IPA notation (e.g., '/b/' or 'b')
            
        Returns:
            Normalized phoneme (e.g., 'b')
        """
        phoneme = phoneme.strip()
        if phoneme.startswith('/') and phoneme.endswith('/'):
            phoneme = phoneme[1:-1]
        return phoneme.lower()
    
    def _generate_explanation(
        self,
        is_correct: Optional[bool],
        predicted_phoneme: Optional[str],
        expected_phoneme: Optional[str],
        confidence: float,
        probabilities: Dict[str, float]
    ) -> str:
        """
        Generate human-readable explanation of the validation result.
        """
        if predicted_phoneme is None:
            return (
                "Unable to predict phoneme. The model could not determine the phoneme "
                "from the acoustic features."
            )
        
        if expected_phoneme is None:
            return (
                f"The model predicted phoneme '{predicted_phoneme}' "
                f"with {confidence:.1%} confidence. "
                f"Probabilities: {', '.join([f'{k}={v:.1%}' for k, v in probabilities.items()])}."
            )
        
        if is_correct is None:
            return (
                f"Validation result unclear. The model predicted '{predicted_phoneme}' "
                f"(expected '{expected_phoneme}') with {confidence:.1%} confidence. "
                f"Probabilities: {', '.join([f'{k}={v:.1%}' for k, v in probabilities.items()])}."
            )
        
        if is_correct:
            return (
                f"Correct pronunciation detected. The model identified phoneme '{predicted_phoneme}' "
                f"(expected '{expected_phoneme}') with {confidence:.1%} confidence. "
                f"The acoustic features match the expected phoneme."
            )
        else:
            return (
                f"Incorrect pronunciation detected. The model predicted '{predicted_phoneme}' "
                f"but expected '{expected_phoneme}'. Confidence: {confidence:.1%}. "
                f"Probabilities: {', '.join([f'{k}={v:.1%}' for k, v in probabilities.items()])}. "
                f"The acoustic features suggest a different phoneme than expected."
            )
    
    def validate_phoneme(
        self,
        audio: Union[str, Path, np.ndarray],
        phoneme: str,
        position_ms: float,
        expected_phoneme: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate phoneme pronunciation according to Research Brief specification.
        
        This is the main API function that matches the documentation requirements.
        
        Args:
            audio: Audio segment - can be:
                - Path to WAV file (str or Path)
                - numpy array of audio samples (16kHz, mono)
            phoneme: Target phoneme in IPA notation (e.g., '/b/' or 'b')
            position_ms: Timestamp in milliseconds indicating where the phoneme occurs
            expected_phoneme: Expected correct phoneme in IPA notation (optional)
            
        Returns:
            Dictionary with validation results:
            {
                'is_correct': bool,
                'confidence': float (0-1),
                'features': dict,
                'explanation': str
            }
        """
        try:
            # Normalize phoneme notation
            phoneme_normalized = self._normalize_phoneme_notation(phoneme)
            expected_phoneme_normalized = None
            if expected_phoneme is not None:
                expected_phoneme_normalized = self._normalize_phoneme_notation(expected_phoneme)
            
            # Load audio if it's a file path
            if isinstance(audio, (str, Path)):
                audio_path = Path(audio)
                if not audio_path.exists():
                    return {
                        'is_correct': None,
                        'confidence': 0.0,
                        'features': {},
                        'explanation': f'Audio file not found: {audio_path}',
                        'error': f'File not found: {audio_path}'
                    }
                
                audio_array, sr = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
                
                if sr != SAMPLE_RATE:
                    audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=SAMPLE_RATE)
                    sr = SAMPLE_RATE
            elif isinstance(audio, np.ndarray):
                audio_array = audio.copy()
                sr = SAMPLE_RATE
            else:
                return {
                    'is_correct': None,
                    'confidence': 0.0,
                    'features': {},
                    'explanation': f'Unsupported audio type: {type(audio)}. Expected str, Path, or numpy.ndarray.',
                    'error': f'Unsupported audio type: {type(audio)}'
                }
            
            # Validate audio duration (3-5 seconds as per spec)
            duration_ms = len(audio_array) / sr * 1000
            
            # Validate position_ms is within audio bounds
            if position_ms < 0 or position_ms > duration_ms:
                return {
                    'is_correct': None,
                    'confidence': 0.0,
                    'features': {},
                    'explanation': f'Position {position_ms}ms is outside audio bounds (0-{duration_ms:.1f}ms)',
                    'error': f'Position out of bounds: {position_ms}ms'
                }
            
            # Extract audio segment around position_ms
            window_ms = 220.0  # Default window size
            start_ms = max(0, position_ms - window_ms)
            end_ms = min(duration_ms, position_ms + window_ms)
            
            audio_segment = self.extract_audio_segment(
                audio_array,
                start_ms,
                end_ms,
                sr=sr,
                context_ms=0
            )
            
            # Determine phoneme pair
            if expected_phoneme_normalized is None:
                expected_phoneme_normalized = phoneme_normalized
            
            phoneme_pair = self.get_phoneme_pair(
                expected_phoneme_normalized,
                phoneme_normalized
            )
            
            if phoneme_pair is None:
                return {
                    'is_correct': None,
                    'confidence': 0.0,
                    'features': {},
                    'explanation': (
                        f'No model available for phoneme pair involving '
                        f'"{phoneme_normalized}" and "{expected_phoneme_normalized}". '
                        f'Available pairs: {", ".join(self.available_pairs)}.'
                    ),
                    'error': f'No model for phoneme pair'
                }
            
            # Validate using existing method
            validation_result = self.validate_phoneme_segment(
                audio_segment,
                phoneme_pair,
                expected_phoneme_normalized,
                suspected_phoneme=phoneme_normalized,
                sr=sr
            )
            
            # Extract features if available
            features = validation_result.get('features', {})
            
            # Generate explanation
            explanation = self._generate_explanation(
                validation_result.get('is_correct'),
                validation_result.get('predicted_phoneme'),
                expected_phoneme_normalized,
                validation_result.get('confidence', 0.0),
                validation_result.get('probabilities', {})
            )
            
            # Format result according to specification
            result = {
                'is_correct': validation_result.get('is_correct'),
                'confidence': validation_result.get('confidence', 0.0),
                'features': features,
                'explanation': explanation
            }
            
            # Add error if present
            if 'error' in validation_result:
                result['error'] = validation_result['error']
            
            return result
            
        except (FileNotFoundError, IOError) as e:
            return {
                'is_correct': None,
                'confidence': 0.0,
                'features': {},
                'explanation': f'File error: {str(e)}',
                'error': str(e)
            }
        except ValueError as e:
            return {
                'is_correct': None,
                'confidence': 0.0,
                'features': {},
                'explanation': f'Invalid input: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            import traceback
            return {
                'is_correct': None,
                'confidence': 0.0,
                'features': {},
                'explanation': f'Error during validation: {str(e)}',
                'error': str(e),
                'traceback': traceback.format_exc()
            }


# Thread-local storage for validator instances (thread-safe)
_validator_storage = threading.local()


def get_validator(artifacts_dir: Optional[Path] = None) -> PhonemeValidator:
    """Get or create thread-local validator instance (thread-safe)."""
    if not hasattr(_validator_storage, 'validator') or _validator_storage.validator is None:
        _validator_storage.validator = PhonemeValidator(artifacts_dir=artifacts_dir)
    return _validator_storage.validator


def validate_phoneme(
    audio: Union[str, Path, np.ndarray],
    phoneme: str,
    position_ms: float,
    expected_phoneme: Optional[str] = None,
    artifacts_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Standalone function for phoneme validation (matches Research Brief specification).
    
    This is a convenience wrapper around PhonemeValidator.validate_phoneme().
    
    Args:
        audio: Audio segment - can be path to WAV file (str/Path) or numpy array (16kHz, mono)
        phoneme: Target phoneme in IPA notation (e.g., '/b/' or 'b')
        position_ms: Timestamp in milliseconds indicating where the phoneme occurs
        expected_phoneme: Expected correct phoneme in IPA notation (optional)
        artifacts_dir: Path to artifacts directory (optional, uses default if None)
        
    Returns:
        Dictionary with validation results:
        {
            'is_correct': bool,
            'confidence': float (0-1),
            'features': dict,
            'explanation': str
        }
    """
    validator = get_validator(artifacts_dir=artifacts_dir)
    return validator.validate_phoneme(audio, phoneme, position_ms, expected_phoneme)

