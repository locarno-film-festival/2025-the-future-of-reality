#!/usr/bin/env python3
"""FilmLibrary class for scene detection and clip management."""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import warnings
import gc

# Suppress specific PySceneDetect deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="scenedetect")

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector, AdaptiveDetector
import cv2
import numpy as np


class FilmLibrary:
    """Manages film scene detection and clip library."""

    def __init__(
        self,
        film_path,
        threshold=30.0,
        min_scene_len=1.0,
        force_regenerate=False,
        clips_library_dir="clips_library",
        detector="content",
        luma_only=False,
        adaptive_window_width=2,
    ):
        """Initialize FilmLibrary.

        Args:
            film_path: Path to source video file
            threshold: Scene detection sensitivity (10-50 range)
            min_scene_len: Minimum scene duration in seconds
            force_regenerate: Force regeneration even if cache exists
            clips_library_dir: Base directory for clip library storage
            detector: Detector type ('content' or 'adaptive')
            luma_only: Use only luminance for detection (ContentDetector only)
            adaptive_window_width: Window width for AdaptiveDetector (default: 2)
        """
        # Validate film exists
        if not os.path.exists(film_path):
            raise FileNotFoundError(f"Film not found: {film_path}")

        self.film_path = str(film_path)
        self.film_name = Path(film_path).stem
        self.threshold = threshold
        self.min_scene_len = min_scene_len
        self.force_regenerate = force_regenerate
        self.detector = detector
        self.luma_only = luma_only
        self.adaptive_window_width = adaptive_window_width

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

    def _load_metadata(self):
        """Load metadata from JSON file.

        Returns:
            bool: True if successfully loaded
        """
        metadata_path = self.library_dir / "metadata.json"

        if not metadata_path.exists():
            return False

        try:
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def _check_cache(self):
        """Check if valid cached clips exist with matching parameters.

        Returns:
            bool: True if cache exists and parameters match
        """
        # Try to load metadata (also populates self.metadata)
        if not self._load_metadata():
            return False

        # Check if parameters match
        cached_params = self.metadata.get("scene_detection_params", {})

        if (
            cached_params.get("threshold") == self.threshold
            and cached_params.get("min_scene_len") == self.min_scene_len
            and cached_params.get("detector", "content") == self.detector
            and cached_params.get("luma_only", False) == self.luma_only
        ):
            return True

        return False

    def _load_from_cache(self):
        """Load scenes and metadata from existing cache.

        Returns:
            bool: True if successfully loaded from cache
        """
        if not self._load_metadata():
            print(f"✗ Failed to load cache: metadata not found or invalid")
            return False

        self.scenes = self.metadata.get("scenes", [])

        # Validate scenes is a list
        if not isinstance(self.scenes, list):
            print(f"✗ Failed to load cache: invalid scenes format")
            self.scenes = []
            return False

        print(f"✓ Loaded {len(self.scenes)} scenes from cache")
        print(f"  Cache location: {self.library_dir}")

        return True

    def detect_scenes(self):
        """Run PySceneDetect scene detection.

        Returns:
            list: Scene metadata dictionaries
        """
        print(f"\n🎬 Detecting scenes in {self.film_name}...")
        print(f"   Detector: {self.detector}")
        print(f"   Threshold: {self.threshold}")
        if self.detector in ("content", "both"):
            print(f"   Luma only: {self.luma_only}")
        print(f"   Min scene length: {self.min_scene_len}s")

        video_manager = None
        try:
            # Set up scene detection
            video_manager = VideoManager([self.film_path])
            scene_manager = SceneManager()

            # Choose detector based on settings
            if self.detector == "adaptive":
                scene_manager.add_detector(
                    AdaptiveDetector(
                        adaptive_threshold=self.threshold,
                        min_scene_len=int(
                            self.min_scene_len * 30
                        ),  # Approximate frames
                        window_width=self.adaptive_window_width,
                    )
                )
            elif self.detector == "both":
                # Use both detectors - scene detected when EITHER triggers
                print(f"   Using combined detection (content + adaptive)")
                scene_manager.add_detector(
                    ContentDetector(threshold=self.threshold, luma_only=self.luma_only)
                )
                scene_manager.add_detector(
                    AdaptiveDetector(
                        adaptive_threshold=self.threshold
                        / 10,  # Scale threshold for adaptive
                        min_scene_len=int(self.min_scene_len * 30),
                        window_width=self.adaptive_window_width,
                    )
                )
            else:
                # Default: ContentDetector
                scene_manager.add_detector(
                    ContentDetector(threshold=self.threshold, luma_only=self.luma_only)
                )

            # Detect scenes
            video_manager.set_duration()
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()

            print(f"   Found {len(scene_list)} raw scenes")

            # Process scenes
            self.scenes = []
            filtered_scene_id = 0
            for i, scene in enumerate(scene_list):
                start_time = self.safe_float(scene[0].get_seconds())
                end_time = self.safe_float(scene[1].get_seconds())
                duration = end_time - start_time

                # Filter by minimum duration
                if duration < self.min_scene_len:
                    continue

                scene_info = {
                    "id": filtered_scene_id,  # Use sequential ID for kept scenes
                    "start": start_time,
                    "end": end_time,
                    "duration": duration,
                    "clip_filename": f"scene_{filtered_scene_id:04d}.mp4",
                    "thumbnail_filename": f"thumb_{filtered_scene_id:04d}.jpg",
                }

                self.scenes.append(scene_info)
                filtered_scene_id += 1

                # Progress reporting
                if (i + 1) % 20 == 0:
                    print(f"   Analyzed {i + 1}/{len(scene_list)} raw scenes...")

            print(
                f"   ✓ Detected {len(self.scenes)} scenes (filtered by min_scene_len)"
            )

            return self.scenes

        except Exception as e:
            print(f"   ✗ Scene detection failed: {e}")
            return []
        finally:
            if video_manager is not None:
                video_manager.release()

    def extract_clips(self, scenes):
        """Extract individual scene clips to clips/ directory using FFmpeg.

        Args:
            scenes: List of scene metadata dictionaries (will be modified with 'has_clip' flag)

        Returns:
            int: Count of successfully exported clips
        """
        # Validate input
        if not scenes or not isinstance(scenes, list):
            print("   ✗ No scenes provided for clip extraction")
            return 0

        print(f"\n🎞️  Extracting {len(scenes)} scene clips...")

        # Ensure clips directory exists
        self.clips_dir.mkdir(parents=True, exist_ok=True)

        # Get video duration and check for audio using ffprobe
        video_duration = self._get_video_duration()
        has_audio = self._check_has_audio()

        if has_audio:
            print(f"   Source video has audio (will be preserved in clips)")
        else:
            print(f"   Source video has no audio track")

        clips_exported = 0
        clips_failed = []

        for i, scene in enumerate(scenes):
            # Progress reporting every 20 clips
            if (i + 1) % 20 == 0:
                print(f"   Extracting clip {i + 1}/{len(scenes)}...")

            try:
                start_time = scene["start"]
                end_time = scene["end"]
                clip_path = self.clips_dir / scene["clip_filename"]

                # Validate bounds
                if video_duration and start_time >= video_duration:
                    error_msg = f"Start time {start_time:.2f}s >= video duration {video_duration:.2f}s"
                    clips_failed.append((i, error_msg))
                    scene["has_clip"] = False
                    if len(clips_failed) <= 3:
                        print(f"   ⚠ Clip {i} failed: {error_msg}")
                    continue

                # Clamp end_time to video duration
                if video_duration and end_time > video_duration:
                    end_time = video_duration

                # Calculate duration
                duration = end_time - start_time

                # Ensure minimum duration
                if duration < 0.1:
                    error_msg = f"Duration {duration:.3f}s < 0.1s minimum"
                    clips_failed.append((i, error_msg))
                    scene["has_clip"] = False
                    if len(clips_failed) <= 3:
                        print(f"   ⚠ Clip {i} failed: {error_msg}")
                    continue

                # Use FFmpeg directly for reliable clip extraction with audio
                success = self._ffmpeg_extract_clip(
                    start_time, duration, clip_path, has_audio
                )

                if success:
                    clips_exported += 1
                    scene["has_clip"] = True
                    scene["has_audio"] = has_audio
                else:
                    clips_failed.append((i, "FFmpeg extraction failed"))
                    scene["has_clip"] = False
                    if len(clips_failed) <= 3:
                        print(f"   ⚠ Clip {i} failed: FFmpeg extraction failed")

            except Exception as e:
                clips_failed.append((i, str(e)))
                scene["has_clip"] = False
                if len(clips_failed) <= 3:
                    print(f"   ⚠ Clip {i} failed: {e}")
                continue

        print(f"   ✓ Exported {clips_exported} clips")
        if clips_failed:
            print(f"   ✗ Failed to export {len(clips_failed)} clips")
            print(f"   First errors:")
            for idx, error in clips_failed[:5]:
                print(f"     Clip {idx}: {error}")

        return clips_exported

    def _get_frame_at_time(self, time_seconds):
        """Extract a single frame at the given time using OpenCV.

        Args:
            time_seconds: Time position in seconds

        Returns:
            numpy.ndarray: Frame in RGB format, or None on failure
        """
        cap = cv2.VideoCapture(self.film_path)
        try:
            cap.set(cv2.CAP_PROP_POS_MSEC, time_seconds * 1000)
            ret, frame = cap.read()
            if not ret:
                return None
            # OpenCV reads BGR, convert to RGB
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        finally:
            cap.release()

    def _get_film_properties(self):
        """Get film properties using ffprobe.

        Returns:
            dict: Film properties (duration, resolution, fps, codec)
        """
        defaults = {
            "duration": 0.0,
            "resolution": "unknown",
            "fps": 0.0,
            "codec": "unknown",
        }
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate,codec_name",
                "-show_entries", "format=duration",
                "-of", "json",
                self.film_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return defaults

            data = json.loads(result.stdout)
            stream = data.get("streams", [{}])[0]
            fmt = data.get("format", {})

            # Parse frame rate (e.g. "30/1" or "24000/1001")
            fps_str = stream.get("r_frame_rate", "0/1")
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 0.0

            width = stream.get("width", 0)
            height = stream.get("height", 0)

            return {
                "duration": self.safe_float(fmt.get("duration", 0.0)),
                "resolution": f"{width}x{height}" if width and height else "unknown",
                "fps": round(fps, 2),
                "codec": stream.get("codec_name", "unknown"),
            }
        except Exception:
            return defaults

    def _get_video_duration(self):
        """Get video duration using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                self.film_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception:
            return None

    def _check_has_audio(self):
        """Check if video has audio stream using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                self.film_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return "audio" in result.stdout
        except Exception:
            return False

    def _ffmpeg_extract_clip(
        self, start_time, duration, output_path, include_audio=True
    ):
        """Extract a clip using FFmpeg directly.

        Args:
            start_time: Start time in seconds
            duration: Duration in seconds
            output_path: Output file path
            include_audio: Whether to include audio

        Returns:
            bool: True if successful
        """
        try:
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-ss",
                str(start_time),  # Seek to start (before input for speed)
                "-i",
                self.film_path,
                "-t",
                str(duration),  # Duration
                "-c:v",
                "libx264",  # Video codec
                "-preset",
                "fast",
                "-crf",
                "23",  # Quality (lower = better, 18-28 is good range)
                # No -r flag: preserves original frame rate
            ]

            if include_audio:
                cmd.extend(["-c:a", "aac", "-b:a", "128k"])  # Audio codec
            else:
                cmd.extend(["-an"])  # No audio

            cmd.append(str(output_path))

            # Run FFmpeg silently
            result = subprocess.run(cmd, capture_output=True, text=True)

            return result.returncode == 0

        except Exception:
            return False

    def generate_thumbnails(self, scenes):
        """Generate thumbnail images for each scene."""
        if not scenes or not isinstance(scenes, list):
            print("   ✗ No scenes provided for thumbnail generation")
            return

        print(f"\n🖼️  Generating thumbnails for {len(scenes)} scenes...")
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

        generated = 0
        for i, scene in enumerate(scenes):
            try:
                middle_time = (scene["start"] + scene["end"]) / 2
                frame = self._get_frame_at_time(middle_time)
                if frame is None:
                    print(f"   ⚠ Failed to get frame for scene {i}")
                    continue

                thumb_path = self.thumbnails_dir / scene["thumbnail_filename"]
                thumb_height = 120
                aspect_ratio = frame.shape[1] / frame.shape[0]
                thumb_width = int(thumb_height * aspect_ratio)
                thumb = cv2.resize(frame, (thumb_width, thumb_height))
                thumb_bgr = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(thumb_path), thumb_bgr)
                generated += 1

            except Exception as e:
                print(f"   ⚠ Failed to generate thumbnail for scene {i}: {e}")
                continue

        print(f"   ✓ Generated {generated} thumbnails")

    def analyze_scenes(self, scenes):
        """Add color, brightness, pace analysis to scene metadata."""
        if not scenes or not isinstance(scenes, list):
            print("   ✗ No scenes provided for analysis")
            return scenes

        print(f"\n🔍 Analyzing {len(scenes)} scenes...")

        try:
            props = self._get_film_properties()
            video_duration = props["duration"]
            failed_analyses = 0

            for scene in scenes:
                try:
                    middle_time = (scene["start"] + scene["end"]) / 2
                    frame = self._get_frame_at_time(middle_time)

                    if frame is None:
                        raise ValueError("Could not extract frame")

                    avg_color = np.mean(frame, axis=(0, 1))
                    scene["avg_color_rgb"] = avg_color.tolist()
                    scene["avg_color_hex"] = "#{:02x}{:02x}{:02x}".format(
                        int(avg_color[0]), int(avg_color[1]), int(avg_color[2])
                    )

                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                    scene["avg_brightness"] = float(np.mean(gray))

                    duration = scene["duration"]
                    if duration < 2:
                        scene["pace"] = "fast"
                    elif duration > 10:
                        scene["pace"] = "slow"
                    else:
                        scene["pace"] = "medium"

                    scene["position_ratio"] = (
                        scene["start"] / video_duration if video_duration > 0 else 0.0
                    )

                except Exception:
                    scene["avg_brightness"] = 0.0
                    scene["avg_color_rgb"] = [0.0, 0.0, 0.0]
                    scene["avg_color_hex"] = "#000000"
                    scene["pace"] = "medium"
                    scene["position_ratio"] = 0.0
                    failed_analyses += 1
                    continue

            print(f"   ✓ Analyzed {len(scenes)} scenes")
            if failed_analyses > 0:
                print(f"   ⚠ Failed to analyze {failed_analyses} scenes")

            return scenes

        except Exception as e:
            print(f"   ✗ Scene analysis failed: {e}")
            return scenes

    def save_metadata(self):
        """Save metadata.json to clips_library/{film_name}/"""
        print(f"\n💾 Saving metadata...")
        self.library_dir.mkdir(parents=True, exist_ok=True)

        film_properties = self._get_film_properties()

        metadata = {
            "film_path": self.film_path,
            "film_name": self.film_name,
            "created_at": datetime.now().isoformat(),
            "scene_detection_params": {
                "threshold": self.threshold,
                "min_scene_len": self.min_scene_len,
                "detector": self.detector,
                "luma_only": self.luma_only,
            },
            "film_properties": film_properties,
            "scenes": self.scenes,
            "total_scenes": len(self.scenes),
        }

        metadata_path = self.library_dir / "metadata.json"
        try:
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            print(f"   ✓ Saved metadata: {metadata_path}")
            self.metadata = metadata
        except IOError as e:
            print(f"   ✗ Failed to save metadata: {e}")

    def get_scenes(self):
        """Return list of available scenes with metadata.

        Returns:
            list: Scene metadata dictionaries
        """
        return self.scenes
