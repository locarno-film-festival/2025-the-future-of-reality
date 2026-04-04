#!/usr/bin/env python3
"""
No-Repeat Progressive Music Video Generator
Ensures each scene is used only once throughout the entire video
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

class NoRepeatProgressiveGenerator:
    def __init__(self, video_path, audio_path, output_path="no_repeat_video.mp4"):
        self.video_path = video_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.scenes = []
        self.beat_times = []
        self.used_scenes = set()  # Track which scenes have been used
        
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
                        'duration': duration,
                        'used': False  # Track usage
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
    
    def create_no_repeat_mapping(self, max_clips=None, strategy="progressive_unique"):
        """
        Create scene mapping ensuring no scene repetition
        
        strategy options:
        - "progressive_unique": Progressive through movie, no repeats
        - "smart_distribution": Distribute scenes optimally across beats
        - "priority_sampling": Use best scenes first, fill with others
        """
        print(f"🎯 Creating no-repeat mapping ({strategy})...")
        
        if not self.scenes or not self.beat_times:
            print("❌ Need scenes and beats first")
            return []
        
        # Determine clips to use
        total_beats = len(self.beat_times) - 1
        total_scenes = len(self.scenes)
        num_clips = min(max_clips, total_beats) if max_clips else total_beats
        
        print(f"📊 Mapping {num_clips} beats to {total_scenes} scenes (no repeats)")
        
        if num_clips > total_scenes:
            print(f"⚠️ Warning: {num_clips} clips requested but only {total_scenes} scenes available")
            print(f"   Some scenes will need to be reused (impossible to avoid)")
            allow_reuse = True
        else:
            print(f"✅ Perfect: Enough scenes for no repetition")
            allow_reuse = False
        
        scene_sequence = []
        available_scenes = self.scenes.copy()  # Start with all scenes available
        
        if strategy == "progressive_unique":
            # Divide movie into segments, pick one unused scene from each segment
            for i in range(num_clips):
                progress = i / num_clips
                
                # Find unused scenes in this portion of the movie
                window_size = 1.0 / num_clips * 1.5  # Slightly larger windows for flexibility
                window_start = max(0, progress - window_size/2)
                window_end = min(1.0, progress + window_size/2)
                
                # Get unused scenes in this window
                unused_scenes_in_window = [
                    scene for scene in available_scenes
                    if (window_start <= scene['position_ratio'] <= window_end) and not scene['used']
                ]
                
                # If no unused scenes in window, expand search
                if not unused_scenes_in_window and not allow_reuse:
                    # Look for any unused scene, prefer closest to target position
                    unused_scenes = [scene for scene in available_scenes if not scene['used']]
                    if unused_scenes:
                        unused_scenes_in_window = [min(unused_scenes, 
                                                     key=lambda s: abs(s['position_ratio'] - progress))]
                
                # If still no scenes and reuse allowed, pick from window regardless of usage
                if not unused_scenes_in_window and allow_reuse:
                    unused_scenes_in_window = [
                        scene for scene in available_scenes
                        if window_start <= scene['position_ratio'] <= window_end
                    ]
                
                # Final fallback: any available scene
                if not unused_scenes_in_window:
                    unused_scenes = [scene for scene in available_scenes if not scene['used']]
                    unused_scenes_in_window = unused_scenes[:1] if unused_scenes else available_scenes[:1]
                
                # Select scene
                if unused_scenes_in_window:
                    selected_scene = random.choice(unused_scenes_in_window)
                    selected_scene['used'] = True  # Mark as used
                    
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
                        'reused': selected_scene['id'] in self.used_scenes
                    })
                    
                    self.used_scenes.add(selected_scene['id'])
        
        elif strategy == "smart_distribution":
            # Distribute scenes evenly across the song duration
            # Select scenes to maximize coverage without repetition
            
            # Calculate ideal scene indices for even distribution
            scene_indices = np.linspace(0, len(available_scenes) - 1, num_clips).astype(int)
            used_indices = set()
            
            for i in range(num_clips):
                # Try to use the ideal scene for this position
                ideal_index = scene_indices[i]
                
                # Find unused scene closest to ideal
                available_indices = [j for j in range(len(available_scenes)) 
                                   if j not in used_indices]
                
                if available_indices:
                    # Pick unused scene closest to ideal position
                    best_index = min(available_indices, key=lambda x: abs(x - ideal_index))
                    selected_scene = available_scenes[best_index]
                    used_indices.add(best_index)
                    
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
                        'movie_progress': i / num_clips,
                        'reused': False
                    })
        
        elif strategy == "priority_sampling":
            # Use longer/more important scenes first, fill with others
            # Sort scenes by some priority metric (e.g., duration)
            sorted_scenes = sorted(available_scenes, key=lambda s: -s['duration'])  # Longer scenes first
            
            for i in range(num_clips):
                if i < len(sorted_scenes):
                    selected_scene = sorted_scenes[i]
                else:
                    # Fallback to any remaining scene
                    selected_scene = available_scenes[i % len(available_scenes)]
                
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
                    'movie_progress': selected_scene['position_ratio'],
                    'reused': False
                })
        
        self.scene_sequence = scene_sequence
        
        # Analyze uniqueness
        unique_scenes = len(set(mapping['scene']['id'] for mapping in scene_sequence))
        total_mappings = len(scene_sequence)
        uniqueness_rate = unique_scenes / total_mappings * 100
        
        print(f"✅ Created {len(scene_sequence)} mappings")
        print(f"📊 Uniqueness: {unique_scenes}/{total_mappings} scenes ({uniqueness_rate:.1f}% unique)")
        
        if uniqueness_rate == 100:
            print("🎉 Perfect! No scene repetition!")
        elif uniqueness_rate > 90:
            print("✅ Excellent scene variety!")
        else:
            print("⚠️ Some repetition (more beats than available scenes)")
        
        return scene_sequence
    
    def generate_video_clips(self, max_clips=None):
        """Generate video clips ensuring no scene repetition"""
        print("🎬 Generating unique video clips...")
        
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
                        # Random start point within scene
                        max_start = scene_clip.duration - beat_duration
                        start_offset = random.uniform(0, max_start) if max_start > 0 else 0
                        scene_clip = scene_clip.subclip(start_offset, start_offset + beat_duration)
                    else:
                        # Speed up clip to fit beat duration
                        speed_factor = scene_clip.duration / beat_duration
                        scene_clip = scene_clip.fx('speedx', speed_factor)
                    
                    video_clips.append(scene_clip)
                    
                except Exception as e:
                    print(f"⚠️ Skipping clip {i}: {e}")
                    continue
            
            self.video_clips = video_clips
            print(f"✅ Generated {len(video_clips)} unique clips")
            return video_clips
            
        except Exception as e:
            print(f"❌ Video clip generation failed: {e}")
            return []
    
    def render_music_video(self, fade_duration=0.05):
        """Render the final no-repeat music video"""
        print("🎥 Rendering no-repeat music video...")
        
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
            
            print(f"🎉 No-repeat music video saved as {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Rendering failed: {e}")
            return False
    
    def generate_no_repeat_music_video(self, max_clips=None, strategy="progressive_unique", threshold=30.0):
        """Complete pipeline ensuring no scene repetition"""
        print("🚀 Starting no-repeat music video generation...")
        print("=" * 60)
        
        # Step 1: Detect scenes
        if not self.detect_scenes(threshold=threshold):
            return False
        
        # Step 2: Analyze beats
        if not self.analyze_audio_beats():
            return False
        
        # Step 3: Create no-repeat mapping
        if not self.create_no_repeat_mapping(max_clips=max_clips, strategy=strategy):
            return False
        
        # Step 4: Generate clips
        if not self.generate_video_clips(max_clips=max_clips):
            return False
        
        # Step 5: Render
        if not self.render_music_video():
            return False
        
        print(f"\n🎊 NO-REPEAT MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        
        try:
            # Final uniqueness analysis
            unique_scenes = len(set(mapping['scene']['id'] for mapping in self.scene_sequence))
            total_clips = len(self.scene_sequence)
            
            print(f"\n📊 Final Analysis:")
            print(f"   Total clips: {total_clips}")
            print(f"   Unique scenes used: {unique_scenes}")
            print(f"   Uniqueness rate: {unique_scenes/total_clips*100:.1f}%")
            print(f"   Strategy: {strategy}")
            
            total_duration = sum(clip.duration for clip in self.video_clips)
            print(f"   Duration: {total_duration:.1f} seconds")
            
            if unique_scenes == total_clips:
                print("🎉 Perfect! Zero scene repetition achieved!")
            elif unique_scenes / total_clips > 0.95:
                print("✅ Excellent! Minimal scene repetition!")
            else:
                print(f"⚠️ Some repetition unavoidable ({len(self.scenes)} scenes for {total_clips} clips)")
            
        except Exception as e:
            print(f"⚠️ Analysis failed: {e}")
        
        return True

# Test function
def test_no_repeat():
    """Test the no-repeat generator"""
    print("🧪 TESTING NO-REPEAT GENERATOR")
    print("=" * 40)
    
    generator = NoRepeatProgressiveGenerator("movie.mp4", "song.mp3", "no_repeat_test.mp4")
    
    success = generator.generate_no_repeat_music_video(
        max_clips=None,                    # Full song
        strategy="progressive_unique",     # Progressive through movie, no repeats
        threshold=30.0                     # Scene detection sensitivity
    )
    
    if success:
        print("\n🎉 NO-REPEAT TEST SUCCESS!")
        print("📁 Check: no_repeat_test.mp4")
        print("🎯 This video should have zero repeated scenes!")
    else:
        print("\n❌ Test failed")
    
    return success

if __name__ == "__main__":
    test_no_repeat()
