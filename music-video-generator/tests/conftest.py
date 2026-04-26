#!/usr/bin/env python3
"""
Pytest configuration and fixtures for the music video project test suite.
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path

# Test data paths
TEST_ASSETS_DIR = Path(__file__).parent.parent / "test-assets"
TEST_DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def test_video_path():
    """Path to the test video file."""
    return TEST_ASSETS_DIR / "test_video.mp4"


@pytest.fixture
def test_audio_path():
    """Path to the test audio file."""
    return TEST_ASSETS_DIR / "test_audio.wav"


@pytest.fixture
def long_test_video_path():
    """Path to the long test video file (300+ scenes)."""
    return TEST_ASSETS_DIR / "test_video_long.mp4"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix="mvp_test_")
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_generator_config():
    """Sample configuration for generators."""
    return {
        "max_clips": 20,
        "scene_threshold": 30.0,
        "beat_sensitivity": 0.5,
        "output_resolution": (1920, 1080),
        "output_fps": 24,
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for each test."""
    # Ensure test assets exist
    if not TEST_ASSETS_DIR.exists():
        pytest.skip("Test assets directory not found")

    # Set environment variables for testing
    os.environ["MVP_TEST_MODE"] = "true"
    yield
    # Cleanup
    os.environ.pop("MVP_TEST_MODE", None)


@pytest.fixture
def mock_librosa_data():
    """Mock data for librosa operations."""
    import numpy as np

    return {
        "audio_data": np.random.randn(44100 * 30),  # 30 seconds of audio
        "sample_rate": 22050,
        "tempo": 120.0,
        "beats": np.array([0, 0.5, 1.0, 1.5, 2.0]),  # Beat positions
    }


@pytest.fixture(scope="session")
def test_requirements():
    """Check that all required dependencies are available."""
    required_modules = ["librosa", "scenedetect", "opencv", "numpy"]

    missing_modules = []
    for module in required_modules:
        try:
            if module == "opencv":
                import cv2
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        pytest.skip(f"Missing required modules: {missing_modules}")

    return True
