# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-01-21

### Added
- Model versioning with alias support (v1/v2 aliases map to backend model names)
- Integration tests for `IntelligibilityClient` and `TranscribeClient`
- Standard deviation (`std_dev`) output when calling `_poll_multiple`

### Changed
- **Breaking**: Renamed package from `redenlab_ml` to `redenlab_extract`
- Updated imports throughout codebase to use new package name
- Improved type annotations for mypy compliance

## [0.3.0] - 2026-01-13

### Added
- Added all intelligibility and naturalness models
- Intelligibility and naturalness can chunk audio and run inference on them to provide aggregate results
- Users can check health of endpoints and wake them up

### Changed
- Updated minimum Python version requirement to 3.10+ (using modern `|` union type syntax)
- Fixed code formatting to comply with Black formatter
- Fixed type checking issues for mypy compliance

## [0.2.0] - 2025-01-15

### Added
- **New `submit()` method** - Upload file and submit inference job without blocking, returns `job_id` immediately
- **New `poll()` method** - Poll for job completion with customizable timeout and progress callbacks
- Support for efficient batch processing by separating submit and poll phases
- Ability to resume polling for jobs after program restart (using `job_id`)

### Changed
- Refactored `predict()` to use `submit()` + `poll()` internally (backward compatible, same behavior)
- Improved documentation with batch processing examples
- Added `test_batch_inference.py` demonstrating three usage patterns

### Documentation
- Added batch processing guide in README
- Updated API documentation with submit/poll examples

## [0.1.0] - 2025-01-10

### Added
- Initial release
- Core `InferenceClient` for ML inference
- File upload to S3 via presigned URLs
- Async job management with polling
- Authentication via API key
- Support for multiple models (intelligibility, speaker diarization, etc.)
- Retry logic with exponential backoff
- Comprehensive error handling
- Configuration via environment variables and config files

[Unreleased]: https://github.com/redenlab/redenlab-ml-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/redenlab/redenlab-ml-sdk/releases/tag/v0.1.0
