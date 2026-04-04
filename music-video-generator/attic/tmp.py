#!/usr/bin/env python3
"""
ARCHIVAL REMIX ENGINE: A Music Video Generator for Cultural Memory
================================================================
This tool transforms archival film footage into new artistic expressions,
demonstrating how AI can reimagine cultural heritage as living material.

For "The Future of Reality" Conference, Locarno
Session: The Future of the Archive
"""

import warnings
warnings.filterwarnings("ignore")  # Suppress technical warnings for clarity

# Core libraries for our archival transformation
import os
import sys
import subprocess
import numpy as np
from pathlib import Path

# Libraries for analyzing visual and sonic patterns
try:
    import librosa  # For musical analysis
    import cv2  # For visual analysis
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
except ImportError as e:
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║  SETUP REQUIRED: Missing Libraries                          ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Please install the required libraries by running:          ║
    ║                                                              ║
    ║  pip install librosa moviepy scenedetect[opencv] numpy      ║
    ║                                                              ║
    ║  Note: You may also need FFmpeg installed on your system    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    sys.exit(1)


class ArchivalRemixEngine:
    """
    This class embodies our philosophical approach: treating the archive
    not as a tomb but as a workshop where memories are reconstructed.
    """
    
    def __init__(self, film_path, song_path, output_path="archival_remix.mp4"):
        """
        Initialize our remix engine with source materials.
        
        Args:
            film_path: Path to the archival film (your cultural artifact)
            song_path: Path to the song (your temporal framework)
            output_path: Where to save the new creation
        """
        self.film_path = film_path
        self.song_path = song_path
        self.output_path = output_path
        
        # These will hold our analytical data
        self.scenes = []  # Visual segments detected in the film
        self.beats = []   # Temporal markers from the music
        self.tempo = 0    # The song's pulse
        
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  ARCHIVAL REMIX ENGINE INITIALIZED                          ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  Film Archive: {Path(film_path).name:<45} ║
        ║  Sonic Framework: {Path(song_path).name:<42} ║
        ║  New Artifact: {Path(output_path).name:<45} ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
    def analyze_visual_memory(self, threshold=30.0):
        """
        STEP 1: READING THE VISUAL ARCHIVE
        
        This function "watches" the film, detecting scene changes—moments
        where the visual narrative shifts. Each scene becomes a unit of
        memory that can be recombined.
        
        The threshold parameter (30.0) determines sensitivity to change:
        - Lower values: More sensitive, detecting subtle transitions
        - Higher values: Less sensitive, only major scene changes
        
        This mirrors how human memory segments experience into episodes.
        """
        print("\n📽️  ANALYZING VISUAL MEMORY...")
        print("   The algorithm is 'watching' your film, segmenting it into scenes...")
        
        try:
            # Initialize the video analysis system
            video_manager = VideoManager([self.film_path])
            scene_manager = SceneManager()
            
            # Configure scene detection sensitivity
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            
            # Perform the analysis
            video_manager.set_duration()
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()
            
            # Process detected scenes
            self.scenes = []
            for i, scene in enumerate(scene_list):
                start_time = float(scene[0].get_seconds())
                end_time = float(scene[1].get_seconds())
                duration = end_time - start_time
                
                # Only keep scenes longer than 1 second (avoid flickers)
                if duration >= 1.0:
                    self.scenes.append({
                        'id': i,
                        'start': start_time,
                        'end': end_time,
                        'duration': duration
                    })
            
            # Sort scenes chronologically and add position metadata
            self.scenes.sort(key=lambda x: x['start'])
            if self.scenes:
                film_duration = self.scenes[-1]['end']
                for scene in self.scenes:
                    # Calculate where in the film's timeline this scene occurs (0-1)
                    scene['position_ratio'] = scene['start'] / film_duration
            
            print(f"   ✓ Found {len(self.scenes)} scenes in {film_duration/60:.1f} minutes")
            print(f"   ✓ Average scene duration: {np.mean([s['duration'] for s in self.scenes]):.1f} seconds")
            
            # Provide insight into the film's rhythm
            scene_durations = [s['duration'] for s in self.scenes]
            print(f"   ✓ Visual rhythm: {np.std(scene_durations):.1f}s variation")
            
            return self.scenes
            
        except Exception as e:
            print(f"   ✗ Scene analysis failed: {e}")
            print("   → Falling back to treating entire film as one scene")
            
            # Fallback: treat the whole film as a single scene
            try:
                video = VideoFileClip(self.film_path)
                self.scenes = [{
                    'id': 0,
                    'start': 0,
                    'end': video.duration,
                    'duration': video.duration,
                    'position_ratio': 0.5
                }]
                video.close()
                return self.scenes
            except:
                return []
    
    def analyze_temporal_rhythm(self):
        """
        STEP 2: DECODING THE SONIC STRUCTURE
        
        This function analyzes the song to find its beats—the temporal
        skeleton that will structure our remix. The beat becomes the
        unit of time that governs how we sample the visual archive.
        
        This process reveals music as a form of time organization,
        a way of structuring duration that we'll impose on the film.
        """
        print("\n🎵 ANALYZING TEMPORAL RHYTHM...")
        print("   Extracting the song's temporal structure...")
        
        try:
            # Load and analyze the audio
            audio_data, sample_rate = librosa.load(self.song_path)
            
            # Detect tempo and beats
            tempo, beat_frames = librosa.beat.beat_track(
                y=audio_data, 
                sr=sample_rate
            )
            
            # Convert beat frames to time stamps
            beat_times = librosa.frames_to_time(
                beat_frames, 
                sr=sample_rate
            )
            
            self.beats = list(beat_times)
            self.tempo = float(tempo)
            self.audio_duration = len(audio_data) / sample_rate
            
            print(f"   ✓ Detected {len(self.beats)} beats at {self.tempo:.1f} BPM")
            print(f"   ✓ Song duration: {self.audio_duration/60:.1f} minutes")
            
            # Calculate beat intervals to understand rhythm variations
            if len(self.beats) > 1:
                intervals = np.diff(self.beats)
                print(f"   ✓ Beat interval: {np.mean(intervals):.3f}s ± {np.std(intervals):.3f}s")
            
            return self.beats, self.tempo
            
        except Exception as e:
            print(f"   ✗ Beat analysis failed: {e}")
            print("   → Creating synthetic rhythm at 120 BPM")
            
            # Fallback: create artificial beats at 120 BPM
            try:
                audio = AudioFileClip(self.song_path)
                duration = audio.duration
                audio.close()
                
                # Generate beats every 0.5 seconds (120 BPM)
                self.beats = list(np.arange(0, duration, 0.5))
                self.tempo = 120.0
                self.audio_duration = duration
                
                return self.beats, self.tempo
            except:
                return [], 120.0
    
    def create_temporal_mapping(self, strategy="progressive"):
        """
        STEP 3: THE ALGORITHMIC MONTAGE
        
        This is where the magic happens—we create a mapping between
        musical time and cinematic time. Different strategies represent
        different philosophical approaches to archival remix:
        
        - "progressive": Respects the film's chronology (historical fidelity)
        - "random": Fragments and recombines (Dadaist collage)
        - "rhythmic": Matches scene energy to musical intensity (affective resonance)
        
        This is montage not as human craft but as algorithmic process,
        raising questions about authorship and interpretation.
        """
        print(f"\n🎬 CREATING TEMPORAL MAPPING...")
        print(f"   Strategy: {strategy.upper()} - ", end="")
        
        if strategy == "progressive":
            print("Preserving narrative chronology")
        elif strategy == "random":
            print("Fragmenting and recombining")
        elif strategy == "rhythmic":
            print("Matching visual and sonic energy")
        
        if not self.scenes or not self.beats:
            print("   ✗ Missing scenes or beats for mapping")
            return []
        
        mapping = []
        num_beats = len(self.beats) - 1  # We need pairs of beats for durations
        
        for i in range(min(num_beats, 200)):  # Limit to 200 clips for performance
            beat_start = self.beats[i]
            beat_end = self.beats[i + 1]
            beat_duration = beat_end - beat_start
            
            # Calculate progress through the song (0-1)
            song_progress = i / num_beats
            
            if strategy == "progressive":
                # Map song progress to film progress
                # Early beats → early scenes, late beats → late scenes
                target_scenes = [
                    s for s in self.scenes 
                    if abs(s['position_ratio'] - song_progress) < 0.2
                ]
                if not target_scenes:
                    target_scenes = self.scenes
                selected_scene = np.random.choice(target_scenes)
                
            elif strategy == "random":
                # Pure chance—any scene can appear anywhere
                selected_scene = np.random.choice(self.scenes)
                
            elif strategy == "rhythmic":
                # Match short beats to short scenes, long beats to long scenes
                scene_durations = [abs(s['duration'] - beat_duration) for s in self.scenes]
                best_match_idx = np.argmin(scene_durations)
                selected_scene = self.scenes[best_match_idx]
            
            else:
                selected_scene = np.random.choice(self.scenes)
            
            mapping.append({
                'beat_start': beat_start,
                'beat_end': beat_end,
                'beat_duration': beat_duration,
                'scene': selected_scene,
                'beat_index': i
            })
        
        print(f"   ✓ Created {len(mapping)} scene-beat pairings")
        
        # Analyze the mapping pattern
        unique_scenes = len(set(m['scene']['id'] for m in mapping))
        print(f"   ✓ Using {unique_scenes}/{len(self.scenes)} unique scenes")
        print(f"   ✓ Average reuse: {len(mapping)/unique_scenes:.1f} times per scene")
        
        self.mapping = mapping
        return mapping
    
    def generate_remix(self):
        """
        STEP 4: CONSTRUCTING THE NEW ARTIFACT
        
        Here we actually create the video clips, cutting the film
        according to the musical rhythm. Each beat becomes a frame
        through which we view a fragment of the film.
        
        This process makes visible the violence of editing—how we
        tear images from their context and give them new meaning.
        """
        print("\n🎞️  GENERATING THE REMIX...")
        print("   Cutting and assembling the new artifact...")
        
        if not hasattr(self, 'mapping'):
            print("   ✗ No temporal mapping available")
            return []
        
        video_clips = []
        
        try:
            # Load the source film
            source_video = VideoFileClip(self.film_path, audio=False)
            
            # Process each beat-scene pairing
            for i, pair in enumerate(self.mapping):
                if i % 20 == 0:  # Progress indicator
                    print(f"   Processing beat {i+1}/{len(self.mapping)}...")
                
                try:
                    scene = pair['scene']
                    beat_duration = pair['beat_duration']
                    
                    # Extract the scene from the film
                    scene_clip = source_video.subclip(scene['start'], scene['end'])
                    
                    # Adjust clip to match beat duration
                    if scene_clip.duration > beat_duration:
                        # If scene is longer than beat, take a random segment
                        max_start = scene_clip.duration - beat_duration
                        if max_start > 0:
                            start_offset = np.random.uniform(0, max_start)
                            scene_clip = scene_clip.subclip(
                                start_offset, 
                                start_offset + beat_duration
                            )
                    else:
                        # If scene is shorter than beat, slow it down
                        # This creates a dreamy, contemplative effect
                        speed_factor = scene_clip.duration / beat_duration
                        if speed_factor > 0.1:  # Prevent extreme slow motion
                            scene_clip = scene_clip.fx('speedx', speed_factor)
                    
                    video_clips.append(scene_clip)
                    
                except Exception as e:
                    # Skip problematic clips silently
                    continue
            
            source_video.close()
            
            print(f"   ✓ Generated {len(video_clips)} video fragments")
            self.video_clips = video_clips
            return video_clips
            
        except Exception as e:
            print(f"   ✗ Clip generation failed: {e}")
            return []
    
    def render_artifact(self):
        """
        STEP 5: MATERIALIZING THE NEW MEMORY
        
        The final step: rendering our algorithmic remix into a new
        video file. This transforms our conceptual mapping into a
        concrete artifact that can circulate, be archived, and
        generate new meanings.
        
        The output is both derivative and original—a paradox of
        digital culture where copies can become more real than originals.
        """
        print("\n💾 RENDERING THE NEW ARTIFACT...")
        
        if not hasattr(self, 'video_clips') or not self.video_clips:
            print("   ✗ No video clips to render")
            return False
        
        try:
            print("   Concatenating video fragments...")
            final_video = concatenate_videoclips(
                self.video_clips, 
                method="compose"
            )
            
            print("   Adding sonic framework...")
            audio = AudioFileClip(self.song_path)
            
            # Trim audio to match video length if needed
            if audio.duration > final_video.duration:
                audio = audio.subclip(0, final_video.duration)
            
            final_video = final_video.set_audio(audio)
            
            print(f"   Writing to {self.output_path}...")
            final_video.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                fps=24,
                verbose=False,
                logger=None
            )
            
            # Clean up resources
            final_video.close()
            audio.close()
            for clip in self.video_clips:
                clip.close()
            
            print(f"""
            ╔══════════════════════════════════════════════════════════════╗
            ║  ✓ NEW ARTIFACT CREATED                                     ║
            ╠══════════════════════════════════════════════════════════════╣
            ║  Output: {self.output_path:<52} ║
            ║  Duration: {final_video.duration:.1f} seconds{' '*(46-len(f'{final_video.duration:.1f} seconds'))} ║
            ║  Clips: {len(self.video_clips)} fragments{' '*(49-len(f'{len(self.video_clips)} fragments'))} ║
            ╚══════════════════════════════════════════════════════════════╝
            """)
            
            return True
            
        except Exception as e:
            print(f"   ✗ Rendering failed: {e}")
            print("   Note: Make sure FFmpeg is installed on your system")
            return False
    
    def create_complete_remix(self, strategy="progressive"):
        """
        THE COMPLETE ARCHIVAL TRANSFORMATION
        
        This method orchestrates the entire process, transforming
        archive into artwork, memory into remix, past into present.
        """
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  BEGINNING ARCHIVAL TRANSFORMATION                          ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        # 1. Analyze the visual archive
        scenes = self.analyze_visual_memory()
        if not scenes:
            print("\n✗ Cannot proceed without scene analysis")
            return False
        
        # 2. Decode the temporal structure
        beats, tempo = self.analyze_temporal_rhythm()
        if not beats:
            print("\n✗ Cannot proceed without beat detection")
            return False
        
        # 3. Create the algorithmic montage
        mapping = self.create_temporal_mapping(strategy=strategy)
        if not mapping:
            print("\n✗ Cannot proceed without temporal mapping")
            return False
        
        # 4. Generate the remix
        clips = self.generate_remix()
        if not clips:
            print("\n✗ Cannot proceed without video clips")
            return False
        
        # 5. Render the new artifact
        success = self.render_artifact()
        
        if success:
            print(f"""
            ╔══════════════════════════════════════════════════════════════╗
            ║  TRANSFORMATION COMPLETE                                    ║
            ╠══════════════════════════════════════════════════════════════╣
            ║  The archive has been reimagined. A new cultural artifact   ║
            ║  has emerged from the collision of image and sound,         ║
            ║  past and present, human curation and machine vision.       ║
            ╚══════════════════════════════════════════════════════════════╝
            """)
        
        return success


def check_dependencies():
    """
    Verify that all required tools are installed.
    """
    print("\n🔍 Checking system dependencies...\n")
    
    all_good = True
    
    # Check Python packages
    packages = {
        'librosa': 'Audio analysis',
        'moviepy': 'Video manipulation',
        'cv2': 'Computer vision',
        'numpy': 'Numerical computing'
    }
    
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"   ✓ {package:<12} - {description}")
        except ImportError:
            print(f"   ✗ {package:<12} - {description} (MISSING)")
            all_good = False
    
    # Check for FFmpeg
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✓ FFmpeg      - Video encoding")
        else:
            print(f"   ✗ FFmpeg      - Video encoding (FAILED)")
            all_good = False
    except FileNotFoundError:
        print(f"   ✗ FFmpeg      - Video encoding (NOT FOUND)")
        all_good = False
    
    if not all_good:
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  SETUP INSTRUCTIONS                                         ║
        ╠══════════════════════════════════════════════════════════════╣
        ║  1. Install Python packages:                                ║
        ║     pip install librosa moviepy scenedetect[opencv] numpy   ║
        ║                                                              ║
        ║  2. Install FFmpeg:                                         ║
        ║     • macOS:   brew install ffmpeg                          ║
        ║     • Ubuntu:  sudo apt install ffmpeg                      ║
        ║     • Windows: Download from ffmpeg.org                     ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        return False
    
    return True


def main():
    """
    Interactive interface for the archival remix engine.
    """
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║            THE ARCHIVE AS LIVING MEMORY                     ║
    ║         An Algorithmic Music Video Generator                ║
    ║                                                              ║
    ║     "The Future of Reality" Conference - Locarno            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Welcome to our exploration of how artificial intelligence can
    transform archival materials into new forms of cultural expression.
    
    This tool will take a film from your archive and a song of your
    choice, then algorithmically remix them into a music video that
    exists somewhere between preservation and transformation.
    """)
    
    # Check dependencies first
    if not check_dependencies():
        print("\nPlease install missing dependencies and try again.")
        return
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║  SELECT YOUR MATERIALS                                      ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Get input files
    film_path = input("\n📽️  Enter path to your film file: ").strip()
    if not os.path.exists(film_path):
        print(f"   ✗ Film not found: {film_path}")
        return
    
    song_path = input("🎵 Enter path to your song file: ").strip()
    if not os.path.exists(song_path):
        print(f"   ✗ Song not found: {song_path}")
        return
    
    output_path = input("💾 Enter output filename (or press Enter for 'archival_remix.mp4'): ").strip()
    if not output_path:
        output_path = "archival_remix.mp4"
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║  CHOOSE YOUR PHILOSOPHICAL APPROACH                         ║
    ╚══════════════════════════════════════════════════════════════╝
    
    How should the algorithm interpret your archive?
    
    1. PROGRESSIVE - Preserve chronological order (Historical fidelity)
    2. RANDOM     - Fragment and recombine (Dadaist collage)  
    3. RHYTHMIC   - Match visual to musical energy (Affective resonance)
    """)
    
    strategy_choice = input("\nEnter your choice (1-3): ").strip()
    
    strategies = {
        '1': 'progressive',
        '2': 'random',
        '3': 'rhythmic'
    }
    
    strategy = strategies.get(strategy_choice, 'progressive')
    
    # Create and run the remix engine
    engine = ArchivalRemixEngine(film_path, song_path, output_path)
    success = engine.create_complete_remix(strategy=strategy)
    
    if success:
        print(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║  QUESTIONS FOR REFLECTION                                   ║
        ╚══════════════════════════════════════════════════════════════╝
        
        As you watch your algorithmic remix, consider:
        
        • What new meanings emerge from this collision of image and sound?
        • How does algorithmic editing differ from human montage?
        • What is lost and what is gained in this transformation?
        • Who is the author of this new work—you, the algorithm, or both?
        • How might this approach change how we think about archives?
        
        The archive is no longer a tomb but a garden where new forms
        of memory can grow. What you've created is both preservation
        and transformation, both homage and reimagination.
        """)


if __name__ == "__main__":
    main()
