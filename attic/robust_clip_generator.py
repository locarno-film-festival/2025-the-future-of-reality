#!/usr/bin/env python3
"""
Robust Clip Generator with comprehensive error handling
Identifies and skips problematic clips instead of failing completely
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

class RobustClipGenerator:
    def __init__(self, video_path, audio_path, output_path="robust_video.mp4"):
        self.video_path = video_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.scenes = []
        self.beat_times = []
        self.failed_clips = []
        
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
        """Create mapping with guaranteed zero backward jumps"""
        print("🎯 Creating guaranteed perfect forward mapping...")
        
        if not self.scenes or not self.beat_times:
            print("❌ Need scenes and beats first")
            return []
        
        total_beats = len(self.beat_times) - 1
        num_clips = min(max_clips, total_beats) if max_clips else total_beats
        total_scenes = len(self.scenes)
        
        print(f"📊 Perfect allocation: {num_clips} beats → {total_scenes} scenes")
        
        scene_sequence = []
        
        # Calculate scene indices for perfect distribution
        scene_indices = []
        for i in range(num_clips):
            scene_position = (i / num_clips) * (total_scenes - 1)
            scene_index = int(round(scene_position))
            scene_indices.append(scene_index)
        
        # Ensure no duplicates and maintain order
        unique_indices = []
        last_index = -1
        
        for target_index in scene_indices:
            actual_index = target_index
            while actual_index in unique_indices or actual_index <= last_index:
                actual_index += 1
                if actual_index >= total_scenes:
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
                    'actual_progress': selected_scene['position_ratio']
                })
        
        self.scene_sequence = scene_sequence
        
        # Verify zero backward jumps
        actual_positions = [mapping['actual_progress'] for mapping in scene_sequence]
        backward_jumps = sum(1 for i in range(1, len(actual_positions)) 
                           if actual_positions[i] < actual_positions[i-1])
        
        print(f"✅ Created {len(scene_sequence)} perfectly ordered mappings")
        print(f"📈 Movie progression: {min(actual_positions):.1%} to {max(actual_positions):.1%}")
        print(f"🎯 Backward jumps: {backward_jumps} (GUARANTEED: 0)")
        
        return scene_sequence
    
    def validate_clip(self, clip, clip_index, scene_id):
        """Validate that a clip is properly formed"""
        try:
            if clip is None:
                self.failed_clips.append(f"Clip {clip_index} (Scene {scene_id}): Clip is None")
                return False
            
            if not hasattr(clip, 'duration'):
                self.failed_clips.append(f"Clip {clip_index} (Scene {scene_id}): No duration attribute")
                return False
            
            if clip.duration <= 0:
                self.failed_clips.append(f"Clip {clip_index} (Scene {scene_id}): Invalid duration {clip.duration}")
                return False
            
            if not hasattr(clip, 'get_frame'):
                self.failed_clips.append(f"Clip {clip_index} (Scene {scene_id}): No get_frame method")
                return False
            
            # Try to get the first frame to validate the clip
            try:
                test_frame = clip.get_frame(0)
                if test_frame is None:
                    self.failed_clips.append(f"Clip {clip_index} (Scene {scene_id}): get_frame returned None")
                    return False
            except Exception as frame_error:
                self.failed_clips.append(f"Clip {clip_index} (Scene {scene_id}): get_frame failed - {frame_error}")
                return False
            
            return True
            
        except Exception as e:
            self.failed_clips.append(f"Clip {clip_index} (Scene {scene_id}): Validation error - {e}")
            return False
    
    def generate_robust_video_clips(self, max_clips=None):
        """Generate video clips with comprehensive error handling and validation"""
        print("🎬 Generating robust video clips with validation...")
        
        if not hasattr(self, 'scene_sequence'):
            print("❌ No scene sequence available")
            return []
        
        video_clips = []
        video = None
        
        try:
            video = VideoFileClip(self.video_path, verbose=False)
            print(f"✅ Video loaded successfully: {video.duration:.1f}s")
        except Exception as e:
            print(f"❌ Cannot load video: {e}")
            return []
        
        sequence = self.scene_sequence
        if max_clips:
            sequence = sequence[:max_clips]
        
        valid_clips = 0
        skipped_clips = 0
        
        for i, mapping in enumerate(sequence):
            try:
                scene = mapping['scene']
                beat_duration = mapping['beat_duration']
                scene_id = scene['id']
                
                print(f"Processing clip {i+1}/{len(sequence)} (Scene {scene_id})...", end=" ")
                
                # Validate scene bounds against video duration
                if scene['end'] > video.duration:
                    print(f"⚠️ Scene extends beyond video duration")
                    scene_end = video.duration - 0.1  # Leave small buffer
                    scene_start = max(scene['start'], scene_end - beat_duration)
                else:
                    scene_start = scene['start']
                    scene_end = scene['end']
                
                if scene_start >= scene_end:
                    print(f"❌ Invalid scene bounds")
                    self.failed_clips.append(f"Clip {i} (Scene {scene_id}): Invalid bounds {scene_start}-{scene_end}")
                    skipped_clips += 1
                    continue
                
                # Extract scene clip with error handling
                try:
                    scene_clip = video.subclip(scene_start, scene_end)
                    
                    # Validate the extracted clip
                    if not self.validate_clip(scene_clip, i, scene_id):
                        print(f"❌ Failed validation")
                        if scene_clip:
                            try:
                                scene_clip.close()
                            except:
                                pass
                        skipped_clips += 1
                        continue
                    
                except Exception as extract_error:
                    print(f"❌ Extraction failed: {extract_error}")
                    self.failed_clips.append(f"Clip {i} (Scene {scene_id}): Extraction failed - {extract_error}")
                    skipped_clips += 1
                    continue
                
                # Adjust clip duration to match beat
                try:
                    if scene_clip.duration > beat_duration:
                        # Trim to beat duration
                        max_start = scene_clip.duration - beat_duration
                        start_offset = random.uniform(0, max_start * 0.5) if max_start > 0 else 0
                        trimmed_clip = scene_clip.subclip(start_offset, start_offset + beat_duration)
                        
                        # Validate trimmed clip
                        if not self.validate_clip(trimmed_clip, i, scene_id):
                            print(f"❌ Trimmed clip failed validation")
                            try:
                                scene_clip.close()
                                trimmed_clip.close()
                            except:
                                pass
                            skipped_clips += 1
                            continue
                        
                        # Close original and use trimmed
                        scene_clip.close()
                        scene_clip = trimmed_clip
                        
                    elif scene_clip.duration < beat_duration and scene_clip.duration > 0.1:
                        # Speed up clip to fit beat duration
                        speed_factor = scene_clip.duration / beat_duration
                        sped_clip = scene_clip.fx('speedx', speed_factor)
                        
                        # Validate sped up clip
                        if not self.validate_clip(sped_clip, i, scene_id):
                            print(f"❌ Sped up clip failed validation")
                            try:
                                scene_clip.close()
                                sped_clip.close()
                            except:
                                pass
                            skipped_clips += 1
                            continue
                        
                        # Close original and use sped up
                        scene_clip.close()
                        scene_clip = sped_clip
                    
                    # Final validation before adding to list
                    if self.validate_clip(scene_clip, i, scene_id):
                        video_clips.append(scene_clip)
                        valid_clips += 1
                        print("✅")
                    else:
                        print("❌ Final validation failed")
                        try:
                            scene_clip.close()
                        except:
                            pass
                        skipped_clips += 1
                    
                except Exception as adjust_error:
                    print(f"❌ Adjustment failed: {adjust_error}")
                    self.failed_clips.append(f"Clip {i} (Scene {scene_id}): Adjustment failed - {adjust_error}")
                    try:
                        scene_clip.close()
                    except:
                        pass
                    skipped_clips += 1
                    continue
                
            except Exception as e:
                print(f"❌ Processing failed: {e}")
                self.failed_clips.append(f"Clip {i}: Processing failed - {e}")
                skipped_clips += 1
                continue
        
        # Cleanup
        if video:
            video.close()
        
        self.video_clips = video_clips
        
        print(f"\n📊 CLIP GENERATION SUMMARY:")
        print(f"   Valid clips: {valid_clips}")
        print(f"   Skipped clips: {skipped_clips}")
        print(f"   Success rate: {(valid_clips / len(sequence) * 100):.1f}%")
        
        if self.failed_clips:
            print(f"\n⚠️ Failed clips ({len(self.failed_clips)}):")
            for failure in self.failed_clips[:5]:  # Show first 5 failures
                print(f"   • {failure}")
            if len(self.failed_clips) > 5:
                print(f"   ... and {len(self.failed_clips) - 5} more")
        
        return video_clips
    
    def render_robust_music_video(self, fade_duration=0.05):
        """Render music video with additional validation"""
        print("🎥 Rendering robust music video...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("❌ No valid video clips to render")
            return False
        
        # Final validation of all clips before rendering
        print("🔍 Final validation of all clips before rendering...")
        valid_clips = []
        
        for i, clip in enumerate(self.video_clips):
            if self.validate_clip(clip, i, f"final_{i}"):
                valid_clips.append(clip)
            else:
                print(f"⚠️ Removing invalid clip {i} before rendering")
        
        if not valid_clips:
            print("❌ No valid clips remain after final validation")
            return False
        
        print(f"✅ {len(valid_clips)} clips passed final validation")
        
        try:
            # Concatenate valid clips
            final_video = concatenate_videoclips(valid_clips, method="compose")
            
            # Add audio
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
            
            # Cleanup
            final_video.close()
            audio.close()
            for clip in valid_clips:
                try:
                    clip.close()
                except:
                    pass
            
            print(f"🎉 Robust music video saved as {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Rendering failed: {e}")
            return False
    
    def generate_robust_music_video(self, max_clips=None, threshold=30.0):
        """Generate music video with comprehensive error handling"""
        print("🛡️ Starting ROBUST music video generation...")
        print("=" * 55)
        print("This version validates every clip and skips problematic ones!")
        print()
        
        # Step 1: Scene detection
        if not self.detect_scenes(threshold=threshold):
            return False
        
        # Step 2: Beat analysis
        if not self.analyze_audio_beats():
            return False
        
        # Step 3: Perfect forward mapping
        if not self.create_guaranteed_forward_mapping(max_clips=max_clips):
            return False
        
        # Step 4: Robust clip generation with validation
        if not self.generate_robust_video_clips(max_clips=max_clips):
            return False
        
        # Step 5: Robust rendering with final validation
        if not self.render_robust_music_video():
            return False
        
        print(f"\n🎊 ROBUST MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        
        # Final analysis
        try:
            if hasattr(self, 'scene_sequence') and hasattr(self, 'video_clips'):
                total_requested = len(self.scene_sequence)
                total_rendered = len(self.video_clips)
                success_rate = (total_rendered / total_requested * 100)
                
                print(f"\n📊 ROBUST GENERATION REPORT:")
                print(f"   Clips requested: {total_requested}")
                print(f"   Clips rendered: {total_rendered}")
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Failed clips: {len(self.failed_clips)}")
                
                if success_rate >= 95:
                    print("🏆 EXCELLENT! Minimal clip failures!")
                elif success_rate >= 80:
                    print("✅ GOOD! Most clips rendered successfully!")
                else:
                    print("⚠️ Many clips failed - check video file quality")
        
        except Exception as e:
            print(f"⚠️ Report generation failed: {e}")
        
        return True

def test_robust():
    """Test the robust clip generator"""
    print("🛡️ TESTING ROBUST CLIP GENERATOR")
    print("=" * 45)
    print("This version validates every clip and skips any problematic ones!")
    print()
    
    generator = RobustClipGenerator("movie.mp4", "song.mp3", "robust_test.mp4")
    
    success = generator.generate_robust_music_video(
        max_clips=None,     # Full song
        threshold=30.0      # Scene detection sensitivity
    )
    
    if success:
        print("\n🎉 ROBUST TEST SUCCESS!")
        print("📁 Check: robust_test.mp4")
        print("🎯 This should render successfully even if some clips fail!")
    else:
        print("\n❌ Robust test failed")
    
    return success

if __name__ == "__main__":
    test_robust()
