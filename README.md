# Music Video Generator

An intelligent Music Video Generation & Archival Remix Engine that creates artistic video remixes by synchronizing archival film footage with music through AI-driven scene detection, audio analysis, and video manipulation.

## Features

- **Three-Phase Architecture**: Separate film and music preparation (one-time) from video generation (fast, repeatable)
- **Direct FFmpeg Integration**: All video operations (clip extraction, trimming, concatenation, audio) use FFmpeg directly
- **Intelligent Caching**:
  - Film clips extracted via FFmpeg with audio preserved
  - Music analysis (beats, BPM) cached and reused across multiple films
- **Four Scene Selection Strategies**:
  - **Progressive**: Evenly distributed chronological journey through the film
  - **Random**: Pure random selection with repetition for energetic cuts
  - **Forward-only**: Sequential progression, never backtracks
  - **No-repeat**: Random selection without repetition
- **Beat Synchronization**: Flexible beat-skip parameter (1=every beat, 2=every other beat, etc.)
- **Rich Metadata**: Comprehensive HTML reports with scene analysis, thumbnails, and playback
- **Production Ready**: Robust error handling, type-safe numpy conversions, extensive testing

## Installation

### Virtual Environment (Recommended)

It's recommended to install dependencies into an isolated Python virtual environment so they don't conflict with other projects or your system Python.

```bash
# Create a venv in the project root
python3 -m venv .venv

# Activate it
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (cmd.exe)
.venv\Scripts\activate.bat

# Upgrade pip inside the venv
pip install --upgrade pip
```

When the venv is active, your shell prompt will be prefixed with `(.venv)`. Run all subsequent `pip install` and `python` commands from inside the activated venv. To leave the venv later, run `deactivate`.

### Dependencies

```bash
pip install librosa scenedetect[opencv] numpy matplotlib opencv-python scipy
```

**FFmpeg is required** (used directly for clip extraction) and must be installed separately:
```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Verify Installation

```bash
python test_setup.py
```

## Quick Start

### 1. Prepare Film Library (One-Time Per Film)

Analyze a film and build a reusable scene library:

```bash
python music_video_generator.py --prepare --film movie.mp4
```

This creates a scene library at `clips_library/{film_name}/` containing:
- Scene detection metadata
- Individual scene clips **with audio preserved**
- Thumbnail images
- Scene analysis (color, brightness, pace)

**Optional parameters:**
- `--threshold 30.0` - Scene detection sensitivity (10-50, default: 30)
- `--min-scene-len 1.0` - Minimum scene duration in seconds

### 2. Prepare Music Library (One-Time Per Song)

Analyze a song and cache beat detection results:

```bash
python music_video_generator.py --prepare --song track.mp3
```

This creates a music library at `music_library/{song_name}/` containing:
- Beat detection data (beat times, BPM)
- Audio duration and sample rate
- Tempo confidence metrics

**You can also prepare both at once:**
```bash
python music_video_generator.py --prepare --film movie.mp4 --song track.mp3
```

### 3. Generate Music Video

Create a music video using the prepared libraries:

```bash
# Basic usage (progressive strategy, every beat)
# Uses cached film clips and music analysis automatically
python music_video_generator.py --film movie.mp4 --song track.mp3

# Fewer cuts (every 2nd beat)
python music_video_generator.py --film movie.mp4 --song track.mp3 --beat-skip 2

# Random strategy with every 4th beat
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy random --beat-skip 4

# Forward-only progression
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy forward_only
```

**Note:** The generator automatically:
- Trims clips to beat duration using FFmpeg
- Concatenates clips and adds music track via FFmpeg
- Uses cached music analysis if available (faster!)
- Creates timestamped output in `music_videos/` directory

**Strategy Details:**

| Strategy | Description | Best For |
|----------|-------------|----------|
| `progressive` | Evenly distributed journey through entire film | Narrative films, documentaries |
| `random` | Pure random selection with repetition | High-energy music, abstract visuals |
| `forward_only` | Sequential, never backtracks | Maintaining chronological flow |
| `no_repeat` | Random without repetition | Maximizing visual variety |

**Output:** `output/{film_name}_{song_name}_{timestamp}.mp4`

## Advanced Usage

### Custom Output Location

```bash
python music_video_generator.py --film movie.mp4 --song track.mp3 \
  --output my_remix.mp4
```

### Force Scene Re-analysis

```bash
python music_video_generator.py --prepare --film movie.mp4 --force
```

### Custom Cache Directory

```bash
python music_video_generator.py --film movie.mp4 --song track.mp3 \
  --clips-dir /path/to/clips_library
```

## Usage Examples

### Example 1: Create Your First Music Video

Complete workflow from start to finish:

```bash
# Step 1: Prepare a film (one-time, ~2 minutes for 10-min video)
python music_video_generator.py --prepare --film test-assets/movie.mp4

# Step 2: Generate music video (fast, ~1 minute for 3-min song)
python music_video_generator.py --film test-assets/movie.mp4 --song test-assets/song.m4a

# Output: output/movie_song_progressive_20260126_120000/final_output.mp4
```

**What you'll see:**
```
🎬 Detecting scenes in movie...
   Threshold: 30.0
   Min scene length: 1.0s
   Found 127 raw scenes
   ✓ Detected 89 scenes (filtered by min_scene_len)

🎵 Analyzing audio: song
   Duration: 180.5s
   BPM: 128.3
   Beats detected: 384

✓ Scene-beat ratio: 89 scenes / 384 beats = 0.23 (sufficient)

🎨 Selecting scenes using progressive strategy...
   ✓ Selected 384 scenes

🎬 Assembling music video...
   ✓ Generated: output/movie_song_progressive_20260126_120000/final_output.mp4
```

### Example 2: Archival Footage + Hip-Hop Beat

Fast-paced music video with random cuts:

```bash
# Prepare 1950s archival footage
python music_video_generator.py --prepare \
  --film films/1950s_archive.mp4 \
  --threshold 25.0 \
  --min-scene-len 0.5

# Generate with random strategy, every other beat
python music_video_generator.py \
  --film films/1950s_archive.mp4 \
  --song music/hiphop_track.mp3 \
  --strategy random \
  --beat-skip 2 \
  --output remixes/1950s_hiphop_remix.mp4
```

**Why these settings:**
- Lower threshold (25.0) detects more subtle scene changes in old footage
- Shorter min-scene-len (0.5s) allows rapid cuts
- Random strategy creates energetic, non-linear flow
- Every 2nd beat (beat-skip 2) prevents overwhelming rapid cuts

### Example 3: Documentary + Ambient Music

Smooth, contemplative progression:

```bash
# Prepare nature documentary
python music_video_generator.py --prepare \
  --film films/nature_doc.mp4 \
  --threshold 35.0 \
  --min-scene-len 2.0

# Generate with progressive strategy, every 4th beat
python music_video_generator.py \
  --film films/nature_doc.mp4 \
  --song music/ambient_track.mp3 \
  --strategy progressive \
  --beat-skip 4
```

**Why these settings:**
- Higher threshold (35.0) only detects major scene changes
- Longer min-scene-len (2.0s) creates smoother flow
- Progressive strategy maintains narrative chronology
- Every 4th beat allows scenes to breathe

### Example 4: Multiple Songs, Same Film

Reuse cached film analysis for different songs:

```bash
# Prepare film once
python music_video_generator.py --prepare --film films/classic_film.mp4

# Generate multiple variations
python music_video_generator.py --film films/classic_film.mp4 --song music/song1.mp3 --strategy progressive
python music_video_generator.py --film films/classic_film.mp4 --song music/song2.mp3 --strategy random
python music_video_generator.py --film films/classic_film.mp4 --song music/song3.mp3 --strategy forward_only --beat-skip 2
python music_video_generator.py --film films/classic_film.mp4 --song music/song4.mp3 --strategy no_repeat --beat-skip 3

# Each subsequent generation is fast (~1-2 minutes) since film is cached
```

### Example 5: Experimenting with Scene Detection

If you get too few or too many scenes:

```bash
# Too few scenes? Lower threshold and min-scene-len
python music_video_generator.py --prepare \
  --film movie.mp4 \
  --threshold 20.0 \
  --min-scene-len 0.5 \
  --force  # Force regeneration

# Too many scenes? Raise threshold and min-scene-len
python music_video_generator.py --prepare \
  --film movie.mp4 \
  --threshold 40.0 \
  --min-scene-len 2.0 \
  --force
```

### Example 6: Batch Processing

Process multiple films and songs:

```bash
#!/bin/bash
# prepare_all_films.sh

# Prepare all films in films/ directory
for film in films/*.mp4; do
    echo "Preparing $(basename $film)..."
    python music_video_generator.py --prepare --film "$film"
done

# Generate videos for each film+song combination
for film in films/*.mp4; do
    for song in music/*.mp3; do
        echo "Generating: $(basename $film) + $(basename $song)"
        python music_video_generator.py \
            --film "$film" \
            --song "$song" \
            --strategy progressive
    done
done
```

### Example 7: Python API Usage

Use the Music Video Generator in your Python scripts:

```python
from music_video_generator import FilmLibrary, MusicVideoGenerator

# Prepare film library
library = FilmLibrary(
    film_path="films/movie.mp4",
    threshold=30.0,
    min_scene_len=1.0,
    clips_library_dir="clips_library"
)

# Check if cached, otherwise process
if not library._check_cache():
    library.detect_scenes()
    library.extract_clips(library.scenes)
    library.generate_thumbnails(library.scenes)
    library.analyze_scenes(library.scenes)
    library.save_metadata()
else:
    library._load_from_cache()

# Generate music video
generator = MusicVideoGenerator(
    film_library=library,
    song_path="music/track.mp3",
    strategy="progressive",
    beat_skip=2
)

# Run the generation pipeline
generator.analyze_audio()
if generator.validate_scene_beat_ratio():
    generator.select_scenes()
    generator.generate()
```

### Strategy Comparison Examples

Same film, same song, different strategies:

```bash
# Progressive: Evenly distributed through film
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy progressive
# Result: Scene 1, 23, 45, 67, 89... (evenly spaced)

# Random: Pure chaos
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy random
# Result: Scene 12, 89, 12, 3, 67, 89, 45... (repetition allowed)

# Forward-only: One-way journey
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy forward_only
# Result: Scene 1, 2, 5, 8, 12, 15... (always increasing)

# No-repeat: Maximum variety
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy no_repeat
# Result: Scene 34, 12, 78, 5, 90, 23... (each scene used once)
```

### Tips for Best Results

**Scene Detection:**
- Start with default threshold (30.0) and adjust
- Very static content (interviews): threshold 20-25
- Dynamic content (action films): threshold 30-35
- Subtle transitions (art films): threshold 15-20

**Beat Skip:**
- High-energy tracks: beat-skip 1 (every beat)
- Medium tempo: beat-skip 2 (every other beat)
- Slow/ambient: beat-skip 3-4
- Experimental: beat-skip 1 with longer min-scene-len

**Strategy Selection:**
- Narrative coherence needed? → `progressive` or `forward_only`
- Abstract/experimental? → `random`
- Maximum visual variety? → `no_repeat`
- Building tension/climax? → `forward_only`

## Architecture

### Two-Phase Design

**Phase 1: Film Preparation** (slow, one-time per film)
- Scene detection with PySceneDetect
- Clip extraction
- Thumbnail generation
- Scene analysis (color, brightness, pace)
- Metadata persistence

**Phase 2: Video Generation** (fast, repeatable)
- Audio analysis with librosa (beat detection, tempo)
- Scene-beat ratio validation
- Strategy-based scene selection
- Video assembly and final rendering with FFmpeg (concat demuxer + audio attachment)

### Project Structure

```
music_video_project/
├── music_video_generator.py        # Main CLI entry point
├── music_video_generator/          # Core package
│   ├── film_library.py             # Film analysis & caching
│   └── music_video_generator.py    # Video generation
├── clips_library/                  # Cached film libraries
│   └── {film_name}/
│       ├── metadata.json           # Scene metadata
│       ├── clips/                  # Individual scene clips
│       └── thumbnails/             # Scene thumbnails
├── output/                         # Generated music videos
├── tests/                          # Comprehensive test suite
│   ├── unit/
│   ├── integration/
│   └── performance/
└── attic/                          # Legacy generators
```

## Testing

### Run All Tests

```bash
python run_tests.py
```

### Run Specific Test Categories

```bash
pytest tests/unit/                 # Unit tests only
pytest tests/integration/          # Integration tests
pytest tests/performance/          # Performance benchmarks
```

### Generate Test Assets

If test assets are missing or need regeneration:

```bash
# Generate 3-minute audio with varying BPM (120→60→90)
python tests/utils/create_test_audio.py

# Generate 10-minute video with 300+ color transitions
python tests/utils/create_test_video.py
```

### Run with Coverage

```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html to view coverage report
```

## Legacy Generators

Previous generator implementations have been moved to `attic/` and are kept for reference:

- `ultraRobustArchivalTool.py` - Original production tool
- `premiere_style_archival_engine.py` - Premiere-style interface
- `progressive_sampling_generator.py` - Chronological sampling
- `robust_music_video_generator.py` - Numpy-safe implementation
- `forward_only_generator.py` - Forward-only progression
- And many more experimental versions

**Use the new `music_video_generator.py` for all new projects.**

## Technical Details

### Scene Detection

Uses PySceneDetect's ContentDetector:
- **Threshold**: 10-50 (default: 30)
  - Lower = more sensitive (more scenes)
  - Higher = less sensitive (fewer scenes)
- **Min Scene Length**: Filters out very short scenes

### Audio Analysis

Uses librosa for:
- Beat detection with `librosa.beat.beat_track()`
- Tempo estimation
- Onset strength analysis

### Type Safety

All generators use `safe_float()` and `safe_int()` helpers to handle numpy type conversions safely, preventing JSON serialization errors.

### Video Processing

- Clip extraction: FFmpeg via subprocess (audio preserved)
- Thumbnails & frame analysis: OpenCV
- Probing (duration, audio streams): ffprobe
- Clip trimming, concatenation, and final render: FFmpeg (concat demuxer + audio attachment)

## Troubleshooting

### Scene Detection Memory Issues

**Symptom**: Out of memory with long videos
**Solution**: Increase `--min-scene-len` parameter to reduce scene count

### Librosa Loading Failures

**Symptom**: `audioread` or `soundfile` errors
**Solution**: Ensure FFmpeg is properly installed and in PATH

### No Scenes Detected

**Symptom**: "No scenes detected" error
**Solution**: Lower the `--threshold` parameter (try 20.0 or 15.0)

## Performance

- **Audio analysis**: < 10 seconds for 3-minute track
- **Scene detection**: < 60 seconds for 10-minute video
- **Video generation**: ~1-2 minutes for 3-minute music video (after film prepared)

## Contributing

### Development Setup

```bash
# Install dev dependencies
pip install pytest pytest-cov pre-commit

# Install pre-commit hooks
pre-commit install
```

### Pre-commit Checks

Automatically runs before each commit:
- Black formatting
- Flake8 linting
- Bandit security scan
- Numpy safety validation
- Unit tests

### Adding New Features

1. Write tests first (TDD approach)
2. Implement feature
3. Run test suite: `python run_tests.py`
4. Verify numpy safety: `python scripts/check_numpy_safety.py`
5. Update documentation

## License

[Add your license here]

## Credits

Built with:
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) - Scene detection
- [librosa](https://librosa.org/) - Audio analysis
- [OpenCV](https://opencv.org/) - Frame extraction and thumbnails
- [FFmpeg](https://ffmpeg.org/) - Clip extraction, assembly, and encoding
