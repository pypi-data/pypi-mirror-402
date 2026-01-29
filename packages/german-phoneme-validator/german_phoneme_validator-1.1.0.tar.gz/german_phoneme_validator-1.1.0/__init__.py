"""
German Phoneme Pronunciation Validator

A production-ready Python module for acoustic validation of German phoneme pronunciation.
Implements the Research Brief specification for L2 German pronunciation assessment.
"""

from .core.validator import validate_phoneme, PhonemeValidator, get_validator
from .core.feature_extraction import (
    extract_all_features,
    extract_spectrogram_window,
    SAMPLE_RATE,
    HOP_LENGTH,
    SPECTROGRAM_WINDOW_MS,
    N_MELS
)

__version__ = "1.1.0"
__all__ = [
    'validate_phoneme',
    'PhonemeValidator',
    'get_validator',
    'extract_all_features',
    'extract_spectrogram_window',
    'SAMPLE_RATE',
    'HOP_LENGTH',
    'SPECTROGRAM_WINDOW_MS',
    'N_MELS'
]

