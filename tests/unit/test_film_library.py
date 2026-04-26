#!/usr/bin/env python3
"""Unit tests for FilmLibrary class."""
import pytest
import json
import os
import numpy as np
from pathlib import Path
from music_video_generator.film_library import FilmLibrary


TEST_ASSETS_DIR = Path(__file__).parent.parent.parent / "test-assets"


@pytest.fixture
def film_library_with_video(tmp_path):
    """FilmLibrary instance backed by the real test video."""
    video_path = TEST_ASSETS_DIR / "test_video.mp4"
    if not video_path.exists():
        pytest.skip("Test video not available")
    return FilmLibrary(str(video_path), clips_library_dir=str(tmp_path / "lib"))


class TestFilmLibrary:
    """Test FilmLibrary class."""

    def test_init_with_valid_film(self, tmp_path):
        """Test FilmLibrary initialization with valid film path."""
        # Create a mock film path
        film_path = tmp_path / "test_movie.mp4"
        film_path.touch()

        library = FilmLibrary(str(film_path), threshold=30.0)

        assert library.film_path == str(film_path)
        assert library.threshold == 30.0
        assert library.min_scene_len == 1.0
        assert library.film_name == "test_movie"

    def test_init_with_invalid_film(self):
        """Test FilmLibrary initialization with non-existent film."""
        with pytest.raises(FileNotFoundError):
            FilmLibrary("nonexistent.mp4")

    def test_safe_float_conversion(self, tmp_path):
        """Test safe float conversion utility."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()
        library = FilmLibrary(str(film_path))

        import numpy as np

        assert library.safe_float(3.14) == 3.14
        assert library.safe_float(np.float64(3.14)) == 3.14
        assert library.safe_float("invalid") == 0.0
        assert library.safe_float(None) == 0.0

    def test_safe_int_conversion(self, tmp_path):
        """Test safe int conversion utility."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()
        library = FilmLibrary(str(film_path))

        import numpy as np

        assert library.safe_int(42) == 42
        assert library.safe_int(np.int64(42)) == 42
        assert library.safe_int("invalid") == 0
        assert library.safe_int(None) == 0

    def test_check_cache_no_metadata(self, tmp_path):
        """Test cache check when no metadata exists."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()

        library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
        result = library._check_cache()

        assert result is False

    def test_check_cache_with_matching_params(self, tmp_path):
        """Test cache check with matching parameters."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()

        # Create library and save metadata
        library = FilmLibrary(
            str(film_path), threshold=30.0, clips_library_dir=str(tmp_path / "lib")
        )
        library.library_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "scene_detection_params": {"threshold": 30.0, "min_scene_len": 1.0},
            "total_scenes": 10,
        }

        with open(library.library_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)

        result = library._check_cache()
        assert result is True

    def test_check_cache_with_different_params(self, tmp_path):
        """Test cache check with different parameters."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()

        library = FilmLibrary(
            str(film_path), threshold=25.0, clips_library_dir=str(tmp_path / "lib")
        )
        library.library_dir.mkdir(parents=True, exist_ok=True)

        metadata = {"scene_detection_params": {"threshold": 30.0, "min_scene_len": 1.0}}

        with open(library.library_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)

        result = library._check_cache()
        assert result is False

    def test_load_from_cache_success(self, tmp_path):
        """Test successful loading from cache."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()

        library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
        library.library_dir.mkdir(parents=True, exist_ok=True)

        # Create valid metadata
        metadata = {
            "scene_detection_params": {"threshold": 30.0, "min_scene_len": 1.0},
            "scenes": [
                {"id": 0, "start": 0.0, "end": 2.0, "duration": 2.0},
                {"id": 1, "start": 2.0, "end": 4.0, "duration": 2.0},
            ],
            "total_scenes": 2,
        }

        with open(library.library_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)

        result = library._load_from_cache()

        assert result is True
        assert len(library.scenes) == 2
        assert library.scenes[0]["id"] == 0
        assert library.metadata["total_scenes"] == 2

    def test_load_from_cache_malformed_json(self, tmp_path):
        """Test loading fails gracefully with malformed JSON."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()

        library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
        library.library_dir.mkdir(parents=True, exist_ok=True)

        # Write malformed JSON
        with open(library.library_dir / "metadata.json", "w") as f:
            f.write("{invalid json")

        result = library._load_from_cache()

        assert result is False

    @pytest.mark.skipif(
        not os.path.exists("test-assets/test_video.mp4"),
        reason="Test video not available",
    )
    def test_detect_scenes(self):
        """Test scene detection with real video."""
        library = FilmLibrary("test-assets/test_video.mp4", threshold=30.0)
        scenes = library.detect_scenes()

        assert len(scenes) > 0
        assert all("id" in s for s in scenes)
        assert all("start" in s for s in scenes)
        assert all("end" in s for s in scenes)
        assert all("duration" in s for s in scenes)

    @pytest.mark.skipif(
        not os.path.exists("test-assets/test_video.mp4"),
        reason="Test video not available",
    )
    def test_extract_clips(self, tmp_path):
        """Test clip extraction from detected scenes."""
        library = FilmLibrary(
            "test-assets/test_video.mp4", clips_library_dir=str(tmp_path)
        )

        # Create sample scenes
        library.scenes = [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "duration": 2.0,
                "clip_filename": "scene_0000.mp4",
            },
            {
                "id": 1,
                "start": 2.0,
                "end": 4.0,
                "duration": 2.0,
                "clip_filename": "scene_0001.mp4",
            },
        ]

        library.clips_dir.mkdir(parents=True, exist_ok=True)

        count = library.extract_clips(library.scenes)

        assert count > 0
        assert (library.clips_dir / "scene_0000.mp4").exists()

    @pytest.mark.skipif(
        not os.path.exists("test-assets/test_video.mp4"),
        reason="Test video not available",
    )
    def test_generate_thumbnails_and_analyze(self, tmp_path):
        """Test thumbnail generation and scene analysis."""
        library = FilmLibrary(
            "test-assets/test_video.mp4", clips_library_dir=str(tmp_path)
        )

        library.thumbnails_dir.mkdir(parents=True, exist_ok=True)

        # Create sample scenes
        library.scenes = [
            {
                "id": 0,
                "start": 1.0,
                "end": 3.0,
                "duration": 2.0,
                "thumbnail_filename": "thumb_0000.jpg",
            }
        ]

        library.generate_thumbnails(library.scenes)
        library.analyze_scenes(library.scenes)

        assert (library.thumbnails_dir / "thumb_0000.jpg").exists()
        assert "avg_brightness" in library.scenes[0]
        assert "avg_color_hex" in library.scenes[0]
        assert "pace" in library.scenes[0]

    def test_save_and_load_metadata(self, tmp_path):
        """Test saving and loading metadata."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()

        library = FilmLibrary(
            str(film_path), threshold=25.0, clips_library_dir=str(tmp_path / "lib")
        )
        library.library_dir.mkdir(parents=True, exist_ok=True)

        # Add sample scenes
        library.scenes = [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "duration": 2.0,
                "avg_brightness": 100.0,
                "pace": "fast",
            }
        ]

        # Save metadata
        library.save_metadata()

        # Verify file exists
        assert (library.library_dir / "metadata.json").exists()

        # Load in new instance
        library2 = FilmLibrary(
            str(film_path), threshold=25.0, clips_library_dir=str(tmp_path / "lib")
        )
        success = library2._load_from_cache()

        assert success is True
        assert len(library2.scenes) == 1
        assert library2.scenes[0]["id"] == 0


def test_get_frame_at_time(film_library_with_video):
    """Test that _get_frame_at_time returns a valid numpy array."""
    frame = film_library_with_video._get_frame_at_time(1.0)
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert len(frame.shape) == 3  # height, width, channels
    assert frame.shape[2] == 3   # RGB


def test_get_film_properties(film_library_with_video):
    """Test that _get_film_properties returns valid metadata."""
    props = film_library_with_video._get_film_properties()
    assert "duration" in props
    assert "resolution" in props
    assert "fps" in props
    assert props["duration"] > 0
    assert "x" in props["resolution"]
    assert props["fps"] > 0
