#!/usr/bin/env python3
"""
Minimal test to verify audio functionality works
"""

import sys
import warnings
warnings.filterwarnings("ignore")

from ultraRobustArchivalToolv21 import UltraRobustArchivalEngine

def test_audio_export():
    """Test just the audio export functionality on a few scenes."""
    
    film_path = "movie.mp4"
    song_path = "song.m4a"
    
    print("🧪 MINIMAL AUDIO FUNCTIONALITY TEST")
    print("=" * 50)
    
    try:
        # Create engine
        engine = UltraRobustArchivalEngine(film_path, song_path)
        print(f"✓ Engine created successfully")
        print(f"✓ Audio detected: {engine.has_audio}")
        
        # Test with just 5 scenes
        print("\n📽️ Testing scene analysis with 5 scenes...")
        scenes = engine.analyze_and_export_scenes(
            export_clips=True,
            max_scenes=5,
            max_clip_duration=10,  # Short clips for quick test
            with_audio=True
        )
        
        if scenes:
            print(f"✓ Scene analysis completed: {len(scenes)} scenes")
            
            # Count audio clips
            audio_clips = sum(1 for s in scenes if s.get('has_audio', False))
            total_clips = sum(1 for s in scenes if s.get('has_clip', False))
            
            print(f"✓ Total clips exported: {total_clips}")
            print(f"✓ Clips with audio: {audio_clips}")
            
            # Create visualization
            success = engine.create_visualization_html()
            if success:
                print(f"✓ HTML visualization created")
                print(f"📁 Output: {engine.output_dir}")
                print(f"🌐 Open: {engine.output_dir}/analysis.html")
                
                # Show some details about audio clips
                for i, scene in enumerate(scenes[:3]):  # Show first 3
                    audio_status = "🔊 Audio" if scene.get('has_audio', False) else "🔇 No audio"
                    clip_status = "📹 Clip" if scene.get('has_clip', False) else "❌ No clip"
                    print(f"  Scene {scene['id']}: {clip_status}, {audio_status}")
                
                return True
            else:
                print("✗ HTML visualization failed")
                return False
        else:
            print("✗ Scene analysis failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_audio_export()
    if success:
        print("\n🎉 MINIMAL AUDIO TEST PASSED!")
        print("Check the analysis.html file and click on scenes to verify audio playback.")
    else:
        print("\n❌ MINIMAL AUDIO TEST FAILED!")
        sys.exit(1)