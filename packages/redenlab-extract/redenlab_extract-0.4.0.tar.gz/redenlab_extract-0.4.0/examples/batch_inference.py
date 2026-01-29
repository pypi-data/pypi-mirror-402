#!/usr/bin/env python3
"""
Test script for RedenLab ML SDK - Batch inference test

This script demonstrates the new submit() + poll() API for efficient batch processing.
"""

import os
import sys
import time
from pathlib import Path

# Add src directory to path to import directly from source files
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import the SDK directly from source files
try:
    from redenlab_extract.client import InferenceClient
except ImportError as e:
    print("Error: Could not import redenlab_extract from source files.")
    print(f"Error details: {e}")
    sys.exit(1)


def test_single_file_traditional():
    """Test single file inference using traditional predict() method."""
    print("=" * 70)
    print("TEST 1: Single File (Traditional predict() method)")
    print("=" * 70)

    API_KEY = os.environ.get('REDENLAB_ML_API_KEY')
    BASE_URL = "https://daq8c71oh4.execute-api.us-west-2.amazonaws.com/prod/"
    TEST_AUDIO = "/Users/ayushranjan/Documents/Redenlab/Git_projects/Intelligens-ML-Endpoints/test_data/medum_file/ActiveMS_Reading_1.wav"

    if not Path(TEST_AUDIO).exists():
        print(f"Error: Test audio file not found: {TEST_AUDIO}")
        return

    client = InferenceClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model_name="speaker_diarisation_workflow",
        timeout=3600
    )

    print(f"Client: {client}")
    print(f"Test file: {TEST_AUDIO}")
    print()

    # Traditional approach: submit and poll in one call
    print("Running predict() - this will block until complete...")
    result = client.predict(file_path=TEST_AUDIO)

    print(f"✓ Complete! Job ID: {result.get('job_id')}")
    print(f"  Result: {result.get('result')}")
    print()


def test_single_file_new_api():
    """Test single file inference using new submit() + poll() API."""
    print("=" * 70)
    print("TEST 2: Single File (New submit() + poll() API)")
    print("=" * 70)

    API_KEY = os.environ.get('REDENLAB_ML_API_KEY')
    BASE_URL = "https://daq8c71oh4.execute-api.us-west-2.amazonaws.com/prod/"
    TEST_AUDIO = "/Users/ayushranjan/Documents/Redenlab/Git_projects/Intelligens-ML-Endpoints/test_data/medum_file/ActiveMS_Reading_1.wav"

    if not Path(TEST_AUDIO).exists():
        print(f"Error: Test audio file not found: {TEST_AUDIO}")
        return

    client = InferenceClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model_name="speaker_diarisation_workflow",
        timeout=3600
    )

    print(f"Client: {client}")
    print(f"Test file: {TEST_AUDIO}")
    print()

    # New approach: submit and poll separately
    print("Step 1: Submitting job (non-blocking)...")
    job_id = client.submit(file_path=TEST_AUDIO)
    print(f"✓ Job submitted! Job ID: {job_id}")
    print()

    # Could do other work here...
    print("Step 2: Polling for completion (blocking)...")

    def on_progress(status_data):
        status = status_data.get('status', 'unknown')
        print(f"  Current status: {status}")

    result = client.poll(job_id, progress_callback=on_progress)

    print(f"✓ Complete!")
    print(f"  Result: {result.get('result')}")
    print()


def test_batch_sequential():
    """Test batch inference - submit all, then poll all (simulated with 1 file)."""
    print("=" * 70)
    print("TEST 3: Batch Processing (Submit All + Poll All)")
    print("=" * 70)

    API_KEY = os.environ.get('REDENLAB_ML_API_KEY')
    BASE_URL = "https://daq8c71oh4.execute-api.us-west-2.amazonaws.com/prod/"
    TEST_AUDIO = "/Users/ayushranjan/Documents/Redenlab/Git_projects/Intelligens-ML-Endpoints/test_data/medum_file/ActiveMS_Reading_1.wav"

    if not Path(TEST_AUDIO).exists():
        print(f"Error: Test audio file not found: {TEST_AUDIO}")
        return

    client = InferenceClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model_name="speaker_diarisation_workflow",
        timeout=3600
    )

    # Simulate batch with multiple copies of same file
    # In real usage, this would be different files
    audio_files = [TEST_AUDIO] * 3  # Simulate 3 files

    print(f"Client: {client}")
    print(f"Batch size: {len(audio_files)} files")
    print()

    # PHASE 1: Submit all jobs (fast!)
    print("PHASE 1: Submitting all jobs...")
    job_ids = []
    for i, audio_file in enumerate(audio_files, 1):
        print(f"  [{i}/{len(audio_files)}] Submitting {Path(audio_file).name}...")
        job_id = client.submit(audio_file)
        job_ids.append(job_id)
        print(f"    ✓ Job ID: {job_id}")

    print(f"\n✓ All {len(job_ids)} jobs submitted!")
    print()

    # PHASE 2: Poll all jobs (efficient!)
    print("PHASE 2: Polling for all results...")
    results = {}
    pending = set(job_ids)

    while pending:
        for job_id in list(pending):
            status_data = client.get_status(job_id)
            status = status_data.get('status')

            if status == 'completed':
                results[job_id] = status_data
                pending.remove(job_id)
                print(f"  ✓ Job {job_id[:8]}... completed ({len(results)}/{len(job_ids)})")
            elif status == 'failed':
                results[job_id] = status_data
                pending.remove(job_id)
                print(f"  ✗ Job {job_id[:8]}... failed ({len(results)}/{len(job_ids)})")
            else:
                print(f"  ⏳ Job {job_id[:8]}... still {status}")

        if pending:
            print(f"  Waiting 10 seconds before next check...")
            time.sleep(10)

    print(f"\n✓ All jobs complete!")
    print()
    print("Results:")
    for i, (job_id, result) in enumerate(results.items(), 1):
        print(f"  [{i}] Job {job_id[:8]}...")
        if result.get('status') == 'completed':
            print(f"      Result: {result.get('result')}")
        else:
            print(f"      Error: {result.get('error')}")
    print()


def test_transcribe_with_language():
    """Test transcribe model with language_code parameter."""
    print("=" * 70)
    print("TEST 4: Transcribe with Language Code")
    print("=" * 70)

    API_KEY = os.environ.get('REDENLAB_ML_API_KEY')
    BASE_URL = "https://daq8c71oh4.execute-api.us-west-2.amazonaws.com/prod/"
    TEST_AUDIO = "/Users/ayushranjan/Documents/Redenlab/Git_projects/Intelligens-ML-Endpoints/test_data/medum_file/ActiveMS_Reading_1.wav"

    if not Path(TEST_AUDIO).exists():
        print(f"Error: Test audio file not found: {TEST_AUDIO}")
        return

    # Example 1: Client with default language_code
    print("\nExample 1: Client with default language_code")
    print("-" * 70)
    client = InferenceClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model_name="transcribe",
        timeout=3600,
        language_code="en-US"  # Set default language for all jobs
    )

    print(f"Client: {client}")
    print(f"Test file: {TEST_AUDIO}")
    print()

    print("Submitting job with language_code='en-US' (from client)...")
    job_id = client.submit(file_path=TEST_AUDIO)
    print(f"✓ Job submitted! Job ID: {job_id}")
    print()

    # Example 2: Per-job override
    print("\nExample 2: Per-job language_code override")
    print("-" * 70)
    client2 = InferenceClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        model_name="transcribe",
        timeout=3600,
        language_code="en-AU"  # Default is en-AU
    )

    print(f"Client default language: en-AU")
    print(f"Submitting with override language_code='en-US'...")
    job_id2 = client2.submit(file_path=TEST_AUDIO, language_code="en-US")
    print(f"✓ Job submitted with en-US! Job ID: {job_id2}")
    print()

    # Poll for completion
    print("Polling for job completion...")
    result = client.poll(job_id)
    print(f"✓ Complete! Job ID: {result.get('job_id')}")
    if 'transcript' in result:
        transcript = result['transcript']
        print(f"  Transcript preview: {transcript[:150]}...")
    print()


def main():
    """Run all tests."""
    API_KEY = os.environ.get('REDENLAB_ML_API_KEY')
    if not API_KEY:
        print("Error: REDENLAB_ML_API_KEY environment variable not set")
        print("Set it with: export REDENLAB_ML_API_KEY='your-api-key'")
        sys.exit(1)

    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "RedenLab ML SDK - Batch Inference Test" + " " * 14 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print("This test demonstrates four usage patterns:")
    print("  1. Traditional predict() - single file, blocks until complete")
    print("  2. New submit() + poll() - single file, explicit control")
    print("  3. Batch processing - submit all, then poll all efficiently")
    print("  4. Transcribe with language_code - demonstrate language parameter")
    print()
    input("Press Enter to start tests...")
    print()

    try:
        # Test 1: Traditional single file
        test_single_file_traditional()

        # Test 2: New API single file
        test_single_file_new_api()

        # Test 3: Batch processing
        test_batch_sequential()

        # Test 4: Transcribe with language code
        test_transcribe_with_language()

        print("=" * 70)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR!")
        print("=" * 70)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
