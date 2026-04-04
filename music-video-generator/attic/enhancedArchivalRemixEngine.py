#!/usr/bin/env python3
"""
ENHANCED ARCHIVAL REMIX ENGINE
With tempo change detection and flexible beat control
================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import os
import sys
import numpy as np
from pathlib import Path

try:
    import librosa
    import librosa.display
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"Missing required libraries: {e}")
    sys.exit(1)


class EnhancedArchivalRemixEngine:
    """
    Enhanced version with tempo change detection and beat control.
    """
    
    def __init__(self, film_path, song_path, output_path="archival_remix.mp4"):
        self.film_path = film_path
        self.song_path = song_path
        self.output_path = output_path
        self.scenes = []
        self.beats = []
        self.tempo = 0
        self.tempo_sections = []  # For tempo change tracking
        
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  ENHANCED ARCHIVAL REMIX ENGINE                             ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Film: {Path(film_path).name:<53} ║
        ║  Song: {Path(song_path).name:<53} ║
        ║  Output: {Path(output_path).name:<51} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
    def analyze_visual_memory(self, threshold=30.0):
        """Analyze film for scene changes with better error handling."""
        print("\n📽️  ANALYZING VISUAL MEMORY...")
        
        try:
            # First, verify the video file
            test_video = VideoFileClip(self.film_path)
            video_duration = test_video.duration
            print(f"   ✓ Video verified: {video_duration:.1f} seconds")
            test_video.close()
            
            # Now detect scenes
            video_manager = VideoManager([self.film_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            
            video_manager.set_duration()
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()
            
            self.scenes = []
            for i, scene in enumerate(scene_list):
                start_time = float(scene[0].get_seconds())
                end_time = float(scene[1].get_seconds())
                duration = end_time - start_time
                
                # Only keep substantial scenes
                if duration >= 0.5:  # Minimum 0.5 seconds
                    self.scenes.append({
                        'id': i,
                        'start': start_time,
                        'end': min(end_time, video_duration - 0.1),  # Ensure within bounds
                        'duration': duration,
                        'energy': 'normal'  # We'll classify this later
                    })
            
            # If too few scenes detected, create more segments
            if len(self.scenes) < 10:
                print(f"   ⚠️ Only {len(self.scenes)} scenes found, creating additional segments...")
                segment_duration = video_duration / 20  # Create ~20 segments
                self.scenes = []
                for i in range(20):
                    start = i * segment_duration
                    end = min((i + 1) * segment_duration, video_duration - 0.1)
                    self.scenes.append({
                        'id': i,
                        'start': start,
                        'end': end,
                        'duration': end - start,
                        'energy': 'normal'
                    })
            
            # Sort and add position ratios
            self.scenes.sort(key=lambda x: x['start'])
            for scene in self.scenes:
                scene['position_ratio'] = scene['start'] / video_duration
            
            print(f"   ✓ Found {len(self.scenes)} scenes")
            
            # Classify scene energy based on duration
            short_duration = np.percentile([s['duration'] for s in self.scenes], 33)
            long_duration = np.percentile([s['duration'] for s in self.scenes], 67)
            
            for scene in self.scenes:
                if scene['duration'] < short_duration:
                    scene['energy'] = 'high'  # Quick cuts = high energy
                elif scene['duration'] > long_duration:
                    scene['energy'] = 'low'   # Long takes = contemplative
                else:
                    scene['energy'] = 'normal'
            
            return self.scenes
            
        except Exception as e:
            print(f"   ✗ Scene analysis failed: {e}")
            return []
    
    def analyze_temporal_rhythm_advanced(self, visualize=False):
        """
        Advanced beat and tempo analysis that detects tempo changes.
        Uses dynamic programming to track local tempo variations.
        """
        print("\n🎵 ANALYZING TEMPORAL RHYTHM (ADVANCED)...")
        
        try:
            # Load audio
            audio_data, sample_rate = librosa.load(self.song_path)
            self.audio_duration = len(audio_data) / sample_rate
            
            print("   Detecting tempo changes...")
            
            # 1. Get onset envelope for rhythm analysis
            onset_env = librosa.onset.onset_strength(y=audio_data, sr=sample_rate)
            
            # 2. Dynamic tempo estimation using tempogram
            tempogram = librosa.feature.tempogram(
                onset_envelope=onset_env,
                sr=sample_rate,
                hop_length=512
            )
            
            # 3. Estimate tempo over time
            tempo_over_time = []
            window_length = 384  # ~8 seconds at default hop length
            
            for i in range(0, tempogram.shape[1] - window_length, window_length // 4):
                local_tempogram = tempogram[:, i:i+window_length]
                local_tempo = librosa.tempo(
                    onset_envelope=onset_env[i:i+window_length],
                    sr=sample_rate,
                    hop_length=512
                )[0]
                tempo_over_time.append({
                    'time': i * 512 / sample_rate,
                    'tempo': local_tempo
                })
            
            # 4. Detect significant tempo changes
            self.tempo_sections = []
            current_tempo = tempo_over_time[0]['tempo'] if tempo_over_time else 120
            current_start = 0
            
            for i, section in enumerate(tempo_over_time[1:], 1):
                tempo_change = abs(section['tempo'] - current_tempo) / current_tempo
                
                # If tempo changes by more than 15%, mark new section
                if tempo_change > 0.15:
                    self.tempo_sections.append({
                        'start': current_start,
                        'end': section['time'],
                        'tempo': current_tempo,
                        'energy': self._classify_tempo_energy(current_tempo)
                    })
                    current_tempo = section['tempo']
                    current_start = section['time']
            
            # Add final section
            self.tempo_sections.append({
                'start': current_start,
                'end': self.audio_duration,
                'tempo': current_tempo,
                'energy': self._classify_tempo_energy(current_tempo)
            })
            
            # 5. Global beat tracking
            print("   Tracking beats...")
            tempo, beat_frames = librosa.beat.beat_track(
                y=audio_data,
                sr=sample_rate,
                trim=False
            )
            
            beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
            self.beats = list(beat_times)
            self.tempo = float(tempo)
            
            print(f"   ✓ Detected {len(self.beats)} beats")
            print(f"   ✓ Average tempo: {self.tempo:.1f} BPM")
            
            if len(self.tempo_sections) > 1:
                print(f"   ✓ Found {len(self.tempo_sections)} tempo sections:")
                for i, section in enumerate(self.tempo_sections):
                    print(f"      Section {i+1}: {section['tempo']:.1f} BPM ({section['energy']} energy)")
            
            # 6. Optional visualization
            if visualize and len(self.tempo_sections) > 1:
                self._visualize_tempo_analysis(audio_data, sample_rate, onset_env)
            
            return self.beats, self.tempo, self.tempo_sections
            
        except Exception as e:
            print(f"   ✗ Advanced analysis failed: {e}")
            print("   Falling back to simple beat detection...")
            
            # Fallback to simple beat detection
            try:
                audio_data, sample_rate = librosa.load(self.song_path)
                tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
                beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
                
                self.beats = list(beat_times)
                self.tempo = float(tempo)
                self.audio_duration = len(audio_data) / sample_rate
                
                # Create single tempo section
                self.tempo_sections = [{
                    'start': 0,
                    'end': self.audio_duration,
                    'tempo': self.tempo,
                    'energy': 'normal'
                }]
                
                print(f"   ✓ Simple detection: {len(self.beats)} beats at {self.tempo:.1f} BPM")
                return self.beats, self.tempo, self.tempo_sections
                
            except Exception as e2:
                print(f"   ✗ Fallback also failed: {e2}")
                return [], 120.0, []
    
    def _classify_tempo_energy(self, tempo):
        """Classify energy level based on tempo."""
        if tempo < 100:
            return 'low'
        elif tempo > 140:
            return 'high'
        else:
            return 'normal'
    
    def _visualize_tempo_analysis(self, audio_data, sample_rate, onset_env):
        """Create visualization of tempo analysis."""
        try:
            fig, axes = plt.subplots(3, 1, figsize=(12, 8))
            
            # Plot waveform
            times = np.arange(len(audio_data)) / sample_rate
            axes[0].plot(times, audio_data, alpha=0.6)
            axes[0].set_title('Audio Waveform')
            axes[0].set_ylabel('Amplitude')
            
            # Plot onset strength
            onset_times = np.arange(len(onset_env)) * 512 / sample_rate
            axes[1].plot(onset_times, onset_env, alpha=0.6)
            axes[1].set_title('Onset Strength (Rhythm Detection)')
            axes[1].set_ylabel('Strength')
            
            # Plot tempo sections
            for section in self.tempo_sections:
                color = {'low': 'blue', 'normal': 'green', 'high': 'red'}[section['energy']]
                axes[2].axvspan(section['start'], section['end'], 
                               alpha=0.3, color=color, 
                               label=f"{section['tempo']:.0f} BPM")
            
            axes[2].set_title('Tempo Sections')
            axes[2].set_xlabel('Time (seconds)')
            axes[2].set_ylabel('Tempo Sections')
            axes[2].legend()
            
            plt.tight_layout()
            plt.savefig('tempo_analysis.png')
            print("   ✓ Saved tempo visualization to tempo_analysis.png")
            plt.close()
            
        except Exception as e:
            print(f"   ⚠️ Could not create visualization: {e}")
    
    def create_tempo_aware_mapping(self, strategy="adaptive", beat_skip=1, max_clips=None):
        """
        Create mapping with tempo awareness and beat skipping.
        
        Args:
            strategy: "adaptive" (match energy), "progressive", or "random"
            beat_skip: 1 = every beat, 2 = every other beat, 3 = every third, etc.
            max_clips: Maximum number of clips to generate
        """
        print(f"\n🎬 CREATING TEMPO-AWARE MAPPING...")
        print(f"   Strategy: {strategy.upper()}")
        print(f"   Beat skip: Using every {beat_skip} beat(s)")
        
        if not self.scenes or not self.beats:
            print("   ✗ Missing scenes or beats")
            return []
        
        # Apply beat skipping
        selected_beats = self.beats[::beat_skip]
        print(f"   Using {len(selected_beats)} of {len(self.beats)} beats")
        
        mapping = []
        num_beats = len(selected_beats) - 1
        
        if max_clips:
            num_beats = min(num_beats, max_clips)
        
        for i in range(num_beats):
            beat_start = selected_beats[i]
            beat_end = selected_beats[i + 1]
            beat_duration = beat_end - beat_start
            
            # Skip very short durations
            if beat_duration < 0.1:
                continue
            
            # Find current tempo section
            current_tempo_section = None
            for section in self.tempo_sections:
                if section['start'] <= beat_start < section['end']:
                    current_tempo_section = section
                    break
            
            if not current_tempo_section:
                current_tempo_section = {'energy': 'normal', 'tempo': self.tempo}
            
            song_progress = i / num_beats
            
            if strategy == "adaptive":
                # Match scene energy to tempo energy
                if current_tempo_section['energy'] == 'high':
                    # High tempo: prefer short, high-energy scenes
                    candidate_scenes = [s for s in self.scenes if s['energy'] == 'high']
                    if not candidate_scenes:
                        candidate_scenes = [s for s in self.scenes if s['duration'] < 5]
                elif current_tempo_section['energy'] == 'low':
                    # Low tempo: prefer long, contemplative scenes
                    candidate_scenes = [s for s in self.scenes if s['energy'] == 'low']
                    if not candidate_scenes:
                        candidate_scenes = [s for s in self.scenes if s['duration'] > 5]
                else:
                    # Normal tempo: any scene
                    candidate_scenes = self.scenes
                
                if not candidate_scenes:
                    candidate_scenes = self.scenes
                
                selected_scene = np.random.choice(candidate_scenes)
                
            elif strategy == "progressive":
                # Progressive through film
                target_scenes = [
                    s for s in self.scenes 
                    if abs(s['position_ratio'] - song_progress) < 0.3
                ]
                if not target_scenes:
                    target_scenes = self.scenes
                selected_scene = np.random.choice(target_scenes)
                
            else:  # random
                selected_scene = np.random.choice(self.scenes)
            
            mapping.append({
                'beat_start': beat_start,
                'beat_end': beat_end,
                'beat_duration': beat_duration,
                'scene': selected_scene,
                'beat_index': i,
                'tempo_energy': current_tempo_section['energy'],
                'tempo_bpm': current_tempo_section['tempo']
            })
        
        print(f"   ✓ Created {len(mapping)} mappings")
        
        # Analyze mapping
        if mapping and 'tempo_energy' in mapping[0]:
            energy_counts = {'low': 0, 'normal': 0, 'high': 0}
            for m in mapping:
                energy_counts[m['tempo_energy']] += 1
            print(f"   Energy distribution: {energy_counts}")
        
        self.mapping = mapping
        return mapping
    
    def generate_tempo_aware_remix(self):
        """Generate clips with improved error handling."""
        print("\n🎞️  GENERATING TEMPO-AWARE REMIX...")
        
        if not hasattr(self, 'mapping'):
            print("   ✗ No mapping available")
            return []
        
        video_clips = []
        source_video = None
        
        try:
            # Load and validate source video
            source_video = VideoFileClip(self.film_path, audio=False)
            video_duration = source_video.duration
            print(f"   ✓ Source video: {video_duration:.1f} seconds")
            
            successful_clips = 0
            failed_clips = 0
            
            for i, pair in enumerate(self.mapping):
                if i % 20 == 0 and i > 0:
                    print(f"   Processed {i}/{len(self.mapping)} beats...")
                
                try:
                    scene = pair['scene']
                    beat_duration = pair['beat_duration']
                    tempo_energy = pair.get('tempo_energy', 'normal')
                    
                    # Validate and adjust scene boundaries
                    scene_start = max(0, min(scene['start'], video_duration - 1))
                    scene_end = min(scene['end'], video_duration)
                    
                    # Ensure valid duration
                    if scene_end - scene_start < 0.1:
                        failed_clips += 1
                        continue
                    
                    # Extract scene clip
                    clip = source_video.subclip(scene_start, scene_end)
                    
                    if not clip or clip.duration <= 0:
                        failed_clips += 1
                        continue
                    
                    # Adjust clip duration based on tempo energy
                    if clip.duration > beat_duration:
                        # For high energy, take more dynamic part (middle)
                        # For low energy, take beginning (usually calmer)
                        if tempo_energy == 'high':
                            # Take from middle of scene
                            offset_ratio = 0.3 + np.random.random() * 0.4
                        elif tempo_energy == 'low':
                            # Take from beginning
                            offset_ratio = np.random.random() * 0.3
                        else:
                            # Random
                            offset_ratio = np.random.random()
                        
                        max_offset = clip.duration - beat_duration
                        offset = min(offset_ratio * clip.duration, max_offset)
                        
                        clip = clip.subclip(offset, offset + beat_duration)
                        
                    elif clip.duration < beat_duration:
                        # Adjust speed if reasonable
                        speed_factor = clip.duration / beat_duration
                        if 0.5 <= speed_factor <= 2.0:
                            clip = clip.speedx(speed_factor)
                        # Otherwise keep original duration
                    
                    # Final validation
                    if clip and clip.duration > 0:
                        video_clips.append(clip)
                        successful_clips += 1
                    else:
                        failed_clips += 1
                    
                except Exception as e:
                    failed_clips += 1
                    if failed_clips <= 3:
                        print(f"   ⚠️ Clip {i} failed: {str(e)[:50]}")
            
            print(f"   ✓ Generated {successful_clips} clips")
            if failed_clips > 0:
                print(f"   ⚠️ {failed_clips} clips failed")
            
            if len(video_clips) == 0:
                print("   ✗ No valid clips generated!")
                if source_video:
                    source_video.close()
                return []
            
            self.video_clips = video_clips
            self.source_video = source_video
            return video_clips
            
        except Exception as e:
            print(f"   ✗ Generation failed: {e}")
            if source_video:
                source_video.close()
            return []
    
    def render_final_artifact(self):
        """Render with robust error handling."""
        print("\n💾 RENDERING FINAL ARTIFACT...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("   ✗ No clips available")
            return False
        
        try:
            # Filter valid clips
            valid_clips = [c for c in self.video_clips if c is not None and c.duration > 0]
            
            if not valid_clips:
                print("   ✗ No valid clips to render")
                return False
            
            print(f"   Concatenating {len(valid_clips)} clips...")
            final_video = concatenate_videoclips(valid_clips, method="compose")
            
            print("   Adding audio track...")
            audio = AudioFileClip(self.song_path)
            
            # Sync lengths
            if audio.duration > final_video.duration:
                audio = audio.subclip(0, final_video.duration)
            elif final_video.duration > audio.duration:
                final_video = final_video.subclip(0, audio.duration)
            
            final_video = final_video.set_audio(audio)
            
            print(f"   Writing to {self.output_path}...")
            print("   (This may take a few minutes...)")
            
            final_video.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                fps=24,
                preset='medium',
                threads=4,
                verbose=False,
                logger=None
            )
            
            # Cleanup
            final_video.close()
            audio.close()
            
            if hasattr(self, 'source_video'):
                self.source_video.close()
            
            for clip in valid_clips:
                try:
                    clip.close()
                except:
                    pass
            
            print(f"   ✓ Success! Created: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"   ✗ Rendering failed: {e}")
            return False
    
    def create_enhanced_remix(self, strategy="adaptive", beat_skip=1, 
                            max_clips=None, visualize_tempo=False):
        """
        Create remix with all enhancements.
        
        Args:
            strategy: "adaptive", "progressive", or "random"
            beat_skip: 1 = every beat, 2 = every other beat, etc.
            max_clips: Limit number of clips (None = use all)
            visualize_tempo: Save tempo analysis visualization
        """
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  ENHANCED ARCHIVAL TRANSFORMATION                           ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Strategy: {strategy:<49} ║
        ║  Beat pattern: Every {beat_skip} beat(s){' '*(40-len(str(beat_skip)))} ║
        ║  Max clips: {str(max_clips) if max_clips else 'Unlimited':<48} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        # 1. Analyze visual
        scenes = self.analyze_visual_memory()
        if not scenes:
            return False
        
        # 2. Advanced tempo analysis
        beats, tempo, tempo_sections = self.analyze_temporal_rhythm_advanced(
            visualize=visualize_tempo
        )
        if not beats:
            return False
        
        # 3. Create tempo-aware mapping
        mapping = self.create_tempo_aware_mapping(
            strategy=strategy,
            beat_skip=beat_skip,
            max_clips=max_clips
        )
        if not mapping:
            return False
        
        # 4. Generate clips
        clips = self.generate_tempo_aware_remix()
        if not clips:
            return False
        
        # 5. Render
        success = self.render_final_artifact()
        
        if success:
            print(f"""
            ╔══════════════════════════════════════════════════════════════╗
            ║  TRANSFORMATION COMPLETE                                    ║
            ╠══════════════════════════════════════════════════════════════╣
            ║  Your enhanced remix is ready!                              ║
            ║  Check for tempo changes and energy matching.               ║
            ╚══════════════════════════════════════════════════════════════╝
            """)
        
        return success


# Example usage
def example_usage():
    """Show how to use the enhanced engine."""
    
    print("""
    USAGE EXAMPLES:
    
    # Basic usage - adapts to tempo changes
    engine = EnhancedArchivalRemixEngine("film.mp4", "song.mp3")
    engine.create_enhanced_remix(strategy="adaptive")
    
    # Use every other beat (good for fast songs)
    engine.create_enhanced_remix(strategy="adaptive", beat_skip=2)
    
    # Use every third beat (for very fast songs)
    engine.create_enhanced_remix(strategy="adaptive", beat_skip=3)
    
    # Limit to 50 clips for testing
    engine.create_enhanced_remix(strategy="adaptive", beat_skip=1, max_clips=50)
    
    # Progressive with tempo visualization
    engine.create_enhanced_remix(strategy="progressive", visualize_tempo=True)
    """)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python enhanced_remix.py <film> <song> [beat_skip] [strategy]")
        print("\nExample: python enhanced_remix.py movie.mp4 song.mp3 2 adaptive")
        example_usage()
    else:
        film = sys.argv[1]
        song = sys.argv[2]
        beat_skip = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        strategy = sys.argv[4] if len(sys.argv) > 4 else "adaptive"
        
        engine = EnhancedArchivalRemixEngine(film, song, "enhanced_remix.mp4")
        engine.create_enhanced_remix(
            strategy=strategy,
            beat_skip=beat_skip,
            max_clips=None,
            visualize_tempo=True
        )
