# Music Video Generator Refactor Design

**Date:** 2026-01-25
**Status:** Approved for Implementation

## Overview

Refactor the existing archival remix tools into a unified Music Video Generator with two-phase architecture: reusable film clip library preparation and fast music video generation with multiple strategies.

## Goals

1. **Optimize workflow**: Run expensive scene detection once per film, generate multiple music videos quickly
2. **Intelligent caching**: Store clips with parameter tracking, regenerate only when needed
3. **Enhanced tracking**: Include command reproduction, music analysis, and system info in reports
4. **Clean architecture**: Two focused classes instead of multiple scattered generators
5. **Preserve stability**: Keep working v20 patterns (FFmpeg rendering, numpy safety, memory management)

## Architecture

### Two-Phase Design

**Phase 1: Film Preparation (`FilmLibrary` class)**
- Scene detection with PySceneDetect
- Clip extraction to `clips_library/{film_name}/clips/`
- Thumbnail generation
- Scene analysis (color, brightness, pace)
- Metadata storage with detection parameters

**Phase 2: Music Video Generation (`MusicVideoGenerator` class)**
- Audio analysis (beats, tempo, BPM)
- Scene selection via configurable strategy
- Video composition from cached clips
- HTML report with comprehensive metadata
- FFmpeg rendering

### Directory Structure

```
clips_library/
  {film_name}/
    clips/
      scene_000.mp4
      scene_001.mp4
      ...
    thumbnails/
      thumb_000.jpg
      thumb_001.jpg
      ...
    metadata.json

music_videos/
  {film_name}_{song_name}_{strategy}_{timestamp}/
    output.mp4
    report.html
    generation_metadata.json
```

## Data Models

### FilmLibrary Metadata

```json
{
  "film_path": "/path/to/movie.mp4",
  "film_name": "movie",
  "created_at": "2026-01-25T10:30:00",
  "scene_detection_params": {
    "threshold": 30.0,
    "min_scene_len": 1.0
  },
  "film_properties": {
    "duration": 7200.5,
    "resolution": "1920x1080",
    "fps": 24.0,
    "codec": "h264"
  },
  "scenes": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "duration": 5.2,
      "clip_path": "clips/scene_000.mp4",
      "thumbnail_path": "thumbnails/thumb_000.jpg",
      "avg_color_rgb": [120, 85, 45],
      "avg_color_hex": "#78552d",
      "avg_brightness": 95.3,
      "pace": "medium"
    }
  ],
  "total_scenes": 342
}
```

### Generation Metadata

```json
{
  "generated_at": "2026-01-25T14:45:30",
  "command": "python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy progressive --beat-skip 2",
  "parameters": {
    "film_library": "clips_library/movie/",
    "song_path": "/path/to/track.mp3",
    "song_name": "track",
    "strategy": "progressive",
    "beat_skip": 2,
    "output_path": "music_videos/movie_track_progressive_20260125_144530/output.mp4"
  },
  "music_analysis": {
    "duration": 180.5,
    "bpm": 128.0,
    "beats_detected": 384,
    "tempo_confidence": 0.92,
    "sample_rate": 22050
  },
  "scene_selection": {
    "total_scenes_available": 342,
    "scenes_used": 156,
    "strategy_details": "Progressive sampling: chronological journey through film"
  },
  "system_info": {
    "python_version": "3.11.5",
    "libraries": {
      "librosa": "0.10.1",
      "moviepy": "1.0.3",
      "scenedetect": "0.6.2",
      "opencv": "4.8.0"
    },
    "processing_time": 12.4,
    "machine": "Darwin-24.6.0-x86_64"
  }
}
```

## Core Components

### FilmLibrary Class

**Responsibilities:**
- Scene detection and clip extraction
- Cache management with parameter tracking
- Metadata persistence

**Key Methods:**
```python
class FilmLibrary:
    def __init__(self, film_path, threshold=30.0, min_scene_len=1.0,
                 force_regenerate=False, clips_library_dir="clips_library")

    def _check_cache(self) -> bool
        # Check if valid cached clips exist with matching parameters

    def _load_from_cache(self) -> bool
        # Load scenes and metadata from existing cache

    def detect_scenes(self) -> List[dict]
        # Run PySceneDetect scene detection

    def extract_clips(self, scenes) -> int
        # Extract individual scene clips (progress every 20 clips)

    def generate_thumbnails(self, scenes) -> None
        # Generate thumbnail images for each scene

    def analyze_scenes(self, scenes) -> List[dict]
        # Add color, brightness, pace analysis

    def save_metadata(self) -> None
        # Save metadata.json to clips_library/{film_name}/

    def get_scenes(self) -> List[dict]
        # Return list of available scenes with metadata
```

**Cache Invalidation Logic:**
1. Check if `clips_library/{film_name}/metadata.json` exists
2. If exists, compare `scene_detection_params` in metadata vs requested params
3. If params match: load from cache (log "Using cached clips")
4. If params differ: regenerate (log "Parameters changed, regenerating")
5. If `--force-regenerate-clips` flag: always regenerate

### MusicVideoGenerator Class

**Responsibilities:**
- Audio analysis and beat detection
- Scene selection strategy application
- Video composition and rendering
- Report generation

**Key Methods:**
```python
class MusicVideoGenerator:
    def __init__(self, film_library, song_path, strategy='progressive',
                 beat_skip=1, output_dir="music_videos")

    def analyze_audio(self) -> dict
        # Librosa beat detection, tempo analysis
        # Returns: {duration, bpm, beats, tempo_confidence, sample_rate}

    def validate_scene_beat_ratio(self) -> bool
        # Check if enough scenes for beats, warn/suggest alternatives

    def select_scenes(self) -> List[dict]
        # Apply strategy to map scenes to beats

    def _select_progressive(self, scenes, beat_times) -> List[dict]
        # Evenly distributed chronological sampling
        # Formula: scene_index = int((beat_index / total_beats) * len(scenes))

    def _select_random(self, scenes, beat_times) -> List[dict]
        # Pure random selection, allows repetition

    def _select_forward_only(self, scenes, beat_times) -> List[dict]
        # Sequential progression, no backtracking

    def _select_no_repeat(self, scenes, beat_times) -> List[dict]
        # Random selection from unused pool

    def generate_video_clips(self, scene_mapping) -> List[VideoClip]
        # Create video clips from cached scene files

    def render_final_video(self, video_clips) -> bool
        # Concatenate clips and render with FFmpeg

    def generate_html_report(self) -> None
        # Create comprehensive HTML report

    def save_generation_metadata(self) -> None
        # Save generation_metadata.json

    def generate(self) -> bool
        # Main orchestration method - runs full pipeline
```

## Scene Selection Strategies

### Strategy Comparison

**Progressive** (`_select_progressive`)
- Evenly distributed chronological sampling
- Maps beats to specific positions: beat 1 → 0%, beat 50 → 50%, beat 100 → 100%
- Guarantees content from beginning, middle, and end
- Use case: Maintain narrative flow, journey through entire film

**Forward Only** (`_select_forward_only`)
- Sequential progression without backtracking
- Tracks current scene index, always picks next available
- No repetition, but distribution depends on scene durations
- Use case: Never repeat, maintain forward momentum

**Random** (`_select_random`)
- Pure random selection, can repeat scenes
- High-energy, non-linear cuts
- Use case: Energetic videos without chronology

**No Repeat** (`_select_no_repeat`)
- Random selection from unused pool
- Falls back to forward-only if pool exhausted
- Use case: Random feel without repetition

## Parameters

### Film Preparation Parameters

- `film_path` (required): Path to source video file
- `threshold` (default: 30.0): Scene detection sensitivity (10-50 range, lower = more scenes)
- `min_scene_len` (default: 1.0): Minimum scene duration in seconds
- `force_regenerate_clips` (flag): Regenerate even if cache exists

### Music Video Generation Parameters

- `film_library`: FilmLibrary instance with cached clips
- `song_path` (required): Path to audio file
- `strategy` (default: 'progressive'): Scene selection strategy
- `beat_skip` (default: 1): Use every Nth beat
  - 1 = every beat (default, most cuts)
  - 2 = every other beat (half as many cuts)
  - 4 = every 4th beat (quarter as many cuts, longer scenes)
  - Higher values = fewer cuts, useful for fast songs
- `output_path` (optional): Custom output location

### CLI Examples

```bash
# Prepare film library (one-time operation)
python music_video_generator.py --prepare --film movie.mp4 --threshold 30.0

# Generate with every beat (default)
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy progressive

# Use every 2nd beat (half as many cuts)
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy progressive --beat-skip 2

# Use every 4th beat (quarter as many cuts, longer scenes)
python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy random --beat-skip 4

# Force regenerate clips with different threshold
python music_video_generator.py --prepare --film movie.mp4 --threshold 20.0 --force-regenerate-clips
```

### Python API Examples

```python
# Prepare library
library = FilmLibrary('movie.mp4', threshold=30.0)

# Generate with every beat
gen = MusicVideoGenerator(library, 'track.mp3', strategy='progressive', beat_skip=1)
gen.generate()

# Generate with every 4th beat
gen = MusicVideoGenerator(library, 'track.mp3', strategy='random', beat_skip=4)
gen.generate()
```

## Error Handling & Validation

### FilmLibrary Validation

- Verify film file exists and is readable
- Validate supported video format (mp4, mov, avi, mkv)
- Check FFmpeg availability in system PATH
- Warn if film duration > 3 hours (long processing time)
- Validate threshold range (10.0 - 50.0 recommended)
- Check available disk space (estimate: ~1MB per scene clip)
- Validate scene count is reasonable (warn if < 10 or > 5000)
- Progress reporting every 20 scenes during clip extraction

### MusicVideoGenerator Validation

- Verify FilmLibrary has valid cached clips
- Verify song file exists and is readable
- Check song duration vs available scenes

**Clips-to-Beats Validation:**
```python
if len(scenes) < len(beat_times):
    ratio = len(beat_times) / len(scenes)
    suggested_skip = int(np.ceil(ratio))
    print(f"⚠️  WARNING: Insufficient clips for beat count")
    print(f"   Scenes available: {len(scenes)}")
    print(f"   Beats detected: {len(beat_times)}")
    print(f"   Ratio: {ratio:.1f} beats per scene")
    print(f"\n   SUGGESTIONS:")
    print(f"   1. Use --beat-skip {suggested_skip} (1 clip per {suggested_skip} beats)")
    print(f"   2. Use 'random' or 'no-repeat' strategy (allows scene reuse)")
    print(f"   3. Lower scene detection --threshold to detect more scenes")

    user_input = input("\n   Continue anyway? (y/N): ")
    if user_input.lower() != 'y':
        sys.exit(1)
```

### Audio Analysis Validation

- Handle librosa loading failures (corrupt files, unsupported formats)
- Validate detected BPM is reasonable (40-200 BPM)
- Warn if very few beats detected (< 20 beats)
- Fallback to default tempo (120 BPM) if beat detection fails

### Video Generation Validation

- Validate scene bounds before clip extraction
- Handle MoviePy subclip failures (continue with warnings)
- Track failed clip count, warn if > 10% fail
- Memory monitoring with gc.collect() after every 100 clips
- Progress reporting every 50 beats

### Graceful Degradation

- If clip export fails during FilmLibrary creation, still save metadata
- If some scenes can't be extracted, continue with available scenes
- If audio analysis fails, allow video-only generation

## Technical Implementation Details

### Critical Patterns from v20

**1. FFmpeg Direct Rendering**
```python
def render_with_ffmpeg_directly(self, video_path, audio_path, output_path):
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_path),
        '-i', str(audio_path),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        '-loglevel', 'error',
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```

**Workflow:** Write video-only with MoviePy → Combine with audio via FFmpeg subprocess

**2. Numpy Type Safety**
```python
def safe_float(self, value):
    try:
        return float(value)
    except:
        return 0.0

def safe_int(self, value):
    try:
        return int(value)
    except:
        return 0
```

Use for all conversions from librosa/PySceneDetect to prevent JSON serialization errors.

**3. Memory Management**
- Close VideoFileClip objects immediately after use
- Explicit `gc.collect()` after processing batches
- Limit clip export to 2000 clips max
- Use `audio=False` when loading source video for clip generation

**4. Scene Clip Export Settings**
```python
clip.write_videofile(
    str(clip_path),
    codec='libx264',
    audio=False,
    verbose=False,
    logger=None,
    preset='fast',
    threads=2,
    fps=15,  # Lower FPS for web playback efficiency
    write_logfile=False
)
```

**5. HTML Report Structure**

Keep v20's interactive features:
- Thumbnail hover previews
- Clickable video playback
- Plotly timeline and brightness charts
- Scene pacing distribution
- Custom tooltips with scene metadata

Add new sections:
- Command reproduction (copyable code block)
- Parameters table (all settings)
- Music analysis (BPM, duration, beat count, waveform)
- System info (versions, processing time, machine specs)

**6. Progress Reporting**
- Scene detection: Report every 20 scenes
- Clip generation: Report every 50 beats
- Use v20's formatted box headers for visual clarity

## HTML Report Enhancements

### New Sections to Add

**1. Command Section**
```html
<div class="command-section">
    <h3>Reproduction Command</h3>
    <pre><code>python music_video_generator.py --film movie.mp4 --song track.mp3 --strategy progressive --beat-skip 2</code></pre>
    <button onclick="copyCommand()">Copy Command</button>
</div>
```

**2. Parameters Table**
```html
<div class="parameters-section">
    <h3>Generation Parameters</h3>
    <table>
        <tr><th>Parameter</th><th>Value</th></tr>
        <tr><td>Film Library</td><td>clips_library/movie/</td></tr>
        <tr><td>Song</td><td>track.mp3</td></tr>
        <tr><td>Strategy</td><td>progressive</td></tr>
        <tr><td>Beat Skip</td><td>2 (every 2nd beat)</td></tr>
        <tr><td>Threshold</td><td>30.0</td></tr>
    </table>
</div>
```

**3. Music Analysis Section**
```html
<div class="music-analysis-section">
    <h3>Music Analysis</h3>
    <div class="music-stats">
        <div class="stat-card">
            <div class="stat-value">128.0 BPM</div>
            <div class="stat-label">Tempo</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">3:00</div>
            <div class="stat-label">Duration</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">384</div>
            <div class="stat-label">Beats Detected</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">192</div>
            <div class="stat-label">Beats Used (skip=2)</div>
        </div>
    </div>
</div>
```

**4. System Info Section**
```html
<div class="system-info-section">
    <h3>System Information</h3>
    <table>
        <tr><td>Python Version</td><td>3.11.5</td></tr>
        <tr><td>Librosa</td><td>0.10.1</td></tr>
        <tr><td>MoviePy</td><td>1.0.3</td></tr>
        <tr><td>PySceneDetect</td><td>0.6.2</td></tr>
        <tr><td>Processing Time</td><td>12.4 seconds</td></tr>
        <tr><td>Machine</td><td>Darwin-24.6.0-x86_64</td></tr>
    </table>
</div>
```

## Execution Workflow

### Film Preparation Workflow
```
FilmLibrary.__init__()
  ↓
_check_cache()
  ↓
If cache valid → _load_from_cache() → Done
  ↓
If cache invalid or force_regenerate:
  ↓
detect_scenes()
  ↓
extract_clips() [Progress every 20 clips]
  ↓
generate_thumbnails()
  ↓
analyze_scenes()
  ↓
save_metadata()
```

### Music Video Generation Workflow
```
MusicVideoGenerator.__init__()
  ↓
analyze_audio()
  ↓
validate_scene_beat_ratio() [Warn if insufficient clips]
  ↓
select_scenes() [Apply strategy]
  ↓
generate_video_clips() [Load cached clips, adjust to beat duration]
  ↓
render_final_video() [Concatenate, FFmpeg rendering]
  ↓
generate_html_report() [Enhanced v20 report + new sections]
  ↓
save_generation_metadata()
```

## Migration Strategy

### Move Existing Generators to Attic

After new Music Video Generator is implemented and tested:

```bash
# Move all old generators to attic/
mv robust_music_video_generator.py attic/
mv progressive_sampling_generator.py attic/
mv forward_only_generator.py attic/
mv perfect_forward_generator.py attic/
mv no_repeat_generator.py attic/
mv robust_clip_generator.py attic/
mv full_song_generator.py attic/
mv ultraRobustArchivalTool.py attic/
mv premiere_style_archival_engine.py attic/
```

### Update Documentation

- Update CLAUDE.md to reference new Music Video Generator
- Mark old generators as deprecated in README.md
- Add migration guide for users of old tools

## Success Criteria

1. **Performance**: Scene detection runs once, subsequent mixes generate in < 30 seconds
2. **Usability**: Clear CLI interface, helpful error messages, progress reporting
3. **Reproducibility**: HTML reports include all info needed to recreate exact output
4. **Stability**: No regressions from v20 stability (FFmpeg rendering, memory management)
5. **Flexibility**: Easy to experiment with different songs, strategies, beat-skip values
6. **Code Quality**: Clean two-phase architecture, well-tested, follows v20 patterns

## Implementation Notes

- Base implementation on v20 (`ultraRobustArchivalToolv20.py`)
- Preserve all working patterns: FFmpeg rendering, numpy safety, memory management
- Keep v20's HTML interactive features (hover, click, charts)
- Add comprehensive validation and error messages
- Use argparse for CLI with clear help text
- Write unit tests for validation logic and scene selection strategies
- Integration test: full workflow with test assets
