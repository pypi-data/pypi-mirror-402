"""
Utility functions for RedenLab ML SDK.

Provides validation, file handling, and other helper functions.
"""

import os
import tempfile
from pathlib import Path

import numpy as np

from .exceptions import ValidationError

# Supported audio file extensions and their MIME types
# NOTE: These supported file formated are based on what soundfile library supports
# That is used for calculating audio file duration
SUPPORTED_AUDIO_FORMATS = {
    ".wav": "audio/wav",
    ".wave": "audio/wav",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
}


def validate_file_path(file_path: str) -> Path:
    """
    Validate that a file path exists and is readable.

    Args:
        file_path: Path to the file to validate

    Returns:
        Path object for the validated file

    Raises:
        ValidationError: If file doesn't exist or is not readable
    """
    if not file_path:
        raise ValidationError("File path cannot be empty")

    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    if not os.access(path, os.R_OK):
        raise ValidationError(f"File is not readable: {file_path}")

    return path


def get_content_type(file_path: str) -> str:
    """
    Determine the content type (MIME type) for a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        Content type string (e.g., 'audio/wav')

    Raises:
        ValidationError: If file extension is not supported
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in SUPPORTED_AUDIO_FORMATS:
        supported = ", ".join(SUPPORTED_AUDIO_FORMATS.keys())
        raise ValidationError(
            f"Unsupported file format: {extension}. " f"Supported formats: {supported}"
        )

    return SUPPORTED_AUDIO_FORMATS[extension]


def validate_model_name(model_name: str | None) -> str:
    """
    Validate that the model name is valid.

    Args:
        model_name: Name of the model

    Returns:
        Validated model name

    Raises:
        ValidationError: If model name is invalid
    """
    if not model_name:
        raise ValidationError("Model name cannot be empty")

    if not isinstance(model_name, str):
        raise ValidationError(f"Model name must be a string, got {type(model_name)}")

    # Model names should be lowercase with hyphens or underscores
    valid_chars = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if not all(c in valid_chars for c in model_name):
        raise ValidationError(
            f"Invalid model name: {model_name}. "
            "Model names must contain only lowercase letters, numbers, hyphens, and underscores."
        )

    return model_name


def validate_timeout(timeout: int | None) -> int:
    """
    Validate and normalize timeout value.

    Args:
        timeout: Timeout in seconds (None for default)

    Returns:
        Validated timeout in seconds

    Raises:
        ValidationError: If timeout is invalid
    """
    if timeout is None:
        return 3600  # Default: 1 hour

    if not isinstance(timeout, int):
        raise ValidationError(f"Timeout must be an integer, got {type(timeout)}")

    if timeout <= 0:
        raise ValidationError(f"Timeout must be positive, got {timeout}")

    if timeout > 86400:  # 24 hours
        raise ValidationError(f"Timeout cannot exceed 24 hours (86400 seconds), got {timeout}")

    return timeout


def validate_api_key_format(api_key: str) -> None:
    """
    Validate API key format.

    Args:
        api_key: API key to validate

    Raises:
        ValidationError: If API key format is invalid
    """
    if not api_key:
        raise ValidationError("API key cannot be empty")

    if not isinstance(api_key, str):
        raise ValidationError(f"API key must be a string, got {type(api_key)}")

    # and have reasonable length
    if len(api_key) < 10:
        raise ValidationError(
            f"API key is too short (minimum 10 characters), got {len(api_key)} characters"
        )

    if len(api_key) > 100:
        raise ValidationError(
            f"API key is too long (maximum 100 characters), got {len(api_key)} characters"
        )

    # Check for common mistakes
    if api_key.startswith(" ") or api_key.endswith(" "):
        raise ValidationError("API key contains leading or trailing whitespace")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes

    Raises:
        ValidationError: If file cannot be accessed
    """
    try:
        path = Path(file_path)
        return path.stat().st_size
    except OSError as e:
        raise ValidationError(f"Cannot get file size: {e}") from e


def get_audio_duration(file_path: str) -> float:
    """
    Get audio file duration in seconds without loading the entire file.

    Args:
        file_path: Path to the audio file

    Returns:
        Duration in seconds

    Raises:
        ValidationError: If file cannot be read or soundfile is not installed
        ImportError: If soundfile is not installed
    """
    try:
        import soundfile as sf
    except ImportError as e:
        raise ImportError(
            "soundfile is required for audio chunking. Install it with: pip install soundfile"
        ) from e

    try:
        info = sf.info(file_path)
        return float(info.duration)
    except Exception as e:
        raise ValidationError(f"Cannot read audio file duration: {e}") from e


def split_audio_into_chunks(
    file_path: str, chunk_duration: int = 60, overlap: float = 1.0
) -> list[str]:
    """
    Split audio file into chunks with overlap.

    Creates temporary chunk files with naming pattern:
    {base_name}_chunk_{index}_of_{total}.{ext}

    Args:
        file_path: Path to the audio file to split
        chunk_duration: Duration of each chunk in seconds (default: 60)
        overlap: Overlap between chunks in seconds (default: 1.0)

    Returns:
        List of paths to temporary chunk files

    Raises:
        ValidationError: If file cannot be read or split
        ImportError: If soundfile is not installed

    Example:
        >>> chunks = split_audio_into_chunks("long_audio.wav", chunk_duration=60)
        >>> # Returns: ["/tmp/xyz/long_audio_chunk_0_of_3.wav", ...]
    """
    try:
        import soundfile as sf
    except ImportError as e:
        raise ImportError(
            "soundfile and numpy are required for audio chunking. "
            "Install them with: pip install soundfile numpy"
        ) from e

    # Validate file exists
    path = validate_file_path(file_path)

    try:
        # Read audio file
        data, samplerate = sf.read(str(path))

        # Calculate total duration
        total_duration = len(data) / samplerate

        # If audio is shorter than chunk_duration, no need to split
        if total_duration <= chunk_duration:
            # Return empty list to signal no chunking needed
            return []

        # Calculate chunk parameters
        chunk_samples = int(chunk_duration * samplerate)
        overlap_samples = int(overlap * samplerate)
        step_samples = chunk_samples - overlap_samples

        # Calculate number of chunks
        num_chunks = int(np.ceil((len(data) - overlap_samples) / step_samples))

        # Create temp directory for chunks
        temp_dir = tempfile.mkdtemp(prefix="redenlab_audio_chunks_")

        # Get file info for naming
        base_name = path.stem
        ext = path.suffix

        chunk_files = []

        for i in range(num_chunks):
            # Calculate chunk boundaries
            start = i * step_samples
            end = min(start + chunk_samples, len(data))

            # Extract chunk data
            chunk_data = data[start:end]

            # Create chunk filename with pattern
            chunk_filename = f"{base_name}_chunk_{i}_of_{num_chunks}{ext}"
            chunk_path = os.path.join(temp_dir, chunk_filename)

            # Write chunk to temp file
            sf.write(chunk_path, chunk_data, samplerate)
            chunk_files.append(chunk_path)

        return chunk_files

    except Exception as e:
        raise ValidationError(f"Failed to split audio file: {e}") from e


def cleanup_chunk_files(chunk_files: list[str]) -> None:
    """
    Clean up temporary chunk files and their parent directory.

    Args:
        chunk_files: List of chunk file paths to clean up

    Note:
        Silently ignores errors during cleanup to avoid disrupting main workflow.
    """
    if not chunk_files:
        return

    try:
        # Get parent directory (should be the temp dir we created)
        temp_dir = os.path.dirname(chunk_files[0])

        # Remove all files
        for chunk_file in chunk_files:
            try:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
            except Exception:
                pass  # Ignore individual file errors

        # Remove temp directory
        try:
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception:
            pass  # Ignore directory removal errors

    except Exception:
        pass  # Silently ignore all cleanup errors
