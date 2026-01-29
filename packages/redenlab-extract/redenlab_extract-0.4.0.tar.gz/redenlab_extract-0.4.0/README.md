# RedenLab Extract SDK

Python SDK for RedenLab's ML inference service. Run machine learning models on audio files using Redenlab's proprietary endpoints.

## Features

- Simple, Pythonic API for ML inference
- Async job management with polling
- Built-in retry logic and error handling
- Support for multiple ML models

## Installation

```bash
pip install redenlab-extract
```

## Quick Start

```python
from redenlab_extract import InferenceClient

# Initialize client with API key
client = InferenceClient(api_key="sk_live_your_api_key_here")

# Run inference on an audio file
result = client.predict(file_path="audio.wav")

print(result)
# {
#   'job_id': 'uuid',
#   'status': 'completed',
#   'result': {'intelligibility_score': 0.85},
#   'created_at': '2025-01-15T10:30:00Z',
#   'completed_at': '2025-01-15T10:35:00Z'
# }
```

## Authentication

The SDK looks for your API key in the following order:

1. **Constructor parameter**: `InferenceClient(api_key="sk_live_...")`
2. **Environment variable**: `REDENLAB_ML_API_KEY`
3. **Config file**: `~/.redenlab-ml/config.yaml`

### Using Environment Variables

```bash
export REDENLAB_ML_API_KEY=sk_live_your_api_key_here
```

```python
from redenlab_extract import InferenceClient

# API key is loaded from environment
client = InferenceClient()
result = client.predict(file_path="audio.wav")
```

### Using Config File

Create `~/.redenlab-ml/config.yaml`:

```yaml
api_key: sk_live_your_api_key_here
base_url: https://your-api-gateway-url.amazonaws.com/prod  # optional
model_name: als-intelligibility
```

```python
from redenlab_extract import InferenceClient

# API key is loaded from config file
client = InferenceClient()
result = client.predict(file_path="audio.wav")
```

## Advanced Usage

### Specify Model

```python
client = InferenceClient(
    api_key="sk_live_...",
    model_name="speaker_diarisation_workflow"
)
```

Available models:
- `als-intelligibility`
- `speaker_diarisation_workflow`
- `ataxia-naturalness`
- `ataxia-intelligibility`

### Custom Timeout

```python
client = InferenceClient(
    api_key="sk_live_...",
    timeout=7200  # 2 hours
)
```

### Batch Processing (Submit + Poll Pattern)

For processing multiple files efficiently, use `submit()` and `poll()` separately:

```python
# Submit all jobs first (fast - no waiting)
job_ids = []
for audio_file in audio_files:
    job_id = client.submit(file_path=audio_file)
    job_ids.append(job_id)
    print(f"Submitted: {job_id}")

# Poll for results (efficient - single loop checking all jobs)
results = {}
pending = set(job_ids)

while pending:
    for job_id in list(pending):
        status = client.get_status(job_id)

        if status['status'] == 'completed':
            results[job_id] = status['result']
            pending.remove(job_id)
        elif status['status'] == 'failed':
            results[job_id] = {'error': status.get('error')}
            pending.remove(job_id)

    if pending:
        time.sleep(10)  # Check all jobs every 10 seconds

print(f"Processed {len(results)} files!")
```

### Submit and Poll Separately

```python
# Submit job and get job_id immediately
job_id = client.submit(file_path="audio.wav")
print(f"Job submitted: {job_id}")

# ... do other work, or even exit and resume later ...

# Poll when ready
result = client.poll(job_id)
print(result['result'])
```

### Check Job Status (Non-blocking)

```python
# Get status of a running job without blocking
status = client.get_status(job_id="existing-job-uuid")
print(status['status'])  # 'upload_pending', 'processing', 'completed', 'failed'
```

## Configuration Options

| Parameter | Environment Variable | Config File | Default |
|-----------|---------------------|-------------|---------|
| `api_key` | `REDENLAB_ML_API_KEY` | `api_key` | Required |
| `base_url` | `REDENLAB_ML_BASE_URL` | `base_url` | Production endpoint |
| `model_name` | `REDENLAB_ML_MODEL` | `model_name` | `intelligibility` |
| `timeout` | `REDENLAB_ML_TIMEOUT` | `timeout` | `3600` (1 hour) |

## Supported File Types

- WAV (`.wav`)
- FLAC (`.flac`)

## Requirements

- Python 3.10+
- `requests`
- `tenacity`
- `pyyaml`

## Examples

See the [examples/](examples/) directory for more usage examples:

- [quickstart.py](examples/quickstart.py) - Basic usage
- [batch_inference.py](examples/batch_inference.py) - Process multiple files
- [error_handling.py](examples/error_handling.py) - Robust error handling

## Documentation

- [API Reference](docs/api_reference.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

## Support

- Email: support@redenlab.com
- Website: https://redenlab.com

## License

MIT License - see [LICENSE](LICENSE) file for details

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.
