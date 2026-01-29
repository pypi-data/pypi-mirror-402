#!/usr/bin/env python3
"""
Batch Transcription Example for RedenLab ML SDK

This script demonstrates how to batch process multiple audio files for transcription,
poll for completion, and export results to TextGrid and JSON formats.

Usage:
    export REDENLAB_ML_API_KEY='your-api-key'
    python batch_transcribe.py --input /path/to/audio/folder --output /path/to/output --language en-US

Arguments:
    --input, -i     : Input folder containing audio files
    --output, -o    : Output folder for results (will create textgrid/ and aws_results/ subfolders)
    --language, -l  : Language code for transcription (e.g., 'en-US', 'en-AU', 'es-ES')
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from praatio import textgrid

from redenlab_extract import TranscribeClient

# Supported audio extensions
AUDIO_EXTENSIONS = {".wav", ".flac", ".ogg"}


def read_json_from_url(url: str, timeout: float = 30.0) -> dict:
    """Fetch JSON data from a URL."""
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def process_transcribe_result_to_textgrid(
    url: str, timeout: float = 30.0
) -> textgrid.Textgrid:
    """
    Process AWS Transcribe result JSON and convert to Praat TextGrid format.

    Creates three tiers:
    - VAD: Voice Activity Detection (speech intervals)
    - Words: Individual word alignments
    - Confidence: Confidence scores for each word

    Args:
        url: URL to the AWS Transcribe result JSON
        timeout: Request timeout in seconds

    Returns:
        A praatio Textgrid object
    """
    # Parse items from AWS Transcribe JSON
    columns = ["index_ST", "start", "end", "confidence", "content"]
    dtypes = {
        "index_ST": float,
        "start": float,
        "end": float,
        "confidence": float,
        "content": str,
    }
    df = pd.DataFrame(columns=columns).astype(dtypes)

    data = read_json_from_url(url, timeout)
    items = data["results"].get("items", [])

    # Extract pronunciation items (skip punctuation)
    for i, cont in enumerate(items):
        if cont["type"] == "pronunciation":
            df.loc[len(df)] = [
                i,
                float(cont["start_time"]),
                float(cont["end_time"]),
                float(cont["alternatives"][0]["confidence"]),
                cont["alternatives"][0]["content"],
            ]

    # Handle empty results
    if len(df) == 0:
        # Create empty TextGrid with just duration
        audio_duration = float(data.get("duration", 0))
        tg = textgrid.Textgrid()
        vadTier = textgrid.IntervalTier("VAD", [], 0, audio_duration)
        tg.addTier(vadTier)
        wordTier = textgrid.IntervalTier("Words", [], 0, audio_duration)
        tg.addTier(wordTier)
        confidenceTier = textgrid.IntervalTier("Confidence", [], 0, audio_duration)
        tg.addTier(confidenceTier)
        return tg

    # Create word tier
    word_TG_cols = ["start", "end", "content"]
    word_TG_df = df[word_TG_cols]
    word_TG_df_list = word_TG_df.values.tolist()
    word_TG_df_list = [tuple(item) for item in word_TG_df_list]

    # Create confidence tier
    conf_TG_cols = ["start", "end", "confidence"]
    conf_TG_df = df[conf_TG_cols]
    conf_TG_df_list = conf_TG_df.values.tolist()
    conf_TG_df_list = [
        (start, end, str(confidence)) for start, end, confidence in conf_TG_df_list
    ]

    # Create VAD tier
    speech_start_time = df["start"].iloc[0]
    speech_end_time = df["end"].iloc[len(df) - 1]

    # Get audio duration from result
    audio_duration = float(data.get("duration", speech_end_time))

    # Build TextGrid
    tg = textgrid.Textgrid()

    vadTier = textgrid.IntervalTier(
        "VAD", [(speech_start_time, speech_end_time, "speech")], 0, audio_duration
    )
    tg.addTier(vadTier)

    wordTier = textgrid.IntervalTier("Words", word_TG_df_list, 0, audio_duration)
    tg.addTier(wordTier)

    confidenceTier = textgrid.IntervalTier(
        "Confidence", conf_TG_df_list, 0, audio_duration
    )
    tg.addTier(confidenceTier)

    return tg


def get_audio_files(input_folder: str) -> list[str]:
    """Get list of audio files from input folder."""
    folder = Path(input_folder)
    if not folder.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    files = []
    for f in folder.iterdir():
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS:
            files.append(str(f))

    if not files:
        raise ValueError(
            f"No audio files found in {input_folder}. "
            f"Supported formats: {', '.join(AUDIO_EXTENSIONS)}"
        )

    return sorted(files)


def poll_all_jobs(
    client: TranscribeClient,
    job_ids: list[str],
    poll_interval: int = 10,
    timeout: int = 3600,
) -> dict[str, dict]:
    """
    Poll all jobs until they complete or fail.

    Args:
        client: TranscribeClient instance
        job_ids: List of job IDs to poll
        poll_interval: Seconds between poll attempts
        timeout: Maximum time to wait for all jobs

    Returns:
        Dictionary mapping job_id to final status dict
    """
    results = {}
    pending = set(job_ids)
    start_time = time.time()

    print(f"\nPolling {len(job_ids)} jobs for completion...")
    print("-" * 60)

    while pending and (time.time() - start_time) < timeout:
        for job_id in list(pending):
            try:
                status_data = client.get_status(job_id)
                status = status_data.get("status")

                if status == "completed":
                    results[job_id] = status_data
                    pending.remove(job_id)
                    completed_count = len(results)
                    total = len(job_ids)
                    print(f"  [COMPLETED] Job {job_id[:12]}... ({completed_count}/{total})")

                elif status == "failed":
                    results[job_id] = status_data
                    pending.remove(job_id)
                    completed_count = len(results)
                    total = len(job_ids)
                    error_msg = status_data.get("error", "Unknown error")
                    print(f"  [FAILED] Job {job_id[:12]}... - {error_msg}")

            except Exception as e:
                print(f"  [ERROR] Checking job {job_id[:12]}...: {e}")

        if pending:
            elapsed = int(time.time() - start_time)
            print(
                f"  ... {len(pending)} jobs still processing "
                f"(elapsed: {elapsed}s, waiting {poll_interval}s)"
            )
            time.sleep(poll_interval)

    # Handle timeout for remaining jobs
    for job_id in pending:
        results[job_id] = {"job_id": job_id, "status": "timeout", "error": "Polling timeout"}
        print(f"  [TIMEOUT] Job {job_id[:12]}...")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Batch transcribe audio files using RedenLab ML SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python batch_transcribe.py -i ./audio_files -o ./results -l en-US
    python batch_transcribe.py --input /data/recordings --output /data/transcripts --language en-AU
        """,
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Input folder containing audio files"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output folder for results"
    )
    parser.add_argument(
        "-l",
        "--language",
        required=True,
        help="Language code (e.g., 'en-US', 'en-AU', 'es-ES')",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Maximum time to wait for jobs in seconds (default: 3600)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Seconds between status checks (default: 10)",
    )

    args = parser.parse_args()

    # Check for API key
    api_key = os.environ.get("REDENLAB_ML_API_KEY")
    if not api_key:
        print("Error: REDENLAB_ML_API_KEY environment variable not set")
        print("Set it with: export REDENLAB_ML_API_KEY='your-api-key'")
        sys.exit(1)

    # Setup output directories
    output_path = Path(args.output)
    textgrid_dir = output_path / "textgrid"
    aws_results_dir = output_path / "aws_results"

    output_path.mkdir(parents=True, exist_ok=True)
    textgrid_dir.mkdir(exist_ok=True)
    aws_results_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 60)
    print("RedenLab ML SDK - Batch Transcription")
    print("=" * 60)
    print(f"Input folder:  {args.input}")
    print(f"Output folder: {args.output}")
    print(f"Language:      {args.language}")
    print("=" * 60)

    # Get audio files
    try:
        audio_files = get_audio_files(args.input)
        print(f"\nFound {len(audio_files)} audio files to process")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Create DataFrame
    df = pd.DataFrame(
        {
            "filename": [Path(p).name for p in audio_files],
            "path": audio_files,
        }
    )

    # Initialize client
    client = TranscribeClient(
        api_key=api_key,
        language_code=args.language,
        timeout=args.timeout,
    )
    print(f"\nClient initialized: {client}")

    # Submit all jobs
    print("\n" + "-" * 60)
    print("PHASE 1: Submitting jobs")
    print("-" * 60)

    job_ids = []
    for i, row in df.iterrows():
        print(f"  [{i + 1}/{len(df)}] Submitting {row['filename']}...")
        try:
            job_id = client.submit(file_path=row["path"])
            job_ids.append(job_id)
            print(f"         Job ID: {job_id[:12]}...")
        except Exception as e:
            print(f"         ERROR: {e}")
            job_ids.append(None)

    df["job_id"] = job_ids
    print(f"\nSubmitted {sum(1 for j in job_ids if j is not None)}/{len(df)} jobs")

    # Poll all jobs
    print("\n" + "-" * 60)
    print("PHASE 2: Polling for completion")
    print("-" * 60)

    valid_job_ids = [j for j in job_ids if j is not None]
    job_results = poll_all_jobs(
        client,
        valid_job_ids,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )

    # Get final status and result URLs
    final_statuses = []
    result_urls = []
    for job_id in df["job_id"]:
        if job_id is None:
            final_statuses.append("submit_failed")
            result_urls.append(None)
        elif job_id in job_results:
            result = job_results[job_id]
            final_statuses.append(result.get("status", "unknown"))
            result_urls.append(result.get("result_url"))
        else:
            final_statuses.append("unknown")
            result_urls.append(None)

    df["status"] = final_statuses
    df["result_url"] = result_urls

    # Process results
    print("\n" + "-" * 60)
    print("PHASE 3: Processing results")
    print("-" * 60)

    textgrids = []
    for i, row in df.iterrows():
        filename = row["filename"]
        result_url = row["result_url"]
        status = row["status"]

        if status != "completed" or result_url is None:
            print(f"  [{i + 1}/{len(df)}] Skipping {filename} (status: {status})")
            textgrids.append(None)
            continue

        print(f"  [{i + 1}/{len(df)}] Processing {filename}...")

        try:
            # Download and save raw JSON
            json_data = read_json_from_url(result_url)
            json_filename = Path(filename).stem + ".json"
            json_path = aws_results_dir / json_filename
            with open(json_path, "w") as f:
                json.dump(json_data, f, indent=2)
            print(f"         Saved JSON: {json_filename}")

            # Convert to TextGrid
            tg = process_transcribe_result_to_textgrid(result_url)
            textgrids.append(tg)

            # Save TextGrid
            tg_filename = Path(filename).stem + ".TextGrid"
            tg_path = textgrid_dir / tg_filename
            tg.save(str(tg_path), format="short_textgrid", includeBlankSpaces=True)
            print(f"         Saved TextGrid: {tg_filename}")

        except Exception as e:
            print(f"         ERROR processing: {e}")
            textgrids.append(None)

    df["textgrid"] = textgrids

    # Save summary DataFrame
    summary_df = df[["filename", "path", "job_id", "status"]].copy()
    summary_path = output_path / "transcription_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"\nSaved summary to: {summary_path}")

    # Print final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    completed = sum(1 for s in final_statuses if s == "completed")
    failed = sum(1 for s in final_statuses if s in ("failed", "submit_failed"))
    other = len(final_statuses) - completed - failed

    print(f"  Total files:     {len(df)}")
    print(f"  Completed:       {completed}")
    print(f"  Failed:          {failed}")
    if other > 0:
        print(f"  Other:           {other}")
    print()
    print(f"  Output folder:   {output_path}")
    print(f"  TextGrids:       {textgrid_dir}")
    print(f"  JSON results:    {aws_results_dir}")
    print(f"  Summary CSV:     {summary_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
