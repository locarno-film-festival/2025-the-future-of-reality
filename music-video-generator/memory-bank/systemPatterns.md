# System Patterns: Music Video Generation & Archival Remix Engine

## System Architecture

### Core Processing Pipeline
```
Input Files (Video + Audio)
    ↓
Parallel Analysis
    ├── Scene Detection (PySceneDetect)
    └── Audio Analysis (librosa)
    ↓
Synchronization Engine
    ↓
Video Assembly (FFmpeg)
    ↓
Output Generation (Video + Reports)
```

### Component Relationships

#### Generator Classes Hierarchy
- **Base Pattern**: All generators inherit common safety methods
- **Specialized Implementations**: Each targets specific use cases
  - `ArchivalRemixEngine`: Original cultural heritage focus
  - `UltraRobustArchivalTool`: Advanced with HTML reporting
  - `ProgressiveSamplingGenerator`: Chronological scene progression
  - `BulletproofGenerator`: Maximum error resistance
  - `ForwardOnlyGenerator`: Anti-repetition strategy

#### Analysis Components
- **Scene Detection**: ContentDetector with configurable thresholds
- **Audio Processing**: Beat tracking and tempo analysis
- **Metadata Generation**: JSON output for scene timing and analysis
- **Report Generation**: HTML with thumbnail previews

## Key Technical Decisions

### Generator Strategy: Multiple Implementations
**Decision**: Maintain multiple generator classes rather than single unified version
**Rationale**: Different use cases benefit from different approaches
- Cultural heritage projects need different handling than music videos
- Error tolerance varies by application
- Scene selection strategies serve different artistic goals
**Trade-offs**: Code duplication vs. specialized optimization

### Error Handling: Safety-First Pattern
**Decision**: Comprehensive error handling with graceful degradation
**Pattern**: 
```python
def safe_float(self, value):
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0
```
**Rationale**: Numpy scalar types cause unpredictable failures
**Implementation**: Standard safety methods across all generators

### Scene Selection: Strategy Pattern
**Decision**: Multiple scene selection algorithms
**Strategies**:
- **Random**: Energy and unpredictability
- **Progressive**: Narrative continuity
- **Forward-only**: Anti-repetition
- **Conservative**: Cautious error handling
**Benefits**: Artistic flexibility and robustness

### Output Structure: Timestamped Archives
**Decision**: Create dated output directories
**Pattern**: `archival_output/YYYY-MM-DD_HH-MM-SS/`
**Benefits**: 
- Prevents overwriting previous runs
- Maintains experimental history
- Enables comparative analysis

## Design Patterns in Use

### Template Method Pattern
**Application**: Generator classes follow consistent structure
```python
class BaseGenerator:
    def generate_music_video(self):
        scenes = self.detect_scenes()      # Template method
        audio = self.analyze_audio()       # Template method  
        return self.assemble_video()       # Template method
```
**Benefit**: Consistent interface with specialized implementations

### Strategy Pattern  
**Application**: Scene selection algorithms
**Implementation**: Different generators use different selection strategies
**Flexibility**: Easy to add new selection algorithms

### Factory Pattern
**Application**: Test data generation
**Usage**: Creating synthetic test videos and audio for validation
**Benefit**: Reliable testing without external dependencies

### Observer Pattern
**Application**: Progress reporting
**Implementation**: Progress callbacks during long-running operations
**User Experience**: Real-time feedback during processing

## Critical Implementation Paths

### Scene Detection Flow
1. **Video Loading**: OpenCV VideoCapture / ffprobe for properties
2. **Scene Analysis**: PySceneDetect ContentDetector processing
3. **Threshold Tuning**: Adaptive threshold based on content type
4. **Metadata Extraction**: Scene timing and statistical analysis
5. **Error Recovery**: Fallback to time-based segmentation

### Audio Analysis Flow
1. **Audio Loading**: librosa load with error handling
2. **Beat Detection**: librosa.beat.beat_track analysis
3. **Tempo Analysis**: BPM calculation and rhythm mapping
4. **Synchronization Points**: Beat timing to scene transition mapping
5. **Fallback Strategy**: Default timing if beat detection fails

### Video Assembly Flow
1. **Clip Extraction**: Individual scene clip creation
2. **Duration Calculation**: Beat-to-scene timing mapping
3. **Transition Planning**: Cut point optimization
4. **Assembly Process**: FFmpeg concat demuxer (with audio attachment)
5. **Quality Control**: Output validation and error checking

### Report Generation Flow
1. **Thumbnail Creation**: Scene preview image generation
2. **Metadata Collection**: Scene and audio analysis data
3. **HTML Template**: Interactive report with navigation
4. **Asset Organization**: File system structure creation
5. **Analysis Output**: JSON and HTML report generation

## Component Integration Patterns

### Loose Coupling
- Generators don't depend on specific analysis implementations
- Scene detection can be swapped without changing generators
- Audio analysis is abstracted behind consistent interface

### Error Isolation
- Each processing stage has independent error handling
- Failures in one component don't cascade to others
- Graceful degradation with default values

### Data Flow Control
- Pipeline stages communicate through well-defined interfaces
- Metadata flows consistently through all processing stages
- State management is explicit and trackable

## Performance Considerations

### Memory Management
- Large video files processed in chunks where possible
- Temporary files cleaned up after processing
- Generator instances designed for single-use to avoid memory leaks

### Processing Optimization
- Parallel analysis of video and audio where possible
- Lazy loading of video segments during assembly
- Caching of computed analysis results

### Scalability Patterns
- Modular architecture enables distributed processing
- File-based communication allows process isolation
- Timestamped outputs enable batch processing workflows
