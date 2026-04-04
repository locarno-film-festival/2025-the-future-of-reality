#!/usr/bin/env python3
"""
Quick Setup Test for Music Video Generator
Run this to verify all dependencies are working
"""

def test_imports():
    """Test if all required libraries can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import librosa
        print("✅ librosa - OK")
    except ImportError as e:
        print(f"❌ librosa - FAILED: {e}")
        return False
    
    try:
        import scenedetect
        print("✅ scenedetect - OK")
    except ImportError as e:
        print(f"❌ scenedetect - FAILED: {e}")
        return False
    
    try:
        import cv2
        print("✅ opencv (cv2) - OK")
    except ImportError as e:
        print(f"❌ opencv - FAILED: {e}")
        return False
    
    try:
        import moviepy.editor
        print("✅ moviepy - OK")
    except ImportError as e:
        print(f"❌ moviepy - FAILED: {e}")
        return False
    
    try:
        import matplotlib.pyplot
        print("✅ matplotlib - OK")
    except ImportError as e:
        print(f"❌ matplotlib - FAILED: {e}")
        return False
    
    try:
        import numpy
        print("✅ numpy - OK")
    except ImportError as e:
        print(f"❌ numpy - FAILED: {e}")
        return False
    
    return True

def test_ffmpeg():
    """Test if FFmpeg is available"""
    print("\n🎬 Testing FFmpeg...")
    
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg - OK ({version_line})")
            return True
        else:
            print("❌ FFmpeg - Command failed")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg - Not found in PATH")
        print("   Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Ubuntu)")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg - Command timed out")
        return False

def create_test_files():
    """Create simple test audio and video files"""
    print("\n🎵 Creating test files...")
    
    try:
        import numpy as np
        import cv2
        import librosa
        from scipy.io.wavfile import write
        
        # Create a simple test video (5 seconds, 24fps)
        print("Creating test video...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter('test_video.mp4', fourcc, 24.0, (640, 480))
        
        for frame_num in range(120):  # 5 seconds at 24fps
            # Create a simple colored frame that changes
            color = int((frame_num / 120) * 255)
            frame = np.ones((480, 640, 3), dtype=np.uint8)
            
            # Different scenes (color changes)
            if frame_num < 30:
                frame[:, :] = [color, 0, 0]  # Red
            elif frame_num < 60:
                frame[:, :] = [0, color, 0]  # Green  
            elif frame_num < 90:
                frame[:, :] = [0, 0, color]  # Blue
            else:
                frame[:, :] = [color, color, 0]  # Yellow
            
            video_writer.write(frame)
        
        video_writer.release()
        print("✅ test_video.mp4 created")
        
        # Create a simple test audio (5 seconds, 120 BPM)
        print("Creating test audio...")
        sample_rate = 22050
        duration = 5.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create a simple beat pattern (120 BPM = 2 beats per second)
        beat_freq = 2.0  # 2 beats per second
        audio = np.sin(2 * np.pi * 440 * t)  # Base tone
        
        # Add beat emphasis
        beat_times = np.arange(0, duration, 1/beat_freq)
        for beat_time in beat_times:
            beat_idx = int(beat_time * sample_rate)
            if beat_idx < len(audio):
                # Add a brief high tone for the beat
                beat_samples = int(0.1 * sample_rate)
                end_idx = min(beat_idx + beat_samples, len(audio))
                audio[beat_idx:end_idx] += 0.5 * np.sin(2 * np.pi * 880 * t[beat_idx:end_idx])
        
        # Normalize audio
        audio = audio / np.max(np.abs(audio))
        audio_int = (audio * 32767).astype(np.int16)
        
        write('test_audio.wav', sample_rate, audio_int)
        print("✅ test_audio.wav created")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test files: {e}")
        return False

def run_quick_test():
    """Run a quick analysis test on the generated files"""
    print("\n🚀 Running quick analysis test...")
    
    try:
        # Test scene detection
        from scenedetect import VideoManager, SceneManager
        from scenedetect.detectors import ContentDetector
        
        print("Testing scene detection...")
        video_manager = VideoManager(['test_video.mp4'])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=30.0))
        
        video_manager.set_duration()
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()
        
        print(f"✅ Scene detection: Found {len(scene_list)} scenes")
        
        # Test beat detection
        import librosa
        
        print("Testing beat detection...")
        y, sr = librosa.load('test_audio.wav')
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        print(f"✅ Beat detection: {tempo:.1f} BPM, {len(beats)} beats")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis test failed: {e}")
        return False

def main():
    """Run complete setup test"""
    print("🎬🎵 Music Video Generator - Setup Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test FFmpeg
    ffmpeg_ok = test_ffmpeg()
    
    if not imports_ok:
        print("\n❌ Some Python packages are missing. Install with:")
        print("pip install librosa scenedetect[opencv] moviepy matplotlib numpy")
        return False
    
    if not ffmpeg_ok:
        print("\n⚠️  FFmpeg not found but Python packages OK")
        print("You can still run analysis, but video rendering will fail")
    
    # Create and test with sample files
    files_ok = create_test_files()
    if files_ok:
        test_ok = run_quick_test()
        
        if test_ok:
            print("\n🎉 SETUP TEST COMPLETE!")
            print("✅ All dependencies working")
            print("✅ Test files created and analyzed")
            print("\nYou're ready to create music videos!")
            print("\nNext steps:")
            print("1. Replace test_video.mp4 with your movie file")
            print("2. Replace test_audio.wav with your song file") 
            print("3. Run the full music video generator")
            
            # Cleanup test files
            import os
            try:
                os.remove('test_video.mp4')
                os.remove('test_audio.wav')
                print("\n🧹 Cleaned up test files")
            except:
                pass
                
            return True
    
    print("\n❌ Setup test failed. Check error messages above.")
    return False

if __name__ == "__main__":
    main()
