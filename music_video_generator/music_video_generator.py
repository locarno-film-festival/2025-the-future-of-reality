#!/usr/bin/env python3
"""MusicVideoGenerator class for creating music videos from film libraries."""

import os
import re
import sys
import subprocess
import tempfile
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


class MusicVideoGenerator:
    """Generates music videos from FilmLibrary using various strategies."""

    VALID_STRATEGIES = ["progressive", "random", "forward_only", "no_repeat"]

    def __init__(
        self,
        film_library,
        song_path,
        strategy="progressive",
        beat_skip=1,
        output_dir="music_videos",
        music_library=None,
        subtitle_path=None,
    ):
        """Initialize MusicVideoGenerator.

        Args:
            film_library: FilmLibrary instance with cached clips
            song_path: Path to audio file
            strategy: Scene selection strategy (progressive|random|forward_only|no_repeat)
            beat_skip: Use every Nth beat (1=every beat, 2=every other beat)
            output_dir: Base directory for music video outputs
            music_library: Optional MusicLibrary instance with cached audio analysis
            subtitle_path: Optional path to SRT subtitle file for burn-in

        Raises:
            FileNotFoundError: If song_path does not exist
            ValueError: If strategy is not valid
        """
        # Validate song exists
        if not os.path.exists(song_path):
            raise FileNotFoundError(f"Song not found: {song_path}")

        # Validate strategy
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(
                f"Invalid strategy: {strategy}. Must be one of {self.VALID_STRATEGIES}"
            )

        self.film_library = film_library
        self.music_library = music_library
        self.song_path = str(song_path)
        self.strategy = strategy
        self.beat_skip = beat_skip

        # Derive song identifiers — YouTube downloads land at
        # music_library/<sanitized-title>/song.<ext>, so fall back to the
        # parent directory name when the stem is the generic "song".
        song_path_obj = Path(song_path)
        raw_song_name = (
            song_path_obj.parent.name
            if song_path_obj.stem == "song"
            else song_path_obj.stem
        )
        if " - " in raw_song_name:
            artist_raw, title_raw = raw_song_name.split(" - ", 1)
        else:
            artist_raw, title_raw = "", raw_song_name

        self.song_name = raw_song_name
        self.artist = self._sanitize_name(artist_raw)
        self.title = self._sanitize_name(title_raw)
        self.film_slug = self._sanitize_name(film_library.film_name)

        # Build a basename for output files: film_artist_title_date (artist omitted if absent)
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.basename = "_".join(
            p for p in (self.film_slug, self.artist, self.title, date_str) if p
        )

        # Set up output directory (keep timestamp + strategy for per-run uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        song_slug = f"{self.artist}-{self.title}" if self.artist else self.title
        self.output_dir = (
            Path(output_dir)
            / f"{self.film_slug}_{song_slug}_{strategy}_{timestamp}"
        )

        self.subtitle_path = subtitle_path
        self.beats = []
        self.beat_times = []
        self.music_analysis = {}
        self.selected_scenes = []

    @staticmethod
    def _sanitize_name(name):
        """Make a name filesystem-safe: collapse whitespace into dashes, drop reserved chars."""
        if not name:
            return ""
        name = re.sub(r"\s+", "-", name.strip())
        name = re.sub(r'[/\\:*?"<>|]', "", name)
        return name

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

        Uses cached analysis from MusicLibrary if available.

        Returns:
            dict: Music analysis with duration, bpm, beats, tempo_confidence, sample_rate
        """
        # Use cached analysis if available
        if self.music_library:
            cached_analysis = self.music_library.get_analysis()
            if cached_analysis:
                print(f"\n🎵 Using cached audio analysis: {self.song_name}")
                print(f"   Duration: {cached_analysis['duration']:.1f}s")
                print(f"   BPM: {cached_analysis['bpm']:.1f}")
                print(f"   Beats detected: {cached_analysis['beats_detected']}")

                self.beats = []  # Frame data not cached
                self.beat_times = cached_analysis["beats"]
                self.music_analysis = cached_analysis

                return self.music_analysis

        # Otherwise, run analysis
        print(f"\n🎵 Analyzing audio: {self.song_name}")

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

            self.music_analysis = {
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

            return self.music_analysis

        except Exception as e:
            print(f"   ✗ Audio analysis failed: {e}")

            # Return defaults
            self.music_analysis = {
                "duration": 0.0,
                "bpm": 120.0,
                "beats_detected": 0,
                "beats": [],
                "tempo_confidence": 0.0,
                "sample_rate": 22050,
            }

            return self.music_analysis

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
            print(
                f"   1. Use --beat-skip {suggested_skip} (1 clip per {suggested_skip} beats)"
            )
            print(f"   2. Use 'random' or 'no-repeat' strategy (allows scene reuse)")
            print(f"   3. Lower scene detection --threshold to detect more scenes")
            print(f"\n   Continuing with current settings...")

            return True

        print(
            f"\n✓ Scene-beat ratio valid: {len(scenes)} scenes for {effective_beats} beats"
        )
        return True

    def select_scenes(self):
        """Apply strategy to map scenes to beats.

        Returns:
            list: Scene-to-beat mappings
        """
        print(f"\n🎬 Selecting scenes using '{self.strategy}' strategy...")

        scenes = self.film_library.get_scenes()

        # Apply beat_skip
        selected_beats = self.beat_times[:: self.beat_skip]

        print(f"   Available scenes: {len(scenes)}")
        print(f"   Beats to use: {len(selected_beats)} (every {self.beat_skip} beat)")

        # Call appropriate strategy method
        strategy_map = {
            "progressive": self._select_progressive,
            "random": self._select_random,
            "forward_only": self._select_forward_only,
            "no_repeat": self._select_no_repeat,
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

            mappings.append(
                {
                    "beat_start": beat_start,
                    "beat_end": beat_end,
                    "beat_duration": beat_duration,
                    "scene": selected_scene,
                    "beat_index": i,
                }
            )

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

            mappings.append(
                {
                    "beat_start": beat_start,
                    "beat_end": beat_end,
                    "beat_duration": beat_duration,
                    "scene": selected_scene,
                    "beat_index": i,
                }
            )

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

            mappings.append(
                {
                    "beat_start": beat_start,
                    "beat_end": beat_end,
                    "beat_duration": beat_duration,
                    "scene": selected_scene,
                    "beat_index": i,
                }
            )

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

            mappings.append(
                {
                    "beat_start": beat_start,
                    "beat_end": beat_end,
                    "beat_duration": beat_duration,
                    "scene": selected_scene,
                    "beat_index": i,
                }
            )

        return mappings

    def assemble_video(self, fade_duration=0.0):
        """Assemble final music video from selected scenes and audio using FFmpeg.

        Args:
            fade_duration: Duration of crossfade between clips (not yet implemented in FFmpeg version)

        Returns:
            str: Path to output video file, or None on failure
        """
        print(f"\n🎬 Assembling final video using FFmpeg...")

        if not self.selected_scenes:
            print("   ✗ No scenes selected")
            return None

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        clips_dir = self.film_library.clips_dir
        output_path = self.output_dir / f"{self.basename}.mp4"

        # Create a temporary concat file for FFmpeg
        concat_file = self.output_dir / "concat_list.txt"
        temp_trimmed_dir = self.output_dir / "temp_clips"
        temp_trimmed_dir.mkdir(exist_ok=True)

        try:
            # Step 1: Create trimmed clips matching beat durations
            print(f"   Trimming {len(self.selected_scenes)} clips to beat durations...")
            trimmed_clips = []

            for i, mapping in enumerate(self.selected_scenes):
                scene = mapping["scene"]
                beat_duration = mapping["beat_duration"]
                source_clip = clips_dir / scene["clip_filename"]
                trimmed_clip = temp_trimmed_dir / f"trim_{i:04d}.mp4"

                if not source_clip.exists():
                    print(f"   ⚠ Clip {i} not found: {source_clip}")
                    continue

                # Trim clip to beat duration using FFmpeg (no audio)
                success = self._ffmpeg_trim_clip(
                    source_clip, trimmed_clip, beat_duration
                )

                if success:
                    trimmed_clips.append(trimmed_clip)
                else:
                    print(f"   ⚠ Failed to trim clip {i}")

                # Progress reporting
                if (i + 1) % 50 == 0:
                    print(f"   Trimmed {i + 1}/{len(self.selected_scenes)} clips...")

            if not trimmed_clips:
                print("   ✗ No clips successfully trimmed")
                return None

            print(f"   ✓ Trimmed {len(trimmed_clips)} clips")

            # Verify trimmed clips exist and have content
            valid_clips = []
            for clip_path in trimmed_clips:
                if clip_path.exists() and clip_path.stat().st_size > 0:
                    valid_clips.append(clip_path)

            if len(valid_clips) != len(trimmed_clips):
                print(
                    f"   ⚠ Only {len(valid_clips)}/{len(trimmed_clips)} clips are valid"
                )

            if not valid_clips:
                print("   ✗ No valid trimmed clips")
                return None

            # Step 2: Write concat file
            print(f"   Creating concat list with {len(valid_clips)} clips...")
            with open(concat_file, "w") as f:
                for clip_path in valid_clips:
                    # Use absolute path and escape single quotes for FFmpeg concat
                    abs_path = str(clip_path.resolve())
                    # FFmpeg concat requires escaping: ' becomes '\''
                    escaped_path = abs_path.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")

            # Step 3: Concatenate all clips (without audio)
            print(f"   Concatenating clips...")
            temp_video = self.output_dir / "temp_video.mp4"
            concat_success = self._ffmpeg_concat(concat_file, temp_video)

            if not concat_success:
                print("   ✗ Failed to concatenate clips")
                return None

            # Step 4: Add music track
            print(f"   Adding music track...")
            final_success = self._ffmpeg_add_audio(
                temp_video, self.song_path, output_path
            )

            if not final_success:
                print("   ✗ Failed to add audio")
                return None

            # Step 5: Burn in subtitles if available
            if self.subtitle_path and os.path.exists(self.subtitle_path):
                print(f"   Burning in subtitles...")
                subtitled_output = (
                    self.output_dir / f"{self.basename}_subtitled.mp4"
                )
                sub_success = self._ffmpeg_burn_subtitles(
                    output_path, self.subtitle_path, subtitled_output
                )
                if sub_success:
                    # Replace output with subtitled version
                    output_path.unlink()
                    subtitled_output.rename(output_path)
                    print(f"   ✓ Subtitles burned in")
                else:
                    print(f"   ⚠ Subtitle burn-in failed, continuing without subtitles")

            # Cleanup temp files
            print(f"   Cleaning up temporary files...")
            for clip in trimmed_clips:
                try:
                    clip.unlink()
                except Exception:
                    pass
            try:
                temp_trimmed_dir.rmdir()
                concat_file.unlink()
                temp_video.unlink()
            except Exception:
                pass

            print(f"   ✓ Video exported successfully: {output_path.name}")
            return str(output_path)

        except Exception as e:
            print(f"   ✗ Video assembly failed: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _ffmpeg_trim_clip(self, input_path, output_path, duration):
        """Trim a clip to specified duration using FFmpeg.

        Args:
            input_path: Source clip path
            output_path: Output clip path
            duration: Target duration in seconds

        Returns:
            bool: True if successful
        """
        try:
            # Ensure minimum duration (very short clips can cause issues)
            duration = max(duration, 0.04)  # At least 1 frame at 24fps

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-t",
                str(duration),
                "-an",  # No audio (will add music later)
                "-c:v",
                "copy",  # Stream copy (fast, no re-encode needed)
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # Only log first error to avoid spam
                if not hasattr(self, "_trim_error_logged"):
                    print(f"   FFmpeg trim error: {result.stderr[:300]}")
                    self._trim_error_logged = True
            return result.returncode == 0
        except Exception as e:
            print(f"   FFmpeg trim exception: {e}")
            return False

    def _ffmpeg_concat(self, concat_file, output_path):
        """Concatenate clips using FFmpeg concat demuxer.

        Args:
            concat_file: Path to concat list file
            output_path: Output video path

        Returns:
            bool: True if successful
        """
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",  # Stream copy (fast, clips from same source are compatible)
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   FFmpeg concat error: {result.stderr[:500]}")
            return result.returncode == 0
        except Exception as e:
            print(f"   FFmpeg concat exception: {e}")
            return False

    def _ffmpeg_burn_subtitles(self, video_path, subtitle_path, output_path):
        """Burn subtitles into video using FFmpeg.

        Args:
            video_path: Input video path (with audio)
            subtitle_path: Path to SRT subtitle file
            output_path: Output video path

        Returns:
            bool: True if successful
        """
        try:
            # Escape path for FFmpeg subtitles filter (colons and backslashes)
            escaped_sub_path = (
                str(subtitle_path)
                .replace("\\", "\\\\")
                .replace(":", "\\:")
                .replace("'", "\\'")
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"subtitles='{escaped_sub_path}':force_style='FontSize=22,Alignment=2,BorderStyle=3,Outline=2'",
                "-c:a",
                "copy",
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   FFmpeg subtitle error: {result.stderr[:500]}")
            return result.returncode == 0
        except Exception as e:
            print(f"   FFmpeg subtitle exception: {e}")
            return False

    def _ffmpeg_add_audio(self, video_path, audio_path, output_path):
        """Add audio track to video using FFmpeg.

        Args:
            video_path: Input video path (no audio)
            audio_path: Audio file path
            output_path: Output video path

        Returns:
            bool: True if successful
        """
        try:
            # Get video duration to trim audio
            duration_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]
            duration_result = subprocess.run(
                duration_cmd, capture_output=True, text=True
            )
            video_duration = float(duration_result.stdout.strip())

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(audio_path),
                "-t",
                str(video_duration),  # Trim to video length
                "-map",
                "0:v",  # Video from first input
                "-map",
                "1:a",  # Audio from second input
                "-c:v",
                "copy",  # Copy video (no re-encode)
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",  # End when shortest stream ends
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
