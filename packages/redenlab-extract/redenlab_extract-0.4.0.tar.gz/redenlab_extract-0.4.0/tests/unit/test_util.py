"""
Tests for the utility module
"""

import sys

sys.path.append("/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/src")

import pytest

from redenlab_extract.exceptions import ValidationError
from redenlab_extract.utils import get_content_type, validate_api_key_format

# --- Happy path: exact mappings ---


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("clip.wav", "audio/wav"),
        ("clip.wave", "audio/wav"),
        ("clip.flac", "audio/flac"),
        ("clip.ogg", "audio/ogg"),
    ],
)
def test_get_content_type_supported(filename, expected):
    assert get_content_type(filename) == expected


# --- Case-insensitivity + funky names ---


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("UPPER.WAV", "audio/wav"),
        ("mix.cAsE.fLaC", "audio/flac"),
        ("speace name.ogg", "audio/ogg"),
        ("multiple.dots.name.WAVE", "audio/wav"),
    ],
)
def test_get_content_type_is_case_sensitive_and_handles_multiple_dots(filename, expected):
    assert get_content_type(filename) == expected


# --- Unsupported extensions raise ValidationError ---


@pytest.mark.parametrize("filename", ["song.mp3", "audio.m4a", "noext", "weird.ext"])
def test_get_content_type_unsupported(filename):
    with pytest.raises(ValidationError):
        get_content_type(filename)


####### validate_api_key_format #######

# --- Happy path: correct keys ---


@pytest.mark.parametrize(
    "api_key",
    ["A8531V9AfBaCyVaU3WXV25AjYb0eCb4aaDggfs5s", "hagHjkeUyN67IOJBabdkifn7842JbjslI8Hlksnf"],
)
def test_api_key_format_supported(api_key):
    assert validate_api_key_format(api_key) is None


# --- small + empty + long + with whitespaces---


@pytest.mark.parametrize(
    "api_key",
    [
        "jYb0eCb4a",
        "",
        " A8531V9AfBaCyVaU3WXV25AjYb0eCb4aaDggfs5s",
        "hagHjkeUyN67IOJBabdkifn7842JbjslI8Hlksnf ",
    ],
)
def test_api_key_format_is_small_and_empty_and_has_whitespaces_raises(api_key):
    with pytest.raises(ValidationError):
        validate_api_key_format(api_key)


def test_api_key_format_long_raises():
    api_key = "x" * 101
    with pytest.raises(ValidationError):
        validate_api_key_format(api_key)
