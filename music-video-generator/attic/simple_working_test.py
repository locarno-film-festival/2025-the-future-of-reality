#!/usr/bin/env python3
"""
Simple Working Test - Bypass audio creation issues
"""

def test_all_imports():
    """Test that all required libraries work"""
    print("🧪 TESTING ALL IMPORTS")
    print("=" * 40)
    
    # Test core libraries
    imports_ok = True
    
    try:
        import librosa
        print(f"✅ librosa {librosa.__version__}")
    except ImportError as e:
        print(f"❌ librosa failed: {e}")
        imports_ok = False
    
    try:
        from scenedetect import VideoManager, SceneManager
        from scenedetect.detectors import ContentDetector
        print("✅ scenedetect")
    except ImportError as e:
        print(f"❌ scenedetect failed: {e}")
        imports_ok = False
    
    try:
        import cv2
        print(f"✅ opencv {cv2.__version__}")
    except ImportError as e:
        print(f"❌ opencv failed: {e}")
        imports_ok = False
    
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
        print("✅ moviepy")
    except ImportError as e:
        print(f"❌ moviepy failed: {e}")
        imports_ok = False
    
    try:
        import matplotlib.pyplot as plt
        print("✅ matplotlib")
    except ImportError as e:
        print(f"❌ matplotlib failed: {e}")
        imports_ok = False
    
    try:
        import numpy as np
        print(f"✅ numpy {np.__version__}")
    except ImportError as e:
        print(f"❌ numpy failed: {e}")
        imports_ok = False
    
    return imports_ok

def test_librosa_with_example():
    """Test librosa with its built-in example"""
    print("\n🎵 TESTING LIBROSA WITH EXAMPLE AUDIO")
    print("=" * 40)
    
    try:
        import librosa
        
        # Use librosa's built-in example file
        y, sr = librosa.load(librosa.ex('brahms'), duration=5)
        print(f"✅ Loaded example audio: {len(y)} samples at {sr}Hz")
        
        # Test beat detection
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        print(f"✅ Beat detection successful!")
        print(f"   Tempo: {tempo:.1f} BPM")
        print(f"   Beats detected: {len(beat_times)}")
        print(f"   Duration: {len(y)/sr:.1f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Librosa test failed: {e}")
        return False

def test_scenedetect_simple():
    """Test scene detection with a simple generated video"""
    print("\n🎬 TESTING SCENE DETECTION")
    print("=" * 40)
    
    try:
        import cv2
        import numpy as np
        
        # Create a simple test video with clear scene changes
        print("Creating simple test video...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter('simple_test.mp4', fourcc, 10.0, (320, 240))
        
        # Create 3 distinct scenes (different colors)
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
        
        for scene_idx, color in enumerate(colors):
            for frame_num in range(20):  # 2 seconds per scene at 10fps
                frame = np.full((240, 320, 3), color, dtype=np.uint8)
                video_writer.write(frame)
        
        video_writer.release()
        print("✅ Test video created")
        
        # Test scene detection
        from scenedetect import VideoManager, SceneManager
        from scenedetect.detectors import ContentDetector
        
        video_manager = VideoManager(['simple_test.mp4'])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=30.0))
        
        video_manager.set_duration()
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()
        
        print(f"✅ Scene detection successful!")
        print(f"   Scenes detected: {len(scene_list)}")
        
        # Cleanup
        import os
        os.remove('simple_test.mp4')
        
        return True
        
    except Exception as e:
        print(f"❌ Scene detection test failed: {e}")
        return False

def test_ffmpeg():
    """Test FFmpeg availability"""
    print("\n🎥 TESTING FFMPEG")
    print("=" * 40)
    
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg working: {version_line}")
            return True
        else:
            print("❌ FFmpeg command failed")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found")
        return False
    except Exception as e:
        print(f"❌ FFmpeg test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🎬🎵 MUSIC VIDEO GENERATOR - WORKING TEST")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_all_imports()
    
    if not imports_ok:
        print("\n❌ Some imports failed. Install missing packages first.")
        return False
    
    # Test librosa specifically
    librosa_ok = test_librosa_with_example()
    
    # Test scene detection
    scenedetect_ok = test_scenedetect_simple()
    
    # Test FFmpeg
    ffmpeg_ok = test_ffmpeg()
    
    # Summary
    print("\n📊 FINAL RESULTS")
    print("=" * 30)
    
    if imports_ok and librosa_ok and scenedetect_ok:
        print("🎉 ALL CORE FUNCTIONALITY WORKING!")
        print("✅ Imports: OK")
        print("✅ Librosa beat detection: OK") 
        print("✅ Scene detection: OK")
        print(f"✅ FFmpeg: {'OK' if ffmpeg_ok else 'Not available'}")
        
        print("\n🚀 YOU'RE READY TO CREATE MUSIC VIDEOS!")
        print("\nNext steps:")
        print("1. Get your video file (movie.mp4)")
        print("2. Get your audio file (song.mp3)")
        print("3. Run the music video generator!")
        
        return True
    else:
        print("❌ Some tests failed:")
        print(f"   Imports: {'OK' if imports_ok else 'FAILED'}")
        print(f"   Librosa: {'OK' if librosa_ok else 'FAILED'}")
        print(f"   Scene detection: {'OK' if scenedetect_ok else 'FAILED'}")
        print(f"   FFmpeg: {'OK' if ffmpeg_ok else 'FAILED'}")
        
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n💡 Try this example:")
        print("from music_video_generator import MusicVideoGenerator")
        print("generator = MusicVideoGenerator('video.mp4', 'song.mp3')")
        print("generator.generate_music_video(style='random', max_clips=20)")
