"""
Example usage of the German Phoneme Pronunciation Validator.

This script demonstrates how to use the validate_phoneme() function
according to the Research Brief specification.

Usage:
    # Simplest way - copy project folder to your project directory:
    # Then add to path and import:
    #   import sys
    #   sys.path.insert(0, "path/to/german-phoneme-validator")
    #   from __init__ import validate_phoneme
    
    # If installed as package:
    python -m german_phoneme_validator.example_usage
    
    # If running from project directory:
    python example_usage.py
"""

import numpy as np
from pathlib import Path

# Import from package (works both when installed and when running from project directory)
try:
    # Try importing as installed package (recommended)
    from german_phoneme_validator import validate_phoneme, PhonemeValidator
except ImportError:
    # Fallback: import from local package (when running from project directory)
    try:
        from __init__ import validate_phoneme, PhonemeValidator
    except ImportError:
        # Last resort: direct import (for development)
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from core.validator import validate_phoneme, PhonemeValidator


def example_1_numpy_array():
    """Example 1: Using numpy array"""
    print("=" * 60)
    print("Example 1: Using numpy array")
    print("=" * 60)
    
    # Create dummy audio (3 seconds at 16kHz)
    audio_array = np.random.randn(3 * 16000).astype(np.float32)
    
    result = validate_phoneme(
        audio=audio_array,
        phoneme="/b/",
        position_ms=1500.0,
        expected_phoneme="/b/"
    )
    
    print(f"Result: {result}")
    print(f"Correct: {result['is_correct']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Explanation: {result['explanation']}")
    print()


def example_2_wav_file():
    """Example 2: Using WAV file"""
    print("=" * 60)
    print("Example 2: Using WAV file")
    print("=" * 60)
    
    # Replace with actual audio file path
    audio_path = "path/to/your/audio.wav"
    
    if not Path(audio_path).exists():
        print(f"Audio file not found: {audio_path}")
        print("Please update audio_path with a valid WAV file path.")
        print()
        return
    
    result = validate_phoneme(
        audio=audio_path,
        phoneme="/p/",
        position_ms=1200.0,
        expected_phoneme="/b/"
    )
    
    print(f"Result: {result}")
    print(f"Correct: {result['is_correct']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Explanation: {result['explanation']}")
    print()


def example_3_validator_class():
    """Example 3: Using PhonemeValidator class"""
    print("=" * 60)
    print("Example 3: Using PhonemeValidator class")
    print("=" * 60)
    
    # Initialize validator with custom artifacts directory (optional)
    # validator = PhonemeValidator(artifacts_dir=Path("path/to/artifacts"))
    validator = PhonemeValidator()
    
    # Get available phoneme pairs
    available_pairs = validator.get_available_pairs()
    print(f"Available phoneme pairs: {available_pairs}")
    print()
    
    if len(available_pairs) == 0:
        print("No trained models found. Models will be downloaded from Hugging Face Hub on first use.")
        print("If you have a local artifacts/ directory, it will be used instead.")
        print()
        return
    
    # Validate phoneme
    audio_array = np.random.randn(3 * 16000).astype(np.float32)
    
    result = validator.validate_phoneme(
        audio=audio_array,
        phoneme="/b/",
        position_ms=1500.0,
        expected_phoneme="/b/"
    )
    
    print(f"Result: {result}")
    print(f"Correct: {result['is_correct']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Explanation: {result['explanation']}")
    print()


def example_4_error_handling():
    """Example 4: Error handling"""
    print("=" * 60)
    print("Example 4: Error handling")
    print("=" * 60)
    
    # Example with invalid position
    audio_array = np.random.randn(3 * 16000).astype(np.float32)
    
    result = validate_phoneme(
        audio=audio_array,
        phoneme="/b/",
        position_ms=50000.0,  # Out of bounds
        expected_phoneme="/b/"
    )
    
    print(f"Result: {result}")
    print(f"is_correct: {result['is_correct']}")
    if 'error' in result:
        print(f"Error: {result['error']}")
    print(f"Explanation: {result['explanation']}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("German Phoneme Pronunciation Validator - Examples")
    print("=" * 60)
    print()
    
    # Run examples
    example_1_numpy_array()
    example_3_validator_class()
    example_4_error_handling()
    
    # Uncomment to run example with WAV file (requires actual file)
    # example_2_wav_file()
    
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)
