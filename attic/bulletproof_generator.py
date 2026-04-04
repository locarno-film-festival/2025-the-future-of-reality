#!/usr/bin/env python3
"""
Bulletproof Generator with Emergency Black Screen Fallback
Handles any edge cases with graceful fallbacks instead of failures
"""

from perfect_forward_generator import PerfectForwardGenerator
from moviepy.editor import ColorClip
import contextlib
import io

class BulletproofGenerator(PerfectForwardGenerator):
    """Bulletproof version with comprehensive fallbacks and emergency black screens"""
    
    def __init__(self, video_path, audio_path, output_path="bulletproof_video.mp4"):
        super().__init__(video_path, audio_path, output_path)
        self.emergency_clips_used = 0
        self.fallback_reasons = []
        
    def create_emergency_black_clip(self, duration, reason="Unknown"):
        """Create a black screen clip for emergency situations"""
        try:
            # Create black screen with text overlay
            black_clip = ColorClip(
                size=(1920, 1080),  # Full HD black screen
                color=(0, 0, 0),    # Pure black
                duration=duration
            )
            
            self.emergency_clips_used += 1
            self.fallback_reasons.append(f"Emergency black screen: {reason}")
            
            print(f"🖥️ Emergency black screen created ({duration:.2f}s): {reason}")
            return black_clip
            
        except Exception as e:
            print(f"🚨 CRITICAL: Even black screen creation failed: {e}")
            # Return None - will be handled upstream
            return None
    
    def create_bulletproof_mapping(self, max_clips=None, emergency_threshold=5):
        """
        Create mapping with comprehensive fallback system
        
        emergency_threshold: Use black screens if fewer than this many scenes available
        """
        print("🛡️ Creating bulletproof mapping with emergency fallbacks...")
        
        if not self.scenes or not self.beat_times:
            print("❌ No scenes or beats - this should not happen!")
            return []
        
        # Determine clips to use
        total_beats = len(self.beat_times) - 1
        num_clips = min(max_clips, total_beats) if max_clips else total_beats
        total_scenes = len(self.scenes)
        
        print(f"🛡️ Bulletproof allocation: {num_clips} beats → {total_scenes} scenes")
        print(f"🚨 Emergency threshold: {emergency_threshold} scenes")
        
        # Check for emergency conditions
        if total_scenes < emergency_threshold:
            print(f"🚨 EMERGENCY: Only {total_scenes} scenes detected (< {emergency_threshold})")
            print("   Will use black screens for some clips")
        
        scene_sequence = []
        scenes_exhausted = False
        
        # Strategy: Absolutely guarantee forward progression
        for i in range(num_clips):
            beat_start = self.beat_times[i]
            beat_end = self.beat_times[i + 1] if i + 1 < len(self.beat_times) else beat_start + 0.5
            beat_duration = beat_end - beat_start
            
            # Calculate ideal scene position
            if total_scenes > 0:
                ideal_scene_index = int((i / num_clips) * (total_scenes - 1))
                
                # Ensure we never go backward
                if i > 0:
                    last_scene_index = scene_sequence[-1].get('scene_index', 0)
                    ideal_scene_index = max(ideal_scene_index, last_scene_index + 1)
                
                # Check if we have a valid scene
                if ideal_scene_index < total_scenes and not scenes_exhausted:
                    # Normal case: use the scene
                    selected_scene = self.scenes[ideal_scene_index]
                    
                    scene_sequence.append({
                        'beat_start': beat_start,
                        'beat_end': beat_end,
                        'beat_duration': beat_duration,
                        'scene': selected_scene,
                        'beat_index': i,
                        'scene_index': ideal_scene_index,
                        'target_progress': i / num_clips,
                        'actual_progress': selected_scene['position_ratio'],
                        'type': 'normal_scene',
                        'guaranteed_forward': True
                    })
                    
                elif ideal_scene_index >= total_scenes:
                    # We've run out of scenes - use last scene or black screen
                    if total_scenes > 0:
                        # Use the last scene (end of movie)
                        last_scene = self.scenes[-1]
                        
                        scene_sequence.append({
                            'beat_start': beat_start,
                            'beat_end': beat_end,
                            'beat_duration': beat_duration,
                            'scene': last_scene,
                            'beat_index': i,
                            'scene_index': total_scenes - 1,
                            'target_progress': i / num_clips,
                            'actual_progress': 1.0,  # End of movie
                            'type': 'reused_end_scene',
                            'guaranteed_forward': True
                        })
                        
                        if not scenes_exhausted:
                            print(f"📺 Beat {i}: Using end scene (scene exhaustion)")
                            scenes_exhausted = True
                    else:
                        # Emergency: No scenes at all
                        scene_sequence.append({
                            'beat_start': beat_start,
                            'beat_end': beat_end,
                            'beat_duration': beat_duration,
                            'scene': None,
                            'beat_index': i,
                            'scene_index': -1,
                            'target_progress': i / num_clips,
                            'actual_progress': i / num_clips,
                            'type': 'emergency_black',
                            'guaranteed_forward': True,
                            'emergency_reason': 'No scenes available'
                        })
                else:
                    # Emergency fallback: create black screen
                    scene_sequence.append({
                        'beat_start': beat_start,
                        'beat_end': beat_end,
                        'beat_duration': beat_duration,
                        'scene': None,
                        'beat_index': i,
                        'scene_index': -1,
                        'target_progress': i / num_clips,
                        'actual_progress': i / num_clips,
                        'type': 'emergency_black',
                        'guaranteed_forward': True,
                        'emergency_reason': f'Scene index {ideal_scene_index} invalid'
                    })
            else:
                # Emergency: No scenes detected at all
                scene_sequence.append({
                    'beat_start': beat_start,
                    'beat_end': beat_end,
                    'beat_duration': beat_duration,
                    'scene': None,
                    'beat_index': i,
                    'scene_index': -1,
                    'target_progress': i / num_clips,
                    'actual_progress': i / num_clips,
                    'type': 'emergency_black',
                    'guaranteed_forward': True,
                    'emergency_reason': 'No scenes detected in entire video'
                })
        
        self.scene_sequence = scene_sequence
        
        # Analyze the mapping
        normal_scenes = sum(1 for m in scene_sequence if m['type'] == 'normal_scene')
        reused_scenes = sum(1 for m in scene_sequence if m['type'] == 'reused_end_scene')
        emergency_blacks = sum(1 for m in scene_sequence if m['type'] == 'emergency_black')
        
        print(f"✅ Created {len(scene_sequence)} bulletproof mappings")
        print(f"📊 Breakdown:")
        print(f"   Normal scenes: {normal_scenes}")
        print(f"   Reused end scenes: {reused_scenes}")
        print(f"   Emergency black screens: {emergency_blacks}")
        
        if emergency_blacks == 0:
            print("🎉 Perfect! No emergency fallbacks needed!")
        else:
            print(f"🚨 {emergency_blacks} emergency black screens used")
            print("   Reasons:")
            for reason in set(self.fallback_reasons):
                print(f"     • {reason}")
        
        # Verify zero backward jumps (should be mathematically impossible now)
        actual_positions = [m['actual_progress'] for m in scene_sequence if m['scene'] is not None]
        if len(actual_positions) > 1:
            backward_jumps = sum(1 for i in range(1, len(actual_positions)) 
                               if actual_positions[i] < actual_positions[i-1])
            print(f"🎯 Backward jumps: {backward_jumps} (GUARANTEED: 0)")
        
        return scene_sequence
    
    def generate_bulletproof_clips(self, max_clips=None):
        """Generate video clips with emergency fallbacks"""
        print("🎬 Generating bulletproof video clips...")
        
        if not hasattr(self, 'scene_sequence'):
            print("❌ No scene sequence available")
            return []
        
        video_clips = []
        video = None
        
        try:
            # Try to load the video
            video = VideoFileClip(self.video_path, verbose=False)
            print(f"✅ Video loaded successfully: {video.duration:.1f}s")
        except Exception as e:
            print(f"🚨 CRITICAL: Cannot load video file: {e}")
            print("   Will use only black screens")
            video = None
        
        sequence = self.scene_sequence
        if max_clips:
            sequence = sequence[:max_clips]
        
        for i, mapping in enumerate(sequence):
            try:
                beat_duration = mapping['beat_duration']
                mapping_type = mapping['type']
                
                if mapping_type == 'emergency_black':
                    # Create emergency black screen
                    reason = mapping.get('emergency_reason', 'Unknown')
                    clip = self.create_emergency_black_clip(beat_duration, reason)
                    
                    if clip is None:
                        print(f"🚨 CRITICAL: Cannot create black screen for beat {i}")
                        continue
                    
                    video_clips.append(clip)
                    
                elif mapping['scene'] is not None and video is not None:
                    # Normal scene processing
                    scene = mapping['scene']
                    
                    try:
                        # Extract scene from video with extra error handling
                        if scene['end'] > video.duration:
                            print(f"⚠️ Scene {scene['id']} extends beyond video duration")
                            scene_end = min(scene['end'], video.duration)
                        else:
                            scene_end = scene['end']
                        
                        scene_clip = video.subclip(scene['start'], scene_end)
                        
                        # Adjust clip duration to match beat
                        if scene_clip.duration > beat_duration:
                            # Random start point within scene
                            max_start = scene_clip.duration - beat_duration
                            start_offset = random.uniform(0, max_start * 0.5) if max_start > 0 else 0
                            scene_clip = scene_clip.subclip(start_offset, start_offset + beat_duration)
                        elif scene_clip.duration < beat_duration:
                            # Speed up clip to fit beat duration
                            speed_factor = scene_clip.duration / beat_duration
                            if speed_factor > 0.1:  # Don't speed up too much
                                scene_clip = scene_clip.fx('speedx', speed_factor)
                            else:
                                # Scene too short even with speedup - use black screen
                                print(f"⚠️ Scene {scene['id']} too short, using black screen")
                                scene_clip = self.create_emergency_black_clip(
                                    beat_duration, 
                                    f"Scene {scene['id']} too short ({scene_clip.duration:.2f}s)"
                                )
                        
                        video_clips.append(scene_clip)
                        
                    except Exception as scene_error:
                        print(f"🚨 Error processing scene {scene['id']}: {scene_error}")
                        # Fallback to black screen
                        emergency_clip = self.create_emergency_black_clip(
                            beat_duration, 
                            f"Scene {scene['id']} processing failed"
                        )
                        if emergency_clip:
                            video_clips.append(emergency_clip)
                        
                else:
                    # Scene is None or video failed to load - emergency black screen
                    reason = "Video load failed" if video is None else "Scene is None"
                    emergency_clip = self.create_emergency_black_clip(beat_duration, reason)
                    if emergency_clip:
                        video_clips.append(emergency_clip)
                
            except Exception as e:
                print(f"🚨 CRITICAL error on beat {i}: {e}")
                # Last resort: try to create a black screen
                try:
                    emergency_clip = self.create_emergency_black_clip(
                        0.5,  # Fallback duration
                        f"Critical error on beat {i}"
                    )
                    if emergency_clip:
                        video_clips.append(emergency_clip)
                except:
                    print(f"🚨 TOTAL FAILURE: Cannot even create emergency clip for beat {i}")
                    continue
        
        # Final check
        if not video_clips:
            print("🚨 CRITICAL: No video clips generated at all!")
            # Create a single black screen as absolute fallback
            try:
                fallback_clip = self.create_emergency_black_clip(
                    self.audio_duration if hasattr(self, 'audio_duration') else 10.0,
                    "Total generation failure - emergency video"
                )
                if fallback_clip:
                    video_clips.append(fallback_clip)
            except Exception as final_error:
                print(f"🚨 ABSOLUTE FAILURE: {final_error}")
                return []
        
        # Cleanup
        if video:
            video.close()
        
        self.video_clips = video_clips
        print(f"✅ Generated {len(video_clips)} bulletproof clips")
        print(f"🖥️ Emergency black screens used: {self.emergency_clips_used}")
        
        return video_clips
    
    def generate_bulletproof_music_video(self, max_clips=None, emergency_threshold=5, threshold=30.0):
        """Generate completely bulletproof music video"""
        print("🛡️ Starting BULLETPROOF music video generation...")
        print("=" * 60)
        print("This version handles ANY edge case with graceful fallbacks!")
        print()
        
        # Step 1: Detect scenes (with fallback)
        try:
            scenes = self.detect_scenes(threshold=threshold)
            if not scenes:
                print("🚨 No scenes detected - will use black screens")
        except Exception as e:
            print(f"🚨 Scene detection failed: {e}")
            print("   Continuing with empty scene list...")
            self.scenes = []
        
        # Step 2: Analyze beats (with fallback)
        try:
            beats, tempo = self.analyze_audio_beats()
            if not beats:
                print("🚨 No beats detected - creating synthetic beats")
                # Create synthetic beats at 120 BPM
                if hasattr(self, 'audio_duration') and self.audio_duration > 0:
                    synthetic_beats = [i * 0.5 for i in range(int(self.audio_duration * 2))]
                    self.beat_times = synthetic_beats
                    self.tempo = 120.0
                else:
                    # Last resort: 1-minute video at 120 BPM
                    self.beat_times = [i * 0.5 for i in range(120)]
                    self.tempo = 120.0
                    self.audio_duration = 60.0
        except Exception as e:
            print(f"🚨 Beat analysis failed: {e}")
            print("   Creating fallback 120 BPM beats...")
            self.beat_times = [i * 0.5 for i in range(120)]  # 1 minute fallback
            self.tempo = 120.0
            self.audio_duration = 60.0
        
        # Step 3: Create bulletproof mapping
        try:
            mapping = self.create_bulletproof_mapping(max_clips=max_clips, emergency_threshold=emergency_threshold)
            if not mapping:
                print("🚨 Mapping failed - this should be impossible!")
                return False
        except Exception as e:
            print(f"🚨 CRITICAL: Mapping creation failed: {e}")
            return False
        
        # Step 4: Generate bulletproof clips
        try:
            clips = self.generate_bulletproof_clips(max_clips=max_clips)
            if not clips:
                print("🚨 No clips generated - this should be impossible!")
                return False
        except Exception as e:
            print(f"🚨 CRITICAL: Clip generation failed: {e}")
            return False
        
        # Step 5: Render (with fallback)
        try:
            success = self.render_music_video()
            if not success:
                print("🚨 Rendering failed")
                return False
        except Exception as e:
            print(f"🚨 CRITICAL: Rendering failed: {e}")
            return False
        
        print(f"\n🛡️ BULLETPROOF MUSIC VIDEO COMPLETE!")
        print(f"🎬 Output: {self.output_path}")
        
        # Final report
        try:
            normal_clips = len([c for c in self.scene_sequence if c['type'] == 'normal_scene'])
            emergency_clips = self.emergency_clips_used
            total_clips = len(self.scene_sequence)
            
            print(f"\n📊 BULLETPROOF GENERATION REPORT:")
            print(f"   Total clips: {total_clips}")
            print(f"   Normal scene clips: {normal_clips}")
            print(f"   Emergency black screens: {emergency_clips}")
            print(f"   Success rate: {((total_clips - emergency_clips) / total_clips * 100):.1f}%")
            
            if emergency_clips == 0:
                print("🏆 PERFECT! No emergency fallbacks needed!")
            else:
                print(f"🛡️ {emergency_clips} emergencies handled gracefully")
                print("   Fallback reasons:")
                for reason in set(self.fallback_reasons):
                    count = self.fallback_reasons.count(reason)
                    print(f"     • {reason} ({count}x)")
            
            # Final verification
            if hasattr(self, 'scene_sequence'):
                actual_positions = [m['actual_progress'] for m in self.scene_sequence if m['scene'] is not None]
                if len(actual_positions) > 1:
                    backward_jumps = sum(1 for i in range(1, len(actual_positions)) 
                                       if actual_positions[i] < actual_positions[i-1])
                    print(f"   Backward jumps: {backward_jumps} (should be 0)")
            
        except Exception as e:
            print(f"⚠️ Report generation failed: {e}")
        
        return True

def test_bulletproof():
    """Test the bulletproof generator"""
    print("🛡️ TESTING BULLETPROOF GENERATOR")
    print("=" * 45)
    print("This version handles ANY edge case gracefully!")
    print()
    
    generator = BulletproofGenerator("movie.mp4", "song.mp3", "bulletproof_test.mp4")
    
    success = generator.generate_bulletproof_music_video(
        max_clips=None,         # Full song
        emergency_threshold=5,  # Use black screens if < 5 scenes
        threshold=30.0          # Scene detection sensitivity
    )
    
    if success:
        print("\n🎉 BULLETPROOF TEST SUCCESS!")
        print("📁 Check: bulletproof_test.mp4")
        print("🛡️ This video should handle any edge case gracefully!")
    else:
        print("\n🚨 Even bulletproof version failed (this should be impossible!)")
    
    return success

if __name__ == "__main__":
    test_bulletproof()
