"""
Setup script for German Phoneme Pronunciation Validator package.
Universal installer for any Python project.
"""

from setuptools import setup
from pathlib import Path
import re

# =============================================================================
# Utility functions for reading package metadata
# =============================================================================

def read_file_content(file_path):
    """Safely read file content with proper encoding."""
    file_path = Path(__file__).parent / file_path
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return ""

def get_version():
    """Extract version from __init__.py to avoid duplication."""
    init_file = Path(__file__).parent / "__init__.py"
    if init_file.exists():
        content = init_file.read_text(encoding="utf-8")
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    return "1.0.0"  # fallback version

def parse_requirements(requirements_file="requirements.txt"):
    """Parse requirements.txt and return list of dependencies."""
    requirements = []
    file_path = Path(__file__).parent / requirements_file
    
    if not file_path.exists():
        return requirements
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines, comments, and section headers
            if not line or line.startswith("#") or line.startswith("="):
                continue
            # Extract package name and version (remove inline comments)
            match = re.match(r"^([^#]+)", line)
            if match:
                req = match.group(1).strip()
                if req:
                    requirements.append(req)
    
    return requirements

def get_core_requirements(requirements):
    """Filter core requirements (exclude optional dependencies)."""
    optional_keywords = ["parselmouth", "webrtcvad", "pandas", "tqdm", "torchaudio"]
    return [
        req for req in requirements
        if not any(keyword in req.lower() for keyword in optional_keywords)
    ]


# =============================================================================
# Package metadata
# =============================================================================

# Read metadata files
long_description = read_file_content("README.md")
requirements = parse_requirements("requirements.txt")
core_requirements = get_core_requirements(requirements)
version = get_version()

# Package structure mapping
# Maps Python package name (with underscores) to root directory
# Allows: from german_phoneme_validator import ...
package_dir = {"german_phoneme_validator": "."}
packages = ["german_phoneme_validator", "german_phoneme_validator.core"]

# Note: artifacts/ directory is NOT included in PyPI package.
# Models are automatically downloaded from Hugging Face Hub on first use.
# See core/downloader.py for details.
package_data = {
    "german_phoneme_validator": [
        # artifacts excluded - downloaded automatically from Hugging Face Hub
        # core/*.py is automatically included via packages directive
    ],
}

setup(
    # Basic package information
    name="german-phoneme-validator",
    version=version,
    description="A production-ready Python module for acoustic validation of German phoneme pronunciation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # Author information
    author="Sergej Kurtasch",
    author_email="sergej.kurtasch@gmail.com",
    
    # Project URLs
    url="https://github.com/SergejKurtasch/german-phoneme-validator",
    project_urls={
        "Documentation": "https://github.com/SergejKurtasch/german-phoneme-validator#readme",
        "Source": "https://github.com/SergejKurtasch/german-phoneme-validator",
        "Tracker": "https://github.com/SergejKurtasch/german-phoneme-validator/issues",
    },
    
    # License
    license="MIT",
    
    # Package structure
    package_dir=package_dir,
    packages=packages,
    include_package_data=True,
    package_data=package_data,
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=core_requirements,
    extras_require={
        "optional": [
            "parselmouth>=0.4.0",
            "webrtcvad>=2.0.10",
            "pandas>=1.3.0",
            "tqdm>=4.64.0",
            "torchaudio>=2.0.0",
        ],
        "all": requirements,
    },
    
    # PyPI classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    
    keywords="phoneme validation, speech recognition, german language, acoustic analysis, pronunciation assessment",
    
    # Additional metadata
    zip_safe=False,  # Set to False if package contains non-code files (like artifacts/)
)
