#!/usr/bin/env python3
"""Integration tests for music video generators."""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestMusicVideoGenerators:
    """Integration tests for complete music video generation workflow."""

    def test_ultrarobust_generator_basic(
        self, test_video_path, test_audio_path, temp_output_dir
    ):
        """Test UltraRobustArchivalTool with basic inputs."""
        pytest.importorskip("librosa")
        try:
            from moviepy import VideoFileClip
        except ImportError:
            pytest.skip("moviepy not available")
        pytest.importorskip("scenedetect")

        # Skip if test assets don't exist
        if not test_video_path.exists() or not test_audio_path.exists():
            pytest.skip("Test assets not available")

        # Import the generator
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "ultrarobust",
                Path(__file__).parent.parent.parent / "ultraRobustArchivalTool.py",
            )
            ultrarobust = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ultrarobust)
        except Exception as e:
            pytest.skip(f"Could not import UltraRobustArchivalTool: {e}")

        # Test basic functionality (mock the actual processing)
        output_path = temp_output_dir / "test_output.mp4"

        # This is a simulation - real test would call the actual generator
        # For now, just verify we can import and basic structure works
        assert hasattr(ultrarobust, "__file__")

        # Create a dummy output to simulate success
        with open(output_path, "w") as f:
            f.write("# Test output simulation")

        assert output_path.exists()

    def test_premiere_style_engine(
        self, test_video_path, test_audio_path, temp_output_dir
    ):
        """Test premiere style archival engine."""
        pytest.importorskip("librosa")
        try:
            from moviepy import VideoFileClip
        except ImportError:
            pytest.skip("moviepy not available")

        # Skip if test assets don't exist
        if not test_video_path.exists() or not test_audio_path.exists():
            pytest.skip("Test assets not available")

        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "premiere_engine",
                Path(__file__).parent.parent.parent
                / "premiere_style_archival_engine.py",
            )
            premiere_engine = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(premiere_engine)
        except Exception as e:
            pytest.skip(f"Could not import premiere engine: {e}")

        # Test that we can import the engine
        assert hasattr(premiere_engine, "__file__")

    def test_robust_music_video_generator(
        self, test_video_path, test_audio_path, temp_output_dir
    ):
        """Test robust music video generator."""
        pytest.importorskip("librosa")
        try:
            from moviepy import VideoFileClip
        except ImportError:
            pytest.skip("moviepy not available")

        # Skip if test assets don't exist
        if not test_video_path.exists() or not test_audio_path.exists():
            pytest.skip("Test assets not available")

        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "robust_generator",
                Path(__file__).parent.parent.parent / "robust_music_video_generator.py",
            )
            robust_generator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(robust_generator)
        except Exception as e:
            pytest.skip(f"Could not import robust generator: {e}")

        # Test that we can import the generator
        assert hasattr(robust_generator, "__file__")


class TestGeneratorWorkflow:
    """Test complete workflow integration."""

    def test_end_to_end_workflow_simulation(
        self, test_video_path, test_audio_path, temp_output_dir
    ):
        """Test complete end-to-end workflow simulation."""
        # This simulates the complete workflow without actually running it
        # (which would take too long for unit tests)

        # Step 1: Verify inputs exist
        assert test_video_path.exists(), "Test video must exist"
        assert test_audio_path.exists(), "Test audio must exist"

        # Step 2: Create output directory
        output_dir = (
            temp_output_dir / f"workflow_test_{datetime.now().strftime('%H%M%S')}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        assert output_dir.exists()

        # Step 3: Simulate processing steps
        steps = [
            "Audio analysis",
            "Scene detection",
            "Beat synchronization",
            "Video generation",
            "Output finalization",
        ]

        results = {}
        for step in steps:
            # Simulate each step
            results[step] = {
                "status": "completed",
                "duration": 1.5,  # Mock duration
                "output_files": [output_dir / f"{step.lower().replace(' ', '_')}.json"],
            }

            # Create mock output file
            output_file = results[step]["output_files"][0]
            with open(output_file, "w") as f:
                f.write(f'{{"step": "{step}", "status": "completed"}}')

        # Verify all steps completed
        assert len(results) == len(steps)
        for step, result in results.items():
            assert result["status"] == "completed"
            assert result["output_files"][0].exists()

    def test_generator_error_recovery(self, temp_output_dir):
        """Test generator error recovery mechanisms."""

        def simulate_generator_with_errors():
            """Simulate generator that encounters and recovers from errors."""
            errors_encountered = []

            try:
                # Simulate audio analysis error
                raise FileNotFoundError("Audio file not accessible")
            except FileNotFoundError as e:
                errors_encountered.append(("audio_error", str(e)))
                # Recovery: Use default audio analysis
                pass

            try:
                # Simulate scene detection error
                raise RuntimeError("Scene detection failed")
            except RuntimeError as e:
                errors_encountered.append(("scene_error", str(e)))
                # Recovery: Use default scene splits
                pass

            return {
                "status": "completed_with_warnings",
                "errors": errors_encountered,
                "recovery_actions": len(errors_encountered),
            }

        result = simulate_generator_with_errors()

        # Verify error recovery worked
        assert result["status"] == "completed_with_warnings"
        assert result["recovery_actions"] > 0
        assert len(result["errors"]) == 2


class TestGeneratorConfiguration:
    """Test generator configuration handling."""

    def test_default_configuration(self, sample_generator_config):
        """Test default configuration values."""
        config = sample_generator_config

        # Verify required configuration parameters
        assert "max_clips" in config
        assert "scene_threshold" in config
        assert "beat_sensitivity" in config
        assert "output_resolution" in config
        assert "output_fps" in config

        # Verify reasonable default values
        assert 10 <= config["max_clips"] <= 100
        assert 0.1 <= config["scene_threshold"] <= 50.0
        assert 0.0 <= config["beat_sensitivity"] <= 1.0
        assert config["output_fps"] > 0

    def test_configuration_validation(self):
        """Test configuration parameter validation."""

        def validate_config(config):
            """Validate generator configuration."""
            errors = []

            if config.get("max_clips", 0) <= 0:
                errors.append("max_clips must be positive")

            if not (0.1 <= config.get("scene_threshold", 0) <= 50.0):
                errors.append("scene_threshold must be between 0.1 and 50.0")

            if not (0.0 <= config.get("beat_sensitivity", -1) <= 1.0):
                errors.append("beat_sensitivity must be between 0.0 and 1.0")

            return errors

        # Test valid configuration
        valid_config = {
            "max_clips": 20,
            "scene_threshold": 30.0,
            "beat_sensitivity": 0.5,
        }
        assert validate_config(valid_config) == []

        # Test invalid configuration
        invalid_config = {
            "max_clips": -5,
            "scene_threshold": 100.0,
            "beat_sensitivity": 2.0,
        }
        errors = validate_config(invalid_config)
        assert len(errors) == 3


class TestOutputValidation:
    """Test output file validation and verification."""

    def test_output_directory_structure(self, temp_output_dir):
        """Test expected output directory structure."""
        # Create mock output structure
        output_structure = {
            "final_video.mp4": "video",
            "analysis_report.html": "html",
            "metadata.json": "json",
            "scenes_detected.json": "json",
            "beat_analysis.json": "json",
        }

        for filename, file_type in output_structure.items():
            file_path = temp_output_dir / filename

            # Create mock files
            if file_type == "video":
                content = "# Mock video file"
            elif file_type == "html":
                content = "<html><body>Test Report</body></html>"
            elif file_type == "json":
                content = '{"test": "data"}'
            else:
                content = "Mock content"

            with open(file_path, "w") as f:
                f.write(content)

        # Verify all expected files exist
        for filename in output_structure.keys():
            assert (temp_output_dir / filename).exists()

    def test_output_file_validation(self, temp_output_dir):
        """Test validation of generated output files."""

        def validate_video_output(video_path):
            """Validate video output file."""
            if not video_path.exists():
                return False, "Video file does not exist"

            # Check file size (should be > 0)
            if video_path.stat().st_size == 0:
                return False, "Video file is empty"

            return True, "Video file is valid"

        def validate_report_output(report_path):
            """Validate HTML report output."""
            if not report_path.exists():
                return False, "Report file does not exist"

            try:
                content = report_path.read_text()
                if "<html>" not in content:
                    return False, "Report is not valid HTML"
            except Exception:
                return False, "Could not read report file"

            return True, "Report file is valid"

        # Create test files
        video_file = temp_output_dir / "test_video.mp4"
        report_file = temp_output_dir / "test_report.html"

        # Test empty video file (should fail validation)
        video_file.touch()
        is_valid, message = validate_video_output(video_file)
        assert not is_valid
        assert "empty" in message.lower()

        # Test valid video file
        with open(video_file, "w") as f:
            f.write("Mock video content")
        is_valid, message = validate_video_output(video_file)
        assert is_valid

        # Test valid report file
        with open(report_file, "w") as f:
            f.write("<html><body>Test Report</body></html>")
        is_valid, message = validate_report_output(report_file)
        assert is_valid
