from unittest.mock import patch

import pytest

from redenlab_extract import BaseInferenceClient, IntelligibilityClient, TranscribeClient
from redenlab_extract.exceptions import AuthenticationError, ConfigurationError
from redenlab_extract.payload import IntelligibilityPayloadBuilder, TranscribePayloadBuilder


class TestBaseInferenceClient:

    @patch("redenlab_extract.client.validate_model_name")
    @patch("redenlab_extract.client.get_merged_config")
    def test_init_success(self, mock_config, mock_validate_model):
        """Test client initialisation logic"""

        # setup mocks
        mock_config.return_value = {
            "api_key": "sk_test_12345",
            "model_name": "als-intelligibility-mtpa",
            "timeout": 3600,
            "base_url": "xyz",
        }
        mock_validate_model.return_value = "als-intelligibility-mtpa"

        # Test
        client = BaseInferenceClient(api_key="sk_test_12345")

        # Verify clients state
        assert client.api_key == "sk_test_12345"
        assert client.model_name == "als-intelligibility-mtpa"

    @patch("redenlab_extract.client.validate_model_name")
    @patch("redenlab_extract.client.get_merged_config")
    def test_init_missing_api_key_raises(self, mock_config, mock_validate_model):
        """Test client initialisation failure without api key"""

        # setup mock config
        mock_config.return_value = {
            "api_key": None,
            "model_name": "intelligibility",
            "timeout": 3600,
            "base_url": "xyz",
        }
        mock_validate_model.return_value = "intelligibility"

        with pytest.raises(AuthenticationError):
            BaseInferenceClient()

    @patch("redenlab_extract.client.get_default_base_url")
    @patch("redenlab_extract.client.validate_model_name")
    @patch("redenlab_extract.client.get_merged_config")
    def test_init_missing_base_url_raises(
        self, mock_config, mock_validate_model, mock_get_default_base_url
    ):
        """Test client initialisation failure without base_url"""

        # setup mock config
        mock_config.return_value = {
            "api_key": "sk_test_12345",
            "model_name": "als-intelligibility",
            "timeout": 3600,
            "base_url": None,
        }
        mock_validate_model.return_value = "als-intelligibility"
        mock_get_default_base_url.return_value = None  # No fallback URL either

        with pytest.raises(ConfigurationError):
            BaseInferenceClient(api_key="sk_test_12345")


@pytest.fixture
def valid_client_config():
    return {
        "api_key": "sk_live_test_key_1234567890123456",
        "base_url": "https://api.test.example.com",
    }


class TestTranscribeClient:

    def test_transcribe_client_initialises_with_transcribe_builder(self, valid_client_config):
        client = TranscribeClient(**valid_client_config)
        assert isinstance(client._payload_builder, TranscribePayloadBuilder)


class TestIntelligibilityClient:

    def test_intelligibility_client_initialises_with_intelligibility_builder(
        self, valid_client_config
    ):
        client = IntelligibilityClient(**valid_client_config, model_name="als-intelligibility-v1")
        assert isinstance(client._payload_builder, IntelligibilityPayloadBuilder)
