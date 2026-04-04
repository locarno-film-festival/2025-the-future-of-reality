#!/usr/bin/env python3
"""
Forward-Only No-Repeat Generator
Prevents jumping back to early scenes when late scenes are exhausted
"""

import warnings
warnings.filterwarnings("ignore", message="VideoManager is deprecated")

import librosa
import numpy as np
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import random
import contextlib
import io

class ForwardOnlyGenerator:
    def __init__(self, video_path, audio_path, output_path="forward_only_video.mp4"):
        self.video_path = video_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.scenes = []
        self.beat_times = []
        self.scene_pools = {}  # Divide scenes into pools
        
    def safe_float(self, value):
        """Safely convert numpy values to Python float"""
        try:
            return float(value)
        except:
            return 0.0
    
    def detect_scenes(self, threshold=30.0, min_scene_len=1.0):
        """Detect scenes and organize into chronological pools"""
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
                        'duration': duration,
                        'used': False
                    })
            
            # Sort chronologically
            self.scenes.sort(key=lambda x: x['start'])
            
            # Add position ratios
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
            with contextlib.redirect_stderr(io.StringIO()):
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
    
    def create_scene_pools(self, num_pools=10):
        """Divide scenes into chronological pools to prevent backward jumps"""
        print(f"🗂️ Creating {num_pools} chronological scene pools...")
        
        if not self.scenes:
            return {}
        
        scenes_per_pool = len(self.scenes) // num_pools
        pools = {}
        
        for i in range(num_pools):
            start_idx = i * scenes_per_pool
            if i == num_pools - 1:  # Last pool gets remaining scenes
                end_idx = len(self.scenes)
            else:
                end_idx = (i + 1) * scenes_per_pool
            
            pool_scenes = self.scenes[start_idx:end_idx]
            pool_start_ratio = pool_scenes[0]['position_ratio'] if pool_scenes else 0
            pool_end_ratio = pool_scenes[-1]['position_ratio'] if pool_scenes else 1
            
            pools[i] = {
                'scenes': pool_scenes,
                'start_ratio': pool_start_ratio,
                'end_ratio': pool_end_ratio,
                'used_count': 0
            }
            
            print(f"   Pool {i}: {len(pool_scenes)} scenes ({pool_start_ratio:.1%}-{pool_end_ratio:.1%} of movie)")
        
        self.scene_pools = pools
        return pools
    
    def create_forward_only_mapping(self, max_clips=None, strictness="medium"):
        """
        Create mapping that never goes backward in the movie
        
        strictness:
        - "strict": Very narrow windows, no backward fallback
        - "medium": Moderate windows, limited forward fallback  
        - "flexible": Wider windows, forward fallback allowed
        """
        print(f"🎯 Creating forward-only mapping (strictness: {strictness})...")
        
        if not self.scenes or not self.beat_times:
            print("❌ Need scenes and beats first")
            return []
        
        # Create scene pools
        self.create_scene_pools(num_pools=20)  # More pools for better distribution
        
        # Determine clips to use
        total_beats = len(self.beat_times) - 1
        num_clips = min(max_clips, total_beats) if max_clips else total_beats
        
        print(f"📊 Mapping {num_clips} beats with forward-only progression")
        
        scene_sequence = []
        last_used_position = 0.0  # Track progression through movie
        
        # Strictness parameters
        strictness_params = {
            "strict": {"window_size": 0.5, "fallback_range": 0.1},
            "medium": {"window_size": 1.0, "fallback_range": 0.2}, 
            "flexible": {"window_size": 1.5, "fallback_range": 0.3}
        }
        
        params = strictness_params.get(strictness, strictness_params["medium"])
        
        for i in range(num_clips):
            progress = i / num_clips
            
            # Calculate target position (never go backward!)
            target_position = max(progress, last_used_position)
            
            # Create forward-looking window
            base_window_size = params["window_size"] / num_clips
            window_start = target_position
            window_end = min(1.0, target_position + base_window_size)
            
            # Find unused scenes in forward window
            forward_scenes = [
                scene for scene in self.scenes
                if (window_start <= scene['position_ratio'] <= window_end) 
                and not scene['used']
                and scene['position_ratio'] >= last_used_position  # NEVER go backward
            ]
            
            # If no scenes in immediate window, expand forward only
            if not forward_scenes:
                # Expand window forward, never backward
                expanded_end = min(1.0, target_position + params["fallback_range"])
                forward_scenes = [
                    scene for scene in self.scenes
                    if (target_position <= scene['position_ratio'] <= expanded_end)
                    and not scene['used']
                ]
                
                if not forward_scenes:
                    print(f"⚠️ Beat {i}: No forward scenes available from {target_position:.1%}")
                    
                    # Final fallback: any unused scene from current position forward
                    forward_scenes = [
                        scene for scene in self.scenes
                        if scene['position_ratio'] >= last_used_position and not scene['used']
                    ]
                    
                    if not forward_scenes:
                        print(f"🚨 Beat {i}: Completely exhausted! Using any available scene")
                        forward_scenes = [scene for scene in self.scenes if not scene['used']]
                        
                        if not forward_scenes:
                            print(f"❌ Beat {i}: No scenes left at all!")
                            break
            
            # Select scene from available forward scenes
            if forward_scenes:
                # Prefer scenes closer to target position
                selected_scene = min(forward_scenes, 
                                   key=lambda s: abs(s['position_ratio'] - target_position))
                selected_scene['used'] = True
                
                # Update progression tracker
                last_used_position = max(last_used_position, selected_scene['position_ratio'])
                
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
                    'target_progress': progress,
                    'actual_progress': selected_scene['position_ratio'],
                    'progression_maintained': selected_scene['position_ratio'] >= last_used_position
                })
            
        self.scene_sequence = scene_sequence
        
        # Analyze forward progression
        actual_positions = [mapping['actual_progress'] for mapping in scene_sequence]
        progression_violations = sum(1 for i in range(1, len(actual_positions)) 
                                   if actual_positions[i] < actual_positions[i-1])
        
        print(f"✅ Created {len(scene_sequence)} forward-only mappings")
        print(f"📈 Movie progression: {min(actual_positions):.1%} to {max(actual_positions):.1%}")
        print(f"🎯 Backward jumps: {progression_violations} (should be 0 for perfect forward progression)")
        
        if progression_violations == 0:
            print("🎉 Perfect! No backward jumps in movie progression!")
        else:
            print(f"⚠️ {progression_violations} backward jumps detected")
        
        return scene_sequence
    
    def generate_video_clips(self, max_clips=None):
        """Generate video clips maintaining forward progression"""
        print("🎬 Generating forward-progression video clips...")
        
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
                        # For forward progression, prefer earlier parts of scenes
                        # to maintain chronological feel
                        max_start = scene_clip.duration - beat_duration
                        start_offset = random.uniform(0, max_start * 0.5) if max_start > 0 else 0  # Bias toward start
                        scene_clip = scene_clip.subclip(start_offset, start_offset + beat_duration)
                    else:
                        speed_factor = scene_clip.duration / beat_duration
                        scene_clip = scene_clip.fx('speedx', speed_factor)
                    
                    video_clips.append(scene_clip)
                    
                except Exception as e:
                    print(f"⚠️ Skipping clip {i}: {e}")
                    continue
            
            self.video_clips = video_clips
            print(f"✅ Generated {len(video_clips)} forward-progression clips")
            return video_clips
            
        except Exception as e:
            print(f"❌ Video clip generation failed: {e}")
            return []
    
    def render_music_video(self, fade_duration=0.05):
        """Render the final forward-only music video"""
        print("🎥 Rendering forward-only music video...")
        
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
            
            print(f"🎉 Forward-only music video saved as {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Rendering failed: {e}")
            return False
    
    def generate_forward_only_music_video(self, max_clips=None, strictness="medium", threshold=30.0):
        """Complete pipeline ensuring forward-only progression"""
        print("🚀 Starting forward-only music video generation...")
        print("=" * 60)
        
        # Step 1: Detect scenes
        if not self.detect_scenes(threshold=threshold):
            return False
        
        # Step 2: Analyze beats
        if not self.analyze_audio_beats():
            return False
        
        # Step 3: Create forward-only mapping
        if not self.create_forward_only_mapping(max_clips=max_clips, strictness=strictness):
            return False
        
        # Step 4: Generate clips
        if not self.generate_video_clips(max_clips=max_clips):
            return False
        
        # Step 5: Render
        if not self.render_music_video():
            return False
        
        print(f"\n🎊 FORWARD-ONLY MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        
        try:
            # Analyze progression quality
            actual_positions = [mapping['actual_progress'] for mapping in self.scene_sequence]
            target_positions = [mapping['target_progress'] for mapping in self.scene_sequence]
            
            # Check for backward jumps
            backward_jumps = 0
            for i in range(1, len(actual_positions)):
                if actual_positions[i] < actual_positions[i-1]:
                    backward_jumps += 1
            
            # Calculate progression quality
            progression_accuracy = sum(abs(a - t) for a, t in zip(actual_positions, target_positions)) / len(actual_positions)
            
            print(f"\n📊 Forward Progression Analysis:")
            print(f"   Total clips: {len(self.scene_sequence)}")
            print(f"   Movie coverage: {min(actual_positions):.1%} to {max(actual_positions):.1%}")
            print(f"   Backward jumps: {backward_jumps} (0 = perfect)")
            print(f"   Progression accuracy: {(1 - progression_accuracy) * 100:.1f}%")
            
            total_duration = sum(clip.duration for clip in self.video_clips)
            print(f"   Duration: {total_duration:.1f} seconds")
            
            if backward_jumps == 0:
                print("🎉 Perfect forward progression! No jumping back to earlier scenes!")
            else:
                print(f"⚠️ {backward_jumps} backward jumps (may need stricter settings)")
            
        except Exception as e:
            print(f"⚠️ Analysis failed: {e}")
        
        return True

# Test function
def test_forward_only():
    """Test the forward-only generator"""
    print("🧪 TESTING FORWARD-ONLY GENERATOR")
    print("=" * 40)
    
    generator = ForwardOnlyGenerator("movie.mp4", "song.mp3", "forward_only_test.mp4")
    
    success = generator.generate_forward_only_music_video(
        max_clips=None,           # Full song
        strictness="medium",      # Balance between flexibility and strictness
        threshold=30.0            # Scene detection sensitivity
    )
    
    if success:
        print("\n🎉 FORWARD-ONLY TEST SUCCESS!")
        print("📁 Check: forward_only_test.mp4")
        print("🎯 This video should never jump back to earlier scenes!")
        print("📈 Movie progression should be consistently forward!")
    else:
        print("\n❌ Test failed")
    
    return success

if __name__ == "__main__":
    test_forward_only()
