"""
Tests for the payload module.

Tests payload builder registry and factory function for retrieving
model-specific payload builders.
"""

import pytest

from redenlab_extract.payload import (
    IntelligibilityPayloadBuilder,
    TranscribePayloadBuilder,
    get_payload_builder,
)


class TestGetPayloadBuilder:
    """Test suite for get_payload_builder function."""

    @pytest.mark.parametrize(
        "model_name,expected_builder_class",
        [
            ("transcribe", TranscribePayloadBuilder),
            ("als-intelligibility-mtpa", IntelligibilityPayloadBuilder),
        ],
    )
    def test_returns_correct_builder_for_valid_models(self, model_name, expected_builder_class):
        """Should return the correct builder instance for each valid model name."""
        builder = get_payload_builder(model_name)

        # Verify it's the right type
        assert isinstance(builder, expected_builder_class)

        # Duck typing - verify it has the required methods
        assert hasattr(builder, "build")
        assert callable(builder.build)
        assert hasattr(builder, "validate_params")
        assert callable(builder.validate_params)

    @pytest.mark.parametrize(
        "invalid_model_name",
        [
            "invalid_model",
            "nonexistent",
            "TRANSCRIBE",  # Case sensitive - should not work
            " transcribe ",  # Whitespace - should not work
            "",  # Empty string
        ],
    )
    def test_raises_error_for_invalid_model_names(self, invalid_model_name):
        """Should raise ValueError for invalid or unsupported model names."""
        with pytest.raises(ValueError) as exc_info:
            get_payload_builder(invalid_model_name)

        error_message = str(exc_info.value)

        # Verify error message contains the invalid model name
        assert invalid_model_name in error_message or "Unsupported model" in error_message

        # Verify error message lists supported models
        assert "transcribe" in error_message
        assert "als-intelligibility" in error_message
        assert "Supported models" in error_message

    def test_raises_error_for_none_input(self):
        """Should raise ValueError when None is passed as model name."""
        with pytest.raises(ValueError) as exc_info:
            get_payload_builder(None)

        error_message = str(exc_info.value)
        assert "Unsupported model" in error_message

    def test_raises_error_for_non_string_input(self):
        """Should raise ValueError when non-string types are passed.

        Note: This raises ValueError (not KeyError) because the function
        treats all invalid inputs consistently, providing better error messages.
        """
        with pytest.raises(ValueError) as exc_info:
            get_payload_builder(123)

        error_message = str(exc_info.value)
        assert "Unsupported model" in error_message
        # Should list supported models to help the developer
        assert "Supported models" in error_message


class TestIntelligibilityPayloadBuilder:

    def test_intelligibility_builder_has_no_extra_params(self):
        builder = get_payload_builder("als-intelligibility-mtpa")
        payload = builder.build(
            job_id="test-job",
            file_key="test.wav",
        )

        assert set(payload.keys()) == {"job_id", "file_key"}


class TestTranscribePayloadBuilder:

    def test_transcribe_builder_includes_language_code(self):
        builder = get_payload_builder("transcribe")
        payload = builder.build(job_id="test-job", file_key="test.wav", language_code="en-US")

        assert payload["language_code"] == "en-US"
        assert payload["job_id"] == "test-job"
        assert payload["file_key"] == "test.wav"
