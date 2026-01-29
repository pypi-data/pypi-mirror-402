#!/usr/bin/env python3
"""
Simple example script for transcription with TextGrid generation.

Quick start:
1. Set your API key: export REDENLAB_ML_API_KEY='your-key'
2. Edit the FILES_TO_PROCESS list below
3. Run: python transcribe_example.py
"""

import os
import sys
from pathlib import Path

# Add src directory to path to import directly from source files
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import the batch transcription module
# Make sure batch_transcribe_textgrid.py is in the same directory
import batch_transcribe_textgrid as batch_transcribe

# =============================================================================
# CONFIGURE YOUR FILES HERE
# =============================================================================

# Example 1: Single file with en-US
FILES_TO_PROCESS = [
    ("/Users/ayushranjan/Downloads/Archive 1/ENG/01-129-21_days.wav", "en-US"),
]

# Example 2: Multiple files with different languages
# FILES_TO_PROCESS = [
#     ("/path/to/english_audio.wav", "en-US"),
#     ("/path/to/australian_audio.wav", "en-AU"),
#     ("/path/to/spanish_audio.wav", "es-ES"),
#     ("/path/to/french_audio.wav", "fr-FR"),
# ]

# Example 3: Batch of English files
# FILES_TO_PROCESS = [
#     ("/path/to/file1.wav", "en-US"),
#     ("/path/to/file2.wav", "en-US"),
#     ("/path/to/file3.wav", "en-US"),
# ]

# Example 4: Load from a directory
# import glob
# audio_dir = "/path/to/audio/directory"
# FILES_TO_PROCESS = [
#     (file_path, "en-US")  # All files use en-US
#     for file_path in glob.glob(f"{audio_dir}/*.wav")
# ]

# =============================================================================
# OPTIONAL: Customize output directories
# =============================================================================

# Where to save JSON results
batch_transcribe.RESULTS_DIR = "./results"

# Where to save TextGrid files
batch_transcribe.TEXTGRID_DIR = "./textgrids"

# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    # Set the files to process
    batch_transcribe.FILES_AND_LANGUAGES = FILES_TO_PROCESS

    # Run the batch transcription
    batch_transcribe.main()
