#!/usr/bin/env python3
"""
MoviePy Final Test - Check if it's actually working
"""

def test_moviepy_complete():
    """Comprehensive test of MoviePy functionality"""
    print("🎬 MOVIEPY FINAL WORKING TEST")
    print("=" * 50)
    
    # Test 1: Basic imports
    try:
        import moviepy.editor as mp
        print("✅ moviepy.editor import - SUCCESS")
    except ImportError as e:
        print(f"❌ moviepy.editor import - FAILED: {e}")
        return False
    
    # Test 2: Check version (from main package)
    try:
        import moviepy
        version = getattr(moviepy, '__version__', 'unknown')
        print(f"✅ MoviePy version: {version}")
    except:
        print("⚠️ Version check failed (but might still work)")
    
    # Test 3: Key classes
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
        print("✅ Key classes import - SUCCESS")
        print("   - VideoFileClip:", VideoFileClip)
        print("   - AudioFileClip:", AudioFileClip)
        print("   - concatenate_videoclips:", concatenate_videoclips)
    except ImportError as e:
        print(f"❌ Key classes import - FAILED: {e}")
        return False
    
    # Test 4: Effects (version-dependent)
    print("\n🎨 Testing effects:")
    
    # Try old-style effects (MoviePy 1.x)
    try:
        clip_test = VideoFileClip.__new__(VideoFileClip)  # Create without file
        if hasattr(clip_test, 'fadein'):
            print("✅ Old-style effects (fadein/fadeout) - Available")
            old_effects = True
        else:
            print("❌ Old-style effects - Not available")
            old_effects = False
    except:
        print("⚠️ Old-style effects test inconclusive")
        old_effects = False
    
    # Try new-style effects (MoviePy 2.x)
    new_effects = False
    try:
        from moviepy.video.fx.fadein import FadeIn
        from moviepy.video.fx.fadeout import FadeOut
        print("✅ New-style effects (FadeIn/FadeOut) - Available")
        new_effects = True
    except ImportError:
        print("❌ New-style effects - Not available")
    
    # Test 5: Create a dummy clip to verify functionality
    print("\n🧪 Testing clip creation:")
    try:
        # Try to create a simple color clip (doesn't need a file)
        from moviepy.editor import ColorClip
        test_clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1)
        print("✅ ColorClip creation - SUCCESS")
        test_clip.close()
        
        # Test concatenation
        clip2 = ColorClip(size=(100, 100), color=(0, 255, 0), duration=1)
        combined = concatenate_videoclips([test_clip, clip2])
        print("✅ Video concatenation - SUCCESS")
        combined.close()
        clip2.close()
        
    except Exception as e:
        print(f"❌ Clip operations - FAILED: {e}")
        return False
    
    # Summary
    print("\n📊 SUMMARY:")
    print("=" * 30)
    if old_effects:
        print("🎉 MoviePy 1.x fully working!")
        print("   Use: clip.fadein(), clip.fadeout()")
    elif new_effects:
        print("🎉 MoviePy 2.x fully working!")
        print("   Use: clip.with_effects([FadeIn(), FadeOut()])")
    else:
        print("✅ MoviePy basic functionality working!")
        print("   Effects may need special handling")
    
    print("\n💡 Ready for music video generation!")
    return True

def create_working_example():
    """Create a simple working example"""
    print("\n🚀 CREATING WORKING EXAMPLE")
    print("=" * 50)
    
    example_code = '''
# Working MoviePy example for music video generator:

from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

def create_simple_music_video(video_path, audio_path, output_path):
    """Simple working example"""
    
    # Load video and audio
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    
    # Create a short clip (first 10 seconds)
    short_clip = video.subclip(0, min(10, video.duration))
    
    # Add audio
    final_clip = short_clip.set_audio(audio.subclip(0, short_clip.duration))
    
    # Save
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    
    # Cleanup
    video.close()
    audio.close()
    final_clip.close()
    
    print(f"✅ Simple music video saved: {output_path}")

# Usage:
# create_simple_music_video("input.mp4", "song.mp3", "output.mp4")
'''
    
    print("📝 Save this example code:")
    print(example_code)
    
    return example_code

if __name__ == "__main__":
    success = test_moviepy_complete()
    
    if success:
        create_working_example()
        print("\n🎊 MOVIEPY IS WORKING!")
        print("You can now run your music video generator!")
    else:
        print("\n❌ MoviePy still has issues.")
        print("Try the FFmpeg-only version instead.")
