#!/usr/bin/env python3
"""
Conservative Bulletproof Generator
Uses the proven perfect forward algorithm with minimal emergency fallbacks
"""

from perfect_forward_generator import PerfectForwardGenerator
from moviepy.editor import ColorClip
import contextlib
import io

class ConservativeBulletproofGenerator(PerfectForwardGenerator):
    """Conservative version that only uses emergency fallbacks when truly necessary"""
    
    def __init__(self, video_path, audio_path, output_path="conservative_video.mp4"):
        super().__init__(video_path, audio_path, output_path)
        self.emergency_clips_used = 0
        self.fallback_reasons = []
        
    def create_emergency_black_clip(self, duration, reason="Emergency"):
        """Create emergency black screen only when absolutely necessary"""
        try:
            black_clip = ColorClip(
                size=(1920, 1080),
                color=(0, 0, 0),
                duration=duration
            )
            
            self.emergency_clips_used += 1
            self.fallback_reasons.append(reason)
            print(f"🚨 EMERGENCY: Black screen used ({duration:.2f}s) - {reason}")
            
            return black_clip
            
        except Exception as e:
            print(f"🚨 CRITICAL: Cannot create emergency black screen: {e}")
            return None
    
    def generate_conservative_clips(self, max_clips=None):
        """Generate clips using the proven perfect algorithm with emergency backup"""
        print("🎬 Generating conservative clips (black screens only if critical error)...")
        
        if not hasattr(self, 'scene_sequence'):
            print("❌ No scene sequence available")
            return []
        
        video_clips = []
        video = None
        
        # Load video with error handling
        try:
            video = VideoFileClip(self.video_path, verbose=False)
            print(f"✅ Video loaded: {video.duration:.1f}s")
        except Exception as e:
            print(f"🚨 CRITICAL: Cannot load video: {e}")
            print("   This will require emergency black screens for everything")
            video = None
        
        sequence = self.scene_sequence
        if max_clips:
            sequence = sequence[:max_clips]
        
        successful_clips = 0
        
        for i, mapping in enumerate(sequence):
            try:
                beat_duration = mapping['beat_duration']
                scene = mapping.get('scene')
                
                # Only use black screen if we have no scene AND no video
                if scene is None:
                    if video is None:
                        # TRUE EMERGENCY: No video file at all
                        emergency_clip = self.create_emergency_black_clip(
                            beat_duration, 
                            "No video file available"
                        )
                        if emergency_clip:
                            video_clips.append(emergency_clip)
                        continue
                    else:
                        print(f"🚨 Beat {i}: Scene is None but video exists - this shouldn't happen!")
                        # Try to use a fallback scene
                        fallback_scene = self.scenes[min(i, len(self.scenes) - 1)] if self.scenes else None
                        if fallback_scene:
                            scene = fallback_scene
                            print(f"   Using fallback scene {scene['id']}")
                        else:
                            emergency_clip = self.create_emergency_black_clip(
                                beat_duration,
                                f"No scenes available for beat {i}"
                            )
                            if emergency_clip:
                                video_clips.append(emergency_clip)
                            continue
                
                if video is None:
                    # No video loaded - must use black screen
                    emergency_clip = self.create_emergency_black_clip(
                        beat_duration,
                        "Video file could not be loaded"
                    )
                    if emergency_clip:
                        video_clips.append(emergency_clip)
                    continue
                
                # Normal processing: we have both scene and video
                try:
                    # Validate scene bounds
                    scene_start = max(0, scene['start'])
                    scene_end = min(scene['end'], video.duration)
                    
                    if scene_end <= scene_start:
                        print(f"⚠️ Scene {scene['id']} has invalid bounds, using emergency black")
                        emergency_clip = self.create_emergency_black_clip(
                            beat_duration,
                            f"Scene {scene['id']} invalid bounds"
                        )
                        if emergency_clip:
                            video_clips.append(emergency_clip)
                        continue
                    
                    # Extract scene clip
                    scene_clip = video.subclip(scene_start, scene_end)
                    
                    # Adjust duration to match beat
                    if scene_clip.duration > beat_duration:
                        # Trim to beat duration
                        max_start = scene_clip.duration - beat_duration
                        start_offset = random.uniform(0, max_start * 0.5) if max_start > 0 else 0
                        scene_clip = scene_clip.subclip(start_offset, start_offset + beat_duration)
                    elif scene_clip.duration < beat_duration:
                        # Speed up to match beat
                        if scene_clip.duration > 0.1:  # Only if scene is reasonable length
                            speed_factor = scene_clip.duration / beat_duration
                            scene_clip = scene_clip.fx('speedx', speed_factor)
                        else:
                            # Scene too short - emergency black
                            print(f"⚠️ Scene {scene['id']} too short ({scene_clip.duration:.2f}s)")
                            emergency_clip = self.create_emergency_black_clip(
                                beat_duration,
                                f"Scene {scene['id']} too short"
                            )
                            if emergency_clip:
                                video_clips.append(emergency_clip)
                            continue
                    
                    video_clips.append(scene_clip)
                    successful_clips += 1
                    
                except Exception as scene_error:
                    print(f"🚨 Error processing scene {scene['id']}: {scene_error}")
                    emergency_clip = self.create_emergency_black_clip(
                        beat_duration,
                        f"Scene {scene['id']} processing error"
                    )
                    if emergency_clip:
                        video_clips.append(emergency_clip)
                
            except Exception as beat_error:
                print(f"🚨 Error processing beat {i}: {beat_error}")
                # Try to create emergency clip with fallback duration
                try:
                    emergency_duration = mapping.get('beat_duration', 0.5)
                    emergency_clip = self.create_emergency_black_clip(
                        emergency_duration,
                        f"Beat {i} processing error"
                    )
                    if emergency_clip:
                        video_clips.append(emergency_clip)
                except:
                    print(f"🚨 Cannot even create emergency clip for beat {i}")
                    continue
        
        # Cleanup
        if video:
            video.close()
        
        self.video_clips = video_clips
        
        # Report results
        total_clips = len(video_clips)
        emergency_rate = (self.emergency_clips_used / total_clips * 100) if total_clips > 0 else 0
        
        print(f"✅ Generated {total_clips} clips")
        print(f"   Successful scene clips: {successful_clips}")
        print(f"   Emergency black screens: {self.emergency_clips_used}")
        print(f"   Success rate: {((total_clips - self.emergency_clips_used) / total_clips * 100):.1f}%")
        
        if self.emergency_clips_used == 0:
            print("🎉 Perfect! No emergency fallbacks needed!")
        else:
            print("🚨 Emergency fallbacks used:")
            for reason in set(self.fallback_reasons):
                count = self.fallback_reasons.count(reason)
                print(f"   • {reason} ({count} times)")
        
        return video_clips
    
    def generate_conservative_music_video(self, max_clips=None, threshold=30.0):
        """Generate music video using conservative approach"""
        print("🛡️ Starting CONSERVATIVE bulletproof generation...")
        print("=" * 55)
        print("Uses proven algorithm with emergency fallbacks only when critical!")
        print()
        
        # Use the proven perfect forward algorithm for mapping
        success_steps = 0
        
        # Step 1: Scene detection
        try:
            if self.detect_scenes(threshold=threshold):
                success_steps += 1
                print("✅ Scene detection successful")
            else:
                print("🚨 No scenes detected - will need emergency fallbacks")
        except Exception as e:
            print(f"🚨 Scene detection failed: {e}")
            self.scenes = []  # Continue with empty scenes
        
        # Step 2: Beat analysis
        try:
            if self.analyze_audio_beats():
                success_steps += 1
                print("✅ Beat analysis successful")
            else:
                print("🚨 Beat analysis failed - using fallback beats")
                # Create fallback beats
                self.beat_times = [i * 0.5 for i in range(120)]
                self.tempo = 120.0
                self.audio_duration = 60.0
        except Exception as e:
            print(f"🚨 Beat analysis failed: {e}")
            # Emergency fallback beats
            self.beat_times = [i * 0.5 for i in range(120)]
            self.tempo = 120.0
            self.audio_duration = 60.0
        
        # Step 3: Use proven perfect mapping algorithm
        try:
            if self.create_guaranteed_forward_mapping(max_clips=max_clips):
                success_steps += 1
                print("✅ Perfect forward mapping successful")
            else:
                print("🚨 Mapping failed")
                return False
        except Exception as e:
            print(f"🚨 Mapping failed: {e}")
            return False
        
        # Step 4: Conservative clip generation
        try:
            if self.generate_conservative_clips(max_clips=max_clips):
                success_steps += 1
                print("✅ Conservative clip generation successful")
            else:
                print("🚨 No clips generated")
                return False
        except Exception as e:
            print(f"🚨 Clip generation failed: {e}")
            return False
        
        # Step 5: Render
        try:
            if self.render_music_video():
                success_steps += 1
                print("✅ Rendering successful")
            else:
                print("🚨 Rendering failed")
                return False
        except Exception as e:
            print(f"🚨 Rendering failed: {e}")
            return False
        
        print(f"\n🎊 CONSERVATIVE MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        print(f"📊 Success steps: {success_steps}/5")
        
        # Final analysis
        if hasattr(self, 'scene_sequence') and hasattr(self, 'video_clips'):
            total_clips = len(self.video_clips)
            normal_clips = total_clips - self.emergency_clips_used
            
            print(f"\n📊 FINAL REPORT:")
            print(f"   Total clips: {total_clips}")
            print(f"   Normal scene clips: {normal_clips}")
            print(f"   Emergency black screens: {self.emergency_clips_used}")
            print(f"   Overall success rate: {(normal_clips / total_clips * 100):.1f}%")
            
            if self.emergency_clips_used == 0:
                print("🏆 PERFECT! No emergency fallbacks needed!")
                print("🎬 Your video should be all normal scenes!")
            else:
                print(f"⚠️ {self.emergency_clips_used} emergency situations handled")
        
        return True

def test_conservative():
    """Test the conservative bulletproof generator"""
    print("🛡️ TESTING CONSERVATIVE BULLETPROOF GENERATOR")
    print("=" * 50)
    print("This version uses proven algorithms with minimal emergency fallbacks")
    print()
    
    generator = ConservativeBulletproofGenerator("movie.mp4", "song.mp3", "conservative_test.mp4")
    
    success = generator.generate_conservative_music_video(
        max_clips=None,     # Full song
        threshold=30.0      # Scene detection sensitivity
    )
    
    if success:
        print("\n🎉 CONSERVATIVE TEST SUCCESS!")
        print("📁 Check: conservative_test.mp4")
        print("🎯 This should be mostly/all normal scenes with minimal black screens!")
    else:
        print("\n❌ Conservative test failed")
    
    return success

if __name__ == "__main__":
    test_conservative()
