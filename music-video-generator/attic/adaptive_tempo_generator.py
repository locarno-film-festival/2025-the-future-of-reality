#!/usr/bin/env python3
"""
Adaptive Tempo Music Video Generator
Detects tempo changes and adapts video pacing accordingly
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
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d

class AdaptiveTempoGenerator:
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
        """
        print("🎵 Analyzing adaptive tempo and beat variations...")
        
        try:
            # Load audio
            y, sr = librosa.load(self.audio_path)
            self.audio_duration = len(y) / sr
            
            # Global beat tracking first
            tempo_global, beats_global = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
            beat_times_global = librosa.frames_to_time(beats_global, sr=sr, hop_length=hop_length)
            
            print(f"🌍 Global tempo: {tempo_global:.1f} BPM")
            
            # Sliding window tempo analysis
            window_samples = int(window_length * sr)
            hop_samples = window_samples // 4  # 75% overlap
            
            tempo_segments = []
            time_segments = []
            
            for start_sample in range(0, len(y) - window_samples, hop_samples):
                end_sample = start_sample + window_samples
                window_audio = y[start_sample:end_sample]
                
                # Analyze this window
                try:
                    tempo_local, beats_local = librosa.beat.beat_track(
                        y=window_audio, sr=sr, hop_length=hop_length
                    )
                    
                    start_time = start_sample / sr
                    end_time = end_sample / sr
                    center_time = (start_time + end_time) / 2
                    
                    tempo_segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'center_time': center_time,
                        'tempo': self.safe_float(tempo_local),
                        'confidence': self._calculate_tempo_confidence(window_audio, sr)
                    })
                    
                    time_segments.append(center_time)
                    
                except:
                    # If local analysis fails, use global tempo
                    start_time = start_sample / sr
                    end_time = end_sample / sr
                    center_time = (start_time + end_time) / 2
                    
                    tempo_segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'center_time': center_time,
                        'tempo': self.safe_float(tempo_global),
                        'confidence': 0.5
                    })
            
            # Smooth tempo curve to reduce noise
            tempos = [seg['tempo'] for seg in tempo_segments]
            smoothed_tempos = uniform_filter1d(tempos, size=3)  # 3-point smoothing
            
            for i, seg in enumerate(tempo_segments):
                seg['tempo_smoothed'] = smoothed_tempos[i]
            
            # Detect significant tempo changes
            tempo_changes = self._detect_tempo_changes(tempo_segments)
            
            # Store results
            self.tempo_segments = tempo_segments
            self.tempo_changes = tempo_changes
            self.beat_times = beat_times_global
            self.global_tempo = tempo_global
            
            print(f"✅ Analyzed {len(tempo_segments)} tempo segments")
            print(f"🔄 Detected {len(tempo_changes)} significant tempo changes")
            
            # Print tempo change summary
            if tempo_changes:
                print("📊 Tempo changes detected:")
                for change in tempo_changes:
                    print(f"   {change['time']:.1f}s: {change['old_tempo']:.0f} → {change['new_tempo']:.0f} BPM")
            
            return tempo_segments, tempo_changes
            
        except Exception as e:
            print(f"❌ Adaptive tempo analysis failed: {e}")
            return [], []
    
    def _calculate_tempo_confidence(self, audio_segment, sr):
        """Calculate confidence in tempo detection for a segment"""
        try:
            # Use onset strength as a proxy for rhythmic clarity
            onset_strength = librosa.onset.onset_strength(y=audio_segment, sr=sr)
            confidence = np.std(onset_strength) / (np.mean(onset_strength) + 1e-8)
            return min(confidence, 1.0)  # Cap at 1.0
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
        
        sensitivity: "low", "medium", "high" - how much to vary scene selection
        """
        print(f"🎯 Creating adaptive tempo mapping (sensitivity: {sensitivity})...")
        
        if not self.scenes or not self.beat_times or not self.tempo_segments:
            print("❌ Need scenes, beats, and tempo analysis first")
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
            tempo_factor = current_tempo / self.global_tempo
            
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
            if scene_strategy == "high_energy":
                # Prefer shorter, more dynamic scenes
                selected_scene = min(window_scenes, key=lambda s: s['duration'])
            elif scene_strategy == "contemplative":
                # Prefer longer, more stable scenes
                selected_scene = max(window_scenes, key=lambda s: s['duration'])
            else:
                # Random selection for balanced sections
                selected_scene = random.choice(window_scenes)
            
            # Beat timing
            beat_start = self.beat_times[i]
            beat_end = self.beat_times[i + 1]
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
        strategy_counts = {s: strategies.count(s) for s in set(strategies)}
        
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
                    tempo_factor = mapping['tempo_factor']
                    scene_strategy = mapping['scene_strategy']
                    
                    # Extract scene from video
                    scene_clip = video.subclip(scene['start'], scene['end'])
                    
                    # Tempo-aware clip processing
                    if scene_clip.duration > beat_duration:
                        # For fast sections, prefer more dynamic parts of scenes
                        if scene_strategy == "high_energy":
                            # Pick from middle of scene (usually more action)
                            max_start = scene_clip.duration - beat_duration
                            start_offset = random.uniform(max_start * 0.3, max_start * 0.7)
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
    
    def visualize_tempo_analysis(self, save_path="tempo_analysis.png"):
        """Create visualization of tempo analysis"""
        if not self.tempo_segments:
            print("❌ No tempo analysis to visualize")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Plot 1: Tempo over time
        times = [seg['center_time'] for seg in self.tempo_segments]
        tempos = [seg['tempo_smoothed'] for seg in self.tempo_segments]
        confidences = [seg['confidence'] for seg in self.tempo_segments]
        
        # Color by confidence
        scatter = ax1.scatter(times, tempos, c=confidences, cmap='viridis', alpha=0.7)
        ax1.plot(times, tempos, 'b-', alpha=0.5, linewidth=1)
        ax1.axhline(y=self.global_tempo, color='red', linestyle='--', 
                   label=f'Global Tempo ({self.global_tempo:.1f} BPM)')
        
        # Mark tempo changes
        if hasattr(self, 'tempo_changes'):
            for change in self.tempo_changes:
                ax1.axvline(x=change['time'], color='orange', linestyle=':', alpha=0.8)
                ax1.annotate(f"{change['new_tempo']:.0f}", 
                           xy=(change['time'], change['new_tempo']),
                           xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Tempo (BPM)')
        ax1.set_title('Tempo Analysis Over Time')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Colorbar for confidence
        cbar = plt.colorbar(scatter, ax=ax1)
        cbar.set_label('Detection Confidence')
        
        # Plot 2: Beat positions
        if self.beat_times is not None:
            ax2.eventplot([self.beat_times], lineoffsets=1, linelengths=0.8, colors='blue')
            ax2.set_xlabel('Time (seconds)')
            ax2.set_ylabel('Beats')
            ax2.set_title('Beat Positions')
            ax2.set_ylim(0.5, 1.5)
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()
        
        print(f"📊 Tempo analysis saved as {save_path}")
    
    def render_music_video(self, fade_duration=0.05):
        """Render the final adaptive tempo music video"""
        print("🎥 Rendering adaptive tempo music video...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("❌ No video clips to render")
            return False
        
        try:
            final_video = concatenate_videoclips(self.video_clips, method="compose")
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
    
    def generate_adaptive_music_video(self, max_clips=None, sensitivity="medium", 
                                    threshold=30.0, visualize=True):
        """Complete pipeline for adaptive tempo music video"""
        print("🚀 Starting adaptive tempo music video generation...")
        print("=" * 60)
        
        # Step 1: Detect scenes
        if not self.detect_scenes(threshold=threshold):
            return False
        
        # Step 2: Adaptive tempo analysis
        if not self.analyze_adaptive_tempo():
            return False
        
        # Step 3: Visualize tempo analysis
        if visualize:
            self.visualize_tempo_analysis()
        
        # Step 4: Create adaptive mapping
        if not self.create_adaptive_mapping(max_clips=max_clips, sensitivity=sensitivity):
            return False
        
        # Step 5: Generate clips
        if not self.generate_video_clips(max_clips=max_clips):
            return False
        
        # Step 6: Render
        if not self.render_music_video():
            return False
        
        # Report
        print(f"\n🎊 ADAPTIVE TEMPO MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        
        try:
            # Analyze tempo responsiveness
            tempo_variations = [mapping['tempo_factor'] for mapping in self.scene_sequence]
            strategies = [mapping['scene_strategy'] for mapping in self.scene_sequence]
            
            print(f"\n📊 Adaptive Analysis:")
            print(f"   Tempo range: {min(tempo_variations):.2f}x to {max(tempo_variations):.2f}x")
            print(f"   Strategy distribution: {dict((s, strategies.count(s)) for s in set(strategies))}")
            print(f"   Total clips: {len(self.video_clips)}")
            print(f"   Duration: {sum(clip.duration for clip in self.video_clips):.1f} seconds")
            
        except Exception as e:
            print(f"⚠️ Analysis failed: {e}")
        
        return True

# Usage example
if __name__ == "__main__":
    print("🎵 Adaptive Tempo Music Video Generator")
    print("Perfect for songs like 'The Chain' with tempo changes!")
    print("\nUsage:")
    print("generator = AdaptiveTempoGenerator('movie.mp4', 'song.mp3')")
    print("generator.generate_adaptive_music_video(sensitivity='high')")
