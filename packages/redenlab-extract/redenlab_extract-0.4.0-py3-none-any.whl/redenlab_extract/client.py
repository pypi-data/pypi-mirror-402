"""
Main client for RedenLab ML SDK.

Provides the high-level InferenceClient class for running ML inference.
"""

import functools
import os
import statistics
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import api
from .auth import mask_api_key, validate_api_key
from .config import get_default_base_url, get_merged_config
from .exceptions import AuthenticationError, ConfigurationError, InferenceError, ValidationError
from .payload import get_payload_builder
from .polling import poll_until_complete, poll_with_callback
from .upload import upload_to_presigned_url
from .utils import (
    cleanup_chunk_files,
    get_audio_duration,
    get_content_type,
    split_audio_into_chunks,
    validate_file_path,
    validate_model_name,
    validate_timeout,
)


class BaseInferenceClient:
    """
    Base Client for RedenLab ML inference service.

    This is the superclass that other ML clients inherits from.
    Handles authentication, file upload, job submission, and result retrieval.

    Example:
        >>> client = InferenceClient(api_key="sk_live_...")
        >>> result = client.submit(file_path="audio.wav")
        >>> print(result['result'])

    Args:
        api_key: API key for authentication (optional, can use env var or config file)
        base_url: API base URL (optional, defaults to production endpoint)
        model_name: Model to use for inference (default: 'intelligibility')
        timeout: Maximum time to wait for inference in seconds (default: 3600)
        config_path: Path to config file (optional)
    """

    # Class attribute to indicate if this model supports health checks
    # Models that use SageMaker endpoints support health checks
    # Models that use AWS managed services (like Transcribe) do not
    _supports_health_check: bool = True

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int = 3600,
        config_path: str | None = None,
    ):
        """
        Initialise the inference client.

        Raises:
            AuthenticationError: If no API key is found
            ValidationError: If parameters are invalid
            ConfigurationError: If configuration is invalid
        """
        # Load configuration from all sources
        config_path_obj: Path | None = Path(config_path) if config_path else None
        config = get_merged_config(
            config_path=config_path_obj,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            timeout=timeout,
        )

        # Get and validate API key
        self.api_key: str = config.get("api_key")  # type: ignore
        if not self.api_key:
            raise AuthenticationError(
                "No API key found. Please set via:\n"
                "1. InferenceClient(api_key='...')\n"
                "2. Environment variable: REDENLAB_ML_API_KEY\n"
                "3. Config file: ~/.redenlab-ml/config.yaml"
            )
        validate_api_key(self.api_key)

        # Set base URL (use provided, or from config, or default)
        base_url = config.get("base_url") or get_default_base_url()
        if not base_url or not isinstance(base_url, str):
            raise ConfigurationError(
                "No API base URL configured. Please set via:\n"
                "1. InferenceClient(base_url='https://...')\n"
                "2. Environment variable: REDENLAB_ML_BASE_URL\n"
                "3. Config file: ~/.redenlab-ml/config.yaml"
            )
        self.base_url: str = base_url

        # Validate and set model name
        self.model_name = validate_model_name(model_name or config.get("model_name"))

        # Validate and set timeout
        self.timeout = validate_timeout(timeout if timeout != 3600 else config.get("timeout", 3600))

        # Get the payload builder for this model
        self._payload_builder = get_payload_builder(self.model_name)

    @property
    def display_model_name(self) -> str:
        """Model name for user-facing messages. Overrides in subclasses for alias"""
        return self.model_name

    def submit(self, file_path: str, **model_params: Any) -> str:
        """
        Upload file and submit inference job. Returns immediately without waiting.

        This method handles phases 1-3 of the inference workflow:
        1. Request presigned URL for upload
        2. Upload file to S3
        3. Submit inference job

        The job will process asynchronously on the server. Use poll() or get_status()
        to check results later.

        Args:
            file_path: Path to the audio file to process
            **model_params: Model-specific parameters (vary by model type)

        Returns:
            job_id: Job identifier string that can be used with poll() or get_status()

        Raises:
            ValidationError: If file path is invalid or file type not supported
            AuthenticationError: If API key is invalid
            UploadError: If file upload fails
            APIError: If API communication fails
            ValueError: If model_params are invalid for the model

        Example:
            >>> # Submit job and get job_id immediately
            >>> job_id = client.submit(file_path="audio.wav", language_code="en-US")
            >>> print(f"Submitted job: {job_id}")
            >>> # ... do other work ...
            >>> # Poll for results when ready
            >>> result = client.get_status(job_id)
        """
        # Validate file path
        file_path_obj = validate_file_path(file_path)

        # Get content type from file extension
        content_type = get_content_type(file_path)

        # Get filename
        filename = file_path_obj.name

        # Step 1: Request presigned URL
        job_id, upload_url, file_key, expires_in = api.request_presigned_url(
            base_url=self.base_url,
            api_key=self.api_key,
            filename=filename,
            model_name=self.model_name,
            content_type=content_type,
        )

        # Step 2: Upload file to S3
        upload_to_presigned_url(
            file_path=str(file_path_obj),
            presigned_url=upload_url,
            content_type=content_type,
        )

        # Step 3: Build model-specific payload using strategy pattern
        payload = self._payload_builder.build(job_id=job_id, file_key=file_key, **model_params)

        # Step 4: Submit inference job
        api.submit_inference_job(
            base_url=self.base_url,
            api_key=self.api_key,
            model_name=self.model_name,
            payload=payload,
        )

        return job_id

    def poll(
        self,
        job_id: str,
        timeout: int | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """
        Poll for inference job completion. Blocks until job completes, fails, or times out.

        This method handles phase 4 of the inference workflow:
        4. Poll for completion

        Args:
            job_id: Job identifier (returned from submit())
            timeout: Maximum time to wait in seconds (default: use client timeout)
            progress_callback: Optional callback function that receives status updates
                             during polling. Called with status dict after each check.

        Returns:
            Dictionary containing inference results:
            - job_id: Job identifier
            - status: 'completed'
            - result: Inference result data (model-specific)
            - created_at: Job creation timestamp
            - completed_at: Job completion timestamp

        Raises:
            InferenceError: If inference job fails
            TimeoutError: If inference doesn't complete within timeout
            APIError: If API communication fails

        Example:
            >>> # Poll with custom timeout and progress callback
            >>> def on_progress(status):
            ...     print(f"Status: {status['status']}")
            >>> result = client.poll(
            ...     job_id="abc-123",
            ...     timeout=7200,
            ...     progress_callback=on_progress
            ... )
            >>> print(result['result'])
        """
        poll_timeout = timeout if timeout is not None else self.timeout

        if progress_callback:
            result = poll_with_callback(
                get_status_func=lambda: self.get_status(job_id),
                job_id=job_id,
                progress_callback=progress_callback,
                timeout=poll_timeout,
            )
        else:
            result = poll_until_complete(
                get_status_func=lambda: self.get_status(job_id),
                job_id=job_id,
                timeout=poll_timeout,
            )

        return result

    def predict(
        self,
        file_path: str,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """
        Run inference on an audio file. Convenience method that submits and polls.

        This method handles the complete inference workflow:
        1. Request presigned URL for upload
        2. Upload file to S3
        3. Submit inference job
        4. Poll for completion
        5. Return results

        This is equivalent to: client.poll(client.submit(file_path))

        For batch processing of multiple files, use submit() and poll() separately
        for better efficiency.

        Args:
            file_path: Path to the audio file to process
            progress_callback: Optional callback function that receives status updates
                             during polling. Called with status dict after each check.

        Returns:
            Dictionary containing inference results:
            - job_id: Job identifier
            - status: 'completed'
            - result: Inference result data (model-specific)
            - created_at: Job creation timestamp
            - completed_at: Job completion timestamp

        Raises:
            ValidationError: If file path is invalid or file type not supported
            AuthenticationError: If API key is invalid
            UploadError: If file upload fails
            InferenceError: If inference job fails
            TimeoutError: If inference doesn't complete within timeout
            APIError: If API communication fails

        Example:
            >>> def on_progress(status):
            ...     print(f"Status: {status['status']}")
            >>> result = client.predict(
            ...     file_path="audio.wav",
            ...     progress_callback=on_progress
            ... )
            >>> print(result['result'])
        """
        job_id = self.submit(file_path)
        return self.poll(job_id, progress_callback=progress_callback)

    def get_status(self, job_id: str) -> dict[str, Any]:
        """
        Get the current status of an inference job.

        Args:
            job_id: Job ID to check

        Returns:
            Dictionary containing job status:
            - job_id: Job identifier
            - status: Current status (upload_pending, processing, completed, failed)
            - result: Inference result (if completed)
            - error: Error message (if failed)
            - created_at: Job creation timestamp
            - completed_at: Job completion timestamp (if completed)

        Raises:
            APIError: If status check fails
            AuthenticationError: If API key is invalid

        Example:
            >>> status = client.get_status(job_id="abc-123")
            >>> print(status['status'])
            'processing'
        """
        return api.get_job_status(
            base_url=self.base_url,
            api_key=self.api_key,
            job_id=job_id,
            model_name=self.model_name,
        )

    def health(self, timeout: int = 60) -> dict[str, Any]:
        """
        Check backend health and readiness for this model.

        This method pings the /{model_name}/health endpoint to check if the backend
        is ready to serve requests. It's useful for detecting cold starts - if the
        status is "warming_up" or response time is >5 seconds, the backend is waking
        up from sleep, which may cause longer processing times (up to 10+ minutes) for
        subsequent inference requests.

        IMPORTANT: This method only CHECKS status - it does NOT trigger backend warmup.
        To wake up a cold backend, use the warmup() method or submit an actual job.

        Note: Health checks are only available for SageMaker-based models
        (intelligibility, naturalness). Managed services like Transcribe don't
        support health checks as they're always available.

        Args:
            timeout: Maximum time to wait for health check in seconds (default: 60s)

        Returns:
            Dictionary containing:
            - status: Health status ("ready", "warming_up", "not_supported", or error)
            - ready: Boolean indicating if endpoint is ready to serve requests
            - response_time: Response time in seconds (if applicable)
            - is_warming: Boolean indicating if backend is warming up/cold starting
            - warning: Optional warning message if warming up detected

        Raises:
            APIError: If health check fails or times out (only for supported models)
            AuthenticationError: If API key is invalid

        Example:
            >>> # Check health before batch processing
            >>> health = client.health()
            >>> if health['status'] == 'not_supported':
            ...     print("Health check not supported, proceeding with submission")
            >>> elif not health['ready']:
            ...     print("Backend is cold - use client.warmup() to wake it up")
            ...     client.warmup()  # Wake up the backend
            >>> # Submit jobs...
        """
        # Check if this model supports health checks
        if not self._supports_health_check:
            return {
                "status": "not_supported",
                "ready": True,  # Assume ready since it's a managed service
                "is_warming": False,
                "message": (
                    f"Health checks not supported for {self.display_model_name}. "
                    "This model uses a managed service that is always available."
                ),
            }

        health_result = api.check_health(
            base_url=self.base_url,
            api_key=self.api_key,
            model_name=self.model_name,
            timeout=timeout,
        )

        # Add user-friendly warning message
        if health_result["is_warming"]:
            if health_result["status"] == "warming_up":
                health_result["warning"] = (
                    "Backend is currently warming up from cold start. "
                    "Initial requests may take 10+ minutes to process. "
                    "Please wait and check again, or proceed knowing processing may be delayed."
                )
            else:
                health_result["warning"] = (
                    f"Backend responded slowly ({health_result['response_time']}s), "
                    "which may indicate a cold start. Initial requests may take 10+ minutes. "
                    "Subsequent requests will be faster once the backend is warm."
                )

        return health_result

    def warmup(
        self,
        timeout: int = 900,
        show_progress: bool = True,
        poll_interval: int = 30,
    ) -> dict[str, Any]:
        """
        Warm up the backend by submitting a dummy inference job.

        This method creates a temporary 1-second silent audio file, submits it
        to the backend to trigger scale-up from cold state, waits for completion,
        and cleans up. This is useful before batch processing to avoid the 10+
        minute cold start delay on your first real job.

        Note: Only available for SageMaker-based models (intelligibility, naturalness).
        Managed services like Transcribe don't require warmup as they're always available.

        Args:
            timeout: Maximum time to wait for warmup in seconds (default: 900s = 15 min)
            show_progress: Whether to print progress messages (default: True)
            poll_interval: How often to check job status in seconds (default: 30s)

        Returns:
            Dictionary containing:
            - status: "success" if warmed up, "not_supported" if not applicable
            - warmup_time: Time taken to warm up in seconds
            - message: Informational message

        Raises:
            ConfigurationError: If warmup is not supported for this model
            TimeoutError: If warmup doesn't complete within timeout
            InferenceError: If warmup job fails
            APIError: If API communication fails

        Example:
            >>> # Before batch processing
            >>> client = IntelligibilityClient(api_key="...", model_name="als-intelligibility")
            >>> client.warmup()
            Warming up backend (this may take up to 10 minutes)...
            ⏳ Warming up... (30s)
            ⏳ Warming up... (60s)
            ...
            ✅ Backend warmed up successfully! (took 245s)
            >>>
            >>> # Now submit your real jobs - they'll be fast
            >>> for audio in files:
            ...     job_id = client.submit(audio)
        """
        import time

        # Check if this model supports warmup (only SageMaker models)
        if not self._supports_health_check:
            return {
                "status": "not_supported",
                "message": (
                    f"Warmup not needed for {self.display_model_name}. "
                    "This model uses a managed service that is always available."
                ),
            }

        start_time = time.time()

        if show_progress:
            print(
                f"Warming up backend for {self.display_model_name} (this may take up to 10 minutes)..."
            )

        # Create temporary dummy audio file
        temp_fd = None
        temp_path = None
        try:
            # Import soundfile (lazy import to avoid requiring it for all operations)
            try:
                import numpy as np
                import soundfile as sf
            except ImportError as e:
                raise ConfigurationError(
                    "Warmup requires numpy and soundfile packages. "
                    "Install with: pip install numpy soundfile"
                ) from e

            # Create temporary file with identifiable name
            temp_fd, temp_path = tempfile.mkstemp(
                suffix=".wav", prefix="warmup_redenlab_", dir=None  # Use system temp directory
            )

            # Close the file descriptor, we'll write with soundfile
            os.close(temp_fd)
            temp_fd = None

            # Generate 1 second of silence at 16kHz
            sample_rate = 16000
            duration = 1.0
            dummy_audio = np.zeros(int(sample_rate * duration), dtype=np.float32)

            # Write dummy audio to temp file
            sf.write(temp_path, dummy_audio, sample_rate)

            if show_progress:
                print("Submitting warmup job...")

            # Submit the dummy job to trigger backend warmup
            job_id = self.submit(temp_path)

            # Poll for completion with progress updates
            def progress_callback(status: dict[str, Any]) -> None:
                if show_progress:
                    elapsed = int(time.time() - start_time)
                    print(f"⏳ Warming up... ({elapsed}s)")

            # Poll with custom interval
            self.poll(
                job_id=job_id,
                timeout=timeout,
                progress_callback=progress_callback if show_progress else None,
            )

            warmup_time = int(time.time() - start_time)

            if show_progress:
                print(f"✅ Backend warmed up successfully! (took {warmup_time}s)")

            return {
                "status": "success",
                "warmup_time": warmup_time,
                "message": f"Backend ready. Warmup completed in {warmup_time}s.",
                "warmup_job_id": job_id,
            }

        finally:
            # Always cleanup temp file
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except OSError:
                    pass

            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass  # Best effort cleanup

    def __repr__(self) -> str:
        """Return string representation of the client."""
        parts = [
            f"api_key='{mask_api_key(self.api_key)}'",
            f"base_url='{self.base_url}'",
            f"model_name='{self.display_model_name}'",
            f"timeout={self.timeout}",
        ]
        return f"{self.__class__.__name__}({', '.join(parts)})"


# Client for Trasncribe service
class TranscribeClient(BaseInferenceClient):
    """
    Client to handle inference request for transcribe service.
    Args:
        language_code: Language code for transcription (optional, e.g., 'en-US', 'es-ES').
                    Only applicable for 'transcribe' model. Can be overridden per job.
    """

    # Transcribe uses AWS managed service, no health endpoint
    _supports_health_check = False

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 3600,
        config_path: str | None = None,
        language_code: str | None = None,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model_name="transcribe",
            timeout=timeout,
            config_path=config_path,
        )
        self.language_code = language_code
        # NOTE: need to write a function to validate the language_code and allow only the allowed ones

    def submit(self, file_path: str, **model_params: Any) -> str:
        """
        Upload a file and submit inference job to the transcribe service.

        The job will process asynchronously on the server. Use poll() or get_status()
        to check results later.

        Args:
            file_path: Path to the audio file to process
            **model_params: Model-specific parameters, including:
                language_code: Language code for transcription (optional, e.g., 'en-US', 'es-ES').
                              Overrides the client's default language_code if provided.

        Returns:
            job_id: Job identifier string that can be used with poll() or get_status()

        Raises:
            ValueError: If no language_code is provided (either here or in __init__)

        Example:
            >>> client = TranscribeClient(api_key="...", language_code="en-US")
            >>> job_id = client.submit("audio.wav")  # Uses default language
            >>> job_id = client.submit("audio.wav", language_code="es-ES")  # Override
        """
        # Extract language_code from model_params or use instance default
        language_code = model_params.get("language_code")
        # TODO: We can either decide to have the language code defined before calling submit or for the whole client
        # and enforce one
        lang_code = language_code or self.language_code

        # Call parent submit with language_code as model_param
        return super().submit(file_path, language_code=lang_code)

    def __repr__(self) -> str:
        """Return string representation of the client."""
        parts = [
            f"api_key='{mask_api_key(self.api_key)}'",
            f"base_url='{self.base_url}'",
            f"timeout={self.timeout}",
        ]
        if self.language_code:
            parts.append(f"language_code='{self.language_code}'")
        return f"TranscribeClient({', '.join(parts)})"


class ChunkedInferenceClient(BaseInferenceClient):

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int = 3600,
        config_path: str | None = None,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            model_name=model_name,
            config_path=config_path,
        )

    def submit(self, file_path: str, **model_params: Any) -> str:
        """
        Upload a file and submit inference job to the intelligibility service.

        The job will process asynchronously on the server. Use poll() or get_status()
        to check results later.

        Note: For long audio files (>60s), use predict() instead which handles
        automatic chunking to avoid memory issues.

        Args:
            file_path: Path to the audio file to process
            **model_params: Model-specific parameters (not used by intelligibility model)

        Returns:
            job_id: Job identifier string that can be used with poll() or get_status()

        Example:
            >>> client = IntelligibilityClient(api_key="...")
            >>> job_id = client.submit("audio.wav")
            >>> result = client.poll(job_id)
        """
        # Call parent submit with model params (intelligibility doesn't use any, but signature must match)
        return super().submit(file_path, **model_params)

    def _submit_with_chunking(self, file_path: str) -> list[str]:
        """
        Internal method to submit audio with automatic chunking for long files.

        Checks audio duration and splits into 60-second chunks if needed.
        Each chunk is uploaded separately and gets its own job_id.

        Args:
            file_path: Path to the audio file to process

        Returns:
            List of job_ids (one per chunk, or single job_id if no chunking needed)

        Raises:
            ValidationError: If file is invalid
            ImportError: If soundfile is not installed
        """
        # Check audio duration
        try:
            duration = get_audio_duration(file_path)
        except ImportError:
            # If soundfile not installed, fall back to normal submission
            # and let the backend handle it (may fail for long files)
            return [self.submit(file_path)]

        print(f"audio duration is = {duration}")

        # If duration <= 60s, no chunking needed
        if duration <= 60:
            return [self.submit(file_path)]

        # Split audio into chunks
        chunk_files = split_audio_into_chunks(file_path, chunk_duration=50, overlap=1.0)

        # If split returned empty (shouldn't happen but defensive), submit normally
        if not chunk_files:
            return [self.submit(file_path)]

        # Submit each chunk
        job_ids = []
        try:
            for chunk_file in chunk_files:
                job_id = self.submit(chunk_file)
                job_ids.append(job_id)
            return job_ids
        finally:
            # Always cleanup temp chunk files
            cleanup_chunk_files(chunk_files)

    def poll_multiple(
        self,
        job_ids: list[str],
        timeout: int | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """
        Poll multiple inference jobs and aggregate their results.

        This method is useful when processing long audio files that have been
        split into chunks. It polls all chunk jobs and combines their results.

        Args:
            job_ids: List of job identifiers to poll
            score_key: Which score we are polling i.e. intelligibility or naturalness
            timeout: Maximum time to wait in seconds (default: use client timeout)
            progress_callback: Optional callback function that receives status updates.
                             Called with enhanced status dict including chunk progress.

        Returns:
            Dictionary containing aggregated results:
            - job_id: Combined job identifier
            - status: 'completed' or 'partial' (if some chunks failed)
            - result: Aggregated score
            - chunk_scores: Individual scores from each chunk
            - num_chunks: Total number of chunks
            - failed_chunks: List of failed chunk indices (if any)

        Raises:
            InferenceError: If all chunks fail
            TimeoutError: If polling doesn't complete within timeout
            APIError: If API communication fails

        Example:
            >>> job_ids = ["job-1", "job-2", "job-3"]
            >>> result = client.poll_multiple(job_ids)
            >>> print(result['result']['intelligibility_score'])  # Averaged score
        """
        total_chunks = len(job_ids)
        results = []
        failed_chunks = []

        # Helper to wrap progress callback with chunk context
        def _add_chunk_context(
            status: dict[str, Any],
            chunk_index: int,
            total: int,
            callback: Callable[[dict[str, Any]], None],
        ) -> None:
            enhanced_status = status.copy()
            enhanced_status["chunk_index"] = chunk_index
            enhanced_status["total_chunks"] = total
            callback(enhanced_status)

        for i, job_id in enumerate(job_ids):
            try:
                # Create callback for this specific chunk
                chunk_callback = None
                if progress_callback:
                    chunk_callback = functools.partial(
                        _add_chunk_context,
                        chunk_index=i,
                        total=total_chunks,
                        callback=progress_callback,
                    )

                # Poll this chunk's job
                result = self.poll(
                    job_id,
                    timeout=timeout,
                    progress_callback=chunk_callback,
                )

                if result["status"] == "completed":
                    results.append(result)
                else:
                    failed_chunks.append(i)

            except Exception:
                # Track failed chunk but continue polling others
                failed_chunks.append(i)
                # Optionally log the error or add to results
                continue

        # Check if we have any successful results
        if not results:
            raise InferenceError(
                f"All {total_chunks} chunks failed. " f"Failed chunk indices: {failed_chunks}"
            )

        # Aggregate results (partial results with warning if some failed)
        if isinstance(self, IntelligibilityClient):
            score_key = "intelligibility_score"
        elif isinstance(self, NaturalnessClient):
            score_key = "naturalness_score"

        aggregated = self._aggregate_results(results, score_key, failed_chunks)

        return aggregated

    def _aggregate_results(
        self,
        results: list[dict[str, Any]],
        score_key: str,
        failed_chunks: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Internal method to aggregate scores from multiple chunks.

        Calculates simple average of scores and includes metadata
        about chunking and any failures.

        Args:
            results: List of successful job results
            failed_chunks: Optional list of failed chunk indices

        Returns:
            Aggregated result dictionary
        """
        if failed_chunks is None:
            failed_chunks = []

        # Extract scores
        scores = [r["result"][score_key] for r in results]

        # Calculate simple average
        avg_score = sum(scores) / len(scores)

        # Calculate standard deviation (0 if only one chunk)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0.0

        # Determine status
        status = "completed" if not failed_chunks else "partial"

        # Build aggregated result
        aggregated = {
            "job_id": f"chunked_{results[0]['job_id']}",  # Use first chunk's ID as base
            "status": status,
            "result": {
                score_key: avg_score,
                "std_dev": std_dev,
                "chunk_scores": scores,
                "num_chunks": len(results),
                "aggregation_method": "average",
            },
            "created_at": min(r["created_at"] for r in results),
            "completed_at": max(r.get("completed_at", r["created_at"]) for r in results),
        }

        # Add failure info if applicable
        if failed_chunks:
            aggregated["result"]["failed_chunks"] = failed_chunks
            aggregated["result"][
                "success_rate"
            ] = f"{len(results)}/{len(results) + len(failed_chunks)}"

        return aggregated

    def predict(
        self,
        file_path: str,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """
        Run inference on an audio file with automatic chunking for long files.

        This method automatically detects audio duration and splits files longer
        than 60 seconds into chunks to avoid memory issues. Each chunk is processed
        separately and results are aggregated.

        For short files (<=60s), behaves identically to the base predict() method.
        For long files (>60s), automatically chunks and aggregates results.

        Args:
            file_path: Path to the audio file to process
            score_key: Which score we are predicting i.e. intelligibility_score or naturalness_score
            progress_callback: Optional callback function that receives status updates.
                             For chunked files, status includes chunk_index and total_chunks.

        Returns:
            Dictionary containing inference results:
            - job_id: Job identifier (or composite for chunked files)
            - status: 'completed' or 'partial' (if some chunks failed)
            - result: Inference result with score_key
            - For chunked files, also includes:
              - chunk_scores: Individual scores from each chunk
              - num_chunks: Total number of chunks processed
              - aggregation_method: How scores were combined

        Raises:
            ValidationError: If file path is invalid or file type not supported
            AuthenticationError: If API key is invalid
            UploadError: If file upload fails
            InferenceError: If inference job fails
            TimeoutError: If inference doesn't complete within timeout
            APIError: If API communication fails

        Example:
            >>> client = IntelligibilityClient(api_key="...")
            >>>
            >>> # Short file - normal processing
            >>> result = client.predict("short_audio.wav")
            >>> print(result['result']['intelligibility_score'])
            >>>
            >>> # Long file - automatic chunking
            >>> result = client.predict("long_audio_62s.wav")
            >>> print(result['result']['intelligibility_score'])  # Averaged score
            >>> print(result['result']['chunk_scores'])  # Individual chunk scores
            >>> print(result['result']['num_chunks'])  # Number of chunks (e.g., 2)
        """
        # Submit with automatic chunking
        job_ids = self._submit_with_chunking(file_path)

        # If single job (no chunking), use standard polling
        if len(job_ids) == 1:
            return self.poll(job_ids[0], progress_callback=progress_callback)

        # Multiple jobs (chunked) - use poll_multiple with aggregation
        return self.poll_multiple(job_ids, progress_callback=progress_callback)


# Client for Intelligibility service
class IntelligibilityClient(ChunkedInferenceClient):
    """
    Client to handle inference requests for intelligibility service.

    This is the simplest client - intelligibility requires no additional parameters.

    Example:
        >>> client = IntelligibilityClient(api_key="...")
        >>> job_id = client.submit("audio.wav")
        >>> result = client.get_status(job_id)
        >>> print(result['result'])
    """

    VALID_INTELLIGIBILITY_MODELS: tuple[str, ...] = (
        "ataxia-intelligibility",
        "als-intelligibility-v1",
        "als-intelligibility-v2",
    )

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int = 3600,
        config_path: str | None = None,
    ):

        if model_name not in type(self).VALID_INTELLIGIBILITY_MODELS:
            raise ValidationError(
                f"Invalid model: {model_name}. "
                f"Choose from {type(self).VALID_INTELLIGIBILITY_MODELS}"
            )

        # After validation, model_name is guaranteed to be a valid string
        assert model_name is not None
        self._user_model_name: str = model_name

        _MODEL_ALIAS_MAP = {
            "als-intelligibility-v1": "als-intelligibility-mtpa",
            "als-intelligibility-v2": "als-intelligibility-eals",
        }

        backend_model_name = _MODEL_ALIAS_MAP.get(model_name, model_name)

        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            model_name=backend_model_name,
            config_path=config_path,
        )

    @property
    def display_model_name(self) -> str:
        return self._user_model_name


# Client for Naturalness service
class NaturalnessClient(ChunkedInferenceClient):
    """
    Client to handle inference requests for Naturalness service.

    This is the simplest client - naturalness requires no additional parameters.

    Example:
        >>> client = NaturalnessClient((api_key="...")
        >>> job_id = client.submit("audio.wav")
        >>> result = client.get_status(job_id)
        >>> print(result['result'])
    """

    VALID_INTELLIGIBILITY_MODELS: tuple[str, ...] = (
        "ataxia-naturalness",
        "als-naturalness-v1",
        "als-naturalness-v2",
    )

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int = 3600,
        config_path: str | None = None,
    ):

        if model_name not in type(self).VALID_INTELLIGIBILITY_MODELS:
            raise ValidationError(
                f"Invalid model: {model_name}. "
                f"Choose from {type(self).VALID_INTELLIGIBILITY_MODELS}"
            )

        # After validation, model_name is guaranteed to be a valid string
        assert model_name is not None
        self._user_model_name: str = model_name

        _MODEL_ALIAS_MAP = {
            "als-naturalness-v1": "als-naturalness-mtpa",
            "als-naturalness-v2": "als-naturalness-eals",
        }

        backend_model_name = _MODEL_ALIAS_MAP.get(model_name, model_name)

        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            model_name=backend_model_name,
            config_path=config_path,
        )

    @property
    def display_model_name(self) -> str:
        return self._user_model_name


# Backward compatibility: InferenceClient = BaseInferenceClient
# This allows existing code to continue working
InferenceClient = BaseInferenceClient
