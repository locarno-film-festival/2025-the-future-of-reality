#!/usr/bin/env python3
"""
ULTRA-ROBUST ARCHIVAL ANALYSIS & REMIX ENGINE
Fixes stdout errors and creates timestamped output folders
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
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import gc

try:
    import librosa
    import cv2
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
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
    Ultra-robust version with better audio handling and timestamped folders.
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
        
        # Configure MoviePy to suppress output
        os.environ['IMAGEIO_FFMPEG_EXE'] = 'ffmpeg'
        
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  ULTRA-ROBUST ARCHIVAL ANALYSIS & REMIX ENGINE              ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Film: {Path(film_path).name:<53} ║
        ║  Output: {str(self.output_dir.name):<51} ║
        ║  Timestamp: {timestamp:<48} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
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
    
    def safe_write_videofile_ultra(self, clip, output_path, with_audio=True, audio_source=None):
        """
        Ultra-safe video writing that avoids stdout errors.
        """
        output_path = Path(output_path)
        
        try:
            # Always write video without audio first
            temp_video = self.temp_dir / f"temp_video_{int(time.time())}.mp4"
            
            # Write video only
            clip_no_audio = clip.without_audio() if hasattr(clip, 'audio') else clip
            
            # Use minimal parameters for stability
            clip_no_audio.write_videofile(
                str(temp_video),
                codec='libx264',
                audio=False,
                verbose=False,
                logger=None,
                preset='medium',
                threads=2
            )
            
            if not with_audio:
                # Just move the video file
                import shutil
                shutil.move(str(temp_video), str(output_path))
                return True
            
            # Handle audio separately
            if audio_source:
                # Use provided audio file
                success = self.render_with_ffmpeg_directly(temp_video, audio_source, output_path)
            elif hasattr(clip, 'audio') and clip.audio:
                # Export audio from clip
                temp_audio = self.temp_dir / f"temp_audio_{int(time.time())}.m4a"
                
                # Try to export audio
                try:
                    clip.audio.write_audiofile(
                        str(temp_audio),
                        verbose=False,
                        logger=None,
                        codec='aac',
                        bitrate='192k'
                    )
                    success = self.render_with_ffmpeg_directly(temp_video, temp_audio, output_path)
                    
                    # Cleanup temp audio
                    if temp_audio.exists():
                        temp_audio.unlink()
                        
                except:
                    # If audio export fails, just use video without audio
                    import shutil
                    shutil.move(str(temp_video), str(output_path))
                    success = True
            else:
                # No audio to add
                import shutil
                shutil.move(str(temp_video), str(output_path))
                success = True
            
            # Cleanup temp video
            if temp_video.exists():
                temp_video.unlink()
            
            return success
            
        except Exception as e:
            print(f"     Ultra-safe write failed: {str(e)[:100]}")
            return False
    
    def analyze_and_export_scenes(self, threshold=30.0, export_clips=False, max_scenes=None):
        """
        Analyze scenes with optional clip export.
        """
        print("\n📽️  SCENE ANALYSIS...")
        
        try:
            # Load video for analysis
            video = VideoFileClip(self.film_path)
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
                indices = np.linspace(0, len(scene_list)-1, max_scenes, dtype=int)
                scene_list = [scene_list[i] for i in indices]
            
            self.scenes = []
            self.scene_data = []
            clips_exported = 0
            
            for i, scene in enumerate(scene_list):
                if i % 50 == 0:
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
                    'thumbnail_filename': f"thumb_{i:04d}.jpg"
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
                
                # Export clip if requested (limit to first 50)
                if export_clips and clips_exported < 50:
                    clip_path = self.clips_dir / scene_info['clip_filename']
                    try:
                        clip = video.subclip(start_time, min(end_time, video_duration))
                        if self.safe_write_videofile_ultra(clip, clip_path, with_audio=False):
                            clips_exported += 1
                        clip.close()
                        time.sleep(0.05)  # Brief pause between exports
                    except Exception as e:
                        pass
                
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
            
            return self.scenes
            
        except Exception as e:
            print(f"   ✗ Scene analysis failed: {e}")
            return []
    
    def create_visualization_html(self):
        """Create interactive HTML visualization."""
        print("\n📊 CREATING VISUALIZATION...")
        
        if not self.scene_data:
            print("   ✗ No scene data available")
            return False
        
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archival Film Analysis</title>
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
        .scene-thumb img {
            width: 100%;
            border-radius: 5px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .scene-thumb img:hover {
            transform: scale(1.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Archival Film Analysis</h1>
        
        <div class="metadata">
            <strong>Output Directory:</strong> ''' + str(self.output_dir.name) + '''<br>
            <strong>Timestamp:</strong> ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '''
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
                <div class="stat-value">''' + f"{np.mean([s['duration'] for s in self.scene_data]):.1f}" + ''' sec</div>
                <div class="stat-label">Avg Scene</div>
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
            <h3>Scene Thumbnails</h3>
            <div class="scene-grid">''' + \
            ''.join([f'<div class="scene-thumb"><img src="thumbnails/{s["thumbnail_filename"]}" title="Scene {s["id"]}: {s["start_timecode"]}"></div>' 
                    for s in self.scene_data[:200]]) + \
            '''</div>
        </div>
    </div>
    
    <script>
        const sceneData = ''' + json.dumps(self.scene_data) + ''';
        
        // Timeline
        const timelineTrace = {
            x: sceneData.map(s => s.start),
            y: sceneData.map(s => s.duration),
            mode: 'lines+markers',
            marker: {
                size: 6,
                color: sceneData.map(s => s.avg_brightness),
                colorscale: 'Viridis',
                showscale: true
            },
            text: sceneData.map(s => 'Scene ' + s.id + '<br>' + s.start_timecode),
            hovertemplate: '%{text}<br>Duration: %{y:.1f}s<extra></extra>'
        };
        
        Plotly.newPlot('timeline-chart', [timelineTrace], {
            title: 'Scene Duration Timeline',
            xaxis: {title: 'Time (seconds)'},
            yaxis: {title: 'Duration (seconds)'},
            height: 400
        });
        
        // Color evolution
        const colorTrace = {
            x: sceneData.map(s => s.start),
            y: sceneData.map(s => s.avg_brightness),
            mode: 'markers+lines',
            marker: {
                size: 8,
                color: sceneData.map(s => s.avg_color_hex)
            },
            text: sceneData.map(s => 'Scene ' + s.id),
            hovertemplate: '%{text}<br>Brightness: %{y:.0f}<extra></extra>'
        };
        
        Plotly.newPlot('color-chart', [colorTrace], {
            title: 'Brightness Evolution',
            xaxis: {title: 'Time (seconds)'},
            yaxis: {title: 'Brightness'},
            height: 400
        });
        
        // Pacing
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
    </script>
</body>
</html>'''
        
        html_path = self.output_dir / "analysis.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        print(f"   ✓ Created visualization: {html_path}")
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
                    logger=None,
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
                success = self.safe_write_videofile_ultra(
                    final_video,
                    output_path,
                    with_audio=False
                )
                final_video.close()
            
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
    
    def run_complete_pipeline(self, export_clips=False, max_scenes=None, 
                             beat_skip=1, randomize=False, max_remix_clips=None):
        """
        Run complete analysis and remix pipeline.
        """
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  STARTING ARCHIVAL TRANSFORMATION                           ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Mode: {'Random' if randomize else 'Progressive chronological':<52} ║
        ║  Beat skip: Every {beat_skip} beat(s){' '*(42-len(str(beat_skip)))} ║
        ║  Max scenes: {'None (all)' if not max_scenes else str(max_scenes):<47} ║
        ║  Max clips: {'None (all beats)' if not max_remix_clips else str(max_remix_clips):<47} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Analyze scenes
        scenes = self.analyze_and_export_scenes(
            export_clips=export_clips,
            max_scenes=max_scenes
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
        ║  TRANSFORMATION COMPLETE!                                   ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  📁 Output folder: {str(self.output_dir.name):<41} ║
        ║  📊 Open analysis.html in browser to explore                ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        return True


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("""
        ULTRA-ROBUST ARCHIVAL ENGINE - Usage:
        
        1. Analysis only (fast, no clip export):
           python script.py <film.mp4>
        
        2. Analysis + Progressive music video:
           python script.py <film.mp4> <song.mp3>
           python script.py <film.mp4> <song.mp3> progressive
        
        3. Analysis + Random music video:
           python script.py <film.mp4> <song.mp3> random
        
        4. Analysis with clip export (slower):
           python script.py <film.mp4> export
        
        5. Custom beat skip (use every Nth beat):
           python script.py <film.mp4> <song.mp3> progressive 2
           (uses every other beat - good for fast songs)
        
        Examples:
           python script.py movie.mp4
           python script.py movie.mp4 song.mp3 progressive
           python script.py movie.mp4 song.mp3 random 2
        
        Note: Output will be in timestamped folder under archival_output/
        """)
        return
    
    film_path = sys.argv[1]
    
    # Parse arguments
    export_clips = False
    song_path = None
    mode = "progressive"
    beat_skip = 1
    
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        
        if arg2 == "export":
            export_clips = True
        elif arg2.endswith(('.mp3', '.wav', '.m4a', '.flac')):
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
        export_clips=export_clips,
        max_scenes=None,  # No limit as requested
        beat_skip=beat_skip,
        randomize=(mode == "random"),
        max_remix_clips=None  # Use all beats
    )
    
    if not success:
        print("\n❌ Pipeline failed - check error messages above")
        sys.exit(1)


if __name__ == "__main__":
    main()
