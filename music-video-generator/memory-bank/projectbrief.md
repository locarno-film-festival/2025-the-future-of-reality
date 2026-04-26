# Project Brief: Music Video Generation & Archival Remix Engine

## Overview
This project is a **Music Video Generation & Archival Remix Engine** that creates artistic video remixes by synchronizing archival film footage with music. It uses AI-driven scene detection, audio analysis, and video manipulation to transform cultural heritage materials into new artistic expressions.

## Core Objectives
1. **Artistic Transformation**: Convert archival footage into modern music video format
2. **Cultural Preservation**: Give new life to cultural heritage materials through remix
3. **AI-Driven Synchronization**: Use machine learning for intelligent scene-to-beat mapping
4. **Robust Processing**: Handle various video/audio formats and edge cases reliably

## Key Technologies
- **Scene Detection**: PySceneDetect with ContentDetector
- **Audio Analysis**: librosa for beat detection and tempo analysis
- **Video Processing**: FFmpeg (via subprocess) for clip extraction, trimming, and assembly; OpenCV for frame analysis and thumbnails
- **AI Analysis**: Computer vision for scene understanding

## Primary Use Cases
- Transform archival films into music videos
- Create artistic remixes of cultural heritage content
- Generate synchronized video content from any video/audio pair
- Experiment with different synchronization strategies

## Success Criteria
- Reliable scene detection across different video types
- Accurate beat-to-scene synchronization
- High-quality output video generation
- Robust error handling for various input formats
- Comprehensive analysis and reporting tools

## Target Outputs
- High-quality remixed music videos
- Detailed analysis reports with thumbnails
- Scene metadata for further processing
- Interactive HTML reports for review
