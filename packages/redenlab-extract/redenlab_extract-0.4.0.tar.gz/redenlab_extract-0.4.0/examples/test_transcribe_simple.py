#!/usr/bin/env python3
"""
Simple test to verify batch transcription works with direct imports.
This is a minimal test to ensure the import structure is correct.
"""

import os
import sys
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Test import
try:
    from redenlab_extract.client import InferenceClient
    print("✓ Successfully imported InferenceClient from source files")
except ImportError as e:
    print(f"✗ Failed to import InferenceClient: {e}")
    sys.exit(1)

# Test client initialization
try:
    API_KEY = os.environ.get('REDENLAB_ML_API_KEY')
    if not API_KEY:
        print("⚠ Warning: REDENLAB_ML_API_KEY not set")
        print("  Set it with: export REDENLAB_ML_API_KEY='your-api-key'")
        print("✓ Import test passed (skipping API test)")
        sys.exit(0)

    client = InferenceClient(
        api_key=API_KEY,
        base_url="https://daq8c71oh4.execute-api.us-west-2.amazonaws.com/prod/",
        model_name="transcribe",
        language_code="en-US"
    )
    print("✓ Successfully created InferenceClient")
    print(f"  Client: {client}")
    print("\n✓ All tests passed!")

except Exception as e:
    print(f"✗ Error creating client: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
