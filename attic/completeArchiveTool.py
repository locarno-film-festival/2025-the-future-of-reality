#!/usr/bin/env python3
"""
COMPLETE ARCHIVAL ANALYSIS & REMIX ENGINE
For "The Future of Reality" Conference - Locarno
================================================================
Part 1: Music Video Generation with proper chronological progression
Part 2: Scene Analysis with interactive visualization
"""

import warnings
warnings.filterwarnings("ignore")

import os
import sys
import json
import base64
from pathlib import Path
from datetime import timedelta
import numpy as np

try:
    import librosa
    import cv2
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
except ImportError as e:
    print(f"Missing required libraries: {e}")
    print("Install with: pip install librosa moviepy scenedetect[opencv] matplotlib opencv-python")
    sys.exit(1)


class CompleteArchivalEngine:
    """
    Comprehensive engine for both remix and analysis.
    """
    
    def __init__(self, film_path, song_path=None, output_dir="archival_output"):
        self.film_path = film_path
        self.song_path = song_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.clips_dir = self.output_dir / "clips"
        self.thumbnails_dir = self.output_dir / "thumbnails"
        self.clips_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        
        self.scenes = []
        self.beats = []
        self.scene_data = []
        
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  COMPLETE ARCHIVAL ANALYSIS & REMIX ENGINE                  ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Film: {Path(film_path).name:<53} ║
        ║  Output: {str(self.output_dir):<51} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
    def format_timecode(self, seconds):
        """Convert seconds to timecode format HH:MM:SS.FF"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        frames = int((seconds % 1) * 24)  # Assuming 24fps
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{frames:02d}"
    
    def analyze_and_export_scenes(self, threshold=30.0, export_clips=True):
        """
        Analyze scenes and optionally export each as individual clip with metadata.
        """
        print("\n📽️  COMPREHENSIVE SCENE ANALYSIS...")
        
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
            
            self.scenes = []
            self.scene_data = []
            
            print(f"   Processing {len(scene_list)} detected scenes...")
            
            for i, scene in enumerate(scene_list):
                start_time = float(scene[0].get_seconds())
                end_time = float(scene[1].get_seconds())
                duration = end_time - start_time
                
                # Skip very short scenes
                if duration < 0.5:
                    continue
                
                scene_info = {
                    'id': i,
                    'start': start_time,
                    'end': end_time,
                    'duration': duration,
                    'start_timecode': self.format_timecode(start_time),
                    'end_timecode': self.format_timecode(end_time),
                    'position_ratio': start_time / video_duration,
                    'clip_filename': f"scene_{i:04d}.mp4",
                    'thumbnail_filename': f"thumb_{i:04d}.jpg"
                }
                
                # Analyze visual characteristics
                print(f"   Analyzing scene {i+1}/{len(scene_list)}...")
                
                # Extract a frame for analysis (middle of scene)
                middle_time = (start_time + end_time) / 2
                frame = video.get_frame(middle_time)
                
                # Color analysis
                avg_color = np.mean(frame, axis=(0,1))
                scene_info['avg_color_rgb'] = avg_color.tolist()
                scene_info['avg_color_hex'] = '#{:02x}{:02x}{:02x}'.format(
                    int(avg_color[0]), int(avg_color[1]), int(avg_color[2])
                )
                
                # Brightness analysis
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                scene_info['avg_brightness'] = float(np.mean(gray))
                scene_info['brightness_std'] = float(np.std(gray))
                
                # Motion hint (based on duration and position)
                if duration < 2:
                    scene_info['pace'] = 'fast'
                elif duration > 10:
                    scene_info['pace'] = 'slow'
                else:
                    scene_info['pace'] = 'medium'
                
                # Save thumbnail
                thumb_path = self.thumbnails_dir / scene_info['thumbnail_filename']
                # Resize for thumbnail
                thumb_height = 120
                aspect_ratio = frame.shape[1] / frame.shape[0]
                thumb_width = int(thumb_height * aspect_ratio)
                thumb = cv2.resize(frame, (thumb_width, thumb_height))
                # Convert RGB to BGR for OpenCV
                thumb_bgr = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(thumb_path), thumb_bgr)
                
                # Export individual clip if requested
                if export_clips:
                    clip_path = self.clips_dir / scene_info['clip_filename']
                    try:
                        clip = video.subclip(start_time, end_time)
                        clip.write_videofile(
                            str(clip_path),
                            codec='libx264',
                            audio_codec='aac',
                            verbose=False,
                            logger=None
                        )
                        clip.close()
                    except Exception as e:
                        print(f"     Warning: Could not export clip {i}: {e}")
                
                self.scenes.append(scene_info)
                self.scene_data.append(scene_info)
            
            video.close()
            
            # Save scene metadata as JSON
            metadata_path = self.output_dir / "scene_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(self.scene_data, f, indent=2)
            
            print(f"   ✓ Analyzed {len(self.scenes)} scenes")
            print(f"   ✓ Saved thumbnails to {self.thumbnails_dir}")
            if export_clips:
                print(f"   ✓ Saved clips to {self.clips_dir}")
            print(f"   ✓ Saved metadata to {metadata_path}")
            
            return self.scenes
            
        except Exception as e:
            print(f"   ✗ Scene analysis failed: {e}")
            return []
    
    def create_interactive_visualization(self):
        """
        Create an interactive HTML visualization of the film's structure.
        """
        print("\n📊 CREATING INTERACTIVE VISUALIZATION...")
        
        if not self.scene_data:
            print("   ✗ No scene data available")
            return False
        
        html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archival Film Analysis - Interactive Visualization</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
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
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-style: italic;
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
        .chart-title {
            font-size: 1.3em;
            color: #764ba2;
            margin-bottom: 15px;
            font-weight: bold;
        }
        #thumbnail-preview {
            position: fixed;
            display: none;
            background: white;
            border: 2px solid #764ba2;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 1000;
        }
        #thumbnail-preview img {
            max-width: 300px;
            border-radius: 5px;
        }
        #thumbnail-preview .info {
            margin-top: 10px;
            font-size: 0.9em;
        }
        .scene-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 30px;
        }
        .scene-card {
            cursor: pointer;
            transition: transform 0.3s;
            text-align: center;
        }
        .scene-card:hover {
            transform: scale(1.05);
        }
        .scene-card img {
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        .scene-card .scene-time {
            margin-top: 5px;
            font-size: 0.8em;
            color: #666;
        }
        video {
            width: 100%;
            max-width: 800px;
            margin: 20px auto;
            display: block;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        #video-container {
            display: none;
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .close-video {
            background: #764ba2;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 10px;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Archival Film Analysis</h1>
        <p class="subtitle">The Future of Reality - Algorithmic Memory Exploration</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">''' + str(len(self.scene_data)) + '''</div>
                <div class="stat-label">Total Scenes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + f"{sum(s['duration'] for s in self.scene_data)/60:.1f}" + ''' min</div>
                <div class="stat-label">Total Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + f"{np.mean([s['duration'] for s in self.scene_data]):.1f}" + ''' sec</div>
                <div class="stat-label">Avg Scene Length</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + f"{np.std([s['duration'] for s in self.scene_data]):.1f}" + '''</div>
                <div class="stat-label">Rhythm Variation</div>
            </div>
        </div>
        
        <div class="legend">
            <strong>Interactive Features:</strong> 
            Hover over charts to see scene details | 
            Click on thumbnails to play clips | 
            Charts show temporal and visual patterns
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📈 Scene Duration Timeline</div>
            <div id="timeline-chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">🎨 Color & Brightness Analysis</div>
            <div id="color-chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">🎯 Scene Distribution</div>
            <div id="distribution-chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">🖼️ Scene Gallery (Click to Play)</div>
            <div class="scene-grid" id="scene-grid"></div>
        </div>
        
        <div id="video-container">
            <button class="close-video" onclick="closeVideo()">Close Video</button>
            <video id="video-player" controls></video>
        </div>
    </div>
    
    <div id="thumbnail-preview"></div>
    
    <script>
        const sceneData = ''' + json.dumps(self.scene_data) + ''';
        
        // Timeline Chart
        const timelineTrace = {
            x: sceneData.map(s => s.start),
            y: sceneData.map(s => s.duration),
            mode: 'markers+lines',
            type: 'scatter',
            name: 'Scene Duration',
            marker: {
                size: sceneData.map(s => Math.min(s.duration * 3, 20)),
                color: sceneData.map(s => s.avg_brightness),
                colorscale: 'Viridis',
                showscale: true,
                colorbar: {title: 'Brightness'}
            },
            line: {
                color: 'rgba(118, 75, 162, 0.3)',
                width: 2
            },
            text: sceneData.map(s => `Scene ${s.id}<br>Duration: ${s.duration.toFixed(1)}s<br>Time: ${s.start_timecode}`),
            hovertemplate: '%{text}<extra></extra>'
        };
        
        const timelineLayout = {
            title: 'Scene Duration Over Film Timeline',
            xaxis: {title: 'Time (seconds)'},
            yaxis: {title: 'Duration (seconds)'},
            height: 400,
            paper_bgcolor: '#f8f9fa',
            plot_bgcolor: 'white'
        };
        
        Plotly.newPlot('timeline-chart', [timelineTrace], timelineLayout);
        
        // Color Analysis Chart
        const colorTrace = {
            x: sceneData.map(s => s.start),
            y: sceneData.map(s => s.avg_brightness),
            mode: 'markers',
            type: 'scatter',
            name: 'Brightness',
            marker: {
                size: 12,
                color: sceneData.map(s => `rgb(${s.avg_color_rgb[0]}, ${s.avg_color_rgb[1]}, ${s.avg_color_rgb[2]})`),
                line: {
                    color: 'rgba(0,0,0,0.3)',
                    width: 1
                }
            },
            text: sceneData.map(s => `Scene ${s.id}<br>Brightness: ${s.avg_brightness.toFixed(0)}<br>Color: ${s.avg_color_hex}`),
            hovertemplate: '%{text}<extra></extra>'
        };
        
        const colorLayout = {
            title: 'Visual Characteristics Across Film',
            xaxis: {title: 'Time (seconds)'},
            yaxis: {title: 'Average Brightness'},
            height: 400,
            paper_bgcolor: '#f8f9fa',
            plot_bgcolor: 'white'
        };
        
        Plotly.newPlot('color-chart', [colorTrace], colorLayout);
        
        // Distribution Chart
        const paceCount = {
            fast: sceneData.filter(s => s.pace === 'fast').length,
            medium: sceneData.filter(s => s.pace === 'medium').length,
            slow: sceneData.filter(s => s.pace === 'slow').length
        };
        
        const distributionTrace = {
            values: Object.values(paceCount),
            labels: ['Fast Cuts', 'Medium Pace', 'Long Takes'],
            type: 'pie',
            marker: {
                colors: ['#FF6B6B', '#4ECDC4', '#45B7D1']
            }
        };
        
        const distributionLayout = {
            title: 'Scene Pacing Distribution',
            height: 400,
            paper_bgcolor: '#f8f9fa'
        };
        
        Plotly.newPlot('distribution-chart', [distributionTrace], distributionLayout);
        
        // Create scene gallery
        const sceneGrid = document.getElementById('scene-grid');
        sceneData.forEach(scene => {
            const card = document.createElement('div');
            card.className = 'scene-card';
            card.innerHTML = `
                <img src="thumbnails/${scene.thumbnail_filename}" alt="Scene ${scene.id}">
                <div class="scene-time">${scene.start_timecode}</div>
            `;
            card.onclick = () => playClip(scene);
            sceneGrid.appendChild(card);
        });
        
        function playClip(scene) {
            const videoContainer = document.getElementById('video-container');
            const videoPlayer = document.getElementById('video-player');
            videoPlayer.src = `clips/${scene.clip_filename}`;
            videoContainer.style.display = 'block';
            videoPlayer.play();
            
            // Scroll to video
            videoContainer.scrollIntoView({behavior: 'smooth'});
        }
        
        function closeVideo() {
            const videoContainer = document.getElementById('video-container');
            const videoPlayer = document.getElementById('video-player');
            videoPlayer.pause();
            videoContainer.style.display = 'none';
        }
    </script>
</body>
</html>
        '''
        
        # Save HTML file
        html_path = self.output_dir / "interactive_analysis.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        print(f"   ✓ Created interactive visualization: {html_path}")
        print(f"   📌 Open {html_path} in a web browser to explore")
        
        return True
    
    def analyze_audio_beats(self):
        """Standard beat analysis."""
        if not self.song_path:
            return [], 0
        
        print("\n🎵 ANALYZING AUDIO BEATS...")
        
        try:
            audio_data, sample_rate = librosa.load(self.song_path)
            tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
            
            self.beats = list(beat_times)
            self.tempo = float(tempo)
            self.audio_duration = len(audio_data) / sample_rate
            
            print(f"   ✓ Detected {len(self.beats)} beats at {self.tempo:.1f} BPM")
            return self.beats, self.tempo
            
        except Exception as e:
            print(f"   ✗ Beat analysis failed: {e}")
            return [], 120.0
    
    def create_progressive_mapping(self, beat_skip=1, max_clips=None, randomize=False):
        """
        Create truly progressive mapping through film chronology.
        
        Args:
            beat_skip: Use every Nth beat
            max_clips: Maximum number of clips
            randomize: If True, use random selection; if False, use progressive
        """
        print(f"\n🎬 CREATING {'RANDOM' if randomize else 'PROGRESSIVE'} MAPPING...")
        print(f"   Beat pattern: Every {beat_skip} beat(s)")
        
        if not self.scenes or not self.beats:
            print("   ✗ Missing scenes or beats")
            return []
        
        # Apply beat skipping
        selected_beats = self.beats[::beat_skip]
        num_beats = len(selected_beats) - 1
        
        if max_clips:
            num_beats = min(num_beats, max_clips)
        
        print(f"   Using {num_beats} beats from {len(self.beats)} total")
        
        mapping = []
        
        if randomize:
            # Random selection
            for i in range(num_beats):
                beat_start = selected_beats[i]
                beat_end = selected_beats[i + 1]
                beat_duration = beat_end - beat_start
                
                selected_scene = np.random.choice(self.scenes)
                
                mapping.append({
                    'beat_start': beat_start,
                    'beat_end': beat_end,
                    'beat_duration': beat_duration,
                    'scene': selected_scene,
                    'beat_index': i
                })
        else:
            # TRULY PROGRESSIVE - move through film chronologically
            # Distribute beats across the film timeline
            scenes_per_beat = len(self.scenes) / num_beats
            
            for i in range(num_beats):
                beat_start = selected_beats[i]
                beat_end = selected_beats[i + 1]
                beat_duration = beat_end - beat_start
                
                # Calculate which scene should correspond to this beat
                # to maintain chronological progression
                target_scene_index = int(i * scenes_per_beat)
                
                # Add small window for variety but maintain progression
                window_start = max(0, target_scene_index - 1)
                window_end = min(len(self.scenes), target_scene_index + 2)
                
                # Select from small window around target
                window_scenes = self.scenes[window_start:window_end]
                if window_scenes:
                    selected_scene = np.random.choice(window_scenes)
                else:
                    selected_scene = self.scenes[min(target_scene_index, len(self.scenes)-1)]
                
                mapping.append({
                    'beat_start': beat_start,
                    'beat_end': beat_end,
                    'beat_duration': beat_duration,
                    'scene': selected_scene,
                    'beat_index': i,
                    'film_progress': i / num_beats,
                    'scene_progress': selected_scene['position_ratio']
                })
        
        self.mapping = mapping
        
        # Verify progression
        if not randomize and mapping:
            positions = [m['scene']['position_ratio'] for m in mapping]
            forward_movement = sum(1 for i in range(1, len(positions)) if positions[i] >= positions[i-1])
            print(f"   ✓ Created {len(mapping)} mappings")
            print(f"   ✓ Forward progression: {forward_movement}/{len(positions)-1} steps")
        else:
            print(f"   ✓ Created {len(mapping)} {'random' if randomize else 'progressive'} mappings")
        
        return mapping
    
    def generate_remix_clips(self):
        """Generate video clips from mapping."""
        print("\n🎞️  GENERATING REMIX CLIPS...")
        
        if not hasattr(self, 'mapping'):
            print("   ✗ No mapping available")
            return []
        
        video_clips = []
        source_video = None
        
        try:
            source_video = VideoFileClip(self.film_path, audio=False)
            video_duration = source_video.duration
            
            successful = 0
            failed = 0
            
            for i, pair in enumerate(self.mapping):
                if i % 20 == 0 and i > 0:
                    print(f"   Processed {i}/{len(self.mapping)} beats...")
                
                try:
                    scene = pair['scene']
                    beat_duration = pair['beat_duration']
                    
                    # Ensure valid bounds
                    scene_start = max(0, min(scene['start'], video_duration - 0.5))
                    scene_end = min(scene['end'], video_duration)
                    
                    if scene_end - scene_start < 0.1:
                        failed += 1
                        continue
                    
                    clip = source_video.subclip(scene_start, scene_end)
                    
                    # Adjust duration
                    if clip.duration > beat_duration:
                        max_offset = clip.duration - beat_duration
                        offset = np.random.uniform(0, max_offset) if max_offset > 0 else 0
                        clip = clip.subclip(offset, offset + beat_duration)
                    elif clip.duration < beat_duration * 0.5:
                        failed += 1
                        continue
                    
                    video_clips.append(clip)
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    if failed <= 3:
                        print(f"   ⚠️ Clip {i} failed: {str(e)[:50]}")
            
            print(f"   ✓ Generated {successful} clips ({failed} failed)")
            
            self.video_clips = video_clips
            self.source_video = source_video
            return video_clips
            
        except Exception as e:
            print(f"   ✗ Generation failed: {e}")
            if source_video:
                source_video.close()
            return []
    
    def render_music_video(self, output_filename="remix.mp4"):
        """Render the final music video."""
        print("\n💾 RENDERING MUSIC VIDEO...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("   ✗ No clips to render")
            return False
        
        try:
            output_path = self.output_dir / output_filename
            
            print(f"   Concatenating {len(self.video_clips)} clips...")
            final_video = concatenate_videoclips(self.video_clips, method="compose")
            
            if self.song_path:
                print("   Adding audio...")
                audio = AudioFileClip(self.song_path)
                
                if audio.duration > final_video.duration:
                    audio = audio.subclip(0, final_video.duration)
                elif final_video.duration > audio.duration:
                    final_video = final_video.subclip(0, audio.duration)
                
                final_video = final_video.set_audio(audio)
                audio.close()
            
            print(f"   Writing to {output_path}...")
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=24,
                preset='medium',
                verbose=False,
                logger=None
            )
            
            # Cleanup
            final_video.close()
            if hasattr(self, 'source_video'):
                self.source_video.close()
            
            for clip in self.video_clips:
                try:
                    clip.close()
                except:
                    pass
            
            print(f"   ✓ Music video saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"   ✗ Rendering failed: {e}")
            return False
    
    def complete_analysis_and_remix(self, 
                                   export_clips=True,
                                   create_remix=True,
                                   beat_skip=1,
                                   max_clips=None,
                                   randomize=False):
        """
        Complete pipeline for both analysis and remix.
        """
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  COMPLETE ARCHIVAL TRANSFORMATION                           ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Part 1: Scene Analysis & Export                            ║
        ║  Part 2: Music Video Generation                             ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Part 1: Scene Analysis
        print("\n━━━ PART 1: SCENE ANALYSIS ━━━")
        scenes = self.analyze_and_export_scenes(export_clips=export_clips)
        if not scenes:
            print("✗ Scene analysis failed")
            return False
        
        # Create interactive visualization
        self.create_interactive_visualization()
        
        # Part 2: Music Video (if song provided)
        if create_remix and self.song_path:
            print("\n━━━ PART 2: MUSIC VIDEO GENERATION ━━━")
            
            # Analyze beats
            beats, tempo = self.analyze_audio_beats()
            if not beats:
                print("✗ Beat analysis failed")
                return False
            
            # Create mapping
            mapping = self.create_progressive_mapping(
                beat_skip=beat_skip,
                max_clips=max_clips,
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
            
            # Render
            video_name = "remix_random.mp4" if randomize else "remix_progressive.mp4"
            success = self.render_music_video(video_name)
            
            if success:
                print(f"""
                ╔══════════════════════════════════════════════════════════════╗
                ║  TRANSFORMATION COMPLETE                                    ║
                ╠══════════════════════════════════════════════════════════════╣
                ║  ✓ Scene analysis exported                                  ║
                ║  ✓ Interactive visualization created                        ║
                ║  ✓ Music video generated                                    ║
                ║                                                              ║
                ║  Open {self.output_dir}/interactive_analysis.html           ║
                ║  in your browser to explore!                                ║
                ╚══════════════════════════════════════════════════════════════╝
                """)
        else:
            print(f"""
            ╔══════════════════════════════════════════════════════════════╗
            ║  ANALYSIS COMPLETE                                          ║
            ╠══════════════════════════════════════════════════════════════╣
            ║  ✓ Scene analysis exported                                  ║
            ║  ✓ Interactive visualization created                        ║
            ║                                                              ║
            ║  Open {self.output_dir}/interactive_analysis.html           ║
            ║  in your browser to explore!                                ║
            ╚══════════════════════════════════════════════════════════════╝
            """)
        
        return True


def main():
    """Interactive interface."""
    import sys
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  COMPLETE ARCHIVAL ANALYSIS & REMIX ENGINE                  ║
    ║  The Future of Reality Conference - Locarno                 ║
    ╚══════════════════════════════════════════════════════════════╝
    
    This tool provides:
    1. Complete scene-by-scene analysis with export
    2. Interactive HTML visualization
    3. Music video generation (progressive or random)
    
    Usage modes:
    """)
    
    if len(sys.argv) < 2:
        print("1. Analysis only:")
        print("   python script.py <film.mp4>")
        print("\n2. Analysis + Music Video:")
        print("   python script.py <film.mp4> <song.mp3> [progressive|random] [beat_skip]")
        print("\nExamples:")
        print("   python script.py movie.mp4")
        print("   python script.py movie.mp4 song.mp3 progressive 1")
        print("   python script.py movie.mp4 song.mp3 random 2")
        return
    
    film_path = sys.argv[1]
    song_path = sys.argv[2] if len(sys.argv) > 2 else None
    mode = sys.argv[3] if len(sys.argv) > 3 else "progressive"
    beat_skip = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    
    # Create engine
    engine = CompleteArchivalEngine(film_path, song_path)
    
    # Run complete pipeline
    engine.complete_analysis_and_remix(
        export_clips=True,  # Export individual scene clips
        create_remix=bool(song_path),  # Create music video if song provided
        beat_skip=beat_skip,
        max_clips=None,  # Use all clips
        randomize=(mode == "random")
    )


if __name__ == "__main__":
    main()
