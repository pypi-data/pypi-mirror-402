"""
Integration tests for IntelligibilityClient.

These tests verify that the IntelligibilityClient works correctly against the real
RedenLab API. Run these tests before releasing a new SDK version to ensure
basic workflows function as expected.

Prerequisites:
    - tests/fixtures/config.yaml with valid api_key and base_url
    - tests/fixtures/test_audio.wav exists (short audio file, 2-5 seconds)

Run with:
    pytest tests/integration/test_intelligibility_client.py -v

"""

from pathlib import Path

import pytest
import yaml

from redenlab_extract import IntelligibilityClient
from redenlab_extract.exceptions import AuthenticationError, ValidationError

# Path to test config file
CONFIG_FILE = Path(__file__).parent.parent / "fixtures" / "config.yaml"


class TestIntelligibilityClientInitialization:
    """Tests for IntelligibilityClient initialization."""

    def test_client_initializes_with_valid_credentials(self):
        """Verify client can be created with valid API key from config file."""
        client = IntelligibilityClient(config_path=CONFIG_FILE, model_name="als-intelligibility-v1")

        # Load expected api_key from config file
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
        expected_api_key = config["api_key"]

        assert client.api_key == expected_api_key
        assert client.display_model_name == "als-intelligibility-v1"

    def test_client_accepts_all_valid_models(self):
        """Verify client accepts all valid model names."""
        valid_models = [
            "ataxia-intelligibility",
            "als-intelligibility-v1",
            "als-intelligibility-v2",
        ]

        for model_name in valid_models:
            client = IntelligibilityClient(config_path=CONFIG_FILE, model_name=model_name)
            assert client.display_model_name == model_name

    def test_client_rejects_invalid_model(self):
        """Verify client raises ValidationError for invalid model name."""
        with pytest.raises(ValidationError):
            IntelligibilityClient(config_path=CONFIG_FILE, model_name="invalid-model")

    def test_client_rejects_invalid_api_key(self):
        """Verify client raises AuthenticationError for invalid API key format."""
        with pytest.raises(AuthenticationError):
            IntelligibilityClient(api_key="invalid", model_name="als-intelligibility-v1")

    def test_client_repr_masks_api_key(self):
        """Verify __repr__ doesn't expose full API key."""
        client = IntelligibilityClient(config_path=CONFIG_FILE, model_name="als-intelligibility-v1")
        repr_str = repr(client)

        # Load api_key from config to verify it's masked
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)

        assert config["api_key"] not in repr_str


class TestIntelligibilityClientHealth:
    """Tests for IntelligibilityClient health check functionality."""

    def test_health_returns_status(self, intelligibility_client):
        """
        Verify health() returns valid status.

        IntelligibilityClient uses SageMaker endpoints which support health checks.
        """
        health_result = intelligibility_client.health()

        assert "status" in health_result
        assert "ready" in health_result
        assert health_result["status"] in ["healthy", "warming", "unhealthy"]

    def test_warmup_returns_status(self, intelligibility_client):
        """
        Verify warmup() returns status information.

        IntelligibilityClient uses SageMaker endpoints which support warmup.
        """
        warmup_result = intelligibility_client.warmup()

        assert "status" in warmup_result


class TestIntelligibilityClientSubmit:
    """Tests for IntelligibilityClient job submission."""

    def test_submit_returns_job_id(self, intelligibility_client, test_audio_path):
        """Verify submit() returns a valid job_id."""
        job_id = intelligibility_client.submit(test_audio_path)

        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0


class TestIntelligibilityClientStatus:
    """Tests for IntelligibilityClient job status retrieval."""

    def test_get_status_returns_valid_response(self, intelligibility_client, test_audio_path):
        """Verify get_status() returns valid job status."""
        job_id = intelligibility_client.submit(test_audio_path)

        status = intelligibility_client.get_status(job_id)

        assert "job_id" in status
        assert "status" in status
        assert status["job_id"] == job_id
        assert status["status"] in ["upload_pending", "processing", "completed", "failed"]


class TestIntelligibilityClientEndToEnd:
    """
    End-to-end tests for IntelligibilityClient.

    These tests run the full intelligibility workflow and may take several
    minutes to complete.
    """

    def test_predict_returns_result(self, intelligibility_client, test_audio_path):
        """
        Verify predict() completes and returns intelligibility result.

        This is the primary smoke test - if this passes, the basic SDK
        workflow is functioning correctly.
        """
        result = intelligibility_client.predict(test_audio_path)

        assert result["status"] == "completed"
        assert result["result"] is not None
        assert result["job_id"] is not None

    def test_submit_poll_workflow(self, intelligibility_client, test_audio_path):
        """Verify separate submit() and poll() workflow works."""
        # Submit job
        job_id = intelligibility_client.submit(test_audio_path)
        assert job_id is not None

        # Poll for completion
        result = intelligibility_client.poll(job_id, timeout=600)

        assert result["status"] == "completed"
        assert result["job_id"] == job_id

    def test_progress_callback_is_called(self, intelligibility_client, test_audio_path):
        """Verify progress_callback receives status updates during polling."""
        callback_calls = []

        def progress_callback(status):
            callback_calls.append(status)

        result = intelligibility_client.predict(
            test_audio_path,
            progress_callback=progress_callback,
        )

        assert result["status"] == "completed"
        # Callback should have been called at least once during polling
        assert len(callback_calls) >= 1
        # Each callback should contain status info
        for call in callback_calls:
            assert "status" in call
