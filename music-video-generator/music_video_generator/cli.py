#!/usr/bin/env python3
"""Command-line interface for Music Video Generator."""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from .film_library import FilmLibrary
from .music_library import MusicLibrary
from .music_video_generator import MusicVideoGenerator


def download_song_from_url(url, music_library_dir="music_library"):
    """Download audio (WAV) and English auto-captions (SRT) from a YouTube URL using yt-dlp.

    Args:
        url: YouTube URL
        music_library_dir: Base directory for music library storage

    Returns:
        tuple: (audio_path, subtitle_path_or_None, song_name)

    Raises:
        RuntimeError: If yt-dlp is not installed or download fails
    """
    # Get video metadata to derive song name
    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "%(title)s", "--no-download", url],
            capture_output=True,
            text=True,
            check=True,
        )
        title = result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError(
            "yt-dlp is not installed. Install it with: pip install yt-dlp"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to fetch video metadata: {e.stderr}")

    # Sanitize title for filesystem
    song_name = re.sub(r"[^\w\s-]", "", title).strip()
    song_name = re.sub(r"[\s]+", "-", song_name).lower()
    if not song_name:
        song_name = "downloaded-song"

    song_dir = Path(music_library_dir) / song_name
    song_dir.mkdir(parents=True, exist_ok=True)

    # Check for cached audio (any format)
    existing_audio = glob.glob(str(song_dir / "song.*"))
    if existing_audio:
        audio_path = existing_audio[0]
        print(f"📦 Using cached audio: {audio_path}")
    else:
        print(f"⬇️  Downloading audio...")
        output_template = str(song_dir / "song.%(ext)s")
        try:
            subprocess.run(
                ["yt-dlp", "-f", "bestaudio", "-o", output_template, url],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Audio download failed: {e.stderr}")

        downloaded = glob.glob(str(song_dir / "song.*"))
        if not downloaded:
            raise RuntimeError("Audio download produced no output file")
        audio_path = downloaded[0]
        print(f"   ✓ Downloaded: {audio_path}")

    # Download English auto-captions
    subtitle_path = None
    srt_path = str(song_dir / "subtitles.srt")
    if os.path.exists(srt_path):
        subtitle_path = srt_path
        print(f"📦 Using cached subtitles: {subtitle_path}")
    else:
        print(f"⬇️  Downloading English auto-captions...")
        try:
            subprocess.run(
                [
                    "yt-dlp",
                    "--write-auto-sub",
                    "--sub-lang",
                    "en",
                    "--skip-download",
                    "-o",
                    str(song_dir / "subtitles"),
                    url,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            pass  # Subtitles may not be available

        # Find downloaded subtitle file (any format: .srt, .vtt, etc.)
        found_subs = glob.glob(str(song_dir / "subtitles*.*"))
        # Exclude metadata files (macOS ._* files)
        found_subs = [s for s in found_subs if not os.path.basename(s).startswith("._")]
        if found_subs:
            raw_sub = found_subs[0]
            # Convert to SRT using FFmpeg if not already SRT
            if not raw_sub.endswith(".srt"):
                print(f"   Converting {Path(raw_sub).suffix} to SRT...")
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", raw_sub, srt_path],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    os.remove(raw_sub)
                    subtitle_path = srt_path
                except subprocess.CalledProcessError:
                    print(f"   ⚠ Subtitle conversion failed, using raw file")
                    subtitle_path = raw_sub
            else:
                subtitle_path = raw_sub
            print(f"   ✓ Subtitles ready: {subtitle_path}")
        else:
            print(f"   ⚠ No English subtitles available for this video")

    return str(audio_path), subtitle_path, song_name


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
        """,
    )

    # Operation mode
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Prepare libraries only (no music video generation)",
    )

    # Required arguments
    parser.add_argument("--film", type=str, help="Path to film/video file")
    parser.add_argument("--song", type=str, help="Path to song/audio file")
    parser.add_argument(
        "--song-url",
        type=str,
        help="YouTube URL to download audio + subtitles from (mutually exclusive with --song)",
    )
    parser.add_argument(
        "--no-subtitles",
        action="store_true",
        help="Disable automatic subtitle burn-in when using --song-url",
    )

    # Scene detection parameters
    parser.add_argument(
        "--threshold",
        type=float,
        default=30.0,
        help="Scene detection threshold (10-50 range, default: 30.0). Lower = more sensitive.",
    )
    parser.add_argument(
        "--min-scene-len",
        type=float,
        default=1.0,
        help="Minimum scene duration in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--detector",
        type=str,
        default="content",
        choices=["content", "adaptive", "both"],
        help="Scene detector type (default: content). Use adaptive for varying lighting, both for combined detection.",
    )
    parser.add_argument(
        "--luma-only",
        action="store_true",
        help="Use only luminance for detection (ContentDetector only). Better for dark scenes.",
    )
    parser.add_argument(
        "--force-regenerate-clips",
        action="store_true",
        help="Force regeneration of film clips even if cache exists",
    )
    parser.add_argument(
        "--force-regenerate-music",
        action="store_true",
        help="Force regeneration of music analysis even if cache exists",
    )

    # Music video generation parameters
    parser.add_argument(
        "--strategy",
        type=str,
        default="progressive",
        choices=["progressive", "random", "forward_only", "no_repeat"],
        help="Scene selection strategy (default: progressive)",
    )
    parser.add_argument(
        "--beat-skip",
        type=int,
        default=1,
        help="Use every Nth beat (1=all beats, 2=every other, etc. Default: 1)",
    )

    # Output directories
    parser.add_argument(
        "--clips-library-dir",
        type=str,
        default="clips_library",
        help="Directory for film clip library (default: clips_library)",
    )
    parser.add_argument(
        "--music-library-dir",
        type=str,
        default="music_library",
        help="Directory for music analysis library (default: music_library)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="music_videos",
        help="Directory for music video outputs (default: music_videos)",
    )

    args = parser.parse_args()

    # Validate --song and --song-url mutual exclusivity
    if args.song and args.song_url:
        parser.error("--song and --song-url are mutually exclusive")

    # Handle --song-url: download audio + subtitles
    subtitle_path = None
    url_song_name = None
    if args.song_url:
        try:
            audio_path, subtitle_path, url_song_name = download_song_from_url(
                args.song_url, args.music_library_dir
            )
            args.song = audio_path
        except RuntimeError as e:
            parser.error(str(e))

    # Validate arguments
    if not args.prepare:
        # For generation mode, both --film and --song are required
        if not args.film:
            parser.error("--film is required for music video generation")
        if not args.song:
            parser.error(
                "--song is required for music video generation (use --song or --song-url)"
            )
    else:
        # For preparation mode, at least one of --film or --song is required
        if not args.film and not args.song:
            parser.error("--prepare requires at least --film, --song, or --song-url")

    # Print header
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         MUSIC VIDEO GENERATOR v2.0                           ║
    ╠══════════════════════════════════════════════════════════════╣
    """)

    try:
        library = None
        music_lib = None

        # Step 1: Prepare FilmLibrary (if --film provided)
        if args.film:
            print(f"    ║  Film: {Path(args.film).name:<53} ║")
            print(f"    ║  Detector: {args.detector:<49} ║")
            print(f"    ║  Threshold: {args.threshold:<48} ║")
            if args.luma_only:
                print(f"    ║  Luma only: True{'':<43} ║")
            if args.song:
                print(f"    ║  Song: {Path(args.song).name:<53} ║")
            print(
                "    ╚══════════════════════════════════════════════════════════════╝\n"
            )

            library = FilmLibrary(
                args.film,
                threshold=args.threshold,
                min_scene_len=args.min_scene_len,
                force_regenerate=args.force_regenerate_clips,
                clips_library_dir=args.clips_library_dir,
                detector=args.detector,
                luma_only=args.luma_only,
            )

            # Check cache or generate
            if args.force_regenerate_clips:
                # Force regenerate
                print("🎬 Generating film library (forced)...")
                needs_generate = True
            elif not args.prepare and library._load_metadata():
                # When not in prepare mode, use existing cache regardless of parameters
                cached_params = library.metadata.get("scene_detection_params", {})
                print(
                    f"📦 Using cached film clips (detected with: {cached_params.get('detector', 'content')}, threshold={cached_params.get('threshold', 30.0)})"
                )
                library.scenes = library.metadata.get("scenes", [])
                needs_generate = False
            elif library._check_cache():
                # Prepare mode with matching parameters
                print("📦 Using cached film clips")
                library._load_from_cache()
                needs_generate = False
            else:
                print("🎬 Generating film library...")
                needs_generate = True

            if needs_generate:

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

            # If --prepare only with film, show results
            if args.prepare and not args.song:
                print("\n✓ Film library preparation complete")
                print(f"   Location: {library.library_dir}")
                print(f"   Scenes: {len(library.get_scenes())}")
                return 0

        # Step 2: Prepare MusicLibrary (if --song provided)
        if args.song:
            if not args.film:
                print(f"    ║  Song: {Path(args.song).name:<53} ║")
                print(
                    "    ╚══════════════════════════════════════════════════════════════╝\n"
                )

            music_lib = MusicLibrary(
                args.song,
                force_regenerate=args.force_regenerate_music,
                music_library_dir=args.music_library_dir,
                song_name=url_song_name,
            )

            # Check cache or generate
            if music_lib._check_cache() and not args.force_regenerate_music:
                print("📦 Using cached music analysis")
                music_lib._load_from_cache()
            else:
                print("🎵 Generating music library...")

                # Analyze audio
                analysis = music_lib.analyze_audio()
                if not analysis["beats"]:
                    print("✗ Audio analysis failed")
                    return 1

                # Save metadata
                music_lib.save_metadata(analysis, subtitle_path=subtitle_path)

            # If --prepare only, stop here
            if args.prepare:
                print("\n✓ Music library preparation complete")
                print(f"   Location: {music_lib.library_dir}")
                print(f"   Beats: {len(music_lib.beat_times)}")
                if library:
                    print("\n✓ Film library preparation complete")
                    print(f"   Location: {library.library_dir}")
                    print(f"   Scenes: {len(library.get_scenes())}")
                return 0

        # Step 3: Generate Music Video
        print(f"\n🎵 Generating music video...")
        print(f"   Song: {Path(args.song).name}")
        print(f"   Strategy: {args.strategy}")
        print(f"   Beat skip: {args.beat_skip}")

        generator = MusicVideoGenerator(
            library,
            args.song,
            strategy=args.strategy,
            beat_skip=args.beat_skip,
            output_dir=args.output_dir,
            music_library=music_lib,
            subtitle_path=subtitle_path if not args.no_subtitles else None,
        )

        # Analyze audio
        music_analysis = generator.analyze_audio()
        if not music_analysis["beats"]:
            print("✗ Audio analysis failed")
            return 1

        # Validate scene-beat ratio
        generator.validate_scene_beat_ratio()

        # Select scenes
        selected = generator.select_scenes()
        if not selected:
            print("✗ Scene selection failed")
            return 1

        # Assemble final video
        output_path = generator.assemble_video()
        if not output_path:
            print("✗ Video assembly failed")
            return 1

        print(f"\n✓ Music video generation complete!")
        print(f"   Output: {output_path}")

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


if __name__ == "__main__":
    sys.exit(main())
