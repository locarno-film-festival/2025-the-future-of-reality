#!/usr/bin/env python3
"""
Test v22 with fixed audio handling - all clips should have audio
"""

import sys
import warnings
warnings.filterwarnings("ignore")

from ultraRobustArchivalToolv22 import UltraRobustArchivalEngine

def test_fixed_audio():
    """Test that ALL clips have audio with the fixed version."""
    
    film_path = "movie.mp4"
    song_path = "song.m4a"
    
    print("🧪 TESTING v22 FIXED AUDIO (ALL clips should have audio)")
    print("=" * 60)
    
    try:
        # Create engine
        engine = UltraRobustArchivalEngine(film_path, song_path)
        print(f"✓ Engine created successfully")
        print(f"✓ Source has audio: {engine.has_audio}")
        
        # Test with 3 scenes for speed
        print("\n📽️ Testing with 3 scenes...")
        scenes = engine.analyze_and_export_scenes(
            export_clips=True,
            max_scenes=3,
            max_clip_duration=5,  # Short clips for quick test
            with_audio=True
        )
        
        if scenes:
            print(f"✓ Scene analysis completed: {len(scenes)} scenes")
            
            # Check results - ALL should have audio
            audio_clips = 0
            total_clips = 0
            no_audio_clips = []
            
            for scene in scenes:
                if scene.get('has_clip', False):
                    total_clips += 1
                    if scene.get('has_audio', False):
                        audio_clips += 1
                    else:
                        no_audio_clips.append(scene['id'])
                        
            print(f"✓ Total clips exported: {total_clips}")
            print(f"✓ Clips with audio: {audio_clips}")
            
            if audio_clips == total_clips:
                print("🎉 SUCCESS! ALL clips have audio!")
                
                # Create HTML
                success = engine.create_visualization_html()
                if success:
                    print(f"✓ HTML created: {engine.output_dir}/analysis.html")
                    return True
                    
            else:
                print(f"❌ FAILURE! {len(no_audio_clips)} clips missing audio: {no_audio_clips}")
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
    success = test_fixed_audio()
    if success:
        print("\n🎉 v22 FIXED AUDIO TEST PASSED!")
        print("ALL clips now have audio as expected!")
    else:
        print("\n❌ v22 FIXED AUDIO TEST FAILED!")
        sys.exit(1)