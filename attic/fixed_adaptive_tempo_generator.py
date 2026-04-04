#!/usr/bin/env python3
"""
Fixed Adaptive Tempo Music Video Generator
Handles numpy formatting issues and provides robust tempo change detection
"""

import warnings
warnings.filterwarnings("ignore", message="VideoManager is deprecated")

import librosa
import numpy as np
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import random
import json
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d
import contextlib
import io

class FixedAdaptiveTempoGenerator:
    def __init__(self, video_path, audio_path, output_path="adaptive_tempo_video.mp4"):
        self.video_path = video_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.scenes = []
        self.beat_times = []
        self.tempo_segments = []
        
    def safe_float(self, value):
        """Safely convert numpy values to Python float"""
        try:
            return float(value)
        except:
            return 0.0
    
    def detect_scenes(self, threshold=30.0, min_scene_len=1.0):
        """Detect scenes and sort chronologically"""
        print("🎬 Detecting scenes in video...")
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                video_manager = VideoManager([self.video_path])
                scene_manager = SceneManager()
                scene_manager.add_detector(ContentDetector(threshold=threshold))
                
                video_manager.set_duration()
                video_manager.start()
                scene_manager.detect_scenes(frame_source=video_manager)
                scene_list = scene_manager.get_scene_list()
            
            self.scenes = []
            for i, scene in enumerate(scene_list):
                start_time = self.safe_float(scene[0].get_seconds())
                end_time = self.safe_float(scene[1].get_seconds())
                duration = end_time - start_time
                
                if duration >= min_scene_len:
                    self.scenes.append({
                        'id': i,
                        'start': start_time,
                        'end': end_time,
                        'duration': duration
                    })
            
            # Sort and add position ratios
            self.scenes.sort(key=lambda x: x['start'])
            if self.scenes:
                movie_duration = self.scenes[-1]['end']
                for scene in self.scenes:
                    scene['position_ratio'] = scene['start'] / movie_duration
            
            print(f"✅ Found {len(self.scenes)} scenes")
            return self.scenes
            
        except Exception as e:
            print(f"❌ Scene detection failed: {e}")
            return []
    
    def analyze_adaptive_tempo(self, hop_length=512, window_length=8.0):
        """
        Analyze tempo changes throughout the song using sliding windows
        Fixed to handle numpy formatting issues
        """
        print("🎵 Analyzing adaptive tempo and beat variations...")
        
        try:
            # Suppress librosa warnings
            with contextlib.redirect_stderr(io.StringIO()):
                # Load audio
                y, sr = librosa.load(self.audio_path)
                self.audio_duration = self.safe_float(len(y) / sr)
                
                # Global beat tracking first
                tempo_global, beats_global = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
                beat_times_global = librosa.frames_to_time(beats_global, sr=sr, hop_length=hop_length)
            
            # Safely convert global tempo
            self.global_tempo = self.safe_float(tempo_global)
            self.beat_times = [self.safe_float(bt) for bt in beat_times_global]
            
            print(f"🌍 Global tempo: {self.global_tempo:.1f} BPM")
            
            # Sliding window tempo analysis
            window_samples = int(window_length * sr)
            hop_samples = window_samples // 4  # 75% overlap
            
            tempo_segments = []
            
            for start_sample in range(0, len(y) - window_samples, hop_samples):
                end_sample = start_sample + window_samples
                window_audio = y[start_sample:end_sample]
                
                # Analyze this window
                try:
                    with contextlib.redirect_stderr(io.StringIO()):
                        tempo_local, beats_local = librosa.beat.beat_track(
                            y=window_audio, sr=sr, hop_length=hop_length
                        )
                    
                    start_time = self.safe_float(start_sample / sr)
                    end_time = self.safe_float(end_sample / sr)
                    center_time = (start_time + end_time) / 2
                    tempo_value = self.safe_float(tempo_local)
                    
                    tempo_segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'center_time': center_time,
                        'tempo': tempo_value,
                        'confidence': self._calculate_tempo_confidence(window_audio, sr)
                    })
                    
                except:
                    # If local analysis fails, use global tempo
                    start_time = self.safe_float(start_sample / sr)
                    end_time = self.safe_float(end_sample / sr)
                    center_time = (start_time + end_time) / 2
                    
                    tempo_segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'center_time': center_time,
                        'tempo': self.global_tempo,
                        'confidence': 0.5
                    })
            
            # Smooth tempo curve to reduce noise
            if tempo_segments:
                tempos = [seg['tempo'] for seg in tempo_segments]
                if len(tempos) > 3:
                    smoothed_tempos = uniform_filter1d(tempos, size=3)  # 3-point smoothing
                    for i, seg in enumerate(tempo_segments):
                        seg['tempo_smoothed'] = self.safe_float(smoothed_tempos[i])
                else:
                    for seg in tempo_segments:
                        seg['tempo_smoothed'] = seg['tempo']
                
                # Detect significant tempo changes
                tempo_changes = self._detect_tempo_changes(tempo_segments)
                
                # Store results
                self.tempo_segments = tempo_segments
                self.tempo_changes = tempo_changes
                
                print(f"✅ Analyzed {len(tempo_segments)} tempo segments")
                print(f"🔄 Detected {len(tempo_changes)} significant tempo changes")
                
                # Print tempo change summary without problematic formatting
                if tempo_changes:
                    print("📊 Tempo changes detected:")
                    for change in tempo_changes:
                        time_val = self.safe_float(change['time'])
                        old_tempo = self.safe_float(change['old_tempo'])
                        new_tempo = self.safe_float(change['new_tempo'])
                        print(f"   {time_val:.1f}s: {old_tempo:.0f} → {new_tempo:.0f} BPM")
                
                return tempo_segments, tempo_changes
            else:
                print("⚠️ No tempo segments analyzed, using global tempo")
                return [], []
            
        except Exception as e:
            print(f"❌ Adaptive tempo analysis failed: {e}")
            print("🔄 Falling back to global tempo analysis...")
            
            # Fallback: use global tempo for everything
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    y, sr = librosa.load(self.audio_path)
                    tempo_global, beats_global = librosa.beat.beat_track(y=y, sr=sr)
                    beat_times_global = librosa.frames_to_time(beats_global, sr=sr)
                
                self.global_tempo = self.safe_float(tempo_global)
                self.beat_times = [self.safe_float(bt) for bt in beat_times_global]
                self.audio_duration = self.safe_float(len(y) / sr)
                
                # Create single tempo segment for entire song
                self.tempo_segments = [{
                    'start_time': 0.0,
                    'end_time': self.audio_duration,
                    'center_time': self.audio_duration / 2,
                    'tempo': self.global_tempo,
                    'tempo_smoothed': self.global_tempo,
                    'confidence': 1.0
                }]
                self.tempo_changes = []
                
                print(f"✅ Fallback successful: {self.global_tempo:.1f} BPM constant tempo")
                return self.tempo_segments, self.tempo_changes
                
            except Exception as fallback_error:
                print(f"❌ Even fallback failed: {fallback_error}")
                return [], []
    
    def _calculate_tempo_confidence(self, audio_segment, sr):
        """Calculate confidence in tempo detection for a segment"""
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                onset_strength = librosa.onset.onset_strength(y=audio_segment, sr=sr)
            confidence = np.std(onset_strength) / (np.mean(onset_strength) + 1e-8)
            return self.safe_float(min(confidence, 1.0))  # Cap at 1.0
        except:
            return 0.5  # Default confidence
    
    def _detect_tempo_changes(self, tempo_segments, threshold=15.0):
        """Detect significant tempo changes"""
        changes = []
        
        if len(tempo_segments) < 2:
            return changes
        
        for i in range(1, len(tempo_segments)):
            prev_tempo = tempo_segments[i-1]['tempo_smoothed']
            curr_tempo = tempo_segments[i]['tempo_smoothed']
            
            tempo_diff = abs(curr_tempo - prev_tempo)
            
            if tempo_diff > threshold:
                changes.append({
                    'time': tempo_segments[i]['center_time'],
                    'old_tempo': prev_tempo,
                    'new_tempo': curr_tempo,
                    'change_magnitude': tempo_diff
                })
        
        return changes
    
    def create_adaptive_mapping(self, max_clips=None, sensitivity="medium"):
        """
        Create scene mapping that adapts to tempo changes
        """
        print(f"🎯 Creating adaptive tempo mapping (sensitivity: {sensitivity})...")
        
        if not self.scenes:
            print("❌ No scenes available")
            return []
        
        if not self.beat_times:
            print("❌ No beats available")
            return []
        
        if not self.tempo_segments:
            print("❌ No tempo analysis available")
            return []
        
        # Determine clips to use
        total_beats = len(self.beat_times) - 1
        num_clips = min(max_clips, total_beats) if max_clips else total_beats
        
        scene_sequence = []
        
        # Define sensitivity parameters
        sensitivity_params = {
            "low": {"scene_variety": 0.3, "tempo_response": 0.5},
            "medium": {"scene_variety": 0.6, "tempo_response": 0.8},
            "high": {"scene_variety": 0.9, "tempo_response": 1.2}
        }
        
        params = sensitivity_params.get(sensitivity, sensitivity_params["medium"])
        
        for i in range(num_clips):
            # Calculate progress through song
            progress = i / num_clips
            beat_time = self.beat_times[i]
            
            # Find current tempo at this beat
            current_tempo = self._get_tempo_at_time(beat_time)
            
            # Calculate scene selection strategy based on tempo
            tempo_factor = current_tempo / self.global_tempo if self.global_tempo > 0 else 1.0
            
            if tempo_factor > 1.1:  # Fast section
                scene_strategy = "high_energy"
                window_size = 0.8 / num_clips * params["tempo_response"]  # Larger variety
            elif tempo_factor < 0.9:  # Slow section
                scene_strategy = "contemplative" 
                window_size = 1.2 / num_clips * params["tempo_response"]  # More focused
            else:  # Normal tempo
                scene_strategy = "balanced"
                window_size = 1.0 / num_clips
            
            # Progressive movie position with tempo-based variation
            base_position = progress
            
            # Add tempo-based offset for more dynamic scene selection
            tempo_offset = (tempo_factor - 1.0) * 0.1 * params["scene_variety"]
            movie_position = max(0, min(1, base_position + tempo_offset))
            
            # Create time window
            window_start = max(0, movie_position - window_size/2)
            window_end = min(1.0, movie_position + window_size/2)
            
            # Find scenes in this window
            window_scenes = [
                scene for scene in self.scenes
                if window_start <= scene['position_ratio'] <= window_end
            ]
            
            if not window_scenes:
                # Expand window if no scenes found
                window_scenes = [min(self.scenes, 
                                   key=lambda s: abs(s['position_ratio'] - movie_position))]
            
            # Select scene based on tempo strategy
            if scene_strategy == "high_energy" and len(window_scenes) > 1:
                # Prefer shorter, more dynamic scenes
                selected_scene = min(window_scenes, key=lambda s: s['duration'])
            elif scene_strategy == "contemplative" and len(window_scenes) > 1:
                # Prefer longer, more stable scenes
                selected_scene = max(window_scenes, key=lambda s: s['duration'])
            else:
                # Random selection for balanced sections
                selected_scene = random.choice(window_scenes)
            
            # Beat timing
            beat_start = self.beat_times[i]
            beat_end = self.beat_times[i + 1] if i + 1 < len(self.beat_times) else beat_start + 0.5
            beat_duration = beat_end - beat_start
            
            scene_sequence.append({
                'beat_start': beat_start,
                'beat_end': beat_end,
                'beat_duration': beat_duration,
                'scene': selected_scene,
                'beat_index': i,
                'movie_progress': progress,
                'current_tempo': current_tempo,
                'tempo_factor': tempo_factor,
                'scene_strategy': scene_strategy,
                'window_size': window_size
            })
        
        self.scene_sequence = scene_sequence
        
        # Analyze the adaptive mapping
        strategies = [mapping['scene_strategy'] for mapping in scene_sequence]
        strategy_counts = {}
        for s in set(strategies):
            strategy_counts[s] = strategies.count(s)
        
        print(f"✅ Created {len(scene_sequence)} adaptive mappings")
        print(f"📊 Scene strategies: {strategy_counts}")
        
        return scene_sequence
    
    def _get_tempo_at_time(self, time):
        """Get the tempo at a specific time"""
        # Find the tempo segment that contains this time
        for segment in self.tempo_segments:
            if segment['start_time'] <= time <= segment['end_time']:
                return segment['tempo_smoothed']
        
        # If not found, use global tempo
        return self.global_tempo
    
    def generate_video_clips(self, max_clips=None):
        """Generate video clips with tempo-aware pacing"""
        print("🎬 Generating tempo-adaptive video clips...")
        
        if not hasattr(self, 'scene_sequence'):
            print("❌ No scene sequence available")
            return []
        
        video_clips = []
        
        try:
            video = VideoFileClip(self.video_path, verbose=False)
            
            sequence = self.scene_sequence
            if max_clips:
                sequence = sequence[:max_clips]
            
            for i, mapping in enumerate(sequence):
                try:
                    scene = mapping['scene']
                    beat_duration = mapping['beat_duration']
                    tempo_factor = mapping.get('tempo_factor', 1.0)
                    scene_strategy = mapping.get('scene_strategy', 'balanced')
                    
                    # Extract scene from video
                    scene_clip = video.subclip(scene['start'], scene['end'])
                    
                    # Tempo-aware clip processing
                    if scene_clip.duration > beat_duration:
                        # For fast sections, prefer more dynamic parts of scenes
                        if scene_strategy == "high_energy":
                            # Pick from middle of scene (usually more action)
                            max_start = scene_clip.duration - beat_duration
                            start_offset = random.uniform(max_start * 0.3, max_start * 0.7) if max_start > 0 else 0
                        else:
                            # Random selection for other strategies
                            max_start = scene_clip.duration - beat_duration
                            start_offset = random.uniform(0, max_start) if max_start > 0 else 0
                        
                        scene_clip = scene_clip.subclip(start_offset, start_offset + beat_duration)
                    else:
                        # Speed adjustment based on tempo
                        speed_factor = scene_clip.duration / beat_duration
                        scene_clip = scene_clip.fx('speedx', speed_factor)
                    
                    video_clips.append(scene_clip)
                    
                except Exception as e:
                    print(f"⚠️ Skipping clip {i}: {e}")
                    continue
            
            self.video_clips = video_clips
            print(f"✅ Generated {len(video_clips)} tempo-adaptive clips")
            return video_clips
            
        except Exception as e:
            print(f"❌ Video clip generation failed: {e}")
            return []
    
    def render_music_video(self, fade_duration=0.05):
        """Render the final adaptive tempo music video"""
        print("🎥 Rendering adaptive tempo music video...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("❌ No video clips to render")
            return False
        
        try:
            final_video = concatenate_videoclips(self.video_clips, method="compose")
            
            with contextlib.redirect_stderr(io.StringIO()):
                audio = AudioFileClip(self.audio_path)
            
            if audio.duration > final_video.duration:
                audio = audio.subclip(0, final_video.duration)
            
            final_video = final_video.set_audio(audio)
            
            print(f"💾 Saving to {self.output_path}...")
            final_video.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                fps=24,
                verbose=False,
                logger=None
            )
            
            final_video.close()
            audio.close()
            for clip in self.video_clips:
                clip.close()
            
            print(f"🎉 Adaptive tempo music video saved as {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Rendering failed: {e}")
            return False
    
    def generate_adaptive_music_video(self, max_clips=None, sensitivity="medium", threshold=30.0):
        """Complete pipeline for adaptive tempo music video"""
        print("🚀 Starting adaptive tempo music video generation...")
        print("=" * 60)
        
        success_count = 0
        
        # Step 1: Detect scenes
        if self.detect_scenes(threshold=threshold):
            success_count += 1
            print("✅ Scene detection completed")
        else:
            print("❌ Scene detection failed")
            return False
        
        # Step 2: Adaptive tempo analysis
        tempo_segments, tempo_changes = self.analyze_adaptive_tempo()
        if tempo_segments:
            success_count += 1
            print("✅ Tempo analysis completed")
        else:
            print("❌ Tempo analysis failed")
            return False
        
        # Step 3: Create adaptive mapping
        if self.create_adaptive_mapping(max_clips=max_clips, sensitivity=sensitivity):
            success_count += 1
            print("✅ Adaptive mapping completed")
        else:
            print("❌ Adaptive mapping failed")
            return False
        
        # Step 4: Generate clips
        if self.generate_video_clips(max_clips=max_clips):
            success_count += 1
            print("✅ Video clip generation completed")
        else:
            print("❌ Video clip generation failed")
            return False
        
        # Step 5: Render
        if self.render_music_video():
            success_count += 1
            print("✅ Rendering completed")
        else:
            print("❌ Rendering failed")
            return False
        
        print(f"\n🎊 ADAPTIVE TEMPO MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        
        try:
            # Analyze tempo responsiveness safely
            tempo_variations = [self.safe_float(mapping.get('tempo_factor', 1.0)) for mapping in self.scene_sequence]
            strategies = [mapping.get('scene_strategy', 'balanced') for mapping in self.scene_sequence]
            
            print(f"\n📊 Adaptive Analysis:")
            print(f"   Tempo range: {min(tempo_variations):.2f}x to {max(tempo_variations):.2f}x")
            strategy_counts = {}
            for s in set(strategies):
                strategy_counts[s] = strategies.count(s)
            print(f"   Strategy distribution: {strategy_counts}")
            print(f"   Total clips: {len(self.video_clips)}")
            
            total_duration = 0
            for clip in self.video_clips:
                try:
                    total_duration += clip.duration
                except:
                    total_duration += 0.5  # Fallback duration
            
            print(f"   Duration: {total_duration:.1f} seconds")
            print(f"   Tempo changes detected: {len(self.tempo_changes)}")
            
        except Exception as e:
            print(f"⚠️ Analysis reporting failed: {e}")
        
        return True

# Simple test function
def test_fixed_adaptive():
    """Simple test of the fixed adaptive tempo generator"""
    print("🧪 TESTING FIXED ADAPTIVE TEMPO GENERATOR")
    print("=" * 50)
    
    generator = FixedAdaptiveTempoGenerator("movie.mp4", "song.mp3", "fixed_adaptive_test.mp4")
    
    success = generator.generate_adaptive_music_video(
        max_clips=None,      # Full song
        sensitivity="high",  # High sensitivity to tempo changes
        threshold=30.0       # Scene detection threshold
    )
    
    if success:
        print("\n🎉 SUCCESS! Fixed adaptive tempo generator working!")
        print("📁 Check: fixed_adaptive_test.mp4")
    else:
        print("\n❌ Test failed")
    
    return success

if __name__ == "__main__":
    test_fixed_adaptive()
