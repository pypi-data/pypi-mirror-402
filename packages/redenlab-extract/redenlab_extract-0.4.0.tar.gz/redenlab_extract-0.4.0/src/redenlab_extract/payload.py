"""
Payload builders for model-specific inference requests.

Uses the Strategy pattern to encapsulate model-specific parameter handling.
Each model gets its own builder that knows how to construct the API payload.
"""

from abc import ABC, abstractmethod
from typing import Any


class PayloadBuilder(ABC):
    """
    Abstract base class for model-specific payload builders.

    Each model implementation defines how to build its specific payload
    from core fields and model-specific parameters.

    IMPORTANT: Builder instances are shared (singleton pattern).
    Implementations MUST be stateless - do not store data in self.
    All state should be passed as parameters.
    """

    @abstractmethod
    def build(self, job_id: str, file_key: str, **model_params: Any) -> dict[str, Any]:
        """
        Build the payload for API submission.

        Args:
            job_id: Job identifier
            file_key: S3 file key
            **model_params: Model-specific parameters

        Returns:
            Dictionary payload for API request
        """
        pass

    @abstractmethod
    def validate_params(self, **model_params: Any) -> None:
        """
        Validate model-specific parameters.

        Args:
            **model_params: Parameters to validate

        Raises:
            ValueError: If parameters are invalid
        """
        pass


class TranscribePayloadBuilder(PayloadBuilder):
    """Payload builder for the transcribe model."""

    def build(self, job_id: str, file_key: str, **model_params: Any) -> dict[str, Any]:
        """
        Build transcribe model payload.

        Args:
            job_id: Job identifier
            file_key: S3 file key
            **model_params: Must include 'language_code'

        Returns:
            Payload with job_id, file_key, and language_code
        """
        self.validate_params(**model_params)

        return {
            "job_id": job_id,
            "file_key": file_key,
            "language_code": model_params["language_code"],
        }

    def validate_params(self, **model_params: Any) -> None:
        """Validate that language_code is provided."""
        if "language_code" not in model_params:
            raise ValueError(
                "transcribe model requires 'language_code' parameter "
                "(e.g., 'en-US', 'es-ES')"
                "Provide it either in TranscribeClient(..., language_code='en-US') "
                "or in submit(file_path, language_code='en-US')"
            )

        language_code = model_params["language_code"]
        if not isinstance(language_code, str) or not language_code:
            raise ValueError(f"language_code must be a non-empty string, got: {language_code!r}")


class IntelligibilityPayloadBuilder(PayloadBuilder):
    """Payload builder for the intelligibility model."""

    def build(self, job_id: str, file_key: str, **model_params: Any) -> dict[str, Any]:
        """
        Build intelligibility model payload.

        Args:
            job_id: Job identifier
            file_key: S3 file key
            **model_params: No extra parameters required

        Returns:
            Payload with just job_id and file_key
        """
        self.validate_params(**model_params)

        return {
            "job_id": job_id,
            "file_key": file_key,
        }

    def validate_params(self, **model_params: Any) -> None:
        """Validate that no unexpected parameters are provided."""
        if model_params:
            unexpected = ", ".join(model_params.keys())
            raise ValueError(
                f"intelligibility model does not accept parameters, " f"but got: {unexpected}"
            )


# Registry mapping model names to their payload builders
PAYLOAD_BUILDERS: dict[str, PayloadBuilder] = {
    "transcribe": TranscribePayloadBuilder(),
    "als-intelligibility-mtpa": IntelligibilityPayloadBuilder(),
    "als-intelligibility-eals": IntelligibilityPayloadBuilder(),
    "als-naturalness-mtpa": IntelligibilityPayloadBuilder(),
    "als-naturalness-eals": IntelligibilityPayloadBuilder(),
    "ataxia-intelligibility": IntelligibilityPayloadBuilder(),
    "ataxia-naturalness": IntelligibilityPayloadBuilder(),
}


def get_payload_builder(model_name: str) -> PayloadBuilder:
    """
    Get the payload builder for a given model.

    Args:
        model_name: Name of the model

    Returns:
        PayloadBuilder instance for the model

    Raises:
        ValueError: If model is not supported
    """
    if model_name not in PAYLOAD_BUILDERS:
        supported = ", ".join(PAYLOAD_BUILDERS.keys())
        raise ValueError(f"Unsupported model: {model_name!r}. " f"Supported models: {supported}")

    return PAYLOAD_BUILDERS[model_name]


def register_payload_builder(model_name: str, builder: PayloadBuilder) -> None:
    """
    Register a custom payload builder for a model.

    This allows users to extend the SDK with custom models.

    Args:
        model_name: Name of the model
        builder: PayloadBuilder instance

    Example:
        >>> class CustomBuilder(PayloadBuilder):
        ...     def build(self, job_id, file_key, **params):
        ...         return {"job_id": job_id, "file_key": file_key, "custom": params}
        ...     def validate_params(self, **params):
        ...         pass
        >>> register_payload_builder("custom_model", CustomBuilder())
    """
    PAYLOAD_BUILDERS[model_name] = builder
