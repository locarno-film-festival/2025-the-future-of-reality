#!/usr/bin/env python3
"""
Progressive Sampling Music Video Generator
Creates a journey through the entire movie while syncing to beats
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

class ProgressiveSamplingGenerator:
    def __init__(self, video_path, audio_path, output_path="music_video.mp4"):
        self.video_path = video_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.scenes = []
        self.beat_times = []
        
    def safe_float(self, value):
        """Safely convert numpy values to Python float"""
        try:
            return float(value)
        except:
            return 0.0
    
    def detect_scenes(self, threshold=30.0, min_scene_len=1.0):
        """Detect scenes and sort them chronologically"""
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
                        'duration': duration,
                        'position_ratio': start_time / end_time if end_time > 0 else 0  # Position in movie (0-1)
                    })
            
            # Sort scenes by chronological order (just to be sure)
            self.scenes.sort(key=lambda x: x['start'])
            
            # Add normalized position for each scene (0.0 = beginning, 1.0 = end)
            if self.scenes:
                movie_duration = self.scenes[-1]['end']
                for scene in self.scenes:
                    scene['position_ratio'] = scene['start'] / movie_duration
            
            print(f"✅ Found {len(self.scenes)} scenes spanning {movie_duration/60:.1f} minutes")
            return self.scenes
            
        except Exception as e:
            print(f"❌ Scene detection failed: {e}")
            return []
    
    def analyze_audio_beats(self, hop_length=512):
        """Analyze beats in audio"""
        print("🎵 Analyzing audio beats...")
        
        try:
            y, sr = librosa.load(self.audio_path)
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
            beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)
            
            self.tempo = self.safe_float(tempo)
            self.beat_times = [self.safe_float(bt) for bt in beat_times]
            self.audio_duration = self.safe_float(len(y) / sr)
            
            print(f"✅ Detected {len(self.beat_times)} beats at {self.tempo:.1f} BPM")
            print(f"🎶 Audio duration: {self.audio_duration:.1f} seconds")
            
            return self.beat_times, self.tempo
            
        except Exception as e:
            print(f"❌ Beat analysis failed: {e}")
            return [], 120.0
    
    def create_progressive_mapping(self, max_clips=None, sampling_method="smart_random"):
        """
        Create progressive scene mapping that journeys through the movie
        
        sampling_method options:
        - "smart_random": Random selection within progressive time windows
        - "weighted_random": Higher probability for key scenes (longer scenes)
        - "even_distribution": Evenly spaced samples with random selection
        """
        print(f"🎯 Creating progressive scene mapping ({sampling_method})...")
        
        if not self.scenes or not self.beat_times:
            print("❌ Need scenes and beats first")
            return []
        
        # Determine how many clips to create
        total_beats = len(self.beat_times) - 1
        num_clips = min(max_clips, total_beats) if max_clips else total_beats
        
        print(f"📊 Creating {num_clips} clips from {len(self.scenes)} scenes")
        
        scene_sequence = []
        
        if sampling_method == "smart_random":
            # Divide movie into time windows, randomly select from each window
            for i in range(num_clips):
                # Calculate which portion of the movie this beat represents
                progress = i / num_clips  # 0.0 to 1.0 through the song
                
                # Create a time window around this progress point
                window_size = 1.0 / num_clips  # Size of each window
                window_start = max(0, progress - window_size/2)
                window_end = min(1.0, progress + window_size/2)
                
                # Find scenes within this time window
                window_scenes = [
                    scene for scene in self.scenes
                    if window_start <= scene['position_ratio'] <= window_end
                ]
                
                # If no scenes in window, expand it
                if not window_scenes:
                    window_scenes = [
                        scene for scene in self.scenes
                        if abs(scene['position_ratio'] - progress) <= window_size
                    ]
                
                # If still no scenes, just pick the closest one
                if not window_scenes:
                    window_scenes = [min(self.scenes, 
                                       key=lambda s: abs(s['position_ratio'] - progress))]
                
                # Randomly select from available scenes in this window
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
                    'window': f"{window_start:.2f}-{window_end:.2f}"
                })
        
        elif sampling_method == "weighted_random":
            # Weight longer scenes higher (usually more important)
            for i in range(num_clips):
                progress = i / num_clips
                window_size = 2.0 / num_clips  # Slightly larger windows
                window_start = max(0, progress - window_size/2)
                window_end = min(1.0, progress + window_size/2)
                
                window_scenes = [
                    scene for scene in self.scenes
                    if window_start <= scene['position_ratio'] <= window_end
                ]
                
                if not window_scenes:
                    window_scenes = [min(self.scenes, 
                                       key=lambda s: abs(s['position_ratio'] - progress))]
                
                # Weight by scene duration (longer scenes more likely to be selected)
                weights = [scene['duration'] for scene in window_scenes]
                selected_scene = random.choices(window_scenes, weights=weights)[0]
                
                beat_start = self.beat_times[i]
                beat_end = self.beat_times[i + 1]
                beat_duration = beat_end - beat_start
                
                scene_sequence.append({
                    'beat_start': beat_start,
                    'beat_end': beat_end,
                    'beat_duration': beat_duration,
                    'scene': selected_scene,
                    'beat_index': i,
                    'movie_progress': progress
                })
        
        elif sampling_method == "even_distribution":
            # Evenly distribute samples across the movie
            progress_points = np.linspace(0, 1, num_clips)
            
            for i, progress in enumerate(progress_points):
                # Find scene closest to this progress point
                closest_scene = min(self.scenes, 
                                  key=lambda s: abs(s['position_ratio'] - progress))
                
                # Add some randomness by considering nearby scenes
                nearby_scenes = [
                    scene for scene in self.scenes
                    if abs(scene['position_ratio'] - progress) <= 0.05  # Within 5%
                ]
                
                if len(nearby_scenes) > 1:
                    selected_scene = random.choice(nearby_scenes)
                else:
                    selected_scene = closest_scene
                
                beat_start = self.beat_times[i]
                beat_end = self.beat_times[i + 1]
                beat_duration = beat_end - beat_start
                
                scene_sequence.append({
                    'beat_start': beat_start,
                    'beat_end': beat_end,
                    'beat_duration': beat_duration,
                    'scene': selected_scene,
                    'beat_index': i,
                    'movie_progress': progress
                })
        
        self.scene_sequence = scene_sequence
        
        # Print sampling analysis
        movie_coverage = [mapping['scene']['position_ratio'] for mapping in scene_sequence]
        print(f"✅ Created {len(scene_sequence)} progressive mappings")
        print(f"📈 Movie coverage: {min(movie_coverage):.1%} to {max(movie_coverage):.1%}")
        print(f"🎬 Sampling method: {sampling_method}")
        
        return scene_sequence
    
    def generate_video_clips(self, max_clips=None):
        """Generate video clips from the progressive mapping"""
        print("🎬 Generating progressive video clips...")
        
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
                    
                    # Extract scene from video
                    scene_clip = video.subclip(scene['start'], scene['end'])
                    
                    # Adjust clip duration to match beat
                    if scene_clip.duration > beat_duration:
                        # For longer scenes, randomly pick a good segment
                        max_start = scene_clip.duration - beat_duration
                        start_offset = random.uniform(0, max_start) if max_start > 0 else 0
                        scene_clip = scene_clip.subclip(start_offset, start_offset + beat_duration)
                    else:
                        # Speed up shorter clips
                        speed_factor = scene_clip.duration / beat_duration
                        scene_clip = scene_clip.fx('speedx', speed_factor)
                    
                    video_clips.append(scene_clip)
                    
                except Exception as e:
                    print(f"⚠️ Skipping clip {i}: {e}")
                    continue
            
            self.video_clips = video_clips
            print(f"✅ Generated {len(video_clips)} progressive clips")
            return video_clips
            
        except Exception as e:
            print(f"❌ Video clip generation failed: {e}")
            return []
    
    def render_music_video(self, fade_duration=0.05):
        """Render the final progressive music video"""
        print("🎥 Rendering progressive music video...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("❌ No video clips to render")
            return False
        
        try:
            # Concatenate clips
            final_video = concatenate_videoclips(self.video_clips, method="compose")
            
            # Add audio
            audio = AudioFileClip(self.audio_path)
            if audio.duration > final_video.duration:
                audio = audio.subclip(0, final_video.duration)
            
            final_video = final_video.set_audio(audio)
            
            # Render
            print(f"💾 Saving to {self.output_path}...")
            final_video.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                fps=24,
                verbose=False,
                logger=None
            )
            
            # Cleanup
            final_video.close()
            audio.close()
            for clip in self.video_clips:
                clip.close()
            
            print(f"🎉 Progressive music video saved as {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Rendering failed: {e}")
            return False
    
    def generate_progressive_music_video(self, max_clips=None, sampling_method="smart_random", threshold=30.0):
        """Complete pipeline for progressive sampling"""
        print("🚀 Starting progressive music video generation...")
        print("=" * 60)
        
        # Step 1: Detect scenes
        if not self.detect_scenes(threshold=threshold):
            return False
        
        # Step 2: Analyze beats
        if not self.analyze_audio_beats():
            return False
        
        # Step 3: Create progressive mapping
        if not self.create_progressive_mapping(max_clips=max_clips, sampling_method=sampling_method):
            return False
        
        # Step 4: Generate clips
        if not self.generate_video_clips(max_clips=max_clips):
            return False
        
        # Step 5: Render
        if not self.render_music_video():
            return False
        
        # Report
        print(f"\n🎊 PROGRESSIVE MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        
        try:
            # Analyze the journey
            movie_positions = [mapping['scene']['position_ratio'] for mapping in self.scene_sequence]
            
            print(f"\n📊 Journey Analysis:")
            print(f"   Scenes used: {len(set(mapping['scene']['id'] for mapping in self.scene_sequence))}/{len(self.scenes)}")
            print(f"   Movie coverage: {min(movie_positions):.1%} to {max(movie_positions):.1%}")
            print(f"   Sampling method: {sampling_method}")
            print(f"   Total clips: {len(self.video_clips)}")
            print(f"   Duration: {sum(clip.duration for clip in self.video_clips):.1f} seconds")
            
        except Exception as e:
            print(f"⚠️ Analysis failed: {e}")
        
        return True

# Usage examples
if __name__ == "__main__":
    print("🎬 Progressive Sampling Music Video Generator")
    print("\nUsage examples:")
    print("generator = ProgressiveSamplingGenerator('movie.mp4', 'song.mp3')")
    print("\n# Smart random sampling (recommended):")
    print("generator.generate_progressive_music_video(max_clips=100, sampling_method='smart_random')")
    print("\n# Weighted by scene importance:")
    print("generator.generate_progressive_music_video(max_clips=100, sampling_method='weighted_random')")
    print("\n# Even distribution across movie:")
    print("generator.generate_progressive_music_video(max_clips=100, sampling_method='even_distribution')")
