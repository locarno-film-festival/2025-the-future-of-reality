#!/usr/bin/env python3
"""MusicLibrary class for audio analysis and caching."""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
import warnings

warnings.filterwarnings("ignore")

import librosa
import numpy as np


@contextmanager
def suppress_stderr():
    """Temporarily suppress stderr (for noisy audio decoders)."""
    with open(os.devnull, "w") as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


class MusicLibrary:
    """Manages audio analysis and caching."""

    def __init__(
        self,
        song_path,
        force_regenerate=False,
        music_library_dir="music_library",
        song_name=None,
    ):
        """Initialize MusicLibrary.

        Args:
            song_path: Path to audio file
            force_regenerate: Force regeneration even if cache exists
            music_library_dir: Base directory for music library storage
            song_name: Override for library directory name (default: audio filename stem)
        """
        # Validate song exists
        if not os.path.exists(song_path):
            raise FileNotFoundError(f"Song not found: {song_path}")

        self.song_path = str(song_path)
        self.song_name = song_name or Path(song_path).stem
        self.force_regenerate = force_regenerate

        # Set up library directory
        self.library_dir = Path(music_library_dir) / self.song_name

        self.beats = []
        self.beat_times = []
        self.metadata = {}
        self.subtitle_path = None

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
        """Check if valid cached analysis exists.

        Returns:
            bool: True if cache exists
        """
        return self._load_metadata()

    def _load_from_cache(self):
        """Load analysis from existing cache.

        Returns:
            bool: True if successfully loaded from cache
        """
        if not self._load_metadata():
            print(f"✗ Failed to load cache: metadata not found or invalid")
            return False

        # Extract beat times from metadata
        self.beat_times = self.metadata.get("beats", [])
        self.beats = []  # Frame data not cached, only times

        # Validate beat_times is a list
        if not isinstance(self.beat_times, list):
            print(f"✗ Failed to load cache: invalid beat times format")
            self.beat_times = []
            return False

        # Load subtitle path if stored
        stored_subtitle = self.metadata.get("subtitle_path")
        if stored_subtitle and os.path.exists(stored_subtitle):
            self.subtitle_path = stored_subtitle

        print(f"✓ Loaded audio analysis from cache")
        print(f"  Cache location: {self.library_dir}")
        print(f"  Beats detected: {len(self.beat_times)}")
        print(f"  BPM: {self.metadata.get('bpm', 0):.1f}")
        print(f"  Duration: {self.metadata.get('duration', 0):.1f}s")
        if self.subtitle_path:
            print(f"  Subtitles: {self.subtitle_path}")

        return True

    def analyze_audio(self):
        """Librosa beat detection and tempo analysis.

        Returns:
            dict: Music analysis with duration, bpm, beats, tempo_confidence, sample_rate
        """
        print(f"\n🎵 Analyzing audio: {self.song_name}...")

        try:
            # Load audio (suppress decoder warnings about MP3 headers/tags)
            with suppress_stderr():
                audio_data, sample_rate = librosa.load(self.song_path)

            # Beat tracking
            tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=sample_rate)

            # Convert beat frames to time
            beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)

            # Calculate duration
            duration = len(audio_data) / sample_rate

            # Extract tempo from array (librosa returns array)
            tempo_scalar = tempo[0] if isinstance(tempo, np.ndarray) else tempo

            # Store results
            self.beats = beat_frames
            self.beat_times = [self.safe_float(t) for t in beat_times]

            analysis = {
                "duration": self.safe_float(duration),
                "bpm": self.safe_float(tempo_scalar),
                "beats_detected": len(beat_times),
                "beats": self.beat_times,
                "tempo_confidence": 0.85,  # Placeholder, librosa doesn't provide this
                "sample_rate": self.safe_int(sample_rate),
            }

            print(f"   Duration: {self.safe_float(duration):.1f}s")
            print(f"   BPM: {self.safe_float(tempo_scalar):.1f}")
            print(f"   Beats detected: {len(beat_times)}")

            return analysis

        except Exception as e:
            print(f"   ✗ Audio analysis failed: {e}")

            # Return defaults
            return {
                "duration": 0.0,
                "bpm": 120.0,
                "beats_detected": 0,
                "beats": [],
                "tempo_confidence": 0.0,
                "sample_rate": 22050,
            }

    def save_metadata(self, analysis, subtitle_path=None):
        """Save metadata.json to music_library/{song_name}/

        Args:
            analysis: Audio analysis dictionary
            subtitle_path: Optional path to subtitle SRT file
        """
        print(f"\n💾 Saving metadata...")

        if subtitle_path:
            self.subtitle_path = subtitle_path

        # Ensure directory exists
        self.library_dir.mkdir(parents=True, exist_ok=True)

        # Build metadata
        metadata = {
            "song_path": self.song_path,
            "song_name": self.song_name,
            "created_at": datetime.now().isoformat(),
            "duration": analysis["duration"],
            "bpm": analysis["bpm"],
            "beats_detected": analysis["beats_detected"],
            "beats": analysis["beats"],
            "tempo_confidence": analysis["tempo_confidence"],
            "sample_rate": analysis["sample_rate"],
            "subtitle_path": self.subtitle_path,
        }

        # Save to JSON
        metadata_path = self.library_dir / "metadata.json"
        try:
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            print(f"   ✓ Saved metadata: {metadata_path}")
            self.metadata = metadata

        except IOError as e:
            print(f"   ✗ Failed to save metadata: {e}")

    def get_analysis(self):
        """Return audio analysis metadata.

        Returns:
            dict: Analysis metadata including beats, bpm, duration
        """
        if not self.metadata:
            return None
        return self.metadata
