# Technical Context: Music Video Generator v2.1

## v2.1 Architecture Overview

### Three-Phase Design
The system is architected around three distinct phases that optimize for efficiency, flexibility, and audio handling:

**Phase 1: Film Preparation (FilmLibrary)**
- One-time analysis per film per parameter set
- Scene detection via PySceneDetect
- Clip extraction via **FFmpeg directly** (bypasses MoviePy's subprocess/logger issues)
- Clips saved **with audio preserved** (AAC codec at 128kbps)
- Results cached to disk with parameter-based validation
- Approximately 60 seconds for 10-minute video

**Phase 2: Music Preparation (MusicLibrary)**
- One-time analysis per song
- Beat detection and tempo analysis via librosa
- Beat times, BPM, duration cached to JSON
- Results reusable across multiple film combinations
- Approximately 5-10 seconds for 3-minute audio

**Phase 3: Video Generation (MusicVideoGenerator)**
- Fast, repeatable video creation from both caches
- Loads film clips **without audio** (audio=False)
- Attaches music track in final assembly
- Strategy-based scene selection
- Approximately 1-2 minutes for 3-minute music video

### Core Components

```
music_video_project/
├── music_video_generator.py           # CLI entry point
├── music_video_generator/             # Core package
│   ├── __init__.py                    # Package exports
│   ├── film_library.py                # Phase 1: Film analysis & caching (with audio)
│   ├── music_library.py               # Phase 2: Music analysis & caching
│   ├── music_video_generator.py       # Phase 3: Video generation (no audio)
│   └── cli.py                         # Command-line interface logic
├── clips_library/                     # Cached film libraries
│   └── {film_name}/
│       ├── clips/                     # Scene clips WITH audio
│       ├── thumbnails/                # Scene thumbnails
│       └── metadata.json              # Scene analysis data
├── music_library/                     # Cached music analysis
│   └── {song_name}/
│       └── metadata.json              # Beat detection, BPM, tempo
├── music_videos/                      # Generated music videos
├── tests/                             # Comprehensive test suite
├── attic/                             # Legacy generators (archived)
└── docs/                              # Documentation and plans
```

## Technologies Used

### Core Libraries

**librosa (Audio Analysis)**
- Beat detection and tempo estimation
- Returns numpy arrays (important for type handling)
- Sample rate: 22050 Hz (default)

**FFmpeg (All Video Operations)**
- **Clip Extraction**: `ffmpeg -ss {start} -i {input} -t {duration} -c:v libx264 -c:a aac {output}`
- **Clip Trimming**: Trims clips to beat duration during assembly
- **Video Concatenation**: Uses concat demuxer with stream copy (fast)
- **Audio Attachment**: Adds music track to final video
- ffprobe used for video duration and audio stream detection
- Completely bypasses MoviePy's problematic logger/subprocess handling

**OpenCV (Thumbnails & Frame Analysis)**
- Used for thumbnail generation and per-scene frame analysis (color, brightness, etc.)
- Reads frames via `cv2.VideoCapture` — no audio decoding involved
- Not used for any video encoding/writing operations (FFmpeg handles all writes)

**PySceneDetect (Scene Detection)**
- ContentDetector with configurable threshold (10-50 range)
- Scene boundary detection based on visual content changes

**NumPy (Numerical Computing)**
- Type safety critical: librosa returns numpy arrays not scalars
- Requires safe_float() and safe_int() conversion throughout

**FFmpeg (External Dependency)**
- Direct FFmpeg rendering for final output
- Must be in system PATH
- Critical for all video operations

## Known Technical Issues

### Resolved Issues
1. Numpy Type Errors - Fixed with safe_float/safe_int methods
2. librosa Tempo Array Format - Fixed in commit 40f5e8d
3. Code Duplication - Eliminated through v2.0 refactor
4. MoviePy Logger Issues - Bypassed by using FFmpeg directly for clip extraction
5. Audio Export Failures - Resolved by switching from MoviePy to FFmpeg

### Current Limitations
1. FFmpeg Dependency - External system dependency required (both ffmpeg and ffprobe)
2. Memory for Large Videos - Videos over 1 hour can exhaust RAM
3. Beat Detection Genre Bias - Works best with clear rhythmic patterns
