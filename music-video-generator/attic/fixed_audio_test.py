#!/usr/bin/env python3
"""
Test audio functionality with corrected MoviePy API calls
"""

import warnings
warnings.filterwarnings("ignore")

try:
    from moviepy.editor import VideoFileClip
    print("✓ MoviePy imported successfully")
except ImportError as e:
    print(f"✗ MoviePy import failed: {e}")
    exit(1)

def test_audio_functionality():
    """Test audio detection and basic clip creation."""
    
    film_path = "movie.mp4"
    
    print("🧪 FIXED AUDIO FUNCTIONALITY TEST")
    print("=" * 35)
    
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
            
            # Try to create a short clip with audio
            try:
                print("🎬 Creating test clip with audio...")
                test_clip = video.subclip(10, 15)  # 5 second test clip
                
                if test_clip.audio is not None:
                    print("✓ Test clip has audio")
                    
                    # Try to export a tiny test clip
                    print("💾 Testing audio export...")
                    test_output = "test_audio_clip.mp4"
                    
                    test_clip.write_videofile(
                        test_output,
                        codec='libx264',
                        audio=True,
                        audio_codec='aac',
                        verbose=False,
                        logger=None,
                        preset='fast',
                        fps=24
                    )
                    
                    print(f"🎉 SUCCESS! Audio clip exported: {test_output}")
                    
                    test_clip.close()
                    video.close()
                    return True
                    
                else:
                    print("⚠ Test clip has no audio")
                    test_clip.close()
                    video.close()
                    return False
                    
            except Exception as clip_error:
                print(f"✗ Clip creation failed: {str(clip_error)[:100]}")
                try:
                    test_clip.close()
                except:
                    pass
                video.close()
                return False
                
        else:
            print("🔇 No audio track found")
            video.close()
            return False
            
    except Exception as e:
        print(f"✗ Video loading failed: {str(e)[:100]}")
        return False

if __name__ == "__main__":
    success = test_audio_functionality()
    if success:
        print("\n🎉 AUDIO FUNCTIONALITY TEST PASSED!")
        print("The v21 audio export should work correctly.")
    else:
        print("\n❌ AUDIO FUNCTIONALITY TEST FAILED!")
        exit(1)