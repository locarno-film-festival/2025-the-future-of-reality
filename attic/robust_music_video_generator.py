#!/usr/bin/env python3
"""
Robust Music Video Generator
Handles numpy formatting issues and provides fallbacks
"""

import librosa
import numpy as np
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import random
import json

class RobustMusicVideoGenerator:
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
    
    def safe_int(self, value):
        """Safely convert numpy values to Python int"""
        try:
            return int(value)
        except:
            return 0
    
    def detect_scenes(self, threshold=30.0, min_scene_len=1.0):
        """Detect scenes with error handling"""
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
            
            print(f"✅ Found {len(self.scenes)} scenes")
            return self.scenes
            
        except Exception as e:
            print(f"❌ Scene detection failed: {e}")
            return []
    
    def analyze_audio_beats(self, hop_length=512):
        """Analyze beats with robust error handling"""
        print("🎵 Analyzing audio beats...")
        
        try:
            # Load audio
            y, sr = librosa.load(self.audio_path)
            
            # Beat tracking with error handling
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
            beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)
            
            # Safely convert numpy values
            self.tempo = self.safe_float(tempo)
            self.beat_times = [self.safe_float(bt) for bt in beat_times]
            self.audio_duration = self.safe_float(len(y) / sr)
            
            print(f"✅ Detected {len(self.beat_times)} beats at {self.tempo:.1f} BPM")
            print(f"🎶 Audio duration: {self.audio_duration:.1f} seconds")
            
            return self.beat_times, self.tempo
            
        except Exception as e:
            print(f"❌ Beat analysis failed: {e}")
            # Fallback: create regular beats at 120 BPM
            try:
                y, sr = librosa.load(self.audio_path)
                duration = len(y) / sr
                self.tempo = 120.0
                self.audio_duration = duration
                # Create beats every 0.5 seconds (120 BPM)
                self.beat_times = [t for t in np.arange(0, duration, 0.5)]
                print(f"⚠️ Using fallback: {len(self.beat_times)} beats at 120 BPM")
                return self.beat_times, self.tempo
            except:
                print("❌ Complete audio analysis failure")
                return [], 120.0
    
    def create_scene_beat_mapping(self, style="random", max_clips=30):
        """Create mapping with fallbacks"""
        print("🎯 Creating scene-to-beat mapping...")
        
        if not self.scenes:
            print("❌ No scenes available")
            return []
        
        if not self.beat_times:
            print("❌ No beats available")
            return []
        
        scene_sequence = []
        beat_times = self.beat_times[:max_clips + 1] if max_clips else self.beat_times
        
        for i in range(len(beat_times) - 1):
            beat_start = beat_times[i]
            beat_end = beat_times[i + 1]
            beat_duration = beat_end - beat_start
            
            # Select scene based on style
            if style == "random":
                scene = random.choice(self.scenes)
            elif style == "sequential":
                scene = self.scenes[i % len(self.scenes)]
            else:  # duration_matched
                scene = min(self.scenes, key=lambda s: abs(s['duration'] - beat_duration))
            
            scene_sequence.append({
                'beat_start': beat_start,
                'beat_end': beat_end,
                'beat_duration': beat_duration,
                'scene': scene,
                'beat_index': i
            })
        
        self.scene_sequence = scene_sequence
        print(f"✅ Created {len(scene_sequence)} scene-beat mappings")
        return scene_sequence
    
    def generate_video_clips(self, max_clips=None):
        """Generate video clips with error handling"""
        print("🎬 Generating synchronized video clips...")
        
        if not hasattr(self, 'scene_sequence'):
            print("❌ No scene sequence available")
            return []
        
        video_clips = []
        
        try:
            video = VideoFileClip(self.video_path)
            
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
                        # Trim clip to beat duration
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
            print(f"✅ Generated {len(video_clips)} synchronized clips")
            return video_clips
            
        except Exception as e:
            print(f"❌ Video clip generation failed: {e}")
            return []
    
    def render_music_video(self, fade_duration=0.1):
        """Render final video with comprehensive error handling"""
        print("🎥 Rendering final music video...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("❌ No video clips to render")
            return False
        
        try:
            # Concatenate clips
            final_video = concatenate_videoclips(self.video_clips, method="compose")
            
            # Add audio
            audio = AudioFileClip(self.audio_path)
            
            # Trim audio to match video length
            if audio.duration > final_video.duration:
                audio = audio.subclip(0, final_video.duration)
            
            # Set audio to video
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
            
            print(f"🎉 Music video saved as {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Rendering failed: {e}")
            return False
    
    def generate_music_video(self, style="random", max_clips=25, threshold=30.0):
        """Complete pipeline with maximum error handling"""
        print("🚀 Starting music video generation...")
        print("=" * 50)
        
        success_count = 0
        
        # Step 1: Detect scenes
        if self.detect_scenes(threshold=threshold):
            success_count += 1
            print("✅ Scene detection completed")
        else:
            print("❌ Scene detection failed - cannot continue")
            return False
        
        # Step 2: Analyze beats
        if self.analyze_audio_beats():
            success_count += 1
            print("✅ Beat analysis completed")
        else:
            print("❌ Beat analysis failed - cannot continue")
            return False
        
        # Step 3: Create mapping
        if self.create_scene_beat_mapping(style=style, max_clips=max_clips):
            success_count += 1
            print("✅ Scene-beat mapping completed")
        else:
            print("❌ Scene-beat mapping failed - cannot continue")
            return False
        
        # Step 4: Generate clips
        if self.generate_video_clips(max_clips=max_clips):
            success_count += 1
            print("✅ Video clip generation completed")
        else:
            print("❌ Video clip generation failed - cannot continue")
            return False
        
        # Step 5: Render
        if self.render_music_video():
            success_count += 1
            print("✅ Rendering completed")
        else:
            print("❌ Rendering failed")
            return False
        
        print(f"\n🎊 SUCCESS! Completed {success_count}/5 steps")
        print(f"🎬 Your music video is ready: {self.output_path}")
        
        # Generate report
        try:
            report = {
                'input_video': self.video_path,
                'input_audio': self.audio_path,
                'output_video': self.output_path,
                'scenes_detected': len(self.scenes),
                'tempo_bpm': self.tempo,
                'clips_created': len(self.video_clips),
                'total_duration': sum(clip.duration for clip in self.video_clips)
            }
            
            print("\n📊 Generation Report:")
            for key, value in report.items():
                print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"⚠️ Report generation failed: {e}")
        
        return True

# Quick test function
def quick_test():
    """Quick test to verify everything works"""
    print("🧪 QUICK SYSTEM TEST")
    print("=" * 30)
    
    try:
        # Test imports
        import librosa
        from scenedetect import VideoManager
        from moviepy.editor import VideoFileClip
        print("✅ All imports successful")
        
        # Test librosa basic functionality
        y, sr = librosa.load(librosa.ex('brahms'), duration=2)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        print("✅ Librosa working")
        
        print("🎉 System ready for music video generation!")
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

if __name__ == "__main__":
    if quick_test():
        print("\n💡 Usage example:")
        print("generator = RobustMusicVideoGenerator('video.mp4', 'song.mp3')")
        print("generator.generate_music_video(style='random', max_clips=20)")
    else:
        print("❌ System not ready")
