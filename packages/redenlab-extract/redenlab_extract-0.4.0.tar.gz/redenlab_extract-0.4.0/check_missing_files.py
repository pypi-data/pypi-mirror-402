#!/usr/bin/env python3
"""
Check which files are missing TextGrids and identify failures.
"""

import os
import sys
from pathlib import Path
import json

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Directories
RESULTS_DIR = "./results"
TEXTGRID_DIR = "./textgrids"

# Read the original file list from batch_transcribe_textgrid.py
import batch_transcribe_textgrid as batch_transcribe
FILES_AND_LANGUAGES = batch_transcribe.FILES_AND_LANGUAGES

print("=" * 70)
print("TRANSCRIPTION STATUS CHECKER")
print("=" * 70)
print(f"Total files submitted: {len(FILES_AND_LANGUAGES)}")
print()

# Check which files have JSON results
json_files = set()
if os.path.exists(RESULTS_DIR):
    for f in os.listdir(RESULTS_DIR):
        if f.endswith('_transcript.json'):
            json_files.add(f.replace('_transcript.json', ''))

print(f"JSON results downloaded: {len(json_files)}")

# Check which files have TextGrids
textgrid_files = set()
if os.path.exists(TEXTGRID_DIR):
    for f in os.listdir(TEXTGRID_DIR):
        if f.endswith('.TextGrid'):
            textgrid_files.add(f.replace('.TextGrid', ''))

print(f"TextGrids created: {len(textgrid_files)}")
print()

# Identify missing files
missing_json = []
missing_textgrid = []
complete = []

for file_path, lang_code in FILES_AND_LANGUAGES:
    file_name = Path(file_path).name
    file_name_no_ext = Path(file_path).stem

    has_json = file_name_no_ext in json_files
    has_textgrid = file_name_no_ext in textgrid_files

    if has_json and has_textgrid:
        complete.append((file_path, lang_code))
    elif has_json and not has_textgrid:
        missing_textgrid.append((file_path, lang_code, file_name_no_ext))
    else:
        missing_json.append((file_path, lang_code))

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✓ Complete (JSON + TextGrid): {len(complete)}")
print(f"⚠ Has JSON, missing TextGrid: {len(missing_textgrid)}")
print(f"✗ Missing JSON (failed jobs): {len(missing_json)}")
print()

if missing_textgrid:
    print("=" * 70)
    print("FILES WITH JSON BUT MISSING TEXTGRID")
    print("=" * 70)
    print("These files have JSON results but TextGrid generation failed.")
    print("You can regenerate TextGrids for these files.\n")
    for i, (file_path, lang_code, file_name_no_ext) in enumerate(missing_textgrid[:10], 1):
        print(f"  [{i}] {Path(file_path).name}")
    if len(missing_textgrid) > 10:
        print(f"  ... and {len(missing_textgrid) - 10} more")
    print()

if missing_json:
    print("=" * 70)
    print("FILES WITH FAILED/INCOMPLETE JOBS")
    print("=" * 70)
    print("These files need to be resubmitted for transcription.\n")
    for i, (file_path, lang_code) in enumerate(missing_json[:20], 1):
        print(f"  [{i}] {Path(file_path).name} ({lang_code})")
    if len(missing_json) > 20:
        print(f"  ... and {len(missing_json) - 20} more")
    print()

# Save recovery lists
if missing_textgrid:
    recovery_file = "recovery_textgrids.json"
    with open(recovery_file, 'w') as f:
        json.dump(missing_textgrid, f, indent=2)
    print(f"✓ Saved missing TextGrid list to: {recovery_file}")

if missing_json:
    recovery_file = "recovery_jobs.json"
    recovery_data = missing_json
    with open(recovery_file, 'w') as f:
        json.dump(recovery_data, f, indent=2)
    print(f"✓ Saved failed jobs list to: {recovery_file}")

print()
print("=" * 70)
print("NEXT STEPS")
print("=" * 70)

if missing_textgrid:
    print("1. Run: python regenerate_textgrids.py")
    print("   This will regenerate TextGrids from existing JSON files.")
    print()

if missing_json:
    print("2. Run: python retry_failed_jobs.py")
    print("   This will retry transcription for failed jobs.")
    print()

if not missing_textgrid and not missing_json:
    print("✓ All files processed successfully!")
    print()
