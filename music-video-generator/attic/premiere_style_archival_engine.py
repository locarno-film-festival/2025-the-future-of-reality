#!/usr/bin/env python3
"""
PREMIERE PRO-STYLE ARCHIVAL ANALYSIS ENGINE
Professional video editing interface with clips-first workflow
Features: Proportional timeline, stereo waveforms, spectrogram, monitor panel
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
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
    from moviepy.config import change_settings
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    import matplotlib.pyplot as plt
    from scipy import signal
except ImportError as e:
    print(f"Missing required libraries: {e}")
    print("Install with: pip install librosa moviepy scenedetect[opencv] matplotlib opencv-python scipy")
    sys.exit(1)


class AudioWaveformRenderer:
    """Professional stereo waveform generation and analysis."""
    
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        
    def generate_stereo_waveform(self, audio_file, target_points=1000):
        """Generate stereo waveform data optimized for web display."""
        try:
            # Load as stereo, preserving both channels
            audio_data, sr = librosa.load(audio_file, sr=self.sample_rate, mono=False)
            
            # Handle mono files
            if len(audio_data.shape) == 1:
                left_channel = audio_data
                right_channel = audio_data
            else:
                left_channel = audio_data[0]
                right_channel = audio_data[1] if audio_data.shape[0] > 1 else audio_data[0]
            
            # Downsample for visualization (keeping peaks)
            chunk_size = max(1, len(left_channel) // target_points)
            
            left_waveform = self.downsample_with_peaks(left_channel, chunk_size)
            right_waveform = self.downsample_with_peaks(right_channel, chunk_size)
            
            # Calculate RMS levels and peak levels
            left_rms = float(np.sqrt(np.mean(left_channel**2)))
            right_rms = float(np.sqrt(np.mean(right_channel**2)))
            left_peak = float(np.max(np.abs(left_channel)))
            right_peak = float(np.max(np.abs(right_channel)))
            
            # Time axis
            duration = len(audio_data) / sr if len(audio_data.shape) == 1 else len(audio_data[0]) / sr
            time_axis = np.linspace(0, duration, len(left_waveform))
            
            return {
                'left_waveform': left_waveform.tolist(),
                'right_waveform': right_waveform.tolist(),
                'time_axis': time_axis.tolist(),
                'sample_rate': sr,
                'duration': duration,
                'levels': {
                    'left_rms': left_rms,
                    'right_rms': right_rms,
                    'left_peak': left_peak,
                    'right_peak': right_peak,
                    'left_db': 20 * np.log10(max(left_rms, 1e-6)),
                    'right_db': 20 * np.log10(max(right_rms, 1e-6))
                }
            }
            
        except Exception as e:
            print(f"   Warning: Waveform generation failed: {str(e)[:50]}")
            return self.generate_silent_waveform(5.0, target_points)
    
    def downsample_with_peaks(self, audio_data, chunk_size):
        """Downsample audio while preserving peak information."""
        if chunk_size <= 1:
            return audio_data
        
        # Reshape into chunks and take max/min for peak preservation
        padded_length = (len(audio_data) // chunk_size) * chunk_size
        audio_chunks = audio_data[:padded_length].reshape(-1, chunk_size)
        
        # Take RMS of each chunk for better representation
        downsampled = np.sqrt(np.mean(audio_chunks**2, axis=1))
        
        # Preserve sign information
        signs = np.sign(np.mean(audio_chunks, axis=1))
        return downsampled * signs
    
    def generate_silent_waveform(self, duration, target_points):
        """Generate silent waveform for videos without audio."""
        time_axis = np.linspace(0, duration, target_points)
        silent_wave = np.zeros(target_points)
        
        return {
            'left_waveform': silent_wave.tolist(),
            'right_waveform': silent_wave.tolist(), 
            'time_axis': time_axis.tolist(),
            'sample_rate': 22050,
            'duration': duration,
            'levels': {
                'left_rms': 0.0, 'right_rms': 0.0,
                'left_peak': 0.0, 'right_peak': 0.0,
                'left_db': -120.0, 'right_db': -120.0
            }
        }


class SpectrogramAnalyzer:
    """Real-time spectrogram analysis for audio visualization."""
    
    def __init__(self, n_fft=2048, hop_length=512):
        self.n_fft = n_fft
        self.hop_length = hop_length
    
    def generate_spectrogram(self, audio_file, target_width=200):
        """Generate mel-spectrogram optimized for web visualization."""
        try:
            # Load mono audio for spectrogram
            audio_data, sr = librosa.load(audio_file, sr=22050, mono=True)
            
            # Generate mel-spectrogram
            S = librosa.feature.melspectrogram(
                y=audio_data,
                sr=sr,
                n_mels=64,  # Reasonable resolution for web display
                n_fft=self.n_fft,
                hop_length=self.hop_length,
                fmax=8000
            )
            
            # Convert to dB
            S_dB = librosa.power_to_db(S, ref=np.max)
            
            # Downsample time dimension for web display
            if S_dB.shape[1] > target_width:
                time_factor = S_dB.shape[1] // target_width
                S_dB_downsampled = signal.decimate(S_dB, time_factor, axis=1)
            else:
                S_dB_downsampled = S_dB
            
            # Generate frequency and time axes
            frequencies = librosa.mel_frequencies(n_mels=64, fmax=8000)
            times = librosa.frames_to_time(
                np.arange(S_dB_downsampled.shape[1]),
                sr=sr,
                hop_length=self.hop_length * (S_dB.shape[1] // S_dB_downsampled.shape[1])
            )
            
            return {
                'spectrogram': S_dB_downsampled.tolist(),
                'frequencies': frequencies.tolist(),
                'times': times.tolist(),
                'shape': S_dB_downsampled.shape,
                'duration': float(times[-1]) if len(times) > 0 else 0.0
            }
            
        except Exception as e:
            print(f"   Warning: Spectrogram generation failed: {str(e)[:50]}")
            return self.generate_silent_spectrogram(5.0)
    
    def generate_silent_spectrogram(self, duration):
        """Generate silent spectrogram for videos without audio."""
        n_mels = 64
        n_times = 100
        
        return {
            'spectrogram': [[-120.0] * n_times for _ in range(n_mels)],
            'frequencies': np.linspace(0, 8000, n_mels).tolist(),
            'times': np.linspace(0, duration, n_times).tolist(),
            'shape': [n_mels, n_times],
            'duration': duration
        }


class ProportionalTimelineEngine:
    """Professional timeline rendering with proportional clip widths."""
    
    def __init__(self):
        self.MIN_CLIP_WIDTH = 20
        self.MAX_CLIP_WIDTH = 500
        self.THUMBNAIL_MIN_WIDTH = 40
        self.WAVEFORM_MIN_WIDTH = 60
        
        self.ZOOM_LEVELS = {
            'fit_all': 1.0,
            'fit_selection': 2.0,
            '1_minute': 5.0,
            '30_seconds': 10.0,
            '10_seconds': 30.0,
            '1_second': 300.0
        }
    
    def calculate_clip_widths(self, scenes, timeline_width_px=1200, zoom_level=1.0):
        """Calculate proportional clip widths based on duration."""
        if not scenes:
            return []
        
        total_duration = sum(scene['duration'] for scene in scenes)
        if total_duration <= 0:
            return []
        
        pixels_per_second = (timeline_width_px * zoom_level) / total_duration
        
        clip_widths = []
        current_x = 0
        
        for scene in scenes:
            raw_width = scene['duration'] * pixels_per_second
            # Apply constraints
            width_px = max(self.MIN_CLIP_WIDTH, min(raw_width, self.MAX_CLIP_WIDTH))
            
            clip_data = {
                'scene_id': scene['id'],
                'width_px': float(width_px),
                'duration': scene['duration'],
                'start_px': float(current_x),
                'end_px': float(current_x + width_px),
                'display_mode': self.get_display_mode(width_px)
            }
            
            clip_widths.append(clip_data)
            current_x += width_px
        
        return clip_widths
    
    def get_display_mode(self, clip_width_px):
        """Determine what elements to show based on clip width."""
        if clip_width_px < self.THUMBNAIL_MIN_WIDTH:
            return "minimal"  # Just colored bar with duration
        elif clip_width_px < self.WAVEFORM_MIN_WIDTH:
            return "thumbnail_only"  # Thumbnail but no waveform
        else:
            return "full"  # Thumbnail + waveform + all details


class PremiereStyleArchivalEngine:
    """
    Professional archival analysis engine with clips-first workflow.
    Features Premiere Pro-style timeline with proportional clips.
    """
    
    def __init__(self, film_path, song_path=None, base_output_dir="premiere_analysis"):
        self.film_path = film_path
        self.song_path = song_path
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        film_name = Path(film_path).stem
        self.output_dir = Path(base_output_dir) / f"{film_name}_premiere_{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create workflow directories
        self.working_dir = self.output_dir / "working"
        self.clips_dir = self.working_dir / "clips"
        self.thumbnails_dir = self.working_dir / "thumbnails"
        self.audio_dir = self.working_dir / "audio"
        self.analysis_dir = self.output_dir / "analysis"
        self.temp_dir = self.output_dir / "temp"
        
        for dir_path in [self.working_dir, self.clips_dir, self.thumbnails_dir, 
                        self.audio_dir, self.analysis_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.waveform_renderer = AudioWaveformRenderer()
        self.spectrogram_analyzer = SpectrogramAnalyzer()
        self.timeline_engine = ProportionalTimelineEngine()
        
        self.scenes = []
        self.clips_metadata = []
        
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  PREMIERE PRO-STYLE ARCHIVAL ANALYSIS ENGINE                 ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Film: {Path(film_path).name:<53} ║
        ║  Output: {str(self.output_dir.name):<51} ║
        ║  Workflow: Clips-First → Analysis → Timeline                 ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
    def format_timecode(self, seconds):
        """Convert seconds to professional timecode format."""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        frames = int((seconds % 1) * 24)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
    
    # PHASE 1: CLIPS-FIRST GENERATION
    def phase1_generate_all_clips(self, threshold=30.0, max_scenes=None, force_audio=True):
        """
        PHASE 1: Generate ALL clips with audio and thumbnails FIRST.
        This is the foundation of our clips-first workflow.
        """
        print("\n" + "="*80)
        print("📽️  PHASE 1: CLIPS-FIRST GENERATION")
        print("="*80)
        
        # Step 1: Scene Detection
        print("\n🎬 Step 1: Scene Detection...")
        scenes = self.detect_scenes(threshold, max_scenes)
        if not scenes:
            print("   ✗ Scene detection failed")
            return False
        
        # Step 2: Load video for processing
        print("\n📹 Step 2: Loading video for clip generation...")
        try:
            if force_audio:
                video = VideoFileClip(self.film_path, audio=True)
                if video.audio is None:
                    print("   ⚠ No audio track found, continuing without audio")
                    force_audio = False
            else:
                video = VideoFileClip(self.film_path, audio=False)
                
            video_duration = video.duration
            print(f"   ✓ Video loaded: {video_duration:.1f}s, Audio: {'Yes' if force_audio else 'No'}")
            
        except Exception as e:
            print(f"   ✗ Video loading failed: {str(e)[:50]}")
            return False
        
        # Step 3: Generate all clips with audio
        print(f"\n🎞️  Step 3: Generating {len(scenes)} clips with audio...")
        clips_metadata = []
        successful_clips = 0
        
        for i, scene in enumerate(scenes):
            if i % 25 == 0:
                print(f"   Processing clip {i+1}/{len(scenes)}...")
            
            # Generate clip with audio
            clip_success = self.export_scene_clip_with_audio(
                video, scene, force_audio=force_audio
            )
            
            if clip_success:
                # Generate thumbnail
                thumb_success = self.generate_clip_thumbnail(video, scene)
                
                # Generate audio analysis
                audio_analysis = self.analyze_clip_audio(scene, force_audio)
                
                # Create clip metadata
                clip_metadata = {
                    **scene,
                    'has_clip': True,
                    'has_audio': force_audio,
                    'audio_analysis': audio_analysis,
                    'files': {
                        'video': f"clips/scene_{scene['id']:04d}.mp4",
                        'audio': f"audio/scene_{scene['id']:04d}.wav" if force_audio else None,
                        'thumbnail': f"thumbnails/thumb_{scene['id']:04d}.jpg"
                    }
                }
                
                clips_metadata.append(clip_metadata)
                successful_clips += 1
            else:
                print(f"   ⚠ Failed to generate clip {scene['id']}")
        
        video.close()
        
        # Step 4: Save clips manifest
        print(f"\n💾 Step 4: Saving clips manifest...")
        self.clips_metadata = clips_metadata
        manifest_path = self.working_dir / "clips_manifest.json"
        
        with open(manifest_path, 'w') as f:
            json.dump({
                'total_clips': len(clips_metadata),
                'successful_clips': successful_clips,
                'has_audio': force_audio,
                'generation_time': datetime.now().isoformat(),
                'clips': clips_metadata
            }, f, indent=2)
        
        print(f"   ✓ Generated {successful_clips}/{len(scenes)} clips successfully")
        print(f"   ✓ Clips manifest saved: {manifest_path}")
        print(f"   ✓ Working directory ready: {self.working_dir}")
        
        return successful_clips > 0
    
    def detect_scenes(self, threshold=30.0, max_scenes=None):
        """Detect scene boundaries using PySceneDetect."""
        try:
            video_manager = VideoManager([self.film_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            
            video_manager.set_duration()
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()
            
            # Limit scenes if requested
            if max_scenes and len(scene_list) > max_scenes:
                indices = np.linspace(0, len(scene_list)-1, max_scenes, dtype=int)
                scene_list = [scene_list[i] for i in indices]
            
            # Convert to our format
            scenes = []
            for i, scene in enumerate(scene_list):
                start_time = float(scene[0].get_seconds())
                end_time = float(scene[1].get_seconds())
                duration = end_time - start_time
                
                if duration < 0.1:  # Skip very short scenes
                    continue
                
                scene_info = {
                    'id': i,
                    'start': start_time,
                    'end': end_time,
                    'duration': duration,
                    'start_timecode': self.format_timecode(start_time),
                    'end_timecode': self.format_timecode(end_time)
                }
                scenes.append(scene_info)
            
            self.scenes = scenes
            print(f"   ✓ Detected {len(scenes)} scenes (threshold: {threshold})")
            return scenes
            
        except Exception as e:
            print(f"   ✗ Scene detection failed: {str(e)[:50]}")
            return []
    
    def export_scene_clip_with_audio(self, video, scene, force_audio=True, max_duration=300):
        """Export individual scene as video clip with audio."""
        clip_filename = f"scene_{scene['id']:04d}.mp4"
        clip_path = self.clips_dir / clip_filename
        
        # Limit duration for web compatibility
        start_time = scene['start']
        end_time = min(scene['end'], start_time + max_duration)
        
        # Ensure minimum duration
        if end_time - start_time < 0.1:
            end_time = start_time + 0.1
        
        # Ensure we don't exceed video duration
        if hasattr(video, 'duration') and video.duration:
            end_time = min(end_time, video.duration)
        
        try:
            clip = video.subclip(start_time, end_time)
            
            if force_audio and video.audio is not None:
                # Export with audio
                clip.write_videofile(
                    str(clip_path),
                    codec='libx264',
                    audio=True,
                    audio_codec='aac',
                    audio_bitrate='128k',
                    verbose=False,
                    logger=None,
                    preset='fast',
                    fps=15,
                    write_logfile=False
                )
                
                # Also export audio separately for analysis
                audio_filename = f"scene_{scene['id']:04d}.wav"
                audio_path = self.audio_dir / audio_filename
                
                try:
                    clip.audio.write_audiofile(
                        str(audio_path),
                        verbose=False,
                        logger=None
                    )
                except Exception:
                    print(f"     ⚠ Audio export failed for scene {scene['id']}")
            else:
                # Export without audio
                clip.write_videofile(
                    str(clip_path),
                    codec='libx264',
                    audio=False,
                    verbose=False,
                    logger=None,
                    preset='fast',
                    fps=15,
                    write_logfile=False
                )
            
            clip.close()
            return True
            
        except Exception as e:
            print(f"     ✗ Clip export failed for scene {scene['id']}: {str(e)[:30]}")
            try:
                if 'clip' in locals():
                    clip.close()
            except:
                pass
            return False
    
    def generate_clip_thumbnail(self, video, scene):
        """Generate thumbnail for scene clip."""
        try:
            middle_time = (scene['start'] + scene['end']) / 2
            frame = video.get_frame(middle_time)
            
            # Resize for web display
            thumb_height = 90
            aspect_ratio = frame.shape[1] / frame.shape[0]
            thumb_width = int(thumb_height * aspect_ratio)
            thumb = cv2.resize(frame, (thumb_width, thumb_height))
            
            # Save thumbnail
            thumb_filename = f"thumb_{scene['id']:04d}.jpg"
            thumb_path = self.thumbnails_dir / thumb_filename
            thumb_bgr = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(thumb_path), thumb_bgr)
            
            return True
            
        except Exception as e:
            print(f"     ⚠ Thumbnail generation failed for scene {scene['id']}: {str(e)[:30]}")
            return False
    
    def analyze_clip_audio(self, scene, has_audio=True):
        """Analyze audio for individual clip."""
        if not has_audio:
            return self.waveform_renderer.generate_silent_waveform(scene['duration'], 100)
        
        audio_filename = f"scene_{scene['id']:04d}.wav"
        audio_path = self.audio_dir / audio_filename
        
        if not audio_path.exists():
            return self.waveform_renderer.generate_silent_waveform(scene['duration'], 100)
        
        try:
            # Generate waveform
            waveform_data = self.waveform_renderer.generate_stereo_waveform(str(audio_path))
            
            # Generate spectrogram
            spectrogram_data = self.spectrogram_analyzer.generate_spectrogram(str(audio_path))
            
            return {
                'waveform': waveform_data,
                'spectrogram': spectrogram_data
            }
            
        except Exception as e:
            print(f"     ⚠ Audio analysis failed for scene {scene['id']}: {str(e)[:30]}")
            return self.waveform_renderer.generate_silent_waveform(scene['duration'], 100)
    
    # PHASE 2: PREMIERE PRO-STYLE TIMELINE INTERFACE
    def phase2_create_premiere_timeline(self, zoom_level='fit_all'):
        """
        PHASE 2: Create Premiere Pro-style timeline interface.
        Professional timeline with proportional clips, waveforms, and controls.
        """
        print("\n" + "="*80)
        print("🎬 PHASE 2: PREMIERE PRO-STYLE TIMELINE INTERFACE")
        print("="*80)
        
        if not self.clips_metadata:
            print("   ✗ No clips metadata available. Run Phase 1 first.")
            return False
        
        print(f"\n📐 Creating proportional timeline with {len(self.clips_metadata)} clips...")
        
        # Calculate clip widths for timeline
        timeline_data = self.timeline_engine.calculate_clip_widths(
            self.clips_metadata,
            timeline_width_px=1200,
            zoom_level=self.timeline_engine.ZOOM_LEVELS.get(zoom_level, 1.0)
        )
        
        print(f"   ✓ Timeline calculated: zoom={zoom_level}, clips={len(timeline_data)}")
        
        # Create HTML interface
        html_success = self.create_premiere_html_interface(timeline_data, zoom_level)
        
        if html_success:
            print("   ✓ Premiere Pro-style interface created")
            return True
        else:
            print("   ✗ Interface creation failed")
            return False
    
    def create_premiere_html_interface(self, timeline_data, zoom_level):
        """Create the complete Premiere Pro-style HTML interface."""
        print("\n🌐 Generating professional HTML interface...")
        
        try:
            # Prepare data for interface
            interface_data = {
                'clips': self.clips_metadata,
                'timeline': timeline_data,
                'zoom_level': zoom_level,
                'zoom_levels': self.timeline_engine.ZOOM_LEVELS,
                'project_info': {
                    'film_name': Path(self.film_path).name,
                    'total_clips': len(self.clips_metadata),
                    'total_duration': sum(clip['duration'] for clip in self.clips_metadata),
                    'has_audio': self.clips_metadata[0].get('has_audio', False) if self.clips_metadata else False,
                    'output_dir': str(self.output_dir.name),
                    'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            html_content = self.generate_premiere_html_template(interface_data)
            
            # Save HTML file
            html_path = self.output_dir / "premiere_interface.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"   ✓ Interface saved: {html_path}")
            return True
            
        except Exception as e:
            print(f"   ✗ Interface generation failed: {str(e)[:50]}")
            return False
    
    def generate_premiere_html_template(self, data):
        """Generate the complete Premiere Pro-style HTML template."""
        
        # Calculate timeline stats
        total_duration = data['project_info']['total_duration']
        timeline_width = sum(clip['width_px'] for clip in data['timeline'])
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premiere Pro-Style Archival Analysis - {data['project_info']['film_name']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1e1e1e;
            color: #cccccc;
            overflow-x: hidden;
        }}
        
        /* MAIN LAYOUT */
        .premiere-container {{
            display: grid;
            grid-template-areas: 
                "monitor spectrogram"
                "timeline timeline";
            grid-template-rows: 350px 1fr;
            grid-template-columns: 1fr 400px;
            height: 100vh;
            gap: 2px;
            background: #2d2d30;
        }}
        
        /* MONITOR PANEL */
        .monitor-panel {{
            grid-area: monitor;
            background: #252526;
            border: 1px solid #3e3e42;
            display: flex;
            flex-direction: column;
        }}
        
        .monitor-header {{
            background: #2d2d30;
            padding: 8px 12px;
            border-bottom: 1px solid #3e3e42;
            font-weight: bold;
            font-size: 12px;
            color: #cccccc;
        }}
        
        .video-monitor {{
            flex: 1;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}
        
        #monitor-video {{
            max-width: 100%;
            max-height: 100%;
            background: #000;
        }}
        
        .monitor-controls {{
            background: #2d2d30;
            padding: 8px;
            border-top: 1px solid #3e3e42;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .transport-controls {{
            display: flex;
            gap: 4px;
        }}
        
        .transport-btn {{
            background: #007ACC;
            border: none;
            color: white;
            padding: 6px 8px;
            border-radius: 2px;
            cursor: pointer;
            font-size: 12px;
        }}
        
        .transport-btn:hover {{
            background: #1f9cf0;
        }}
        
        .timecode {{
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            padding: 4px 8px;
            border-radius: 2px;
            min-width: 100px;
            text-align: center;
            font-size: 12px;
        }}
        
        .scrub-bar {{
            flex: 1;
            height: 6px;
            background: #3e3e42;
            border-radius: 3px;
            position: relative;
            cursor: pointer;
            margin: 0 8px;
        }}
        
        .scrub-progress {{
            height: 100%;
            background: #007ACC;
            border-radius: 3px;
            width: 0%;
            transition: width 0.1s;
        }}
        
        .scrub-handle {{
            position: absolute;
            top: -3px;
            width: 12px;
            height: 12px;
            background: #007ACC;
            border-radius: 50%;
            cursor: pointer;
            transform: translateX(-50%);
        }}
        
        /* AUDIO LEVEL METERS */
        .audio-levels {{
            display: flex;
            gap: 4px;
            align-items: center;
        }}
        
        .level-meter {{
            width: 60px;
            height: 16px;
            background: #1e1e1e;
            border-radius: 2px;
            overflow: hidden;
            position: relative;
        }}
        
        .level-bar {{
            height: 100%;
            background: linear-gradient(to right, #00ff00 0%, #ffff00 70%, #ff0000 90%);
            width: 0%;
            transition: width 0.1s;
        }}
        
        .level-label {{
            font-size: 10px;
            color: #999;
            min-width: 8px;
        }}
        
        /* SPECTROGRAM PANEL */
        .spectrogram-panel {{
            grid-area: spectrogram;
            background: #252526;
            border: 1px solid #3e3e42;
            display: flex;
            flex-direction: column;
        }}
        
        .spectrogram-content {{
            flex: 1;
            position: relative;
            background: #1e1e1e;
            margin: 8px;
            border-radius: 4px;
        }}
        
        #spectrogram-canvas {{
            width: 100%;
            height: 100%;
            border-radius: 4px;
        }}
        
        .freq-axis {{
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            width: 40px;
            background: rgba(45, 45, 48, 0.8);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 4px 2px;
            font-size: 9px;
            color: #999;
        }}
        
        /* TIMELINE PANEL */
        .timeline-panel {{
            grid-area: timeline;
            background: #252526;
            border: 1px solid #3e3e42;
            display: flex;
            flex-direction: column;
            min-height: 300px;
        }}
        
        .timeline-header {{
            background: #2d2d30;
            padding: 8px 12px;
            border-bottom: 1px solid #3e3e42;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .timeline-title {{
            font-weight: bold;
            font-size: 12px;
        }}
        
        .zoom-controls {{
            display: flex;
            gap: 4px;
        }}
        
        .zoom-btn {{
            background: #3e3e42;
            border: none;
            color: #cccccc;
            padding: 4px 8px;
            border-radius: 2px;
            cursor: pointer;
            font-size: 10px;
        }}
        
        .zoom-btn:hover {{
            background: #007ACC;
        }}
        
        .zoom-btn.active {{
            background: #007ACC;
        }}
        
        .timeline-ruler {{
            background: #2d2d30;
            height: 30px;
            border-bottom: 1px solid #3e3e42;
            position: relative;
            overflow: hidden;
        }}
        
        .timeline-content {{
            flex: 1;
            overflow-x: auto;
            overflow-y: hidden;
            background: #1e1e1e;
            position: relative;
        }}
        
        .timeline-track {{
            height: 200px;
            border-bottom: 1px solid #3e3e42;
            position: relative;
            display: flex;
            align-items: stretch;
        }}
        
        /* CLIPS IN TIMELINE */
        .timeline-clip {{
            background: #007ACC;
            border: 1px solid #1f9cf0;
            border-radius: 2px;
            display: flex;
            flex-direction: column;
            cursor: pointer;
            position: relative;
            transition: all 0.2s;
            min-height: 100%;
        }}
        
        .timeline-clip:hover {{
            border-color: #ffffff;
            box-shadow: 0 0 8px rgba(31, 156, 240, 0.5);
        }}
        
        .timeline-clip.selected {{
            border-color: #ffffff;
            box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
        }}
        
        .clip-thumbnail {{
            height: 60px;
            background: #000;
            border-radius: 2px 2px 0 0;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .clip-thumbnail img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: cover;
        }}
        
        .clip-info {{
            padding: 4px;
            background: rgba(0, 122, 204, 0.8);
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 30px;
        }}
        
        .clip-duration {{
            font-size: 10px;
            font-weight: bold;
            text-align: center;
            color: white;
        }}
        
        .clip-timecode {{
            font-size: 8px;
            color: rgba(255, 255, 255, 0.8);
            text-align: center;
            font-family: 'Courier New', monospace;
        }}
        
        /* WAVEFORMS IN TIMELINE */
        .clip-waveform {{
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 2px;
            min-height: 60px;
        }}
        
        .waveform-channel {{
            flex: 1;
            position: relative;
            margin: 1px 0;
        }}
        
        .waveform-canvas {{
            width: 100%;
            height: 100%;
        }}
        
        .waveform-label {{
            position: absolute;
            left: 2px;
            top: 2px;
            font-size: 8px;
            color: rgba(255, 255, 255, 0.6);
            background: rgba(0, 0, 0, 0.5);
            padding: 1px 3px;
            border-radius: 1px;
        }}
        
        /* DISPLAY MODES */
        .clip-minimal {{
            background: #555;
            justify-content: center;
            align-items: center;
        }}
        
        .clip-thumbnail-only .clip-waveform {{
            display: none;
        }}
        
        /* RESPONSIVE DESIGN */
        @media (max-width: 1200px) {{
            .premiere-container {{
                grid-template-columns: 1fr 300px;
            }}
        }}
        
        @media (max-width: 900px) {{
            .premiere-container {{
                grid-template-areas: 
                    "monitor"
                    "spectrogram"
                    "timeline";
                grid-template-rows: 250px 150px 1fr;
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="premiere-container">
        <!-- MONITOR PANEL -->
        <div class="monitor-panel">
            <div class="monitor-header">
                📺 Monitor - {data['project_info']['film_name']}
            </div>
            <div class="video-monitor">
                <video id="monitor-video" controls>
                    <source src="" type="video/mp4">
                    Select a clip from timeline to preview
                </video>
            </div>
            <div class="monitor-controls">
                <div class="transport-controls">
                    <button class="transport-btn" id="btn-prev">⏮</button>
                    <button class="transport-btn" id="btn-play">▶</button>
                    <button class="transport-btn" id="btn-next">⏭</button>
                    <button class="transport-btn" id="btn-stop">⏹</button>
                </div>
                <div class="timecode" id="current-timecode">00:00:00:00</div>
                <div class="scrub-bar" id="scrub-bar">
                    <div class="scrub-progress" id="scrub-progress"></div>
                    <div class="scrub-handle" id="scrub-handle"></div>
                </div>
                <div class="audio-levels">
                    <div class="level-label">L</div>
                    <div class="level-meter">
                        <div class="level-bar" id="level-left"></div>
                    </div>
                    <div class="level-label">R</div>
                    <div class="level-meter">
                        <div class="level-bar" id="level-right"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- SPECTROGRAM PANEL -->
        <div class="spectrogram-panel">
            <div class="monitor-header">
                🎵 Audio Spectrogram
            </div>
            <div class="spectrogram-content">
                <canvas id="spectrogram-canvas"></canvas>
                <div class="freq-axis">
                    <div>8kHz</div>
                    <div>4kHz</div>
                    <div>2kHz</div>
                    <div>1kHz</div>
                    <div>500Hz</div>
                    <div>0Hz</div>
                </div>
            </div>
        </div>
        
        <!-- TIMELINE PANEL -->
        <div class="timeline-panel">
            <div class="timeline-header">
                <div class="timeline-title">
                    🎬 Timeline - {len(data['clips'])} Clips - {data['project_info']['total_duration']:.1f}s Total
                </div>
                <div class="zoom-controls">
                    <button class="zoom-btn {'active' if data['zoom_level'] == 'fit_all' else ''}" data-zoom="fit_all">Fit All</button>
                    <button class="zoom-btn {'active' if data['zoom_level'] == '1_minute' else ''}" data-zoom="1_minute">1 Min</button>
                    <button class="zoom-btn {'active' if data['zoom_level'] == '30_seconds' else ''}" data-zoom="30_seconds">30s</button>
                    <button class="zoom-btn {'active' if data['zoom_level'] == '10_seconds' else ''}" data-zoom="10_seconds">10s</button>
                    <button class="zoom-btn {'active' if data['zoom_level'] == '1_second' else ''}" data-zoom="1_second">1s</button>
                </div>
            </div>
            <div class="timeline-ruler" id="timeline-ruler">
                <!-- Time markers will be generated by JavaScript -->
            </div>
            <div class="timeline-content" id="timeline-content">
                <div class="timeline-track" id="video-track">
                    {self.generate_timeline_clips_html(data['clips'], data['timeline'])}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Project data
        const projectData = {json.dumps(data, indent=8)};
        
        // Global state
        let currentClip = null;
        let isPlaying = false;
        let currentZoom = '{data['zoom_level']}';
        
        // DOM elements
        const monitorVideo = document.getElementById('monitor-video');
        const currentTimecode = document.getElementById('current-timecode');
        const scrubProgress = document.getElementById('scrub-progress');
        const scrubHandle = document.getElementById('scrub-handle');
        const levelLeft = document.getElementById('level-left');
        const levelRight = document.getElementById('level-right');
        const spectrogramCanvas = document.getElementById('spectrogram-canvas');
        
        // Initialize interface
        document.addEventListener('DOMContentLoaded', function() {{
            initializeInterface();
            setupEventListeners();
            drawSpectrogram();
            generateTimelineRuler();
        }});
        
        function initializeInterface() {{
            console.log('Initializing Premiere-style interface...');
            console.log('Project:', projectData.project_info);
            
            // Set initial state
            updateTimecode(0);
            updateAudioLevels(0, 0);
        }}
        
        function setupEventListeners() {{
            // Transport controls
            document.getElementById('btn-play').addEventListener('click', togglePlayback);
            document.getElementById('btn-stop').addEventListener('click', stopPlayback);
            document.getElementById('btn-prev').addEventListener('click', previousClip);
            document.getElementById('btn-next').addEventListener('click', nextClip);
            
            // Scrub bar
            const scrubBar = document.getElementById('scrub-bar');
            scrubBar.addEventListener('click', handleScrubClick);
            
            // Timeline clips
            const timelineClips = document.querySelectorAll('.timeline-clip');
            timelineClips.forEach(clip => {{
                clip.addEventListener('click', () => loadClip(clip.dataset.clipId));
            }});
            
            // Zoom controls
            const zoomButtons = document.querySelectorAll('.zoom-btn');
            zoomButtons.forEach(btn => {{
                btn.addEventListener('click', () => changeZoom(btn.dataset.zoom));
            }});
            
            // Video events
            monitorVideo.addEventListener('timeupdate', updatePlaybackPosition);
            monitorVideo.addEventListener('loadedmetadata', updateVideoInfo);
        }}
        
        function loadClip(clipId) {{
            const clip = projectData.clips.find(c => c.id == clipId);
            if (!clip) return;
            
            currentClip = clip;
            
            // Update monitor
            const videoPath = `working/${{clip.files.video}}`;
            monitorVideo.src = videoPath;
            
            // Update UI
            updateClipSelection(clipId);
            updateSpectrogram(clip);
            
            console.log('Loaded clip:', clip.id, clip.start_timecode);
        }}
        
        function updateClipSelection(clipId) {{
            // Remove previous selection
            document.querySelectorAll('.timeline-clip').forEach(clip => {{
                clip.classList.remove('selected');
            }});
            
            // Add selection to current clip
            const clipElement = document.querySelector(`[data-clip-id="${{clipId}}"]`);
            if (clipElement) {{
                clipElement.classList.add('selected');
                clipElement.scrollIntoView({{ behavior: 'smooth', inline: 'center' }});
            }}
        }}
        
        function togglePlayback() {{
            if (isPlaying) {{
                monitorVideo.pause();
                document.getElementById('btn-play').innerHTML = '▶';
            }} else {{
                monitorVideo.play();
                document.getElementById('btn-play').innerHTML = '⏸';
            }}
            isPlaying = !isPlaying;
        }}
        
        function stopPlayback() {{
            monitorVideo.pause();
            monitorVideo.currentTime = 0;
            document.getElementById('btn-play').innerHTML = '▶';
            isPlaying = false;
        }}
        
        function updatePlaybackPosition() {{
            if (!currentClip || !monitorVideo.duration) return;
            
            const progress = monitorVideo.currentTime / monitorVideo.duration;
            const currentSeconds = monitorVideo.currentTime;
            
            // Update scrub bar
            scrubProgress.style.width = `${{progress * 100}}%`;
            scrubHandle.style.left = `${{progress * 100}}%`;
            
            // Update timecode
            updateTimecode(currentSeconds);
            
            // Simulate audio levels (in real implementation, analyze audio)
            const leftLevel = Math.random() * 80 + 10;
            const rightLevel = Math.random() * 80 + 10;
            updateAudioLevels(leftLevel, rightLevel);
        }}
        
        function updateTimecode(seconds) {{
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            const frames = Math.floor((seconds % 1) * 24);
            
            currentTimecode.textContent = 
                `${{hours.toString().padStart(2, '0')}}:` +
                `${{minutes.toString().padStart(2, '0')}}:` +
                `${{secs.toString().padStart(2, '0')}}:` +
                `${{frames.toString().padStart(2, '0')}}`;
        }}
        
        function updateAudioLevels(leftDb, rightDb) {{
            levelLeft.style.width = `${{Math.max(0, Math.min(100, leftDb))}}%`;
            levelRight.style.width = `${{Math.max(0, Math.min(100, rightDb))}}%`;
        }}
        
        function updateSpectrogram(clip) {{
            if (!clip.audio_analysis || !clip.audio_analysis.spectrogram) return;
            
            const canvas = spectrogramCanvas;
            const ctx = canvas.getContext('2d');
            const specData = clip.audio_analysis.spectrogram;
            
            // Resize canvas
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            
            // Draw spectrogram
            drawSpectrogramData(ctx, specData.spectrogram, canvas.width, canvas.height);
        }}
        
        function drawSpectrogramData(ctx, spectrogramData, width, height) {{
            const freqBins = spectrogramData.length;
            const timeBins = spectrogramData[0] ? spectrogramData[0].length : 0;
            
            if (freqBins === 0 || timeBins === 0) return;
            
            const cellWidth = width / timeBins;
            const cellHeight = height / freqBins;
            
            for (let f = 0; f < freqBins; f++) {{
                for (let t = 0; t < timeBins; t++) {{
                    const magnitude = spectrogramData[freqBins - 1 - f][t]; // Flip Y axis
                    const intensity = Math.max(0, Math.min(1, (magnitude + 80) / 80)); // Normalize dB
                    
                    // Color mapping: blue (low) to red (high)
                    const hue = (1 - intensity) * 240; // Blue to red
                    const saturation = 100;
                    const lightness = intensity * 50 + 10;
                    
                    ctx.fillStyle = `hsl(${{hue}}, ${{saturation}}%, ${{lightness}}%)`;
                    ctx.fillRect(t * cellWidth, f * cellHeight, cellWidth, cellHeight);
                }}
            }}
        }}
        
        function generateTimelineRuler() {{
            const ruler = document.getElementById('timeline-ruler');
            const totalDuration = projectData.project_info.total_duration;
            const timelineWidth = {timeline_width};
            
            ruler.innerHTML = '';
            
            // Generate time markers based on zoom level
            const markers = generateTimeMarkers(totalDuration, currentZoom);
            
            markers.forEach(marker => {{
                const markerElement = document.createElement('div');
                markerElement.style.position = 'absolute';
                markerElement.style.left = `${{(marker.time / totalDuration) * timelineWidth}}px`;
                markerElement.style.top = '0';
                markerElement.style.width = '1px';
                markerElement.style.height = '100%';
                markerElement.style.background = '#666';
                markerElement.style.fontSize = '10px';
                markerElement.style.color = '#ccc';
                markerElement.innerHTML = `<div style="margin-top: 2px; margin-left: 2px;">${{marker.label}}</div>`;
                
                ruler.appendChild(markerElement);
            }});
        }}
        
        function generateTimeMarkers(totalDuration, zoomLevel) {{
            const markers = [];
            let interval = 60; // Default 1 minute intervals
            
            switch(zoomLevel) {{
                case 'fit_all': interval = Math.max(60, totalDuration / 10); break;
                case '1_minute': interval = 10; break;
                case '30_seconds': interval = 5; break;
                case '10_seconds': interval = 1; break;
                case '1_second': interval = 0.2; break;
            }}
            
            for (let t = 0; t <= totalDuration; t += interval) {{
                const minutes = Math.floor(t / 60);
                const seconds = Math.floor(t % 60);
                markers.push({{
                    time: t,
                    label: `${{minutes}}:${{seconds.toString().padStart(2, '0')}}`
                }});
            }}
            
            return markers;
        }}
        
        function changeZoom(newZoom) {{
            if (newZoom === currentZoom) return;
            
            currentZoom = newZoom;
            
            // Update active button
            document.querySelectorAll('.zoom-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.dataset.zoom === newZoom);
            }});
            
            // Reload interface with new zoom level
            window.location.href = `premiere_interface.html?zoom=${{newZoom}}`;
        }}
        
        function previousClip() {{
            if (!currentClip) return;
            const currentIndex = projectData.clips.findIndex(c => c.id === currentClip.id);
            if (currentIndex > 0) {{
                loadClip(projectData.clips[currentIndex - 1].id);
            }}
        }}
        
        function nextClip() {{
            if (!currentClip) return;
            const currentIndex = projectData.clips.findIndex(c => c.id === currentClip.id);
            if (currentIndex < projectData.clips.length - 1) {{
                loadClip(projectData.clips[currentIndex + 1].id);
            }}
        }}
        
        function handleScrubClick(event) {{
            if (!monitorVideo.duration) return;
            
            const rect = event.currentTarget.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const progress = x / rect.width;
            
            monitorVideo.currentTime = progress * monitorVideo.duration;
        }}
        
        // Auto-load first clip on startup
        setTimeout(() => {{
            if (projectData.clips.length > 0) {{
                loadClip(projectData.clips[0].id);
            }}
        }}, 500);
    </script>
</body>
</html>'''
    
    def generate_timeline_clips_html(self, clips, timeline_data):
        """Generate HTML for timeline clips with proportional widths."""
        if not clips or not timeline_data:
            return '<div class="no-clips">No clips available</div>'
        
        html_parts = []
        
        for i, (clip, timeline_clip) in enumerate(zip(clips, timeline_data)):
            # Determine display mode based on clip width
            display_mode = timeline_clip['display_mode']
            width_px = timeline_clip['width_px']
            
            # CSS classes based on display mode
            css_classes = f"timeline-clip clip-{display_mode}"
            
            # Generate clip HTML based on display mode
            if display_mode == 'minimal':
                # Very narrow clips - just colored bar with duration
                clip_html = f'''
                <div class="{css_classes}" data-clip-id="{clip['id']}" 
                     style="width: {width_px}px; min-width: {width_px}px;">
                    <div class="clip-info">
                        <div class="clip-duration">{clip['duration']:.1f}s</div>
                    </div>
                </div>'''
                
            elif display_mode == 'thumbnail_only':
                # Medium clips - thumbnail but no waveform
                clip_html = f'''
                <div class="{css_classes}" data-clip-id="{clip['id']}" 
                     style="width: {width_px}px; min-width: {width_px}px;">
                    <div class="clip-thumbnail">
                        <img src="working/{clip['files']['thumbnail']}" alt="Scene {clip['id']}">
                    </div>
                    <div class="clip-info">
                        <div class="clip-duration">{clip['duration']:.1f}s</div>
                        <div class="clip-timecode">{clip['start_timecode']}</div>
                    </div>
                </div>'''
                
            else:  # 'full' mode
                # Wide clips - thumbnail + waveform + all details
                waveform_html = self.generate_waveform_html(clip, width_px)
                
                clip_html = f'''
                <div class="{css_classes}" data-clip-id="{clip['id']}" 
                     style="width: {width_px}px; min-width: {width_px}px;">
                    <div class="clip-thumbnail">
                        <img src="working/{clip['files']['thumbnail']}" alt="Scene {clip['id']}">
                    </div>
                    <div class="clip-info">
                        <div class="clip-duration">{clip['duration']:.1f}s</div>
                        <div class="clip-timecode">{clip['start_timecode']}</div>
                    </div>
                    <div class="clip-waveform">
                        {waveform_html}
                    </div>
                </div>'''
            
            html_parts.append(clip_html)
        
        return ''.join(html_parts)
    
    def generate_waveform_html(self, clip, width_px):
        """Generate waveform visualization HTML for timeline clips."""
        if not clip.get('audio_analysis') or not clip['audio_analysis'].get('waveform'):
            return '<div class="no-waveform">No audio</div>'
        
        waveform_data = clip['audio_analysis']['waveform']
        left_waveform = waveform_data.get('left_waveform', [])
        right_waveform = waveform_data.get('right_waveform', [])
        
        if not left_waveform or not right_waveform:
            return '<div class="no-waveform">No audio</div>'
        
        # Create canvas elements for waveforms
        canvas_id_left = f"waveform_left_{clip['id']}"
        canvas_id_right = f"waveform_right_{clip['id']}"
        
        # Inline JavaScript to draw waveforms
        waveform_script = f'''
        <div class="waveform-channel">
            <div class="waveform-label">L</div>
            <canvas class="waveform-canvas" id="{canvas_id_left}" 
                    width="{int(width_px-4)}" height="25"></canvas>
        </div>
        <div class="waveform-channel">
            <div class="waveform-label">R</div>
            <canvas class="waveform-canvas" id="{canvas_id_right}" 
                    width="{int(width_px-4)}" height="25"></canvas>
        </div>
        <script>
            // Draw left channel waveform
            (function() {{
                const canvas = document.getElementById('{canvas_id_left}');
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                const waveform = {left_waveform};
                const width = canvas.width;
                const height = canvas.height;
                const centerY = height / 2;
                
                ctx.strokeStyle = '#00ff88';
                ctx.lineWidth = 1;
                ctx.beginPath();
                
                for (let i = 0; i < waveform.length; i++) {{
                    const x = (i / (waveform.length - 1)) * width;
                    const y = centerY + (waveform[i] * centerY * 0.8);
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }}
                ctx.stroke();
            }})();
            
            // Draw right channel waveform
            (function() {{
                const canvas = document.getElementById('{canvas_id_right}');
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                const waveform = {right_waveform};
                const width = canvas.width;
                const height = canvas.height;
                const centerY = height / 2;
                
                ctx.strokeStyle = '#ff8800';
                ctx.lineWidth = 1;
                ctx.beginPath();
                
                for (let i = 0; i < waveform.length; i++) {{
                    const x = (i / (waveform.length - 1)) * width;
                    const y = centerY + (waveform[i] * centerY * 0.8);
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }}
                ctx.stroke();
            }})();
        </script>
        '''
        
        return waveform_script
    
    # PHASE 3: ENHANCED ANALYSIS
    def phase3_enhanced_analysis(self):
        """
        PHASE 3: Perform enhanced analysis on pre-generated clips.
        """
        print("\n" + "="*80)
        print("🔬 PHASE 3: ENHANCED ANALYSIS")
        print("="*80)
        
        if not self.clips_metadata:
            print("   ✗ No clips metadata available. Run Phase 1 first.")
            return False
        
        print(f"\n📊 Analyzing {len(self.clips_metadata)} clips...")
        
        # Analyze overall project statistics
        project_stats = self.calculate_project_statistics()
        
        # Generate enhanced metadata
        enhanced_metadata = self.generate_enhanced_metadata(project_stats)
        
        # Save enhanced analysis
        analysis_path = self.analysis_dir / "enhanced_analysis.json"
        with open(analysis_path, 'w') as f:
            json.dump(enhanced_metadata, f, indent=2)
        
        print(f"   ✓ Enhanced analysis saved: {analysis_path}")
        return True
    
    def calculate_project_statistics(self):
        """Calculate comprehensive project statistics."""
        if not self.clips_metadata:
            return {}
        
        durations = [clip['duration'] for clip in self.clips_metadata]
        
        # Audio level statistics
        audio_levels = []
        for clip in self.clips_metadata:
            if clip.get('audio_analysis') and clip['audio_analysis'].get('waveform'):
                levels = clip['audio_analysis']['waveform'].get('levels', {})
                if levels:
                    audio_levels.append(levels)
        
        stats = {
            'total_clips': len(self.clips_metadata),
            'total_duration': sum(durations),
            'duration_stats': {
                'mean': float(np.mean(durations)),
                'median': float(np.median(durations)),
                'std': float(np.std(durations)),
                'min': float(np.min(durations)),
                'max': float(np.max(durations))
            },
            'audio_stats': self.calculate_audio_statistics(audio_levels) if audio_levels else {},
            'generation_info': {
                'timestamp': datetime.now().isoformat(),
                'film_path': str(self.film_path),
                'output_dir': str(self.output_dir)
            }
        }
        
        return stats
    
    def calculate_audio_statistics(self, audio_levels):
        """Calculate audio-related statistics."""
        if not audio_levels:
            return {}
        
        left_rms = [level.get('left_rms', 0) for level in audio_levels]
        right_rms = [level.get('right_rms', 0) for level in audio_levels]
        left_db = [level.get('left_db', -120) for level in audio_levels]
        right_db = [level.get('right_db', -120) for level in audio_levels]
        
        return {
            'left_channel': {
                'rms_mean': float(np.mean(left_rms)),
                'rms_std': float(np.std(left_rms)),
                'db_mean': float(np.mean(left_db)),
                'db_range': [float(np.min(left_db)), float(np.max(left_db))]
            },
            'right_channel': {
                'rms_mean': float(np.mean(right_rms)),
                'rms_std': float(np.std(right_rms)),
                'db_mean': float(np.mean(right_db)),
                'db_range': [float(np.min(right_db)), float(np.max(right_db))]
            }
        }
    
    def generate_enhanced_metadata(self, project_stats):
        """Generate comprehensive enhanced metadata."""
        return {
            'project_info': {
                'name': Path(self.film_path).name,
                'analysis_type': 'Premiere Pro-Style Archival Analysis',
                'generation_time': datetime.now().isoformat(),
                'workflow': 'clips-first'
            },
            'statistics': project_stats,
            'clips_metadata': self.clips_metadata,
            'technical_info': {
                'scene_detection_threshold': 30.0,
                'audio_sample_rate': self.waveform_renderer.sample_rate,
                'spectrogram_settings': {
                    'n_fft': self.spectrogram_analyzer.n_fft,
                    'hop_length': self.spectrogram_analyzer.hop_length,
                    'n_mels': 64
                }
            },
            'directory_structure': {
                'working': str(self.working_dir.relative_to(self.output_dir)),
                'clips': str(self.clips_dir.relative_to(self.output_dir)),
                'thumbnails': str(self.thumbnails_dir.relative_to(self.output_dir)),
                'audio': str(self.audio_dir.relative_to(self.output_dir)),
                'analysis': str(self.analysis_dir.relative_to(self.output_dir))
            }
        }
    
    # COMPLETE PIPELINE
    def run_complete_pipeline(self, threshold=30.0, max_scenes=None, force_audio=True, zoom_level='fit_all'):
        """
        Run the complete clips-first Premiere Pro-style analysis pipeline.
        """
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  PREMIERE PRO-STYLE ARCHIVAL ANALYSIS PIPELINE              ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Workflow: Clips-First → Timeline → Analysis                ║
        ║  Max scenes: {'All' if not max_scenes else str(max_scenes):<49} ║
        ║  Audio: {'Included' if force_audio else 'Video only':<54} ║
        ║  Timeline zoom: {zoom_level:<46} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Phase 1: Generate all clips first
        phase1_success = self.phase1_generate_all_clips(
            threshold=threshold,
            max_scenes=max_scenes,
            force_audio=force_audio
        )
        
        if not phase1_success:
            print("\n❌ Phase 1 failed - cannot continue")
            return False
        
        # Phase 2: Create Premiere Pro-style timeline interface
        phase2_success = self.phase2_create_premiere_timeline(zoom_level=zoom_level)
        
        if not phase2_success:
            print("\n❌ Phase 2 failed - continuing with Phase 3")
        
        # Phase 3: Enhanced analysis
        phase3_success = self.phase3_enhanced_analysis()
        
        if not phase3_success:
            print("\n⚠ Phase 3 failed - basic analysis still available")
        
        # Cleanup
        self.cleanup_temp_files()
        
        success_phases = sum([phase1_success, phase2_success, phase3_success])
        
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  PIPELINE COMPLETE! ({success_phases}/3 phases successful)                 ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  📁 Output: {str(self.output_dir.name):<49} ║
        ║  🎬 Interface: premiere_interface.html                       ║
        ║  📊 Analysis: enhanced_analysis.json                         ║
        ║                                                              ║
        ║  Open premiere_interface.html in browser for professional    ║
        ║  Premiere Pro-style timeline with:                          ║
        ║  • Proportional clip widths                                  ║
        ║  • Stereo waveforms (L/R channels)                          ║
        ║  • Audio spectrogram panel                                   ║
        ║  • Professional monitor controls                             ║
        ║  • Multi-zoom timeline navigation                            ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        return success_phases >= 2  # Success if at least Phase 1 and 2 work
    
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


def main():
    """Main entry point for Premiere Pro-style archival analysis."""
    import sys
    
    if len(sys.argv) < 2:
        print("""
        PREMIERE PRO-STYLE ARCHIVAL ANALYSIS ENGINE - Usage:
        
        1. Basic analysis with clips-first workflow:
           python premiere_style_archival_engine.py <video.mp4>
        
        2. Analysis with custom parameters:
           python premiere_style_archival_engine.py <video.mp4> --max-scenes 100 --zoom fit_all
        
        3. Analysis without audio:
           python premiere_style_archival_engine.py <video.mp4> --no-audio
        
        4. Custom zoom levels:
           python premiere_style_archival_engine.py <video.mp4> --zoom 1_minute
           
        Zoom options: fit_all, 1_minute, 30_seconds, 10_seconds, 1_second
        
        Features:
        ✨ Clips-first workflow: Generate all clips with audio FIRST
        📐 Proportional timeline: Clip widths match actual durations  
        🎵 Stereo waveforms: Left/Right channel visualization
        📊 Audio spectrogram: Real-time frequency analysis
        🎬 Monitor panel: Professional playback controls
        🔍 Multi-zoom timeline: From fit-all to 1-second precision
        
        Output:
        📁 Timestamped output directory with all assets
        🌐 premiere_interface.html - Professional timeline interface
        📊 enhanced_analysis.json - Comprehensive metadata
        🎞️  working/clips/ - All scene clips with audio
        🖼️  working/thumbnails/ - Scene preview images
        🎵 working/audio/ - Extracted audio files
        """)
        return
    
    # Parse arguments
    film_path = sys.argv[1]
    max_scenes = None
    force_audio = True
    zoom_level = 'fit_all'
    threshold = 30.0
    
    # Parse optional arguments
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--max-scenes' and i + 1 < len(args):
            max_scenes = int(args[i + 1])
            i += 2
        elif args[i] == '--zoom' and i + 1 < len(args):
            zoom_level = args[i + 1]
            i += 2
        elif args[i] == '--no-audio':
            force_audio = False
            i += 1
        elif args[i] == '--threshold' and i + 1 < len(args):
            threshold = float(args[i + 1])
            i += 2
        else:
            i += 1
    
    # Validate zoom level
    valid_zooms = ['fit_all', '1_minute', '30_seconds', '10_seconds', '1_second']
    if zoom_level not in valid_zooms:
        print(f"⚠ Invalid zoom level: {zoom_level}")
        print(f"   Valid options: {', '.join(valid_zooms)}")
        zoom_level = 'fit_all'
    
    # Create and run engine
    try:
        engine = PremiereStyleArchivalEngine(film_path)
        success = engine.run_complete_pipeline(
            threshold=threshold,
            max_scenes=max_scenes,
            force_audio=force_audio,
            zoom_level=zoom_level
        )
        
        if not success:
            print("\n❌ Pipeline failed - check error messages above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠ Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
