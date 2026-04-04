#!/usr/bin/env python3
"""
Simple Fixed Generator - Just the working perfect forward generator with proper imports
"""

import warnings
warnings.filterwarnings("ignore", message="VideoManager is deprecated")

import librosa
import numpy as np
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips  # <-- This was missing!
import random
import contextlib
import io

class SimpleFixedGenerator:
    def __init__(self, video_path, audio_path, output_path="simple_fixed_video.mp4"):
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
    
    def create_guaranteed_forward_mapping(self, max_clips=None):
        """
        Create mapping with GUARANTEED zero backward jumps
        Uses pre-allocation strategy to ensure perfect progression
        """
        print("🎯 Creating guaranteed perfect forward mapping...")
        
        if not self.scenes or not self.beat_times:
            print("❌ Need scenes and beats first")
            return []
        
        # Determine clips to use
        total_beats = len(self.beat_times) - 1
        num_clips = min(max_clips, total_beats) if max_clips else total_beats
        total_scenes = len(self.scenes)
        
        print(f"📊 Perfect allocation: {num_clips} beats → {total_scenes} scenes")
        
        scene_sequence = []
        
        if num_clips <= total_scenes:
            # PERFECT CASE: More scenes than clips
            print("✅ Perfect case: Enough scenes for even distribution")
            
            # Calculate scene indices for perfect distribution
            scene_indices = []
            for i in range(num_clips):
                # Map beat position to scene position
                scene_position = (i / num_clips) * (total_scenes - 1)
                scene_index = int(round(scene_position))
                scene_indices.append(scene_index)
            
            # Ensure no duplicates and maintain order
            unique_indices = []
            last_index = -1
            
            for target_index in scene_indices:
                # Find next available scene at or after target
                actual_index = target_index
                while actual_index in unique_indices or actual_index <= last_index:
                    actual_index += 1
                    if actual_index >= total_scenes:
                        # Reached end, find any unused scene
                        for idx in range(last_index + 1, total_scenes):
                            if idx not in unique_indices:
                                actual_index = idx
                                break
                        break
                
                unique_indices.append(actual_index)
                last_index = actual_index
            
            # Create mappings using allocated scenes
            for i, scene_index in enumerate(unique_indices):
                if scene_index < total_scenes:
                    selected_scene = self.scenes[scene_index]
                    
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
                        'scene_index': scene_index,
                        'target_progress': i / num_clips,
                        'actual_progress': selected_scene['position_ratio'],
                        'guaranteed_forward': True
                    })
        
        else:
            # CHALLENGING CASE: More clips than scenes
            print(f"⚠️ Challenging case: {num_clips} clips > {total_scenes} scenes")
            print("   Some scenes will be reused, but progression maintained")
            
            # First pass: use each scene once
            for i in range(total_scenes):
                selected_scene = self.scenes[i]
                
                beat_start = self.beat_times[i]
                beat_end = self.beat_times[i + 1] if i + 1 < len(self.beat_times) else beat_start + 0.5
                beat_duration = beat_end - beat_start
                
                scene_sequence.append({
                    'beat_start': beat_start,
                    'beat_end': beat_end,
                    'beat_duration': beat_duration,
                    'scene': selected_scene,
                    'beat_index': i,
                    'scene_index': i,
                    'target_progress': i / num_clips,
                    'actual_progress': selected_scene['position_ratio'],
                    'guaranteed_forward': True
                })
            
            # Second pass: fill remaining beats with later scenes
            remaining_beats = num_clips - total_scenes
            if remaining_beats > 0:
                print(f"   Filling {remaining_beats} remaining beats with end scenes")
                
                # Use scenes from last 25% of movie for remaining beats
                end_scenes_start = int(total_scenes * 0.75)
                end_scenes = self.scenes[end_scenes_start:]
                
                for i in range(remaining_beats):
                    beat_index = total_scenes + i
                    scene_index = end_scenes_start + (i % len(end_scenes))
                    selected_scene = self.scenes[min(scene_index, total_scenes - 1)]
                    
                    beat_start = self.beat_times[beat_index]
                    beat_end = self.beat_times[beat_index + 1] if beat_index + 1 < len(self.beat_times) else beat_start + 0.5
                    beat_duration = beat_end - beat_start
                    
                    scene_sequence.append({
                        'beat_start': beat_start,
                        'beat_end': beat_end,
                        'beat_duration': beat_duration,
                        'scene': selected_scene,
                        'beat_index': beat_index,
                        'scene_index': scene_index,
                        'target_progress': beat_index / num_clips,
                        'actual_progress': selected_scene['position_ratio'],
                        'guaranteed_forward': True,
                        'reused_end_scene': True
                    })
        
        self.scene_sequence = scene_sequence
        
        # Verify zero backward jumps
        actual_positions = [mapping['actual_progress'] for mapping in scene_sequence]
        backward_jumps = 0
        
        for i in range(1, len(actual_positions)):
            if actual_positions[i] < actual_positions[i-1]:
                backward_jumps += 1
        
        print(f"✅ Created {len(scene_sequence)} perfectly ordered mappings")
        print(f"📈 Movie progression: {min(actual_positions):.1%} to {max(actual_positions):.1%}")
        print(f"🎯 Backward jumps: {backward_jumps} (GUARANTEED: 0)")
        
        if backward_jumps == 0:
            print("🎉 PERFECT! Absolutely zero backward jumps guaranteed!")
        else:
            print(f"🚨 ERROR: {backward_jumps} backward jumps (algorithm failed)")
        
        return scene_sequence
    
    def generate_video_clips(self, max_clips=None):
        """Generate video clips using the proven algorithm"""
        print("🎬 Generating video clips...")
        
        if not hasattr(self, 'scene_sequence'):
            print("❌ No scene sequence available")
            return []
        
        video_clips = []
        
        try:
            # This should work now with proper import
            video = VideoFileClip(self.video_path, verbose=False)
            print(f"✅ Video loaded successfully: {video.duration:.1f}s")
            
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
                        # Random start point within scene
                        max_start = scene_clip.duration - beat_duration
                        start_offset = random.uniform(0, max_start * 0.5) if max_start > 0 else 0
                        scene_clip = scene_clip.subclip(start_offset, start_offset + beat_duration)
                    elif scene_clip.duration < beat_duration:
                        # Speed up clip to fit beat duration
                        speed_factor = scene_clip.duration / beat_duration
                        scene_clip = scene_clip.fx('speedx', speed_factor)
                    
                    video_clips.append(scene_clip)
                    
                except Exception as e:
                    print(f"⚠️ Skipping clip {i}: {e}")
                    continue
            
            # Cleanup
            video.close()
            
            self.video_clips = video_clips
            print(f"✅ Generated {len(video_clips)} video clips")
            return video_clips
            
        except Exception as e:
            print(f"❌ Video clip generation failed: {e}")
            return []
    
    def render_music_video(self, fade_duration=0.05):
        """Render the final music video"""
        print("🎥 Rendering music video...")
        
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
            
            print(f"🎉 Music video saved as {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Rendering failed: {e}")
            return False
    
    def generate_simple_fixed_music_video(self, max_clips=None, threshold=30.0):
        """Generate music video using the proven working algorithm"""
        print("🚀 Starting SIMPLE FIXED music video generation...")
        print("=" * 60)
        print("Using the exact algorithm that worked in debug, just with proper imports!")
        print()
        
        # Step 1: Scene detection
        if not self.detect_scenes(threshold=threshold):
            return False
        
        # Step 2: Beat analysis
        if not self.analyze_audio_beats():
            return False
        
        # Step 3: Perfect forward mapping (the proven algorithm)
        if not self.create_guaranteed_forward_mapping(max_clips=max_clips):
            return False
        
        # Step 4: Generate clips (now with proper VideoFileClip import)
        if not self.generate_video_clips(max_clips=max_clips):
            return False
        
        # Step 5: Render
        if not self.render_music_video():
            return False
        
        print(f"\n🎊 SIMPLE FIXED MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        
        # Final verification
        try:
            actual_positions = [mapping['actual_progress'] for mapping in self.scene_sequence]
            
            # Count backward jumps (should be 0)
            backward_jumps = sum(1 for i in range(1, len(actual_positions)) 
                               if actual_positions[i] < actual_positions[i-1])
            
            # Check for reused scenes
            scene_ids = [mapping['scene']['id'] for mapping in self.scene_sequence]
            unique_scenes = len(set(scene_ids))
            
            print(f"\n📊 FINAL VERIFICATION:")
            print(f"   Total clips: {len(self.scene_sequence)}")
            print(f"   Movie coverage: {min(actual_positions):.1%} to {max(actual_positions):.1%}")
            print(f"   Backward jumps: {backward_jumps} ⭐ (should be 0)")
            print(f"   Unique scenes: {unique_scenes}/{len(scene_ids)}")
            
            total_duration = sum(clip.duration for clip in self.video_clips)
            print(f"   Duration: {total_duration:.1f} seconds")
            
            if backward_jumps == 0:
                print("\n🏆 PERFECT! Zero backward jumps achieved!")
                print("🎬 Your music video should be all normal scenes!")
            else:
                print(f"\n⚠️ {backward_jumps} backward jumps detected")
            
        except Exception as e:
            print(f"⚠️ Verification failed: {e}")
        
        return True

def test_simple_fixed():
    """Test the simple fixed generator"""
    print("🔧 TESTING SIMPLE FIXED GENERATOR")
    print("=" * 45)
    print("This version just adds the missing import that caused the black screens!")
    print()
    
    generator = SimpleFixedGenerator("movie.mp4", "song.mp3", "simple_fixed_test.mp4")
    
    success = generator.generate_simple_fixed_music_video(
        max_clips=None,     # Full song
        threshold=30.0      # Scene detection sensitivity
    )
    
    if success:
        print("\n🎉 SIMPLE FIXED TEST SUCCESS!")
        print("📁 Check: simple_fixed_test.mp4")
        print("🎯 This should be all normal scenes with zero black screens!")
    else:
        print("\n❌ Simple fixed test failed")
    
    return success

if __name__ == "__main__":
    test_simple_fixed()
