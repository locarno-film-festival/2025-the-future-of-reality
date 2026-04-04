#!/usr/bin/env python3
"""
Test just the audio detection functionality without full processing
"""

import warnings
warnings.filterwarnings("ignore")

try:
    from moviepy.editor import VideoFileClip
    print("✓ MoviePy imported successfully")
except ImportError as e:
    print(f"✗ MoviePy import failed: {e}")
    exit(1)

def test_audio_detection():
    """Test if we can detect audio in the video file."""
    
    film_path = "movie.mp4"
    
    print("🧪 AUDIO DETECTION TEST")
    print("=" * 30)
    
    try:
        print("📹 Loading video file...")
        video = VideoFileClip(film_path)
        
        print(f"✓ Video loaded successfully")
        print(f"  Duration: {video.duration:.1f} seconds")
        print(f"  FPS: {video.fps:.1f}")
        print(f"  Size: {video.w}x{video.h}")
        
        # Check audio
        if video.audio is not None:
            print(f"🔊 Audio track detected!")
            print(f"  Audio duration: {video.audio.duration:.1f} seconds")
            
            # Try to get a small sample of audio
            try:
                print("🎵 Testing audio data access...")
                audio_array = video.audio.to_soundarray(fps=22050, nbytes=2, quantize=True, verbose=False)
                print(f"✓ Audio data accessible: {audio_array.shape}")
                print("🎉 AUDIO DETECTION TEST PASSED!")
                
                video.close()
                return True
                
            except Exception as audio_error:
                print(f"⚠ Audio data access failed: {str(audio_error)[:50]}")
                video.close()
                return False
        else:
            print("🔇 No audio track found")
            video.close()
            return False
            
    except Exception as e:
        print(f"✗ Video loading failed: {str(e)[:50]}")
        return False

if __name__ == "__main__":
    success = test_audio_detection()
    if not success:
        print("\n❌ AUDIO DETECTION TEST FAILED!")
        exit(1)