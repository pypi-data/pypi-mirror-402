"""
Shared fixtures for integration tests.

These tests require:
1. A valid API key set as REDENLAB_ML_API_KEY environment variable
2. A test audio file at tests/fixtures/test_audio.wav

Tests will be skipped if these prerequisites are not met.
"""

import os
from pathlib import Path

import pytest

# Path to test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
TEST_AUDIO_FILE = FIXTURES_DIR / "s0001_12.wav"
CONFIG_FILE = FIXTURES_DIR / "config.yaml"


@pytest.fixture
def api_key():
    """
    Get API key from environment.

    Skips the test if REDENLAB_ML_API_KEY is not set.
    """
    key = os.environ.get("REDENLAB_ML_API_KEY")
    if not key:
        pytest.skip(
            "REDENLAB_ML_API_KEY environment variable not set. " "Set it to run integration tests."
        )
    return key


@pytest.fixture
def test_audio_path():
    """
    Get path to test audio file.

    Skips the test if test_audio.wav doesn't exist in fixtures.

    Requirements for test_audio.wav:
    - Short duration (2-5 seconds recommended)
    - Clear speech in English (for transcription tests)
    - WAV format, 16kHz sample rate recommended
    """
    if not TEST_AUDIO_FILE.exists():
        pytest.skip(
            f"Test audio file not found at {TEST_AUDIO_FILE}. "
            "Add a short WAV file (2-5 seconds) to run integration tests."
        )
    return str(TEST_AUDIO_FILE)


@pytest.fixture
def transcribe_client():
    """
    Create a TranscribeClient instance with real credentials.

    Uses config file at tests/fixtures/config.yaml for api_key and base_url.
    """
    from redenlab_extract import TranscribeClient

    return TranscribeClient(language_code="en-US", config_path=CONFIG_FILE)


@pytest.fixture
def intelligibility_client():
    """
    Create an IntelligibilityClient with real credentials.
    We are going to use a fixed model_name als-intelligibility-v1
    """
    from redenlab_extract import IntelligibilityClient

    return IntelligibilityClient(config_path=CONFIG_FILE, model_name="als-intelligibility-v1")
