# Test Utilities

This directory contains utilities for generating test assets used across the test suite.

## Test Asset Generators

### create_test_audio.py
Generates synthetic audio files with varying BPM patterns for testing audio analysis.

**Usage:**
```bash
python tests/utils/create_test_audio.py
```

**Output:** Creates `test-assets/test_audio.wav` (3 minutes, varying BPM: 120→60→90)

### create_test_video.py
Generates synthetic video files with color transitions for testing scene detection.

**Usage:**
```bash
python tests/utils/create_test_video.py
```

**Output:** Creates `test-assets/test_video_long.mp4` (10 minutes, 300+ color transitions)

## When to Use

Run these scripts when:
- Setting up a new test environment
- Test assets are missing or corrupted
- You need to regenerate test data with different parameters
