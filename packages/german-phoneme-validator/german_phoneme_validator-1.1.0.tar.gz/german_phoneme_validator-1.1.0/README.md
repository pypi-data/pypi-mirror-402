# German Phoneme Pronunciation Validator

A production-ready Python module for acoustic validation of German phoneme pronunciation. This module implements the Research Brief specification for L2 German pronunciation assessment.

## Overview

This module provides acoustic feature-based validation to confirm whether a German phoneme was pronounced correctly by a second language learner, using only acoustic evidence from the audio signal.

## Installation

### Prerequisites

- Python 3.8 or higher
- PyTorch 2.0+ (install via conda recommended for better compatibility)

### Install from Local Directory (Development)

If you have the source code locally:

```bash
cd german-phoneme-validator
pip install -e .
```

This installs the package in editable mode, so changes to the source code are immediately available.

### Install from GitHub

Install directly from the GitHub repository:

```bash
pip install git+https://github.com/SergejKurtasch/german-phoneme-validator.git
```

### Install via pip (if published to PyPI)

If the package is published to PyPI:

```bash
pip install german-phoneme-validator
```

### Install via conda (if available)

If a conda package is available:

```bash
conda install -c conda-forge german-phoneme-validator
```

Or if using a custom channel:

```bash
conda install -c your-channel german-phoneme-validator
```

**Note**: For best compatibility, install PyTorch via conda:
```bash
conda install pytorch torchaudio -c pytorch
```

### Optional Dependencies

For advanced formant extraction features:

```bash
pip install -e ".[optional]"
```

### Important Notes

- **Model Download**: Trained models are automatically downloaded from [Hugging Face Hub](https://huggingface.co/SergejKurtasch/german-phoneme-models) on first use. An internet connection is required for the initial download. Models are cached locally for subsequent use.

- **Local development**: If you have a local `artifacts/` directory, it will be used instead of downloading from Hugging Face Hub. This allows for offline development and testing.

- **Dependencies only**: If you only want to install dependencies without the package itself:
  ```bash
  pip install -r requirements.txt
  ```

## Quick Start

**Recommended: Install as package (pip/conda)**

After installing the package (see Installation section above), you can import and use it directly:
```python
from german_phoneme_validator import validate_phoneme
import numpy as np

# Using numpy array
audio_array = np.random.randn(3 * 16000).astype(np.float32)  # 3 seconds at 16kHz
result = validate_phoneme(
    audio=audio_array,
    phoneme="/b/",
    position_ms=1500.0,
    expected_phoneme="/b/"
)

print(f"Correct: {result['is_correct']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Explanation: {result['explanation']}")
```

**Note**: Models are automatically downloaded from Hugging Face Hub on first use. You don't need to specify `artifacts_dir` unless you have local models for development.

### Using WAV File

```python
from german_phoneme_validator import validate_phoneme

result = validate_phoneme(
    audio="path/to/audio.wav",
    phoneme="/p/",
    position_ms=1200.0,
    expected_phoneme="/b/"
)
```

### Using PhonemeValidator Class

```python
from german_phoneme_validator import PhonemeValidator

validator = PhonemeValidator()
available_pairs = validator.get_available_pairs()
print(f"Available pairs: {available_pairs}")

result = validator.validate_phoneme(
    audio="audio.wav",
    phoneme="/b/",
    position_ms=1500.0,
    expected_phoneme="/b/"
)
```

## API Reference

### `validate_phoneme()`

Main function for phoneme validation.

**Parameters:**
- `audio`: Path to WAV file (str/Path) or numpy array (16kHz, mono)
- `phoneme`: Target phoneme in IPA notation (e.g., `/b/` or `b`)
- `position_ms`: Timestamp in milliseconds where the phoneme occurs
- `expected_phoneme`: (Optional) Expected correct phoneme
- `artifacts_dir`: (Optional) Path to artifacts directory

**Returns:**
```python
{
    'is_correct': bool,      # True/False/None (error)
    'confidence': float,     # 0.0 to 1.0
    'features': dict,        # Extracted acoustic features
    'explanation': str        # Human-readable explanation
}
```

## Input/Output

**Audio Format:**
- WAV file or numpy array
- 16kHz sample rate (auto-resampled)
- Mono channel (auto-converted)
- 3-5 seconds recommended

**Phoneme Notation:**
- IPA notation with or without brackets: `/b/`, `b`, `/p/`, `p`
- Case-insensitive

**Output:**
- `is_correct`: True (correct), False (incorrect), None (error)
- `confidence`: Model confidence (0.0-1.0)
- `features`: Dictionary of acoustic features (MFCC, formants, VOT, etc.)
- `explanation`: Human-readable result description

## Supported Phoneme Pairs

The system supports 22 phoneme pairs including:
- Plosives: `b-p`, `d-t`, `g-k`, `kʰ-g`, `tʰ-d`
- Fricatives: `s-ʃ`, `ç-ʃ`, `ç-x`, `z-s`, `ts-s`, `x-k`
- Vowels: `a-ɛ`, `aː-a`, `aɪ̯-aː`, `aʊ̯-aː`, `eː-ɛ`, `iː-ɪ`, `uː-ʊ`, `oː-ɔ`, `ə-ɛ`
- Others: `ŋ-n`, `ʁ-ɐ`

Use `validator.get_available_pairs()` to see available pairs in your installation.

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SergejKurtasch/german-phoneme-validator.git
   cd german-phoneme-validator
   ```

2. **Install dependencies**: 
   ```bash
   pip install -e .
   # or
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```python
   from german_phoneme_validator import validate_phoneme
   print("Installation successful!")
   ```

4. **Automated environment preparation**:
   ```bash
   ./setup_env.sh
   ```
   This helper script creates a `.venv` virtual environment, upgrades `pip`, installs `setuptools<58` (required because `googleads==3.8.0`, a dependency of `parselmouth`, still uses the legacy `use_2to3` flag), and then installs everything from `requirements.txt`.

   Optional dependencies (`parselmouth`, `webrtcvad`, `pandas`, `tqdm`, `torchaudio`) remain in `requirements.txt` for convenience, but you can omit them if you only need the core validator. Run `pip install -r requirements.txt` without the `setup_env.sh` helper if you prefer manual control.

**Note**: Models are automatically downloaded from Hugging Face Hub on first use. The module will automatically detect available phoneme pairs. Currently, 22 phoneme pairs are supported. Models are cached locally after first download, so subsequent runs don't require internet access (unless checking for updates).

## Documentation

- **SETUP.md** - Detailed setup instructions
- **PROJECT_STRUCTURE.md** - Project structure and components
- **TECHNICAL_REPORT.md** - Technical documentation and methodology
- **example_usage.py** - Complete usage examples
- **INSTRUCTIONS_HF_UPLOAD.md** - Instructions for uploading models to Hugging Face Hub (for maintainers)

## Error Handling

The function handles errors gracefully:
- File not found → `is_correct=None` with error message
- Invalid audio format → Error description in `explanation`
- Position out of bounds → Error message
- Unsupported phoneme pair → List of available pairs
- Model loading errors → Error description

## Performance

- Models loaded lazily and cached in memory
- Optimized feature extraction for numpy arrays
- Automatic audio resampling
- First call slower due to model loading

## License

MIT License - see LICENSE file for details.

This module is part of the German Speech Recognition project.
