"""
Integration tests for TranscribeClient.

These tests verify that the TranscribeClient works correctly against the real
RedenLab API. Run these tests before releasing a new SDK version to ensure
basic workflows function as expected.

Prerequisites:
    - tests/fixtures/config.yaml with valid api_key and base_url
    - tests/fixtures/test_audio.wav exists (short audio file, 2-5 seconds)

Run with:
    pytest tests/integration/test_transcribe_client.py -v

"""

from pathlib import Path

import pytest
import yaml

from redenlab_extract import TranscribeClient
from redenlab_extract.exceptions import AuthenticationError

# Path to test config file
CONFIG_FILE = Path(__file__).parent.parent / "fixtures" / "config.yaml"


class TestTranscribeClientInitialization:
    """Tests for TranscribeClient initialization."""

    def test_client_initializes_with_valid_credentials(self):
        """Verify client can be created with valid API key from config file."""
        client = TranscribeClient(config_path=CONFIG_FILE)

        # Load expected api_key from config file
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
        expected_api_key = config["api_key"]

        assert client.api_key == expected_api_key
        assert client.model_name == "transcribe"

    def test_client_accepts_language_code(self):
        """Verify client accepts language_code parameter."""
        client = TranscribeClient(config_path=CONFIG_FILE, language_code="en-AU")

        assert client.language_code == "en-AU"

    def test_client_rejects_invalid_api_key(self):
        """Verify client raises AuthenticationError for invalid API key format."""
        with pytest.raises(AuthenticationError):
            TranscribeClient(api_key="invalid")

    def test_client_repr_masks_api_key(self):
        """Verify __repr__ doesn't expose full API key."""
        client = TranscribeClient(config_path=CONFIG_FILE)
        repr_str = repr(client)

        # Load api_key from config to verify it's masked
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)

        assert config["api_key"] not in repr_str
        assert "TranscribeClient" in repr_str


class TestTranscribeClientHealth:
    """Tests for TranscribeClient health check functionality."""

    def test_health_returns_not_supported(self, transcribe_client):
        """
        Verify health() returns 'not_supported' status.

        TranscribeClient uses AWS managed service which doesn't have
        a health endpoint - it's always available.
        """
        health_result = transcribe_client.health()

        assert health_result["status"] == "not_supported"
        assert health_result["ready"] is True
        assert health_result["is_warming"] is False
        assert "managed service" in health_result["message"].lower()

    def test_warmup_returns_not_supported(self, transcribe_client):
        """
        Verify warmup() returns 'not_supported' status.

        TranscribeClient uses AWS managed service which doesn't require warmup.
        """
        warmup_result = transcribe_client.warmup()

        assert warmup_result["status"] == "not_supported"
        assert "managed service" in warmup_result["message"].lower()


class TestTranscribeClientSubmit:
    """Tests for TranscribeClient job submission."""

    def test_submit_returns_job_id(self, transcribe_client, test_audio_path):
        """Verify submit() returns a valid job_id."""
        job_id = transcribe_client.submit(test_audio_path)

        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    def test_submit_with_language_code_override(self, test_audio_path):
        # TODO: This is not a proper test that shows that we have sucessfuly overwritten the language code
        """Verify language_code can be overridden per submission."""
        client = TranscribeClient(config_path=CONFIG_FILE, language_code="en-US")

        # Override with different language
        job_id = client.submit(test_audio_path, language_code="en-AU")

        assert job_id is not None
        assert isinstance(job_id, str)


class TestTranscribeClientStatus:
    """Tests for TranscribeClient job status retrieval."""

    def test_get_status_returns_valid_response(self, transcribe_client, test_audio_path):
        """Verify get_status() returns valid job status."""
        job_id = transcribe_client.submit(test_audio_path)

        status = transcribe_client.get_status(job_id)

        assert "job_id" in status
        assert "status" in status
        assert status["job_id"] == job_id
        assert status["status"] in ["upload_pending", "processing", "completed", "failed"]


class TestTranscribeClientEndToEnd:
    """
    End-to-end tests for TranscribeClient.

    These tests run the full transcription workflow and may take several
    minutes to complete.
    """

    def test_predict_returns_transcription(self, transcribe_client, test_audio_path):
        """
        Verify predict() completes and returns transcription result.

        This is the primary smoke test - if this passes, the basic SDK
        workflow is functioning correctly.
        """
        result = transcribe_client.predict(test_audio_path)

        assert result["status"] == "completed"
        assert result["transcript"] is not None
        assert result["job_id"] is not None

    def test_submit_poll_workflow(self, transcribe_client, test_audio_path):
        """Verify separate submit() and poll() workflow works."""
        # Submit job
        job_id = transcribe_client.submit(test_audio_path)
        assert job_id is not None

        # Poll for completion
        result = transcribe_client.poll(job_id, timeout=600)

        assert result["status"] == "completed"
        assert result["job_id"] == job_id

    def test_progress_callback_is_called(self, transcribe_client, test_audio_path):
        """Verify progress_callback receives status updates during polling."""
        callback_calls = []

        def progress_callback(status):
            callback_calls.append(status)

        result = transcribe_client.predict(
            test_audio_path,
            progress_callback=progress_callback,
        )

        assert result["status"] == "completed"
        # Callback should have been called at least once during polling
        assert len(callback_calls) >= 1
        # Each callback should contain status info
        for call in callback_calls:
            assert "status" in call
