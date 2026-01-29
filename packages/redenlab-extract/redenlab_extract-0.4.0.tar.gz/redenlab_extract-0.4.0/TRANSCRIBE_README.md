# Batch Transcription with TextGrid Generation

This directory contains scripts for batch transcription of audio files with automatic TextGrid generation.

## Features

- **Batch Processing**: Submit multiple audio files at once
- **Multi-language Support**: Different language codes per file
- **Automatic TextGrid Generation**: Creates Praat TextGrid files from transcription results
- **Resume Capability**: Handles failures gracefully
- **Progress Tracking**: Shows status for each file

## Quick Start

### 1. Install Dependencies

```bash
# Install the RedenLab ML SDK
pip install -e .

# Install TextGrid dependencies (optional but recommended)
pip install praatio pandas
```

### 2. Set API Key

```bash
export REDENLAB_ML_API_KEY='your-api-key-here'
```

### 3. Run Example Script

```bash
# Edit transcribe_example.py to add your files
python transcribe_example.py
```

## Usage Examples

### Example 1: Single File

```python
from redenlab_extract import InferenceClient

client = InferenceClient(
    api_key="sk_live_...",
    base_url="https://daq8c71oh4.execute-api.us-west-2.amazonaws.com/prod/",
    model_name="transcribe",
    language_code="en-US"
)

# Submit and wait for result
result = client.predict("audio.wav")
print(result['transcript'])
```

### Example 2: Batch with Different Languages

```python
# Configure files in transcribe_example.py
FILES_TO_PROCESS = [
    ("/path/to/english.wav", "en-US"),
    ("/path/to/spanish.wav", "es-ES"),
    ("/path/to/french.wav", "fr-FR"),
]

# Run the script
python transcribe_example.py
```

### Example 3: Using the Batch Script Directly

```python
import batch_transcribe_textgrid as batch_transcribe

# Configure
batch_transcribe.FILES_AND_LANGUAGES = [
    ("audio1.wav", "en-US"),
    ("audio2.wav", "en-AU"),
]

batch_transcribe.RESULTS_DIR = "./my_results"
batch_transcribe.TEXTGRID_DIR = "./my_textgrids"

# Run
batch_transcribe.main()
```

## Supported Language Codes

Common language codes:
- `en-US` - English (United States)
- `en-AU` - English (Australia)
- `en-GB` - English (United Kingdom)
- `es-ES` - Spanish (Spain)
- `fr-FR` - French (France)
- `de-DE` - German (Germany)
- `it-IT` - Italian (Italy)
- `pt-BR` - Portuguese (Brazil)
- `ja-JP` - Japanese
- `ko-KR` - Korean
- `zh-CN` - Chinese (Simplified)

For a complete list, refer to AWS Transcribe documentation.

## Output Files

The scripts create two types of output:

### 1. JSON Transcription Results (`./results/`)

Full transcription data from AWS Transcribe, including:
- Transcript text
- Word-level timestamps
- Confidence scores
- Speaker labels (if multiple speakers detected)

Example: `audio_transcript.json`

### 2. TextGrid Files (`./textgrids/`)

Praat TextGrid format with three tiers:
- **VAD Tier**: Voice Activity Detection (speech segments)
- **Words Tier**: Individual words with timestamps
- **Confidence Tier**: Confidence scores per word

Example: `audio.TextGrid`

## API Response Format

The transcription API returns:

```json
{
  "job_id": "uuid",
  "status": "completed",
  "transcript": "Full transcript text here...",
  "word_count": 123,
  "duration": 45.67,
  "speaker_count": 2,
  "result_url": "https://s3-url-to-full-json",
  "subtitle_urls": {
    "srt": "https://s3-url-to-srt",
    "vtt": "https://s3-url-to-vtt"
  },
  "created_at": "timestamp",
  "completed_at": "timestamp"
}
```

## Workflow

The batch transcription process:

1. **Submit Phase**: All files are submitted to the API (fast, non-blocking)
2. **Processing**: Files are transcribed in parallel on the server
3. **Polling Phase**: Script checks status and downloads results
4. **TextGrid Generation**: Creates Praat TextGrid files from JSON results

## Advanced Usage

### Custom Progress Callback

```python
from redenlab_extract import InferenceClient

client = InferenceClient(
    api_key=API_KEY,
    model_name="transcribe",
    language_code="en-US"
)

def on_progress(status):
    print(f"Current status: {status['status']}")

result = client.predict("audio.wav", progress_callback=on_progress)
```

### Submit and Poll Separately

```python
# Submit all jobs first (non-blocking)
job_ids = []
for file_path, lang_code in files:
    job_id = client.submit(file_path, language_code=lang_code)
    job_ids.append(job_id)

# Do other work here...

# Poll for results later
for job_id in job_ids:
    result = client.poll(job_id)
    print(result['transcript'])
```

### Override Client Default Language

```python
# Set default language
client = InferenceClient(
    api_key=API_KEY,
    model_name="transcribe",
    language_code="en-AU"  # Default
)

# This uses en-AU
result1 = client.predict("audio1.wav")

# Override with en-US for this specific job
result2 = client.predict("audio2.wav", language_code="en-US")
```

## Troubleshooting

### TextGrid Generation Fails

Make sure you have the required dependencies:
```bash
pip install praatio pandas
```

### File Not Found Errors

Use absolute paths or ensure relative paths are correct:
```python
from pathlib import Path
file_path = str(Path("audio.wav").resolve())
```

### API Key Issues

Check that your API key is set correctly:
```bash
echo $REDENLAB_ML_API_KEY
```

### Timeout Issues

For long audio files, increase the timeout:
```python
client = InferenceClient(
    api_key=API_KEY,
    model_name="transcribe",
    timeout=7200  # 2 hours
)
```

## Files in This Directory

- `batch_transcribe_textgrid.py` - Main batch transcription script with TextGrid generation
- `transcribe_example.py` - Simple example/template script
- `test_batch_inference.py` - Test script for the SDK (different models)
- `TRANSCRIBE_README.md` - This file

## Additional Resources

- [RedenLab ML SDK Documentation](https://github.com/your-repo)
- [AWS Transcribe Language Codes](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html)
- [Praat TextGrid Format](https://www.fon.hum.uva.nl/praat/manual/TextGrid.html)
