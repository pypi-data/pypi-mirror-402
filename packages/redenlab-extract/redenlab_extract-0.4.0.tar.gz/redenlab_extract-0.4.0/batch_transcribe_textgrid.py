#!/usr/bin/env python3
"""
Batch transcription script with TextGrid generation.

This script:
1. Takes a list of WAV files with language codes
2. Submits them for transcription using RedenLab ML API
3. Downloads the JSON results from S3
4. Creates TextGrid files from the transcription results

Usage:
    python batch_transcribe_textgrid.py

Configuration:
    - Edit the FILES_AND_LANGUAGES list below with your files and language codes
    - Set REDENLAB_ML_API_KEY environment variable
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from urllib.parse import urlparse

# Add src directory to path to import directly from source files
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import the SDK directly from source files
try:
    from redenlab_extract.client import InferenceClient
except ImportError as e:
    print("Error: Could not import redenlab_extract from source files.")
    print(f"Error details: {e}")
    print(f"Make sure the src/redenlab_extract directory exists at: {src_dir}")
    sys.exit(1)

# Optional import - TextGrid generation
try:
    from praatio import tgio
    import pandas as pd
    HAS_TEXTGRID = True
except ImportError:
    HAS_TEXTGRID = False
    print("Warning: praatio or pandas not installed. TextGrid generation will be skipped.")
    print("Install with: pip install praatio pandas")


# =============================================================================
# CONFIGURATION - Edit this section
# =============================================================================

# API Configuration
API_KEY = os.environ.get('REDENLAB_ML_API_KEY')
BASE_URL = "https://daq8c71oh4.execute-api.us-west-2.amazonaws.com/prod/"

# Output directories
RESULTS_DIR = "./results"
TEXTGRID_DIR = "./textgrids"

# Files to process: (file_path, language_code)
# Supported language codes: en-US, en-AU, en-GB, es-ES, fr-FR, de-DE, etc.
FILES_AND_LANGUAGES = [('/Users/ayushranjan/Downloads/Archive 1/NL/09-241-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-253_20012023_Dagenvdweek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-026-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/ACE03589_05-10-21_dagenvdweek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-203-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-003-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-273-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-106-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-038-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-048-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-001-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-248-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-016-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-016-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-266-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-151-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-043-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-013-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-272-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-004-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-166-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-089-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-021-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-182_21_Dagenvdweek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-051-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24_022_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-053-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-141-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-255-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-116-21_Dagen.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-269_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-061-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-228-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-168-21_29-07-2022_Dagen.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-206-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-216-21 Dagen van de week 06-05-2022.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-006-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-005-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-205-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-111-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-079-21_dagen.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-062-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-247-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-219-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24_021_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-019-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-165-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-029-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-260-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-121_21_DagenvdWeek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-121_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-093-21-DAYS.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-190-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-047-21_ days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-209-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-040-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-187_21_DagenvdWeek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-188-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-175-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-200-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-096-21_12082022_Dagen.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-250_21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-055-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-181_130123_Dagenvdweek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-023-21-Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-134_21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-086-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-232-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-029-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-229-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-068-21_Dagen.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-007-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-007-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-192-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-240-21-dagenvdweek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-052-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24_023_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-045-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-210-21-days (2).wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-050-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-020-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-008-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-220-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-020-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-094-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-012-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-012-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-149-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-117-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-075-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-167-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-010-21_24-05-2022_dagen.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-261_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-005-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-180_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-150-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-123_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-049-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-070-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-267-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-017-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-002-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-002-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-015-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-098-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-040-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-047-21-dagenvdweek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-057-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-136-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-054-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-246-21_05-08-2022_Dagen.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-118-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-115-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-189-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-104-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-038-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-201-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-001-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-194-21_13-05-2022_days.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-114-21_Dagen.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-042_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-149-21-days (2).wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-026-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-256-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/ACE03478_24-09-21_dagen vd week.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-043-Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-008-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-263-21_dagenvandeweek.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-208-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-153-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-011-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-044-21_day.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-156-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-041_21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-223-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-046-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-082-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/19-036-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-147-21_28-06-2022_dagen.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-245-21_08072022_Days.wav',
  'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-143-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-218-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-133-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-204-21-days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/24-004-21_days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-215-21_Days.wav', 'nl-NL'),
 ('/Users/ayushranjan/Downloads/Archive 1/NL/09-063-21-days.wav', 'nl-NL')]

# =============================================================================
# Helper Functions
# =============================================================================

def download_json_from_url(url: str, output_path: str) -> bool:
    """
    Download JSON file from a presigned S3 URL.

    Args:
        url: Presigned S3 URL
        output_path: Local path to save the file

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"  Downloading JSON from S3...")
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Save JSON to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)

        print(f"  ✓ JSON saved to: {output_path}")
        return True

    except Exception as e:
        print(f"  ✗ Error downloading JSON: {e}")
        return False


def get_audio_duration_from_result(result: Dict[str, Any]) -> Optional[float]:
    """
    Extract audio duration from the API result.

    Args:
        result: API response dictionary

    Returns:
        Duration in seconds, or None if not found
    """
    # Try to get duration from the result
    if 'duration' in result:
        return float(result['duration'])
    return None


def json2textgrid(json_file_path: str, output_path: str, audio_duration: float) -> bool:
    """
    Convert AWS Transcribe JSON to TextGrid format.

    Args:
        json_file_path: Path to the JSON file
        output_path: Path to save the TextGrid file
        audio_duration: Audio duration in seconds

    Returns:
        True if successful, False otherwise
    """
    if not HAS_TEXTGRID:
        print("  TextGrid generation skipped (praatio not installed)")
        return False

    try:
        # Load JSON data
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        tg = tgio.Textgrid()

        # Parse items from AWS Transcribe JSON
        columns = ['index_ST', 'start', 'end', 'confidence', 'content']
        dtypes = {'index_ST': float, 'start': float, 'end': float, 'confidence': float, 'content': str}
        df = pd.DataFrame(columns=columns).astype(dtypes)

        # Access items correctly from the JSON structure
        items = data['results'].get('items', [])

        # Handle empty transcription (no speech detected)
        if not items:
            print(f"  No speech items found - creating empty TextGrid")
            emptyTier = tgio.IntervalTier('Empty', [], 0, audio_duration)
            tg.addTier(emptyTier)
            tg.save(output_path)
            print(f'  ✓ Empty TextGrid created: {output_path}')
            return True

        # Extract pronunciation items
        for i, cont in enumerate(items):
            if cont['type'] == 'pronunciation':
                df.loc[len(df)] = [
                    i,
                    float(cont['start_time']),
                    float(cont['end_time']),
                    float(cont['alternatives'][0]['confidence']),
                    cont['alternatives'][0]['content']
                ]

        # Check if we have any data
        if len(df) == 0:
            print(f"  No pronunciation items found - creating empty TextGrid")
            emptyTier = tgio.IntervalTier('Empty', [], 0, audio_duration)
            tg.addTier(emptyTier)
            tg.save(output_path)
            print(f'  ✓ Empty TextGrid created: {output_path}')
            return True

        # Create word tier
        word_TG_cols = ['start', 'end', 'content']
        word_TG_df = df[word_TG_cols]
        word_TG_df_list = word_TG_df.values.tolist()
        word_TG_df_list = [tuple(item) for item in word_TG_df_list]

        # Create confidence tier
        conf_TG_cols = ['start', 'end', 'confidence']
        conf_TG_df = df[conf_TG_cols]
        conf_TG_df_list = conf_TG_df.values.tolist()
        conf_TG_df_list = [(start, end, str(confidence)) for start, end, confidence in conf_TG_df_list]

        # Create VAD tier
        speech_start_time = df['start'].iloc[0]
        speech_end_time = df['end'].iloc[len(df) - 1]

        vadTier = tgio.IntervalTier('VAD', [(speech_start_time, speech_end_time, 'speech')], 0, audio_duration)
        tg.addTier(vadTier)

        wordTier = tgio.IntervalTier('Words', word_TG_df_list, 0, audio_duration)
        tg.addTier(wordTier)

        confidenceTier = tgio.IntervalTier('Confidence', conf_TG_df_list, 0, audio_duration)
        tg.addTier(confidenceTier)

        tg.save(output_path)
        print(f'  ✓ TextGrid created: {output_path}')
        return True

    except Exception as e:
        print(f"  ✗ TextGrid generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_transcription_result(
    result: Dict[str, Any],
    file_name: str,
    language_code: str,
    results_dir: str,
    textgrid_dir: str
) -> bool:
    """
    Process a completed transcription result.

    Downloads the JSON result and creates a TextGrid file.

    Args:
        result: API response dictionary
        file_name: Original file name
        language_code: Language code used
        results_dir: Directory to save JSON results
        textgrid_dir: Directory to save TextGrid files

    Returns:
        True if successful, False otherwise
    """
    file_name_no_ext = Path(file_name).stem

    print(f"\n  Processing results for: {file_name}")
    print(f"  Language: {language_code}")
    print(f"  Status: {result.get('status')}")
    print(f"  Transcript: {result.get('transcript', 'N/A')[:100]}...")
    print(f"  Word count: {result.get('word_count', 0)}")
    print(f"  Duration: {result.get('duration', 0):.2f}s")
    print(f"  Speaker count: {result.get('speaker_count', 0)}")

    # Get the result URL (presigned S3 URL for JSON)
    result_url = result.get('result_url')
    if not result_url:
        print(f"  ✗ No result_url found in response")
        return False

    # Download JSON from S3
    json_path = os.path.join(results_dir, f'{file_name_no_ext}_transcript.json')
    if not download_json_from_url(result_url, json_path):
        return False

    # Get audio duration
    audio_duration = get_audio_duration_from_result(result)
    if not audio_duration:
        print(f"  ✗ Could not determine audio duration")
        return False

    print(f"  Audio duration: {audio_duration:.2f}s")

    # Create TextGrid
    if HAS_TEXTGRID:
        textgrid_path = os.path.join(textgrid_dir, f'{file_name_no_ext}.TextGrid')
        success = json2textgrid(json_path, textgrid_path, audio_duration)
        return success
    else:
        print(f"  TextGrid generation skipped (praatio not installed)")
        return True


# =============================================================================
# Main Processing Function
# =============================================================================

def main():
    """
    Main function - batch transcription with TextGrid generation.
    """
    # Validate API key
    if not API_KEY:
        print("Error: REDENLAB_ML_API_KEY environment variable not set")
        print("Set it with: export REDENLAB_ML_API_KEY='your-api-key'")
        sys.exit(1)

    # Validate input files
    if not FILES_AND_LANGUAGES:
        print("Error: No files specified in FILES_AND_LANGUAGES")
        print("Please edit the script and add your files to the FILES_AND_LANGUAGES list")
        sys.exit(1)

    # Create output directories
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(TEXTGRID_DIR, exist_ok=True)

    print("=" * 70)
    print("BATCH TRANSCRIPTION WITH TEXTGRID GENERATION")
    print("=" * 70)
    print(f"API URL: {BASE_URL}")
    print(f"Files to process: {len(FILES_AND_LANGUAGES)}")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"TextGrid directory: {TEXTGRID_DIR}")
    print("=" * 70)

    # Initialize client (no default language_code since we'll specify per job)
    client = InferenceClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model_name="transcribe",
        timeout=3600
    )

    print(f"Client: {client}")
    print()

    # ==========================================================================
    # PHASE 1: Submit all jobs
    # ==========================================================================
    print("PHASE 1: Submitting all jobs...")
    print("=" * 70)

    job_info = []  # List of (job_id, file_path, file_name, language_code)

    for i, (file_path, lang_code) in enumerate(FILES_AND_LANGUAGES, 1):
        # Validate file exists
        if not Path(file_path).exists():
            print(f"[{i}/{len(FILES_AND_LANGUAGES)}] ✗ File not found: {file_path}")
            continue

        file_name = Path(file_path).name
        print(f"[{i}/{len(FILES_AND_LANGUAGES)}] Submitting: {file_name} ({lang_code})")

        try:
            # Submit job with language code
            job_id = client.submit(file_path, language_code=lang_code)
            job_info.append((job_id, file_path, file_name, lang_code))
            print(f"  ✓ Job ID: {job_id}")

        except Exception as e:
            print(f"  ✗ Error submitting job: {e}")

    print()
    print(f"✓ Submitted {len(job_info)} jobs successfully")
    print()

    if not job_info:
        print("No jobs submitted. Exiting.")
        sys.exit(1)

    # ==========================================================================
    # PHASE 2: Poll all jobs and process results
    # ==========================================================================
    print("PHASE 2: Polling for completion and processing results...")
    print("=" * 70)

    results = []
    pending = set(range(len(job_info)))

    while pending:
        for idx in list(pending):
            job_id, file_path, file_name, lang_code = job_info[idx]

            try:
                status_data = client.get_status(job_id)
                status = status_data.get('status')

                if status == 'completed':
                    print(f"\n✓ Job {idx + 1}/{len(job_info)} completed: {file_name}")

                    # Process the result
                    success = process_transcription_result(
                        result=status_data,
                        file_name=file_name,
                        language_code=lang_code,
                        results_dir=RESULTS_DIR,
                        textgrid_dir=TEXTGRID_DIR
                    )

                    results.append({
                        'file_name': file_name,
                        'language_code': lang_code,
                        'job_id': job_id,
                        'status': 'completed',
                        'success': success
                    })

                    pending.remove(idx)

                elif status == 'failed':
                    print(f"\n✗ Job {idx + 1}/{len(job_info)} failed: {file_name}")
                    error_msg = status_data.get('error', 'Unknown error')
                    print(f"  Error: {error_msg}")

                    results.append({
                        'file_name': file_name,
                        'language_code': lang_code,
                        'job_id': job_id,
                        'status': 'failed',
                        'error': error_msg,
                        'success': False
                    })

                    pending.remove(idx)

                else:
                    print(f"  [{idx + 1}/{len(job_info)}] {file_name}: {status}")

            except Exception as e:
                print(f"\n✗ Error checking job {idx + 1}/{len(job_info)}: {e}")

        if pending:
            print(f"\n  {len(pending)} jobs still pending. Waiting 10 seconds...")
            time.sleep(10)

    # ==========================================================================
    # Summary
    # ==========================================================================
    print()
    print("=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Total jobs: {len(results)}")
    print(f"Completed: {len([r for r in results if r['status'] == 'completed'])}")
    print(f"Failed: {len([r for r in results if r['status'] == 'failed'])}")
    print(f"TextGrids created: {len([r for r in results if r.get('success', False)])}")
    print()
    print(f"Results saved to: {RESULTS_DIR}")
    print(f"TextGrids saved to: {TEXTGRID_DIR}")
    print("=" * 70)

    # Print detailed results
    print("\nDetailed Results:")
    for i, r in enumerate(results, 1):
        status_icon = "✓" if r.get('success', False) else "✗"
        print(f"  [{i}] {status_icon} {r['file_name']} ({r['language_code']})")
        if r['status'] == 'failed':
            print(f"      Error: {r.get('error', 'Unknown')}")


if __name__ == "__main__":
    main()
