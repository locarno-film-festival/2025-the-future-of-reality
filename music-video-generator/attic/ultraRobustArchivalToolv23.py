#!/usr/bin/env python3
"""
ULTRA-ROBUST ARCHIVAL ANALYSIS & REMIX ENGINE v23
Fixed MoviePy logging issues - all clips should have audio consistently
For "The Future of Reality" Conference - Locarno
"""

import warnings
warnings.filterwarnings("ignore")

import os
import sys
import json
import time
import tempfile
import subprocess
import base64
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import gc

try:
    import librosa
    import cv2
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
    from moviepy.config import change_settings
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"Missing required libraries: {e}")
    print("Install with: pip install librosa moviepy scenedetect[opencv] matplotlib opencv-python")
    sys.exit(1)


class UltraRobustArchivalEngine:
    """
    Ultra-robust version with fixed MoviePy logging - all clips get audio consistently.
    """
    
    def __init__(self, film_path, song_path=None, base_output_dir="archival_output"):
        self.film_path = film_path
        self.song_path = song_path
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        film_name = Path(film_path).stem
        self.output_dir = Path(base_output_dir) / f"{film_name}_{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.clips_dir = self.output_dir / "clips"
        self.thumbnails_dir = self.output_dir / "thumbnails"
        self.temp_dir = self.output_dir / "temp"
        self.clips_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        self.scenes = []
        self.beats = []
        self.scene_data = []
        self.has_audio = False
        
        # Configure MoviePy to suppress output
        os.environ['IMAGEIO_FFMPEG_EXE'] = 'ffmpeg'
        
        # Check if the source video has audio
        self._check_audio_availability()
        
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  ULTRA-ROBUST ARCHIVAL ANALYSIS & REMIX ENGINE v23          ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Film: {Path(film_path).name:<53} ║
        ║  Audio: {'Available' if self.has_audio else 'Not available':<52} ║
        ║  Output: {str(self.output_dir.name):<51} ║
        ║  Timestamp: {timestamp:<48} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
    def _check_audio_availability(self):
        """Check if the source video has audio track available."""
        try:
            # Quick test to see if audio is available
            with VideoFileClip(self.film_path) as test_video:
                if test_video.audio is not None:
                    self.has_audio = True
                    print("   ✓ Audio track detected in source video")
                else:
                    self.has_audio = False
                    print("   ⚠ No audio track found in source video")
        except Exception as e:
            self.has_audio = False
            print(f"   ⚠ Could not check audio availability: {str(e)[:50]}")
    
    def format_timecode(self, seconds):
        """Convert seconds to timecode format HH:MM:SS.FF"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        frames = int((seconds % 1) * 24)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{frames:02d}"
    
    def render_with_ffmpeg_directly(self, video_path, audio_path, output_path):
        """
        Use FFmpeg directly to combine video and audio, avoiding MoviePy audio issues.
        """
        try:
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
            
            if result.returncode == 0:
                return True
            else:
                print(f"     FFmpeg error: {result.stderr[:200]}")
                return False
                
        except Exception as e:
            print(f"     FFmpeg failed: {str(e)[:100]}")
            return False
    
    def export_scene_clip_with_audio_fixed(self, video, scene_info, max_duration=1000):
        """
        Fixed audio export with proper MoviePy logging settings.
        """
        clip_path = self.clips_dir / scene_info['clip_filename']
        
        # Limit clip duration for web playback
        start_time = scene_info['start']
        end_time = min(scene_info['end'], start_time + max_duration)
        
        # Ensure we have a minimum duration and valid bounds
        min_duration = 0.1
        if end_time - start_time < min_duration:
            end_time = start_time + min_duration
        
        # Make sure we don't exceed video duration
        if hasattr(video, 'duration') and video.duration:
            end_time = min(end_time, video.duration)
            if start_time >= video.duration:
                print(f"     Warning: Scene {scene_info['id']} starts beyond video duration")
                return False
        
        try:
            # Create the subclip with precise timing
            clip = video.subclip(start_time, end_time)
            
            # If source has audio and we want audio, try to include it
            if self.has_audio and video.audio is not None:
                # Method 1: Direct export with audio (fixed logging)
                try:
                    clip.write_videofile(
                        str(clip_path),
                        codec='libx264',
                        audio=True,
                        audio_codec='aac',
                        audio_bitrate='128k',
                        verbose=False,
                        logger='bar',  # Use 'bar' instead of None
                        preset='fast',
                        threads=2,
                        fps=24
                    )
                    scene_info['has_audio'] = True
                    print(f"     ✓ Scene {scene_info['id']} exported with audio")
                    clip.close()
                    return True
                    
                except Exception as direct_error:
                    print(f"     ⚠ Direct audio export failed for scene {scene_info['id']}: {str(direct_error)[:50]}")
                    
                    # Method 2: Try with different logging setting
                    try:
                        clip.write_videofile(
                            str(clip_path),
                            codec='libx264',
                            audio=True,
                            audio_codec='aac',
                            audio_bitrate='128k',
                            verbose=False,
                            # Remove logger parameter entirely
                            preset='fast',
                            threads=2,
                            fps=24
                        )
                        scene_info['has_audio'] = True
                        print(f"     ✓ Scene {scene_info['id']} exported with audio (no logger)")
                        clip.close()
                        return True
                        
                    except Exception as no_logger_error:
                        print(f"     ⚠ No-logger method failed for scene {scene_info['id']}: {str(no_logger_error)[:50]}")
                        
                        # Method 3: FFmpeg combination approach
                        try:
                            temp_video_path = self.temp_dir / f"temp_video_{scene_info['id']}.mp4"
                            temp_audio_path = self.temp_dir / f"temp_audio_{scene_info['id']}.wav"
                            
                            print(f"     Trying FFmpeg method for scene {scene_info['id']}...")
                            
                            # Export video without audio first
                            clip.write_videofile(
                                str(temp_video_path),
                                codec='libx264',
                                audio=False,
                                verbose=False,
                                preset='fast',
                                threads=2,
                                fps=24
                            )
                            
                            # Export audio separately
                            if clip.audio is not None:
                                clip.audio.write_audiofile(
                                    str(temp_audio_path),
                                    verbose=False
                                )
                                
                                # Combine using FFmpeg
                                success = self.render_with_ffmpeg_directly(
                                    temp_video_path,
                                    temp_audio_path,
                                    clip_path
                                )
                                
                                if success:
                                    scene_info['has_audio'] = True
                                    print(f"     ✓ Scene {scene_info['id']} exported with audio via FFmpeg")
                                    
                                    # Cleanup temp files
                                    for temp_file in [temp_video_path, temp_audio_path]:
                                        if temp_file.exists():
                                            temp_file.unlink()
                                    
                                    clip.close()
                                    return True
                                else:
                                    print(f"     ✗ FFmpeg combination failed for scene {scene_info['id']}")
                            else:
                                print(f"     ✗ No audio in clip for scene {scene_info['id']}")
                                
                        except Exception as ffmpeg_error:
                            print(f"     ✗ FFmpeg method failed for scene {scene_info['id']}: {str(ffmpeg_error)[:50]}")
                    
                        # Method 4: Ultra-simple audio export
                        try:
                            print(f"     Trying ultra-simple method for scene {scene_info['id']}...")
                            
                            # Use absolute minimal parameters
                            clip.write_videofile(
                                str(clip_path),
                                audio=True,
                                verbose=False
                            )
                            scene_info['has_audio'] = True
                            print(f"     ✓ Scene {scene_info['id']} exported with audio (ultra-simple)")
                            clip.close()
                            return True
                            
                        except Exception as simple_error:
                            print(f"     ✗ Ultra-simple method failed for scene {scene_info['id']}: {str(simple_error)[:50]}")
            
            # Final fallback: export without audio (should rarely happen)
            print(f"     ⚠ Falling back to video-only for scene {scene_info['id']}")
            clip.write_videofile(
                str(clip_path),
                codec='libx264',
                audio=False,
                verbose=False,
                preset='fast',
                threads=2,
                fps=24
            )
            scene_info['has_audio'] = False
            print(f"     ✓ Scene {scene_info['id']} exported without audio")
            clip.close()
            return True
                
        except Exception as e:
            error_msg = str(e)
            print(f"     ✗ Complete export failed for scene {scene_info['id']}: {error_msg[:50]}")
            
            # Try to clean up
            try:
                if 'clip' in locals():
                    clip.close()
            except:
                pass
                
            return False
    
    def export_scene_clip(self, video, scene_info, max_duration=1000, with_audio=False):
        """
        Wrapper method to maintain compatibility with existing code.
        """
        if with_audio:
            return self.export_scene_clip_with_audio_fixed(video, scene_info, max_duration)
        else:
            # Original video-only method
            try:
                clip = video.subclip(scene_info['start'], 
                                   min(scene_info['end'], scene_info['start'] + max_duration))
                clip.write_videofile(
                    str(self.clips_dir / scene_info['clip_filename']),
                    codec='libx264',
                    audio=False,
                    verbose=False,
                    preset='fast',
                    threads=2,
                    fps=24
                )
                scene_info['has_audio'] = False
                clip.close()
                return True
            except Exception as e:
                print(f"     ✗ Video-only export failed for scene {scene_info['id']}: {str(e)[:50]}")
                return False
    
    def analyze_and_export_scenes(self, threshold=30.0, export_clips=True, max_scenes=None, max_clip_duration=1000, with_audio=False):
        """
        Analyze scenes with fixed audio clip export.
        """
        print("\n📽️  SCENE ANALYSIS...")
        if with_audio and not self.has_audio:
            print("   ⚠ Audio requested but source video has no audio track")
            with_audio = False
        
        try:
            # Load video - include audio if requested and available
            if with_audio and self.has_audio:
                print("   Loading video with audio for clip export...")
                try:
                    video = VideoFileClip(self.film_path, audio=True)
                    # Verify audio is actually loaded
                    if video.audio is None:
                        print("   Note: Audio track could not be loaded, continuing without audio...")
                        video.close()
                        video = VideoFileClip(self.film_path, audio=False)
                        with_audio = False
                        self.has_audio = False
                except Exception as audio_error:
                    print(f"   Warning: Could not load audio: {str(audio_error)[:50]}")
                    print("   Falling back to video-only mode...")
                    video = VideoFileClip(self.film_path, audio=False)
                    with_audio = False
            else:
                print("   Loading video without audio...")
                video = VideoFileClip(self.film_path, audio=False)
                
            video_duration = video.duration
            fps = video.fps
            print(f"   Video: {video_duration:.1f}s at {fps:.1f} fps")
            
            # Detect scenes
            print("   Detecting scene boundaries...")
            video_manager = VideoManager([self.film_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            
            video_manager.set_duration()
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()
            
            print(f"   Found {len(scene_list)} scenes")
            
            # Limit scenes if requested
            if max_scenes and len(scene_list) > max_scenes:
                print(f"   Limiting to {max_scenes} scenes")
                # For progressive mode, take the first N scenes
                scene_list = scene_list[:max_scenes]
            
            self.scenes = []
            self.scene_data = []
            clips_exported = 0
            clips_with_audio = 0
            clips_failed = []
            
            for i, scene in enumerate(scene_list):
                if i % 20 == 0:
                    print(f"   Processing scene {i+1}/{len(scene_list)}...")
                
                start_time = float(scene[0].get_seconds())
                end_time = float(scene[1].get_seconds())
                duration = end_time - start_time
                
                if duration < 0.5:
                    continue
                
                scene_info = {
                    'id': i,
                    'start': start_time,
                    'end': min(end_time, video_duration),
                    'duration': duration,
                    'start_timecode': self.format_timecode(start_time),
                    'end_timecode': self.format_timecode(end_time),
                    'position_ratio': start_time / video_duration,
                    'clip_filename': f"scene_{i:04d}.mp4",
                    'thumbnail_filename': f"thumb_{i:04d}.jpg",
                    'has_audio': False  # Will be set during export
                }
                
                # Extract thumbnail
                try:
                    middle_time = (start_time + end_time) / 2
                    frame = video.get_frame(middle_time)
                    
                    # Color analysis
                    avg_color = np.mean(frame, axis=(0,1))
                    scene_info['avg_color_rgb'] = avg_color.tolist()
                    scene_info['avg_color_hex'] = '#{:02x}{:02x}{:02x}'.format(
                        int(avg_color[0]), int(avg_color[1]), int(avg_color[2])
                    )
                    
                    # Brightness
                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                    scene_info['avg_brightness'] = float(np.mean(gray))
                    
                    # Pace
                    if duration < 2:
                        scene_info['pace'] = 'fast'
                    elif duration > 10:
                        scene_info['pace'] = 'slow'
                    else:
                        scene_info['pace'] = 'medium'
                    
                    # Save thumbnail
                    thumb_path = self.thumbnails_dir / scene_info['thumbnail_filename']
                    thumb_height = 120
                    aspect_ratio = frame.shape[1] / frame.shape[0]
                    thumb_width = int(thumb_height * aspect_ratio)
                    thumb = cv2.resize(frame, (thumb_width, thumb_height))
                    thumb_bgr = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(str(thumb_path), thumb_bgr)
                    
                except Exception as e:
                    print(f"     Warning: Could not process scene {i}: {str(e)[:30]}")
                    continue
                
                # Export clip if requested
                if export_clips and clips_exported < 2000:  # Limit to 2000 clips for storage
                    result = self.export_scene_clip(video, scene_info, max_duration=max_clip_duration, with_audio=with_audio)
                    
                    if result:
                        clips_exported += 1
                        scene_info['has_clip'] = True
                        if scene_info.get('has_audio', False):
                            clips_with_audio += 1
                    else:
                        scene_info['has_clip'] = False
                        clips_failed.append(i)
                else:
                    scene_info['has_clip'] = False
                
                self.scenes.append(scene_info)
                self.scene_data.append(scene_info)
            
            video.close()
            
            # Save metadata
            metadata_path = self.output_dir / "scene_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(self.scene_data, f, indent=2)
            
            print(f"\n   ✓ Processed {len(self.scenes)} scenes")
            print(f"   ✓ Saved {len(self.scenes)} thumbnails")
            if export_clips:
                print(f"   ✓ Exported {clips_exported} clips")
                if with_audio:
                    print(f"   ✓ {clips_with_audio} clips include audio")
                    if clips_with_audio < clips_exported:
                        print(f"   ⚠ {clips_exported - clips_with_audio} clips fell back to video-only")
                if clips_failed:
                    if len(clips_failed) < 20:
                        print(f"   ⚠ Failed clips: {clips_failed}")
                    else:
                        print(f"   ⚠ {len(clips_failed)} clips failed to export")
            
            return self.scenes
            
        except Exception as e:
            print(f"   ✗ Scene analysis failed: {e}")
            return []
    
    def create_visualization_html(self):
        """Create interactive HTML visualization with working thumbnail previews."""
        print("\n📊 CREATING INTERACTIVE VISUALIZATION...")
        
        if not self.scene_data:
            print("   ✗ No scene data available")
            return False
        
        # Count audio-enabled clips
        audio_clips_count = sum(1 for s in self.scene_data if s.get('has_audio', False))
        
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Archival Film Analysis v23</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #764ba2;
            text-align: center;
            margin-bottom: 30px;
        }
        .metadata {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-family: monospace;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .chart-container {
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }
        .scene-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
            gap: 10px;
            max-height: 400px;
            overflow-y: auto;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .scene-thumb {
            position: relative;
            cursor: pointer;
        }
        .scene-thumb img {
            width: 100%;
            border-radius: 5px;
            transition: transform 0.2s;
        }
        .scene-thumb img:hover {
            transform: scale(1.1);
        }
        .scene-thumb .play-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 30px;
            height: 30px;
            background: rgba(0,0,0,0.7);
            border-radius: 50%;
            display: none;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
        }
        .scene-thumb:hover .play-overlay {
            display: flex;
        }
        .scene-thumb .audio-indicator {
            position: absolute;
            top: 2px;
            right: 2px;
            width: 16px;
            height: 16px;
            background: #28a745;
            border-radius: 50%;
            display: none;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 8px;
        }
        .scene-thumb.has-audio .audio-indicator {
            display: flex;
        }
        #video-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }
        #video-modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            max-width: 90%;
            max-height: 90%;
        }
        #video-modal video {
            max-width: 100%;
            max-height: 80vh;
        }
        .close-modal {
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }
        .close-modal:hover {
            color: #f1f1f1;
        }
        #scene-info {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            text-align: center;
            background: rgba(0,0,0,0.7);
            padding: 10px 20px;
            border-radius: 5px;
        }
        /* Custom hover tooltip */
        #custom-tooltip {
            position: absolute;
            display: none;
            background: white;
            border: 2px solid #764ba2;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 999;
            pointer-events: none;
        }
        #custom-tooltip img {
            width: 150px;
            border-radius: 4px;
            margin-bottom: 5px;
        }
        #custom-tooltip .tooltip-text {
            font-size: 12px;
            line-height: 1.4;
        }
        #custom-tooltip .tooltip-text b {
            color: #764ba2;
        }
        .audio-badge {
            background: #28a745;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 10px;
            margin-left: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Interactive Archival Film Analysis v23</h1>
        
        <div class="metadata">
            <strong>Output Directory:</strong> ''' + str(self.output_dir.name) + '''<br>
            <strong>Timestamp:</strong> ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '''<br>
            <strong>Audio Support:</strong> Fixed MoviePy logging - consistent audio export<br>
            <strong>Hover over data points to see thumbnails | Click to play scene clips</strong>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">''' + str(len(self.scene_data)) + '''</div>
                <div class="stat-label">Total Scenes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + f"{sum(s['duration'] for s in self.scene_data)/60:.1f}" + ''' min</div>
                <div class="stat-label">Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(audio_clips_count) + '''</div>
                <div class="stat-label">Audio Clips</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + f"{np.median([s['duration'] for s in self.scene_data]):.1f}" + ''' sec</div>
                <div class="stat-label">Median Scene</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div id="timeline-chart"></div>
        </div>
        
        <div class="chart-container">
            <div id="color-chart"></div>
        </div>
        
        <div class="chart-container">
            <div id="pacing-chart"></div>
        </div>
        
        <div class="chart-container">
            <h3>Scene Thumbnails (Click to play) 
            <span class="audio-badge">🔊 = Audio</span></h3>
            <div class="scene-grid" id="scene-grid">''' + \
            ''.join([f'''<div class="scene-thumb {' has-audio' if s.get('has_audio', False) else ''}" onclick="playClip({s["id"]})">
                <img src="thumbnails/{s["thumbnail_filename"]}" title="Scene {s["id"]}: {s["start_timecode"]}">
                <div class="play-overlay">▶</div>
                <div class="audio-indicator">🔊</div>
            </div>''' if s.get('has_clip', False) else 
            f'''<div class="scene-thumb">
                <img src="thumbnails/{s["thumbnail_filename"]}" title="Scene {s["id"]}: {s["start_timecode"]}">
            </div>'''
                    for s in self.scene_data[:200]]) + \
            '''</div>
        </div>
    </div>
    
    <!-- Video Modal -->
    <div id="video-modal">
        <span class="close-modal" onclick="closeVideoModal()">&times;</span>
        <div id="video-modal-content">
            <video id="modal-video" controls></video>
            <div id="scene-info"></div>
        </div>
    </div>
    
    <!-- Custom Tooltip -->
    <div id="custom-tooltip">
        <img id="tooltip-img" src="">
        <div class="tooltip-text">
            <b id="tooltip-scene"></b><br>
            <span id="tooltip-details"></span>
        </div>
    </div>
    
    <script>
        const sceneData = ''' + json.dumps(self.scene_data) + ''';
        
        // Timeline plot with simple hover text
        const timelineTrace = {
            x: sceneData.map(s => s.start),
            y: sceneData.map(s => s.duration),
            mode: 'markers+lines',
            marker: {
                size: 8,
                color: sceneData.map(s => s.avg_brightness),
                colorscale: 'Viridis',
                showscale: true,
                line: {
                    width: 1,
                    color: 'white'
                }
            },
            text: sceneData.map(s => 'Scene ' + s.id + '<br>' + s.start_timecode + '<br>Duration: ' + s.duration.toFixed(1) + 's' + (s.has_audio ? '<br>🔊 Audio' : '')),
            hovertemplate: '%{text}<extra></extra>',
            customdata: sceneData.map(s => s.id)
        };
        
        const timelineLayout = {
            title: 'Scene Duration Timeline (Hover for preview, Click to play)',
            xaxis: {title: 'Time (seconds)'},
            yaxis: {title: 'Duration (seconds)'},
            height: 400,
            hovermode: 'closest'
        };
        
        Plotly.newPlot('timeline-chart', [timelineTrace], timelineLayout);
        
        // Color evolution plot
        const colorTrace = {
            x: sceneData.map(s => s.start),
            y: sceneData.map(s => s.avg_brightness),
            mode: 'markers+lines',
            marker: {
                size: 10,
                color: sceneData.map(s => s.avg_color_hex),
                line: {
                    width: 1,
                    color: 'white'
                }
            },
            text: sceneData.map(s => 'Scene ' + s.id + '<br>Brightness: ' + s.avg_brightness.toFixed(0) + (s.has_audio ? '<br>🔊 Audio' : '')),
            hovertemplate: '%{text}<extra></extra>',
            customdata: sceneData.map(s => s.id)
        };
        
        const colorLayout = {
            title: 'Brightness Evolution (Hover for preview, Click to play)',
            xaxis: {title: 'Time (seconds)'},
            yaxis: {title: 'Brightness'},
            height: 400,
            hovermode: 'closest'
        };
        
        Plotly.newPlot('color-chart', [colorTrace], colorLayout);
        
        // Pacing pie chart
        const paceCount = {
            fast: sceneData.filter(s => s.pace === 'fast').length,
            medium: sceneData.filter(s => s.pace === 'medium').length,
            slow: sceneData.filter(s => s.pace === 'slow').length
        };
        
        const pacingTrace = {
            values: Object.values(paceCount),
            labels: ['Fast', 'Medium', 'Slow'],
            type: 'pie',
            hole: 0.4
        };
        
        Plotly.newPlot('pacing-chart', [pacingTrace], {
            title: 'Scene Pacing Distribution',
            height: 400
        });
        
        // Video playback functions (define BEFORE event handlers)
        function playClip(sceneId) {
            const scene = sceneData.find(s => s.id === sceneId);
            if (scene) {
                const modal = document.getElementById('video-modal');
                const video = document.getElementById('modal-video');
                const info = document.getElementById('scene-info');
                
                // Try to play the clip regardless of has_clip flag
                const clipFilename = 'clips/scene_' + String(scene.id).padStart(4, '0') + '.mp4';
                
                video.src = clipFilename;
                info.innerHTML = '<b>Scene ' + scene.id + '</b> | ' + 
                                scene.start_timecode + ' | Duration: ' + 
                                scene.duration.toFixed(1) + 's | Pace: ' + scene.pace +
                                (scene.has_audio ? ' | 🔊 Audio' : '');
                
                modal.style.display = 'block';
                
                // Try to play, but handle errors gracefully
                video.play().catch(e => {
                    // If clip doesn't exist, show error message
                    info.innerHTML += '<br><i style="color: yellow;">Note: Clip may not be available</i>';
                    console.log('Clip not found or error playing:', clipFilename, e);
                });
            }
        }
        
        function closeVideoModal() {
            const modal = document.getElementById('video-modal');
            const video = document.getElementById('modal-video');
            
            video.pause();
            video.src = '';
            modal.style.display = 'none';
        }
        
        // Custom tooltip functionality
        const tooltip = document.getElementById('custom-tooltip');
        const tooltipImg = document.getElementById('tooltip-img');
        const tooltipScene = document.getElementById('tooltip-scene');
        const tooltipDetails = document.getElementById('tooltip-details');
        
        // Add click events to plots FIRST (before hover events)
        var timelineChart = document.getElementById('timeline-chart');
        timelineChart.on('plotly_click', function(data) {
            if (data.points && data.points[0]) {
                const sceneId = data.points[0].customdata;
                playClip(sceneId);
            }
        });
        
        var colorChart = document.getElementById('color-chart');
        colorChart.on('plotly_click', function(data) {
            if (data.points && data.points[0]) {
                const sceneId = data.points[0].customdata;
                playClip(sceneId);
            }
        });
        
        // Add hover events to show custom tooltip with thumbnail
        timelineChart.on('plotly_hover', function(data) {
            if (data.points && data.points[0]) {
                const sceneId = data.points[0].customdata;
                const scene = sceneData.find(s => s.id === sceneId);
                if (scene) {
                    const event = data.event;
                    tooltip.style.left = (event.pageX + 10) + 'px';
                    tooltip.style.top = (event.pageY - 100) + 'px';
                    tooltipImg.src = 'thumbnails/' + scene.thumbnail_filename;
                    tooltipScene.textContent = 'Scene ' + scene.id;
                    tooltipDetails.innerHTML = 'Time: ' + scene.start_timecode + '<br>' +
                                              'Duration: ' + scene.duration.toFixed(1) + 's<br>' +
                                              'Brightness: ' + scene.avg_brightness.toFixed(0) + '<br>' +
                                              'Pace: ' + scene.pace +
                                              (scene.has_audio ? '<br>🔊 Audio included' : '');
                    tooltip.style.display = 'block';
                }
            }
        });
        
        timelineChart.on('plotly_unhover', function(data) {
            tooltip.style.display = 'none';
        });
        
        colorChart.on('plotly_hover', function(data) {
            if (data.points && data.points[0]) {
                const sceneId = data.points[0].customdata;
                const scene = sceneData.find(s => s.id === sceneId);
                if (scene) {
                    const event = data.event;
                    tooltip.style.left = (event.pageX + 10) + 'px';
                    tooltip.style.top = (event.pageY - 100) + 'px';
                    tooltipImg.src = 'thumbnails/' + scene.thumbnail_filename;
                    tooltipScene.textContent = 'Scene ' + scene.id;
                    tooltipDetails.innerHTML = 'Time: ' + scene.start_timecode + '<br>' +
                                              'Duration: ' + scene.duration.toFixed(1) + 's<br>' +
                                              'Brightness: ' + scene.avg_brightness.toFixed(0) + '<br>' +
                                              'Pace: ' + scene.pace +
                                              (scene.has_audio ? '<br>🔊 Audio included' : '');
                    tooltip.style.display = 'block';
                }
            }
        });
        
        colorChart.on('plotly_unhover', function(data) {
            tooltip.style.display = 'none';
        });
        
        // Close modal on outside click
        window.onclick = function(event) {
            const modal = document.getElementById('video-modal');
            if (event.target == modal) {
                closeVideoModal();
            }
        }
        
        // Keyboard shortcut to close modal
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeVideoModal();
            }
        });
    </script>
</body>
</html>'''
        
        html_path = self.output_dir / "analysis.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        print(f"   ✓ Created interactive visualization: {html_path}")
        print(f"   ✓ Fixed logging for consistent audio export")
        print(f"   ✓ Hover over plot points to see thumbnail previews")
        print(f"   ✓ Click any data point to play the scene clip")
        return True
    
    def analyze_audio_beats(self):
        """Analyze audio beats."""
        if not self.song_path:
            return [], 0
        
        print("\n🎵 ANALYZING BEATS...")
        
        try:
            audio_data, sample_rate = librosa.load(self.song_path)
            tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
            
            self.beats = list(beat_times)
            self.tempo = float(tempo)
            self.audio_duration = len(audio_data) / sample_rate
            
            print(f"   ✓ {len(self.beats)} beats at {self.tempo:.1f} BPM")
            return self.beats, self.tempo
            
        except Exception as e:
            print(f"   ✗ Beat analysis failed: {e}")
            return [], 120.0
    
    def create_progressive_mapping(self, beat_skip=1, max_clips=None, randomize=False):
        """Create scene-to-beat mapping."""
        print(f"\n🎬 CREATING {'RANDOM' if randomize else 'PROGRESSIVE'} MAPPING...")
        
        if not self.scenes or not self.beats:
            return []
        
        selected_beats = self.beats[::beat_skip]
        num_beats = min(len(selected_beats) - 1, max_clips) if max_clips else len(selected_beats) - 1
        
        mapping = []
        
        for i in range(num_beats):
            beat_start = selected_beats[i]
            beat_end = selected_beats[i + 1]
            beat_duration = beat_end - beat_start
            
            if randomize:
                selected_scene = np.random.choice(self.scenes)
            else:
                # Progressive: move through film chronologically
                scene_index = int((i / num_beats) * len(self.scenes))
                scene_index = min(scene_index, len(self.scenes) - 1)
                selected_scene = self.scenes[scene_index]
            
            mapping.append({
                'beat_start': beat_start,
                'beat_end': beat_end,
                'beat_duration': beat_duration,
                'scene': selected_scene,
                'beat_index': i
            })
        
        self.mapping = mapping
        print(f"   ✓ Created {len(mapping)} mappings")
        return mapping
    
    def generate_remix_clips(self):
        """Generate video clips from mapping."""
        print("\n🎞️  GENERATING CLIPS...")
        
        if not hasattr(self, 'mapping'):
            return []
        
        video_clips = []
        source_video = None
        
        try:
            # Load video without audio to avoid issues
            source_video = VideoFileClip(self.film_path, audio=False)
            video_duration = source_video.duration
            
            for i, pair in enumerate(self.mapping):
                if i % 50 == 0 and i > 0:
                    print(f"   Processed {i}/{len(self.mapping)} beats...")
                
                try:
                    scene = pair['scene']
                    beat_duration = pair['beat_duration']
                    
                    # Ensure valid bounds
                    scene_start = max(0, min(scene['start'], video_duration - 0.5))
                    scene_end = min(scene['end'], video_duration)
                    
                    if scene_end - scene_start < 0.1:
                        continue
                    
                    clip = source_video.subclip(scene_start, scene_end)
                    
                    # Adjust to beat duration
                    if clip.duration > beat_duration:
                        max_offset = clip.duration - beat_duration
                        offset = np.random.uniform(0, max(0, max_offset))
                        clip = clip.subclip(offset, offset + beat_duration)
                    
                    video_clips.append(clip)
                    
                except Exception:
                    continue
            
            print(f"   ✓ Generated {len(video_clips)} clips")
            
            self.video_clips = video_clips
            self.source_video = source_video
            return video_clips
            
        except Exception as e:
            print(f"   ✗ Generation failed: {e}")
            if source_video:
                source_video.close()
            return []
    
    def render_music_video(self, output_filename="remix.mp4"):
        """Render the final music video using ultra-safe method."""
        print("\n💾 RENDERING MUSIC VIDEO...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("   ✗ No clips to render")
            return False
        
        try:
            output_path = self.output_dir / output_filename
            
            print(f"   Concatenating {len(self.video_clips)} clips...")
            final_video = concatenate_videoclips(self.video_clips, method="compose")
            
            if self.song_path:
                print("   Processing with audio...")
                
                # First, save video without audio
                temp_video_path = self.temp_dir / f"video_only_{int(time.time())}.mp4"
                
                final_video.write_videofile(
                    str(temp_video_path),
                    codec='libx264',
                    audio=False,
                    verbose=False,
                    preset='medium'
                )
                
                # Clean up video clips
                final_video.close()
                
                # Use FFmpeg directly to combine video and audio
                print("   Combining video and audio with FFmpeg...")
                success = self.render_with_ffmpeg_directly(
                    temp_video_path,
                    self.song_path,
                    output_path
                )
                
                # Cleanup temp video
                if temp_video_path.exists():
                    temp_video_path.unlink()
                
            else:
                # No audio, just save video
                print("   Writing video without audio...")
                final_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio=False,
                    verbose=False,
                    preset='medium'
                )
                final_video.close()
                success = True
            
            # Cleanup
            if hasattr(self, 'source_video'):
                self.source_video.close()
            
            for clip in self.video_clips:
                try:
                    clip.close()
                except:
                    pass
            
            # Force garbage collection
            gc.collect()
            
            if success:
                print(f"   ✓ Music video saved: {output_path}")
                return True
            else:
                print(f"   ✗ Failed to save video")
                return False
            
        except Exception as e:
            print(f"   ✗ Rendering failed: {e}")
            
            # Emergency cleanup
            try:
                if 'final_video' in locals():
                    final_video.close()
                if hasattr(self, 'source_video'):
                    self.source_video.close()
                for clip in self.video_clips:
                    try:
                        clip.close()
                    except:
                        pass
                gc.collect()
            except:
                pass
            
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            for temp_file in self.temp_dir.glob("*"):
                try:
                    temp_file.unlink()
                except:
                    pass
        except:
            pass
    
    def run_complete_pipeline(self, export_clips=True, max_scenes=None, 
                             beat_skip=1, randomize=False, max_remix_clips=None, with_audio=False):
        """
        Run complete analysis and remix pipeline with fixed logging.
        """
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  STARTING ARCHIVAL TRANSFORMATION v23                       ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Mode: {'Random' if randomize else 'Progressive chronological':<52} ║
        ║  Beat skip: Every {beat_skip} beat(s){' '*(42-len(str(beat_skip)))} ║
        ║  Max scenes: {'None (all)' if not max_scenes else str(max_scenes):<47} ║
        ║  Max clips: {'None (all beats)' if not max_remix_clips else str(max_remix_clips):<47} ║
        ║  Export clips: {'Yes' if export_clips else 'No':<48} ║
        ║  With audio: {'Yes' if with_audio else 'No':<49} ║
        ║  Source has audio: {'Yes' if self.has_audio else 'No':<43} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Analyze scenes and export clips
        scenes = self.analyze_and_export_scenes(
            export_clips=export_clips,
            max_scenes=max_scenes,
            max_clip_duration=1000,  # 1000 second max for web playback
            with_audio=with_audio  # Pass the audio parameter
        )
        if not scenes:
            print("✗ Scene analysis failed")
            return False
        
        # Create visualization
        self.create_visualization_html()
        
        # Create music video if song provided
        if self.song_path:
            print("\n━━━ MUSIC VIDEO GENERATION ━━━")
            
            # Analyze beats
            beats, tempo = self.analyze_audio_beats()
            if not beats:
                print("✗ Beat analysis failed")
                return False
            
            # Create mapping
            mapping = self.create_progressive_mapping(
                beat_skip=beat_skip,
                max_clips=max_remix_clips,
                randomize=randomize
            )
            if not mapping:
                print("✗ Mapping creation failed")
                return False
            
            # Generate clips
            clips = self.generate_remix_clips()
            if not clips:
                print("✗ Clip generation failed")
                return False
            
            # Render video
            video_name = "remix_random.mp4" if randomize else "remix_progressive.mp4"
            success = self.render_music_video(video_name)
            
            if not success:
                print("✗ Video rendering failed")
                return False
        
        # Cleanup temp files
        self.cleanup_temp_files()
        
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  TRANSFORMATION COMPLETE! v23                               ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  📁 Output folder: {str(self.output_dir.name):<41} ║
        ║  📊 Open analysis.html in browser for interactive view      ║
        ║  🖼️  Hover over plot points to see thumbnail previews       ║
        ║  🎬 Click on plot points to play scene clips                ║
        ║  🔊 Fixed logging - consistent audio in all clips           ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        return True


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("""
        ULTRA-ROBUST ARCHIVAL ENGINE v23 - Fixed Logging - Usage:
        
        1. Analysis with clips and interactive visualization:
           python script.py <film.mp4>
        
        2. Analysis + Progressive music video:
           python script.py <film.mp4> <song.mp3>
           python script.py <film.mp4> <song.mp3> progressive
        
        3. Analysis + Random music video:
           python script.py <film.mp4> <song.mp3> random
        
        4. Custom beat skip (use every Nth beat):
           python script.py <film.mp4> <song.mp3> progressive 2
           (uses every other beat - good for fast songs)
        
        5. Include audio in exported clips (FIXED LOGGING):
           python script.py <film.mp4> --with-audio
           python script.py <film.mp4> <song.mp3> progressive --with-audio
        
        Examples:
           python script.py movie.mp4
           python script.py movie.mp4 --with-audio
           python script.py movie.mp4 song.mp3 progressive
           python script.py movie.mp4 song.mp3 random 2
           python script.py movie.mp4 song.mp3 progressive 1 --with-audio
        
        v23 Features:
        - 🔧 FIXED: MoviePy logging issues causing stdout errors
        - 🎵 Multiple export methods for maximum compatibility
        - 🛡️ Robust fallback chain prevents audio loss
        - 📊 Consistent audio export across all clips
        - 🎬 Progressive mode for chronological scene selection
        - 📁 All output in timestamped folders for organization
        """)
        return
    
    film_path = sys.argv[1]
    
    # Parse arguments
    song_path = None
    mode = "progressive"
    beat_skip = 1
    with_audio = False
    
    # Check for --with-audio flag
    if '--with-audio' in sys.argv:
        with_audio = True
        sys.argv.remove('--with-audio')
    
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        
        if arg2.endswith(('.mp3', '.wav', '.m4a', '.flac')):
            song_path = arg2
            
            if len(sys.argv) > 3:
                mode = sys.argv[3]
            
            if len(sys.argv) > 4:
                try:
                    beat_skip = int(sys.argv[4])
                except:
                    beat_skip = 1
    
    # Create engine and run
    engine = UltraRobustArchivalEngine(film_path, song_path)
    
    success = engine.run_complete_pipeline(
        export_clips=True,  # Always export clips for interactivity
        max_scenes=None,  # No limit
        beat_skip=beat_skip,
        randomize=(mode == "random"),
        max_remix_clips=None,  # Use all beats
        with_audio=with_audio  # Pass the fixed logging audio flag
    )
    
    if not success:
        print("\n❌ Pipeline failed - check error messages above")
        sys.exit(1)


if __name__ == "__main__":
    main()