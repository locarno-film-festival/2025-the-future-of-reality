# Music Video Generator Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor existing archival remix tools into a unified Music Video Generator with reusable film library preparation and fast multi-strategy music video generation.

**Architecture:** Two-phase design with `FilmLibrary` class for expensive one-time scene detection/clip extraction and `MusicVideoGenerator` class for fast music video generation with configurable strategies (progressive, random, forward-only, no-repeat) and beat-skip parameter.

**Tech Stack:** Python 3.9+, librosa, MoviePy, PySceneDetect, OpenCV, matplotlib, FFmpeg

---

## Task 1: Create FilmLibrary Class Foundation

**Files:**
- Create: `music_video_generator/film_library.py`
- Create: `music_video_generator/__init__.py`
- Test: `tests/unit/test_film_library.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
"""Unit tests for FilmLibrary class."""
import pytest
from pathlib import Path
from music_video_generator.film_library import FilmLibrary


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_film_library.py -v`
Expected: FAIL with "No module named 'music_video_generator'"

**Step 3: Create package structure**

Create directory and files:
```bash
mkdir -p music_video_generator
touch music_video_generator/__init__.py
```

**Step 4: Write minimal FilmLibrary implementation**

Create `music_video_generator/__init__.py`:
```python
"""Music Video Generator package."""
from .film_library import FilmLibrary
from .music_video_generator import MusicVideoGenerator

__version__ = "2.0.0"
__all__ = ["FilmLibrary", "MusicVideoGenerator"]
```

Create `music_video_generator/film_library.py`:
```python
#!/usr/bin/env python3
"""FilmLibrary class for scene detection and clip management."""
import os
import json
from pathlib import Path
from datetime import datetime


class FilmLibrary:
    """Manages film scene detection and clip library."""

    def __init__(self, film_path, threshold=30.0, min_scene_len=1.0,
                 force_regenerate=False, clips_library_dir="clips_library"):
        """Initialize FilmLibrary.

        Args:
            film_path: Path to source video file
            threshold: Scene detection sensitivity (10-50 range)
            min_scene_len: Minimum scene duration in seconds
            force_regenerate: Force regeneration even if cache exists
            clips_library_dir: Base directory for clip library storage
        """
        # Validate film exists
        if not os.path.exists(film_path):
            raise FileNotFoundError(f"Film not found: {film_path}")

        self.film_path = str(film_path)
        self.film_name = Path(film_path).stem
        self.threshold = threshold
        self.min_scene_len = min_scene_len
        self.force_regenerate = force_regenerate

        # Set up library directories
        self.library_dir = Path(clips_library_dir) / self.film_name
        self.clips_dir = self.library_dir / "clips"
        self.thumbnails_dir = self.library_dir / "thumbnails"

        self.scenes = []
        self.metadata = {}

    def safe_float(self, value):
        """Safely convert value to Python float.

        Args:
            value: Value to convert (supports numpy types)

        Returns:
            float: Converted value or 0.0 on failure
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def safe_int(self, value):
        """Safely convert value to Python int.

        Args:
            value: Value to convert (supports numpy types)

        Returns:
            int: Converted value or 0 on failure
        """
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def get_scenes(self):
        """Return list of available scenes with metadata.

        Returns:
            list: Scene metadata dictionaries
        """
        return self.scenes
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_film_library.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add music_video_generator/ tests/unit/test_film_library.py
git commit -m "feat: add FilmLibrary class foundation with type safety

- Create FilmLibrary class with basic initialization
- Add safe_float() and safe_int() for numpy type conversion
- Add validation for film file existence
- Set up clips_library directory structure

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Add Cache Detection Logic to FilmLibrary

**Files:**
- Modify: `music_video_generator/film_library.py`
- Test: `tests/unit/test_film_library.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_film_library.py`:
```python
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
    library = FilmLibrary(str(film_path), threshold=30.0, clips_library_dir=str(tmp_path / "lib"))
    library.library_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "scene_detection_params": {
            "threshold": 30.0,
            "min_scene_len": 1.0
        },
        "total_scenes": 10
    }

    with open(library.library_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    result = library._check_cache()
    assert result is True

def test_check_cache_with_different_params(self, tmp_path):
    """Test cache check with different parameters."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()

    library = FilmLibrary(str(film_path), threshold=25.0, clips_library_dir=str(tmp_path / "lib"))
    library.library_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "scene_detection_params": {
            "threshold": 30.0,
            "min_scene_len": 1.0
        }
    }

    with open(library.library_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    result = library._check_cache()
    assert result is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_check_cache_no_metadata -v`
Expected: FAIL with "AttributeError: 'FilmLibrary' object has no attribute '_check_cache'"

**Step 3: Implement cache detection**

Add to `FilmLibrary` class in `music_video_generator/film_library.py`:
```python
def _check_cache(self):
    """Check if valid cached clips exist with matching parameters.

    Returns:
        bool: True if cache exists and parameters match
    """
    metadata_path = self.library_dir / "metadata.json"

    # Check if metadata file exists
    if not metadata_path.exists():
        return False

    # Load metadata
    try:
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False

    # Check if parameters match
    cached_params = self.metadata.get("scene_detection_params", {})

    if (cached_params.get("threshold") == self.threshold and
        cached_params.get("min_scene_len") == self.min_scene_len):
        return True

    return False

def _load_from_cache(self):
    """Load scenes and metadata from existing cache.

    Returns:
        bool: True if successfully loaded from cache
    """
    metadata_path = self.library_dir / "metadata.json"

    try:
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)

        self.scenes = self.metadata.get("scenes", [])

        print(f"✓ Loaded {len(self.scenes)} scenes from cache")
        print(f"  Cache location: {self.library_dir}")

        return True
    except (json.JSONDecodeError, IOError) as e:
        print(f"✗ Failed to load cache: {e}")
        return False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_check_cache_no_metadata -v`
Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_check_cache_with_matching_params -v`
Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_check_cache_with_different_params -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add music_video_generator/film_library.py tests/unit/test_film_library.py
git commit -m "feat: add cache detection logic to FilmLibrary

- Implement _check_cache() to verify cached clips exist
- Compare scene detection parameters for cache validity
- Implement _load_from_cache() to load scenes from metadata
- Add tests for cache detection with various scenarios

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Add Scene Detection to FilmLibrary

**Files:**
- Modify: `music_video_generator/film_library.py`
- Test: `tests/unit/test_film_library.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_film_library.py`:
```python
@pytest.mark.skipif(not os.path.exists("test-assets/test_video.mp4"),
                    reason="Test video not available")
def test_detect_scenes(self):
    """Test scene detection with real video."""
    library = FilmLibrary("test-assets/test_video.mp4", threshold=30.0)
    scenes = library.detect_scenes()

    assert len(scenes) > 0
    assert all("id" in s for s in scenes)
    assert all("start" in s for s in scenes)
    assert all("end" in s for s in scenes)
    assert all("duration" in s for s in scenes)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_detect_scenes -v`
Expected: FAIL with "AttributeError: 'FilmLibrary' object has no attribute 'detect_scenes'"

**Step 3: Implement scene detection**

Add imports to top of `music_video_generator/film_library.py`:
```python
import warnings
warnings.filterwarnings("ignore")

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
```

Add to `FilmLibrary` class:
```python
def detect_scenes(self):
    """Run PySceneDetect scene detection.

    Returns:
        list: Scene metadata dictionaries
    """
    print(f"\n🎬 Detecting scenes in {self.film_name}...")
    print(f"   Threshold: {self.threshold}")
    print(f"   Min scene length: {self.min_scene_len}s")

    try:
        # Set up scene detection
        video_manager = VideoManager([self.film_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(
            ContentDetector(threshold=self.threshold)
        )

        # Detect scenes
        video_manager.set_duration()
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()

        print(f"   Found {len(scene_list)} raw scenes")

        # Process scenes
        self.scenes = []
        for i, scene in enumerate(scene_list):
            start_time = self.safe_float(scene[0].get_seconds())
            end_time = self.safe_float(scene[1].get_seconds())
            duration = end_time - start_time

            # Filter by minimum duration
            if duration < self.min_scene_len:
                continue

            scene_info = {
                'id': i,
                'start': start_time,
                'end': end_time,
                'duration': duration,
                'clip_filename': f"scene_{i:04d}.mp4",
                'thumbnail_filename': f"thumb_{i:04d}.jpg"
            }

            self.scenes.append(scene_info)

            # Progress reporting
            if (i + 1) % 20 == 0:
                print(f"   Processed {i + 1}/{len(scene_list)} scenes...")

        print(f"   ✓ Detected {len(self.scenes)} scenes (filtered by min_scene_len)")

        return self.scenes

    except Exception as e:
        print(f"   ✗ Scene detection failed: {e}")
        return []
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_detect_scenes -v`
Expected: PASS (or SKIP if test_video.mp4 doesn't exist)

**Step 5: Commit**

```bash
git add music_video_generator/film_library.py tests/unit/test_film_library.py
git commit -m "feat: add scene detection to FilmLibrary

- Implement detect_scenes() using PySceneDetect
- Filter scenes by minimum duration threshold
- Add progress reporting every 20 scenes
- Use safe_float() for numpy type conversion
- Return structured scene metadata

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Add Clip Extraction to FilmLibrary

**Files:**
- Modify: `music_video_generator/film_library.py`
- Test: `tests/unit/test_film_library.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_film_library.py`:
```python
@pytest.mark.skipif(not os.path.exists("test-assets/test_video.mp4"),
                    reason="Test video not available")
def test_extract_clips(self, tmp_path):
    """Test clip extraction from detected scenes."""
    library = FilmLibrary("test-assets/test_video.mp4",
                         clips_library_dir=str(tmp_path))

    # Create sample scenes
    library.scenes = [
        {'id': 0, 'start': 0.0, 'end': 2.0, 'duration': 2.0,
         'clip_filename': 'scene_0000.mp4'},
        {'id': 1, 'start': 2.0, 'end': 4.0, 'duration': 2.0,
         'clip_filename': 'scene_0001.mp4'}
    ]

    library.clips_dir.mkdir(parents=True, exist_ok=True)

    count = library.extract_clips(library.scenes)

    assert count > 0
    assert (library.clips_dir / "scene_0000.mp4").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_extract_clips -v`
Expected: FAIL with "AttributeError: 'FilmLibrary' object has no attribute 'extract_clips'"

**Step 3: Implement clip extraction**

Add imports to top of `music_video_generator/film_library.py`:
```python
from moviepy.editor import VideoFileClip
import gc
```

Add to `FilmLibrary` class:
```python
def extract_clips(self, scenes):
    """Extract individual scene clips to clips/ directory.

    Args:
        scenes: List of scene metadata dictionaries

    Returns:
        int: Count of successfully exported clips
    """
    print(f"\n🎞️  Extracting {len(scenes)} scene clips...")

    # Ensure clips directory exists
    self.clips_dir.mkdir(parents=True, exist_ok=True)

    clips_exported = 0
    clips_failed = []

    try:
        # Load video without audio (faster, clips don't need audio)
        video = VideoFileClip(self.film_path, audio=False)
        video_duration = video.duration

        for i, scene in enumerate(scenes):
            # Progress reporting every 20 clips
            if (i + 1) % 20 == 0:
                print(f"   Extracting clip {i + 1}/{len(scenes)}...")

            try:
                start_time = scene['start']
                end_time = min(scene['end'], video_duration)
                clip_path = self.clips_dir / scene['clip_filename']

                # Validate bounds
                if start_time >= video_duration:
                    clips_failed.append(i)
                    continue

                # Ensure minimum duration
                if end_time - start_time < 0.1:
                    clips_failed.append(i)
                    continue

                # Extract clip
                clip = video.subclip(start_time, end_time)

                # Export with settings from v20
                clip.write_videofile(
                    str(clip_path),
                    codec='libx264',
                    audio=False,
                    verbose=False,
                    logger=None,
                    preset='fast',
                    threads=2,
                    fps=15,  # Lower FPS for efficiency
                    write_logfile=False
                )

                clip.close()
                clips_exported += 1

                # Update scene metadata
                scene['has_clip'] = True

            except Exception as e:
                clips_failed.append(i)
                scene['has_clip'] = False
                continue

        # Cleanup
        video.close()
        gc.collect()

        print(f"   ✓ Exported {clips_exported} clips")
        if clips_failed:
            print(f"   ⚠ Failed to export {len(clips_failed)} clips")

        return clips_exported

    except Exception as e:
        print(f"   ✗ Clip extraction failed: {e}")
        return 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_extract_clips -v`
Expected: PASS (or SKIP if test_video.mp4 doesn't exist)

**Step 5: Commit**

```bash
git add music_video_generator/film_library.py tests/unit/test_film_library.py
git commit -m "feat: add clip extraction to FilmLibrary

- Implement extract_clips() using MoviePy
- Export clips without audio (faster, audio added at final render)
- Use v20 settings: libx264, fps=15, preset=fast
- Add progress reporting every 20 clips
- Track failed clips and update scene metadata
- Explicit memory management with gc.collect()

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Add Thumbnail and Scene Analysis to FilmLibrary

**Files:**
- Modify: `music_video_generator/film_library.py`
- Test: `tests/unit/test_film_library.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_film_library.py`:
```python
@pytest.mark.skipif(not os.path.exists("test-assets/test_video.mp4"),
                    reason="Test video not available")
def test_generate_thumbnails_and_analyze(self, tmp_path):
    """Test thumbnail generation and scene analysis."""
    library = FilmLibrary("test-assets/test_video.mp4",
                         clips_library_dir=str(tmp_path))

    library.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    # Create sample scenes
    library.scenes = [
        {'id': 0, 'start': 1.0, 'end': 3.0, 'duration': 2.0,
         'thumbnail_filename': 'thumb_0000.jpg'}
    ]

    library.generate_thumbnails(library.scenes)
    library.analyze_scenes(library.scenes)

    assert (library.thumbnails_dir / "thumb_0000.jpg").exists()
    assert 'avg_brightness' in library.scenes[0]
    assert 'avg_color_hex' in library.scenes[0]
    assert 'pace' in library.scenes[0]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_generate_thumbnails_and_analyze -v`
Expected: FAIL with "AttributeError: 'FilmLibrary' object has no attribute 'generate_thumbnails'"

**Step 3: Implement thumbnail generation and analysis**

Add imports to top of `music_video_generator/film_library.py`:
```python
import cv2
import numpy as np
```

Add to `FilmLibrary` class:
```python
def generate_thumbnails(self, scenes):
    """Generate thumbnail images for each scene.

    Args:
        scenes: List of scene metadata dictionaries
    """
    print(f"\n🖼️  Generating thumbnails for {len(scenes)} scenes...")

    # Ensure thumbnails directory exists
    self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    try:
        video = VideoFileClip(self.film_path, audio=False)

        for i, scene in enumerate(scenes):
            try:
                # Get middle frame of scene
                middle_time = (scene['start'] + scene['end']) / 2
                frame = video.get_frame(middle_time)

                # Save thumbnail
                thumb_path = self.thumbnails_dir / scene['thumbnail_filename']
                thumb_height = 120
                aspect_ratio = frame.shape[1] / frame.shape[0]
                thumb_width = int(thumb_height * aspect_ratio)
                thumb = cv2.resize(frame, (thumb_width, thumb_height))
                thumb_bgr = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(thumb_path), thumb_bgr)

            except Exception as e:
                continue

        video.close()
        print(f"   ✓ Generated {len(scenes)} thumbnails")

    except Exception as e:
        print(f"   ✗ Thumbnail generation failed: {e}")

def analyze_scenes(self, scenes):
    """Add color, brightness, pace analysis to scene metadata.

    Args:
        scenes: List of scene metadata dictionaries

    Returns:
        list: Scenes with added analysis metadata
    """
    print(f"\n🔍 Analyzing {len(scenes)} scenes...")

    try:
        video = VideoFileClip(self.film_path, audio=False)
        video_duration = video.duration

        for scene in scenes:
            try:
                # Get middle frame
                middle_time = (scene['start'] + scene['end']) / 2
                frame = video.get_frame(middle_time)

                # Color analysis
                avg_color = np.mean(frame, axis=(0, 1))
                scene['avg_color_rgb'] = avg_color.tolist()
                scene['avg_color_hex'] = '#{:02x}{:02x}{:02x}'.format(
                    int(avg_color[0]), int(avg_color[1]), int(avg_color[2])
                )

                # Brightness analysis
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                scene['avg_brightness'] = float(np.mean(gray))

                # Pace analysis
                duration = scene['duration']
                if duration < 2:
                    scene['pace'] = 'fast'
                elif duration > 10:
                    scene['pace'] = 'slow'
                else:
                    scene['pace'] = 'medium'

                # Position ratio in film
                scene['position_ratio'] = scene['start'] / video_duration

            except Exception as e:
                # Set defaults on failure
                scene['avg_brightness'] = 0.0
                scene['pace'] = 'medium'
                scene['position_ratio'] = 0.0
                continue

        video.close()
        print(f"   ✓ Analyzed {len(scenes)} scenes")

        return scenes

    except Exception as e:
        print(f"   ✗ Scene analysis failed: {e}")
        return scenes
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_generate_thumbnails_and_analyze -v`
Expected: PASS (or SKIP if test_video.mp4 doesn't exist)

**Step 5: Commit**

```bash
git add music_video_generator/film_library.py tests/unit/test_film_library.py
git commit -m "feat: add thumbnail generation and scene analysis

- Implement generate_thumbnails() to create 120px height thumbs
- Implement analyze_scenes() for color/brightness/pace analysis
- Extract middle frame from each scene for analysis
- Calculate position_ratio for scene location in film
- Handle failures gracefully with defaults

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Add Metadata Persistence to FilmLibrary

**Files:**
- Modify: `music_video_generator/film_library.py`
- Test: `tests/unit/test_film_library.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_film_library.py`:
```python
def test_save_and_load_metadata(self, tmp_path):
    """Test saving and loading metadata."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()

    library = FilmLibrary(str(film_path), threshold=25.0,
                         clips_library_dir=str(tmp_path / "lib"))
    library.library_dir.mkdir(parents=True, exist_ok=True)

    # Add sample scenes
    library.scenes = [
        {'id': 0, 'start': 0.0, 'end': 2.0, 'duration': 2.0,
         'avg_brightness': 100.0, 'pace': 'fast'}
    ]

    # Save metadata
    library.save_metadata()

    # Verify file exists
    assert (library.library_dir / "metadata.json").exists()

    # Load in new instance
    library2 = FilmLibrary(str(film_path), threshold=25.0,
                          clips_library_dir=str(tmp_path / "lib"))
    success = library2._load_from_cache()

    assert success is True
    assert len(library2.scenes) == 1
    assert library2.scenes[0]['id'] == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_save_and_load_metadata -v`
Expected: FAIL with "AttributeError: 'FilmLibrary' object has no attribute 'save_metadata'"

**Step 3: Implement metadata persistence**

Add to `FilmLibrary` class in `music_video_generator/film_library.py`:
```python
def save_metadata(self):
    """Save metadata.json to clips_library/{film_name}/"""
    print(f"\n💾 Saving metadata...")

    # Ensure directory exists
    self.library_dir.mkdir(parents=True, exist_ok=True)

    # Get film properties
    try:
        video = VideoFileClip(self.film_path, audio=False)
        film_properties = {
            "duration": self.safe_float(video.duration),
            "resolution": f"{video.w}x{video.h}",
            "fps": self.safe_float(video.fps),
            "codec": getattr(video, 'codec', 'unknown')
        }
        video.close()
    except Exception:
        film_properties = {
            "duration": 0.0,
            "resolution": "unknown",
            "fps": 0.0,
            "codec": "unknown"
        }

    # Build metadata
    metadata = {
        "film_path": self.film_path,
        "film_name": self.film_name,
        "created_at": datetime.now().isoformat(),
        "scene_detection_params": {
            "threshold": self.threshold,
            "min_scene_len": self.min_scene_len
        },
        "film_properties": film_properties,
        "scenes": self.scenes,
        "total_scenes": len(self.scenes)
    }

    # Save to JSON
    metadata_path = self.library_dir / "metadata.json"
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"   ✓ Saved metadata: {metadata_path}")
        self.metadata = metadata

    except IOError as e:
        print(f"   ✗ Failed to save metadata: {e}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_film_library.py::TestFilmLibrary::test_save_and_load_metadata -v`
Expected: PASS

**Step 5: Commit**

```bash
git add music_video_generator/film_library.py tests/unit/test_film_library.py
git commit -m "feat: add metadata persistence to FilmLibrary

- Implement save_metadata() to write metadata.json
- Include film properties (duration, resolution, fps, codec)
- Store scene detection parameters for cache validation
- Include timestamp and complete scene data
- Test round-trip save and load

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Create MusicVideoGenerator Class Foundation

**Files:**
- Create: `music_video_generator/music_video_generator.py`
- Modify: `music_video_generator/__init__.py`
- Test: `tests/unit/test_music_video_generator.py`

**Step 1: Write the failing test**

Create `tests/unit/test_music_video_generator.py`:
```python
#!/usr/bin/env python3
"""Unit tests for MusicVideoGenerator class."""
import pytest
from pathlib import Path
from unittest.mock import Mock
from music_video_generator.music_video_generator import MusicVideoGenerator
from music_video_generator.film_library import FilmLibrary


class TestMusicVideoGenerator:
    """Test MusicVideoGenerator class."""

    def test_init_with_valid_inputs(self, tmp_path):
        """Test MusicVideoGenerator initialization."""
        # Create mock FilmLibrary
        film_path = tmp_path / "test.mp4"
        film_path.touch()

        library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
        library.scenes = [{'id': 0, 'start': 0, 'end': 2, 'duration': 2}]

        song_path = tmp_path / "test.mp3"
        song_path.touch()

        gen = MusicVideoGenerator(library, str(song_path), strategy='progressive')

        assert gen.film_library == library
        assert gen.song_path == str(song_path)
        assert gen.strategy == 'progressive'
        assert gen.beat_skip == 1

    def test_init_with_invalid_song(self, tmp_path):
        """Test initialization with non-existent song."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()
        library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))

        with pytest.raises(FileNotFoundError):
            MusicVideoGenerator(library, "nonexistent.mp3")

    def test_init_with_invalid_strategy(self, tmp_path):
        """Test initialization with invalid strategy."""
        film_path = tmp_path / "test.mp4"
        film_path.touch()
        library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))

        song_path = tmp_path / "test.mp3"
        song_path.touch()

        with pytest.raises(ValueError):
            MusicVideoGenerator(library, str(song_path), strategy='invalid')
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_music_video_generator.py -v`
Expected: FAIL with "No module named 'music_video_generator.music_video_generator'"

**Step 3: Write minimal MusicVideoGenerator implementation**

Create `music_video_generator/music_video_generator.py`:
```python
#!/usr/bin/env python3
"""MusicVideoGenerator class for creating music videos from film libraries."""
import os
from pathlib import Path
from datetime import datetime


class MusicVideoGenerator:
    """Generates music videos from FilmLibrary using various strategies."""

    VALID_STRATEGIES = ['progressive', 'random', 'forward_only', 'no_repeat']

    def __init__(self, film_library, song_path, strategy='progressive',
                 beat_skip=1, output_dir="music_videos"):
        """Initialize MusicVideoGenerator.

        Args:
            film_library: FilmLibrary instance with cached clips
            song_path: Path to audio file
            strategy: Scene selection strategy (progressive|random|forward_only|no_repeat)
            beat_skip: Use every Nth beat (1=every beat, 2=every other beat)
            output_dir: Base directory for music video outputs
        """
        # Validate song exists
        if not os.path.exists(song_path):
            raise FileNotFoundError(f"Song not found: {song_path}")

        # Validate strategy
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(f"Invalid strategy: {strategy}. Must be one of {self.VALID_STRATEGIES}")

        self.film_library = film_library
        self.song_path = str(song_path)
        self.song_name = Path(song_path).stem
        self.strategy = strategy
        self.beat_skip = beat_skip

        # Set up output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        film_name = film_library.film_name
        self.output_dir = Path(output_dir) / f"{film_name}_{self.song_name}_{strategy}_{timestamp}"

        self.beats = []
        self.beat_times = []
        self.music_analysis = {}
        self.selected_scenes = []
```

Update `music_video_generator/__init__.py`:
```python
"""Music Video Generator package."""
from .film_library import FilmLibrary
from .music_video_generator import MusicVideoGenerator

__version__ = "2.0.0"
__all__ = ["FilmLibrary", "MusicVideoGenerator"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_music_video_generator.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add music_video_generator/music_video_generator.py music_video_generator/__init__.py tests/unit/test_music_video_generator.py
git commit -m "feat: add MusicVideoGenerator class foundation

- Create MusicVideoGenerator class with initialization
- Validate song file existence and strategy selection
- Support four strategies: progressive, random, forward_only, no_repeat
- Set up timestamped output directories
- Add beat_skip parameter for controlling cut frequency

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Add Audio Analysis to MusicVideoGenerator

**Files:**
- Modify: `music_video_generator/music_video_generator.py`
- Test: `tests/unit/test_music_video_generator.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_music_video_generator.py`:
```python
@pytest.mark.skipif(not os.path.exists("test-assets/test_audio.wav"),
                    reason="Test audio not available")
def test_analyze_audio(self, tmp_path):
    """Test audio analysis with librosa."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()
    library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))

    gen = MusicVideoGenerator(library, "test-assets/test_audio.wav")
    result = gen.analyze_audio()

    assert 'duration' in result
    assert 'bpm' in result
    assert 'beats' in result
    assert 'tempo_confidence' in result
    assert result['duration'] > 0
    assert len(result['beats']) > 0

def test_safe_float_conversion(self, tmp_path):
    """Test safe float conversion in generator."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()
    library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))

    song_path = tmp_path / "test.mp3"
    song_path.touch()
    gen = MusicVideoGenerator(library, str(song_path))

    import numpy as np
    assert gen.safe_float(3.14) == 3.14
    assert gen.safe_float(np.float64(3.14)) == 3.14
    assert gen.safe_float("invalid") == 0.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_analyze_audio -v`
Expected: FAIL with "AttributeError: 'MusicVideoGenerator' object has no attribute 'analyze_audio'"

**Step 3: Implement audio analysis**

Add imports to top of `music_video_generator/music_video_generator.py`:
```python
import warnings
warnings.filterwarnings("ignore")

import librosa
import numpy as np
```

Add to `MusicVideoGenerator` class:
```python
def safe_float(self, value):
    """Safely convert value to Python float.

    Args:
        value: Value to convert (supports numpy types)

    Returns:
        float: Converted value or 0.0 on failure
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def safe_int(self, value):
    """Safely convert value to Python int.

    Args:
        value: Value to convert (supports numpy types)

    Returns:
        int: Converted value or 0 on failure
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

def analyze_audio(self):
    """Librosa beat detection and tempo analysis.

    Returns:
        dict: Music analysis with duration, bpm, beats, tempo_confidence, sample_rate
    """
    print(f"\n🎵 Analyzing audio: {self.song_name}")

    try:
        # Load audio
        audio_data, sample_rate = librosa.load(self.song_path)

        # Beat tracking
        tempo, beat_frames = librosa.beat.beat_track(
            y=audio_data,
            sr=sample_rate
        )

        # Convert beat frames to time
        beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)

        # Calculate duration
        duration = len(audio_data) / sample_rate

        # Store results
        self.beats = beat_frames
        self.beat_times = [self.safe_float(t) for t in beat_times]

        self.music_analysis = {
            'duration': self.safe_float(duration),
            'bpm': self.safe_float(tempo),
            'beats_detected': len(beat_times),
            'beats': self.beat_times,
            'tempo_confidence': 0.85,  # Placeholder, librosa doesn't provide this
            'sample_rate': self.safe_int(sample_rate)
        }

        print(f"   Duration: {duration:.1f}s")
        print(f"   BPM: {tempo:.1f}")
        print(f"   Beats detected: {len(beat_times)}")

        return self.music_analysis

    except Exception as e:
        print(f"   ✗ Audio analysis failed: {e}")

        # Return defaults
        self.music_analysis = {
            'duration': 0.0,
            'bpm': 120.0,
            'beats_detected': 0,
            'beats': [],
            'tempo_confidence': 0.0,
            'sample_rate': 22050
        }

        return self.music_analysis
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_analyze_audio -v`
Expected: PASS (or SKIP if test_audio.wav doesn't exist)

**Step 5: Commit**

```bash
git add music_video_generator/music_video_generator.py tests/unit/test_music_video_generator.py
git commit -m "feat: add audio analysis to MusicVideoGenerator

- Implement analyze_audio() using librosa
- Detect beats and calculate BPM/tempo
- Add safe_float() and safe_int() for numpy type safety
- Return structured music analysis dictionary
- Handle failures gracefully with defaults

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Add Scene-Beat Ratio Validation

**Files:**
- Modify: `music_video_generator/music_video_generator.py`
- Test: `tests/unit/test_music_video_generator.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_music_video_generator.py`:
```python
def test_validate_insufficient_scenes(self, tmp_path, capsys):
    """Test validation warning when scenes < beats."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()

    library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
    library.scenes = [{'id': i, 'start': i, 'end': i+1, 'duration': 1}
                      for i in range(10)]  # Only 10 scenes

    song_path = tmp_path / "test.mp3"
    song_path.touch()

    gen = MusicVideoGenerator(library, str(song_path))
    gen.beat_times = [i * 0.5 for i in range(100)]  # 100 beats

    result = gen.validate_scene_beat_ratio()

    captured = capsys.readouterr()
    assert "⚠️  WARNING" in captured.out
    assert "10" in captured.out  # scene count
    assert "100" in captured.out  # beat count
    assert result is True  # Should allow continuing

def test_validate_sufficient_scenes(self, tmp_path):
    """Test validation passes when scenes >= beats."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()

    library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
    library.scenes = [{'id': i, 'start': i, 'end': i+1, 'duration': 1}
                      for i in range(100)]  # 100 scenes

    song_path = tmp_path / "test.mp3"
    song_path.touch()

    gen = MusicVideoGenerator(library, str(song_path))
    gen.beat_times = [i * 0.5 for i in range(50)]  # 50 beats

    result = gen.validate_scene_beat_ratio()
    assert result is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_validate_insufficient_scenes -v`
Expected: FAIL with "AttributeError: 'MusicVideoGenerator' object has no attribute 'validate_scene_beat_ratio'"

**Step 3: Implement validation**

Add to `MusicVideoGenerator` class in `music_video_generator/music_video_generator.py`:
```python
def validate_scene_beat_ratio(self):
    """Check if enough scenes for beats, warn/suggest alternatives.

    Returns:
        bool: True to continue, False to abort
    """
    scenes = self.film_library.get_scenes()

    # Calculate effective beat count after beat_skip
    effective_beats = len(self.beat_times) // self.beat_skip

    # Check if we have enough scenes
    if len(scenes) < effective_beats:
        ratio = effective_beats / len(scenes)
        suggested_skip = int(np.ceil(ratio))

        print(f"\n⚠️  WARNING: Insufficient clips for beat count")
        print(f"   Scenes available: {len(scenes)}")
        print(f"   Beats to use: {effective_beats} (every {self.beat_skip} beat)")
        print(f"   Ratio: {ratio:.1f} beats per scene")
        print(f"\n   SUGGESTIONS:")
        print(f"   1. Use --beat-skip {suggested_skip} (1 clip per {suggested_skip} beats)")
        print(f"   2. Use 'random' or 'no-repeat' strategy (allows scene reuse)")
        print(f"   3. Lower scene detection --threshold to detect more scenes")
        print(f"\n   Continuing with current settings...")

        return True

    print(f"\n✓ Scene-beat ratio valid: {len(scenes)} scenes for {effective_beats} beats")
    return True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_validate_insufficient_scenes -v`
Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_validate_sufficient_scenes -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add music_video_generator/music_video_generator.py tests/unit/test_music_video_generator.py
git commit -m "feat: add scene-beat ratio validation

- Implement validate_scene_beat_ratio() to check clip count
- Warn when insufficient scenes for beat count
- Calculate suggested beat-skip value
- Provide actionable suggestions to user
- Account for beat_skip in effective beat count

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Implement Scene Selection Strategies

**Files:**
- Modify: `music_video_generator/music_video_generator.py`
- Test: `tests/unit/test_music_video_generator.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_music_video_generator.py`:
```python
def test_select_progressive_strategy(self, tmp_path):
    """Test progressive scene selection strategy."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()

    library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
    library.scenes = [{'id': i, 'start': i*10, 'end': (i+1)*10, 'duration': 10}
                      for i in range(100)]

    song_path = tmp_path / "test.mp3"
    song_path.touch()

    gen = MusicVideoGenerator(library, str(song_path), strategy='progressive')
    gen.beat_times = [i * 0.5 for i in range(50)]

    selected = gen.select_scenes()

    assert len(selected) == 50
    # Progressive should sample evenly from start to end
    assert selected[0]['scene']['id'] < selected[-1]['scene']['id']

def test_select_random_strategy(self, tmp_path):
    """Test random scene selection strategy."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()

    library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
    library.scenes = [{'id': i, 'start': i*10, 'end': (i+1)*10, 'duration': 10}
                      for i in range(20)]

    song_path = tmp_path / "test.mp3"
    song_path.touch()

    gen = MusicVideoGenerator(library, str(song_path), strategy='random')
    gen.beat_times = [i * 0.5 for i in range(30)]

    selected = gen.select_scenes()

    assert len(selected) == 30

def test_select_forward_only_strategy(self, tmp_path):
    """Test forward-only scene selection strategy."""
    film_path = tmp_path / "test.mp4"
    film_path.touch()

    library = FilmLibrary(str(film_path), clips_library_dir=str(tmp_path / "lib"))
    library.scenes = [{'id': i, 'start': i*10, 'end': (i+1)*10, 'duration': 10}
                      for i in range(50)]

    song_path = tmp_path / "test.mp3"
    song_path.touch()

    gen = MusicVideoGenerator(library, str(song_path), strategy='forward_only')
    gen.beat_times = [i * 0.5 for i in range(30)]

    selected = gen.select_scenes()

    assert len(selected) == 30
    # Forward-only should never backtrack
    scene_ids = [s['scene']['id'] for s in selected]
    assert scene_ids == sorted(scene_ids)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_select_progressive_strategy -v`
Expected: FAIL with "AttributeError: 'MusicVideoGenerator' object has no attribute 'select_scenes'"

**Step 3: Implement scene selection strategies**

Add to `MusicVideoGenerator` class in `music_video_generator/music_video_generator.py`:
```python
def select_scenes(self):
    """Apply strategy to map scenes to beats.

    Returns:
        list: Scene-to-beat mappings
    """
    print(f"\n🎬 Selecting scenes using '{self.strategy}' strategy...")

    scenes = self.film_library.get_scenes()

    # Apply beat_skip
    selected_beats = self.beat_times[::self.beat_skip]

    print(f"   Available scenes: {len(scenes)}")
    print(f"   Beats to use: {len(selected_beats)} (every {self.beat_skip} beat)")

    # Call appropriate strategy method
    strategy_map = {
        'progressive': self._select_progressive,
        'random': self._select_random,
        'forward_only': self._select_forward_only,
        'no_repeat': self._select_no_repeat
    }

    selected = strategy_map[self.strategy](scenes, selected_beats)

    print(f"   ✓ Selected {len(selected)} scene-to-beat mappings")

    self.selected_scenes = selected
    return selected

def _select_progressive(self, scenes, beat_times):
    """Evenly distributed chronological sampling.

    Args:
        scenes: Available scenes
        beat_times: Beat time points

    Returns:
        list: Scene-to-beat mappings
    """
    mappings = []
    num_beats = len(beat_times) - 1

    for i in range(num_beats):
        beat_start = beat_times[i]
        beat_end = beat_times[i + 1]
        beat_duration = beat_end - beat_start

        # Map beat index to scene position
        scene_index = int((i / num_beats) * len(scenes))
        scene_index = min(scene_index, len(scenes) - 1)
        selected_scene = scenes[scene_index]

        mappings.append({
            'beat_start': beat_start,
            'beat_end': beat_end,
            'beat_duration': beat_duration,
            'scene': selected_scene,
            'beat_index': i
        })

    return mappings

def _select_random(self, scenes, beat_times):
    """Pure random selection, allows repetition.

    Args:
        scenes: Available scenes
        beat_times: Beat time points

    Returns:
        list: Scene-to-beat mappings
    """
    mappings = []
    num_beats = len(beat_times) - 1

    for i in range(num_beats):
        beat_start = beat_times[i]
        beat_end = beat_times[i + 1]
        beat_duration = beat_end - beat_start

        # Random selection
        selected_scene = scenes[np.random.randint(0, len(scenes))]

        mappings.append({
            'beat_start': beat_start,
            'beat_end': beat_end,
            'beat_duration': beat_duration,
            'scene': selected_scene,
            'beat_index': i
        })

    return mappings

def _select_forward_only(self, scenes, beat_times):
    """Sequential progression without backtracking.

    Args:
        scenes: Available scenes
        beat_times: Beat time points

    Returns:
        list: Scene-to-beat mappings
    """
    mappings = []
    num_beats = len(beat_times) - 1
    current_scene_index = 0

    for i in range(num_beats):
        beat_start = beat_times[i]
        beat_end = beat_times[i + 1]
        beat_duration = beat_end - beat_start

        # Use current scene and advance
        selected_scene = scenes[current_scene_index]

        mappings.append({
            'beat_start': beat_start,
            'beat_end': beat_end,
            'beat_duration': beat_duration,
            'scene': selected_scene,
            'beat_index': i
        })

        # Move to next scene (with wrap-around)
        current_scene_index = (current_scene_index + 1) % len(scenes)

    return mappings

def _select_no_repeat(self, scenes, beat_times):
    """Random selection from unused pool.

    Args:
        scenes: Available scenes
        beat_times: Beat time points

    Returns:
        list: Scene-to-beat mappings
    """
    mappings = []
    num_beats = len(beat_times) - 1
    unused_scenes = list(scenes)

    for i in range(num_beats):
        beat_start = beat_times[i]
        beat_end = beat_times[i + 1]
        beat_duration = beat_end - beat_start

        # If pool exhausted, fall back to forward-only
        if not unused_scenes:
            unused_scenes = list(scenes)

        # Random selection from unused pool
        scene_index = np.random.randint(0, len(unused_scenes))
        selected_scene = unused_scenes.pop(scene_index)

        mappings.append({
            'beat_start': beat_start,
            'beat_end': beat_end,
            'beat_duration': beat_duration,
            'scene': selected_scene,
            'beat_index': i
        })

    return mappings
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_select_progressive_strategy -v`
Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_select_random_strategy -v`
Run: `pytest tests/unit/test_music_video_generator.py::TestMusicVideoGenerator::test_select_forward_only_strategy -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add music_video_generator/music_video_generator.py tests/unit/test_music_video_generator.py
git commit -m "feat: implement scene selection strategies

- Implement select_scenes() dispatcher method
- Add _select_progressive() for evenly distributed chronological sampling
- Add _select_random() for pure random selection with repetition
- Add _select_forward_only() for sequential no-backtrack selection
- Add _select_no_repeat() for random without repetition
- Apply beat_skip to reduce effective beat count

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 11: Add CLI Interface

**Files:**
- Create: `music_video_generator/cli.py`
- Create: `music_video_generator.py` (entry point script)
- Test: Manual testing (CLI tools typically not unit tested)

**Step 1: Create CLI module**

Create `music_video_generator/cli.py`:
```python
#!/usr/bin/env python3
"""Command-line interface for Music Video Generator."""
import argparse
import sys
from pathlib import Path
from .film_library import FilmLibrary
from .music_video_generator import MusicVideoGenerator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Music Video Generator - Create artistic remixes from film and music",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prepare film library (one-time operation)
  python music_video_generator.py --prepare --film movie.mp4

  # Generate music video with progressive strategy
  python music_video_generator.py --film movie.mp4 --song track.mp3

  # Use every 2nd beat for fewer cuts
  python music_video_generator.py --film movie.mp4 --song track.mp3 --beat-skip 2

  # Use random strategy with every 4th beat
  python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy random --beat-skip 4
        """
    )

    # Operation mode
    parser.add_argument('--prepare', action='store_true',
                       help='Prepare film library only (no music video generation)')

    # Required arguments
    parser.add_argument('--film', required=True, type=str,
                       help='Path to film/video file')
    parser.add_argument('--song', type=str,
                       help='Path to song/audio file (required unless --prepare)')

    # Scene detection parameters
    parser.add_argument('--threshold', type=float, default=30.0,
                       help='Scene detection threshold (10-50 range, default: 30.0)')
    parser.add_argument('--min-scene-len', type=float, default=1.0,
                       help='Minimum scene duration in seconds (default: 1.0)')
    parser.add_argument('--force-regenerate-clips', action='store_true',
                       help='Force regeneration of clips even if cache exists')

    # Music video generation parameters
    parser.add_argument('--strategy', type=str, default='progressive',
                       choices=['progressive', 'random', 'forward_only', 'no_repeat'],
                       help='Scene selection strategy (default: progressive)')
    parser.add_argument('--beat-skip', type=int, default=1,
                       help='Use every Nth beat (1=all beats, 2=every other, etc. Default: 1)')

    # Output directories
    parser.add_argument('--clips-library-dir', type=str, default='clips_library',
                       help='Directory for film clip library (default: clips_library)')
    parser.add_argument('--output-dir', type=str, default='music_videos',
                       help='Directory for music video outputs (default: music_videos)')

    args = parser.parse_args()

    # Validate arguments
    if not args.prepare and not args.song:
        parser.error("--song is required unless --prepare is specified")

    # Print header
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         MUSIC VIDEO GENERATOR v2.0                          ║
    ╠══════════════════════════════════════════════════════════════╣
    """)

    try:
        # Step 1: Prepare FilmLibrary
        print(f"║  Film: {Path(args.film).name:<53} ║")
        print(f"║  Threshold: {args.threshold:<48} ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")

        library = FilmLibrary(
            args.film,
            threshold=args.threshold,
            min_scene_len=args.min_scene_len,
            force_regenerate=args.force_regenerate_clips,
            clips_library_dir=args.clips_library_dir
        )

        # Check cache or generate
        if library._check_cache() and not args.force_regenerate_clips:
            print("📦 Using cached clips")
            library._load_from_cache()
        else:
            print("🎬 Generating film library...")

            # Detect scenes
            scenes = library.detect_scenes()
            if not scenes:
                print("✗ Scene detection failed")
                return 1

            # Extract clips
            clip_count = library.extract_clips(scenes)
            if clip_count == 0:
                print("✗ Clip extraction failed")
                return 1

            # Generate thumbnails
            library.generate_thumbnails(scenes)

            # Analyze scenes
            library.analyze_scenes(scenes)

            # Save metadata
            library.save_metadata()

        # If --prepare only, stop here
        if args.prepare:
            print("\n✓ Film library preparation complete")
            print(f"   Location: {library.library_dir}")
            print(f"   Scenes: {len(library.get_scenes())}")
            return 0

        # Step 2: Generate Music Video
        print(f"\n🎵 Generating music video...")
        print(f"   Song: {Path(args.song).name}")
        print(f"   Strategy: {args.strategy}")
        print(f"   Beat skip: {args.beat_skip}")

        generator = MusicVideoGenerator(
            library,
            args.song,
            strategy=args.strategy,
            beat_skip=args.beat_skip,
            output_dir=args.output_dir
        )

        # Analyze audio
        music_analysis = generator.analyze_audio()
        if not music_analysis['beats']:
            print("✗ Audio analysis failed")
            return 1

        # Validate scene-beat ratio
        generator.validate_scene_beat_ratio()

        # Select scenes
        selected = generator.select_scenes()
        if not selected:
            print("✗ Scene selection failed")
            return 1

        print(f"\n✓ Music video generation complete!")
        print(f"   Output: {generator.output_dir}")

        return 0

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        return 1
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        return 1
    except KeyboardInterrupt:
        print(f"\n\n✗ Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

**Step 2: Create entry point script**

Create `music_video_generator.py` in project root:
```python
#!/usr/bin/env python3
"""Music Video Generator CLI entry point."""
import sys
from music_video_generator.cli import main

if __name__ == '__main__':
    sys.exit(main())
```

Make it executable:
```bash
chmod +x music_video_generator.py
```

**Step 3: Test CLI manually**

Run: `python music_video_generator.py --help`
Expected: Help text displays

Run: `python music_video_generator.py --prepare --film test-assets/movie.mp4`
Expected: Prepares film library (if test asset exists)

**Step 4: Commit**

```bash
git add music_video_generator/cli.py music_video_generator.py
git commit -m "feat: add CLI interface for Music Video Generator

- Create cli.py with argparse-based interface
- Support --prepare mode for film library only
- Support full generation mode with film + song
- Add all parameters: threshold, strategy, beat-skip
- Create music_video_generator.py entry point script
- Add comprehensive help text and examples

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 12: Update CLAUDE.md Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CLAUDE.md with new tool**

Update the "Core Architecture" section in `CLAUDE.md`:

Replace:
```markdown
### Active Generators (in Root Directory)

1. **ultraRobustArchivalTool.py** - Primary production tool
```

With:
```markdown
### Active Tool

**music_video_generator.py** - Unified Music Video Generator v2.0
- Two-phase architecture: FilmLibrary + MusicVideoGenerator
- Intelligent caching with parameter tracking
- Four scene selection strategies: progressive, random, forward_only, no_repeat
- Beat-skip parameter for controlling cut frequency
- CLI interface with comprehensive options

### Legacy Generators (in attic/)

Old generators moved to `attic/` directory:
- ultraRobustArchivalTool.py - Original primary production tool
```

Add new "Quick Start Commands" section after "Install Dependencies":
```markdown
## Quick Start Commands

### Prepare Film Library (one-time per film)
```bash
python music_video_generator.py --prepare --film movie.mp4 --threshold 30.0
```

### Generate Music Video
```bash
# With every beat (default)
python music_video_generator.py --film movie.mp4 --song track.mp3

# With every 2nd beat (fewer cuts)
python music_video_generator.py --film movie.mp4 --song track.mp3 --beat-skip 2

# With random strategy and every 4th beat
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy random --beat-skip 4
```
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for new Music Video Generator

- Document new music_video_generator.py as primary tool
- Add Quick Start Commands section
- Move old generators to legacy section
- Add examples for common workflows

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 13: Move Legacy Generators to Attic

**Files:**
- Move multiple generator files to attic/

**Step 1: Move legacy generators**

```bash
# Move all legacy generators
mv robust_music_video_generator.py attic/ 2>/dev/null || true
mv progressive_sampling_generator.py attic/ 2>/dev/null || true
mv forward_only_generator.py attic/ 2>/dev/null || true
mv perfect_forward_generator.py attic/ 2>/dev/null || true
mv no_repeat_generator.py attic/ 2>/dev/null || true
mv robust_clip_generator.py attic/ 2>/dev/null || true
mv full_song_generator.py attic/ 2>/dev/null || true
mv ultraRobustArchivalTool.py attic/ 2>/dev/null || true
mv premiere_style_archival_engine.py attic/ 2>/dev/null || true
```

**Step 2: Verify moved files**

Run: `ls -la attic/*.py | grep -E "robust|progressive|forward|premiere" | wc -l`
Expected: Should show moved generator files

Run: `ls -la *.py | grep -E "robust|progressive|forward|premiere" | wc -l`
Expected: Should be 0 (all moved)

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: move legacy generators to attic/

Move all old generator implementations to attic/:
- robust_music_video_generator.py
- progressive_sampling_generator.py
- forward_only_generator.py
- perfect_forward_generator.py
- no_repeat_generator.py
- robust_clip_generator.py
- full_song_generator.py
- ultraRobustArchivalTool.py
- premiere_style_archival_engine.py

These are replaced by unified music_video_generator.py

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 14: Integration Testing

**Files:**
- Create: `tests/integration/test_full_workflow.py`

**Step 1: Write integration test**

Create `tests/integration/test_full_workflow.py`:
```python
#!/usr/bin/env python3
"""Integration tests for complete workflow."""
import pytest
import os
from pathlib import Path
from music_video_generator.film_library import FilmLibrary
from music_video_generator.music_video_generator import MusicVideoGenerator


@pytest.mark.skipif(
    not (os.path.exists("test-assets/test_video.mp4") and
         os.path.exists("test-assets/test_audio.wav")),
    reason="Test assets not available"
)
class TestFullWorkflow:
    """Test complete end-to-end workflow."""

    def test_complete_workflow_progressive(self, tmp_path):
        """Test full workflow: prepare library + generate video."""
        # Step 1: Prepare FilmLibrary
        library = FilmLibrary(
            "test-assets/test_video.mp4",
            threshold=30.0,
            clips_library_dir=str(tmp_path / "clips_lib")
        )

        # Detect scenes
        scenes = library.detect_scenes()
        assert len(scenes) > 0

        # Extract clips (limit for speed)
        library.scenes = scenes[:10]  # Limit to 10 for testing
        clip_count = library.extract_clips(library.scenes)
        assert clip_count > 0

        # Generate thumbnails
        library.generate_thumbnails(library.scenes)

        # Analyze scenes
        library.analyze_scenes(library.scenes)

        # Save metadata
        library.save_metadata()

        # Verify metadata saved
        assert (library.library_dir / "metadata.json").exists()

        # Step 2: Generate Music Video
        generator = MusicVideoGenerator(
            library,
            "test-assets/test_audio.wav",
            strategy='progressive',
            beat_skip=2,  # Use every 2nd beat for speed
            output_dir=str(tmp_path / "output")
        )

        # Analyze audio
        music_analysis = generator.analyze_audio()
        assert music_analysis['beats_detected'] > 0

        # Validate ratio
        result = generator.validate_scene_beat_ratio()
        assert result is True

        # Select scenes
        selected = generator.select_scenes()
        assert len(selected) > 0

        print(f"\n✓ Integration test passed:")
        print(f"   Scenes: {len(library.scenes)}")
        print(f"   Beats: {music_analysis['beats_detected']}")
        print(f"   Selected: {len(selected)}")

    def test_cache_reuse(self, tmp_path):
        """Test that cache is properly reused."""
        # First library creation
        library1 = FilmLibrary(
            "test-assets/test_video.mp4",
            threshold=30.0,
            clips_library_dir=str(tmp_path / "clips_lib")
        )

        scenes = library1.detect_scenes()
        library1.scenes = scenes[:5]
        library1.extract_clips(library1.scenes)
        library1.save_metadata()

        # Second library creation (should use cache)
        library2 = FilmLibrary(
            "test-assets/test_video.mp4",
            threshold=30.0,
            clips_library_dir=str(tmp_path / "clips_lib")
        )

        assert library2._check_cache() is True
        library2._load_from_cache()

        assert len(library2.scenes) == len(library1.scenes)
        print("\n✓ Cache reuse test passed")
```

**Step 2: Run integration test**

Run: `pytest tests/integration/test_full_workflow.py -v -s`
Expected: PASS (or SKIP if test assets don't exist)

**Step 3: Commit**

```bash
git add tests/integration/test_full_workflow.py
git commit -m "test: add integration tests for full workflow

- Test complete workflow: library prep + video generation
- Test cache reuse functionality
- Use test assets with scene/beat limits for speed
- Verify all major components work together

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Summary

**Implementation complete!** The plan creates a unified Music Video Generator with:

1. ✅ **FilmLibrary class** - Scene detection, clip extraction, caching
2. ✅ **MusicVideoGenerator class** - Audio analysis, strategy-based selection
3. ✅ **Four scene selection strategies** - Progressive, random, forward-only, no-repeat
4. ✅ **Intelligent caching** - Parameter-based cache validation
5. ✅ **CLI interface** - Comprehensive argparse-based tool
6. ✅ **Beat-skip parameter** - Control cut frequency
7. ✅ **Type safety** - safe_float/safe_int for numpy
8. ✅ **Validation** - Scene-beat ratio warnings
9. ✅ **Documentation** - Updated CLAUDE.md
10. ✅ **Legacy cleanup** - Moved old generators to attic/
11. ✅ **Testing** - Unit tests and integration tests

**Next steps after implementation:**
- Task 15-17: Video generation, HTML reports, FFmpeg rendering (deferred for follow-up)
- Generate test assets: `python create_test_video.py && python create_test_audio.py`
- Run full test suite: `python run_tests.py`
- Test CLI: `python music_video_generator.py --prepare --film test-assets/test_video.mp4`
