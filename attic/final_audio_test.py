#!/usr/bin/env python3
"""
Final test of the fixed v21 with audio support
"""

import sys
import warnings
warnings.filterwarnings("ignore")

from ultraRobustArchivalToolv21 import UltraRobustArchivalEngine

def final_test():
    """Final test with fixed audio functionality."""
    
    film_path = "movie.mp4"
    song_path = "song.m4a"
    
    print("🧪 FINAL AUDIO TEST (v21 Fixed)")
    print("=" * 35)
    
    try:
        # Create engine
        engine = UltraRobustArchivalEngine(film_path, song_path)
        print(f"✓ Engine created successfully")
        print(f"✓ Source has audio: {engine.has_audio}")
        
        # Test with just 3 scenes for speed
        print("\n📽️ Testing with 3 scenes...")
        scenes = engine.analyze_and_export_scenes(
            export_clips=True,
            max_scenes=3,
            max_clip_duration=5,  # Very short clips
            with_audio=True
        )
        
        if scenes:
            print(f"✓ Scene analysis completed: {len(scenes)} scenes")
            
            # Check results
            audio_clips = 0
            total_clips = 0
            
            for scene in scenes:
                if scene.get('has_clip', False):
                    total_clips += 1
                    if scene.get('has_audio', False):
                        audio_clips += 1
                        
            print(f"✓ Total clips exported: {total_clips}")
            print(f"✓ Clips with audio: {audio_clips}")
            
            if audio_clips > 0:
                print("🎉 AUDIO EXPORT SUCCESS!")
                
                # Create HTML
                success = engine.create_visualization_html()
                if success:
                    print(f"✓ HTML created: {engine.output_dir}/analysis.html")
                    print("🔍 Look for 🔊 icons in the HTML interface")
                    return True
                    
            else:
                print("⚠ No audio clips were created")
                return False
                
        else:
            print("✗ Scene analysis failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = final_test()
    if success:
        print("\n🎉 FINAL AUDIO TEST PASSED!")
        print("The v21 enhanced audio support is working correctly!")
    else:
        print("\n❌ FINAL AUDIO TEST FAILED!")
        sys.exit(1)