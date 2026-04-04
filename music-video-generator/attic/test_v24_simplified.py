#!/usr/bin/env python3
"""
Test v24 simplified workflow with progressive mode and 12 clips
"""

import sys
import warnings
warnings.filterwarnings("ignore")

from ultraRobustArchivalToolv24 import UltraRobustArchivalEngine

def test_simplified_workflow():
    """Test the new simplified workflow with 12 clips."""
    
    film_path = "movie.mp4"
    song_path = "song.m4a"
    
    print("🧪 TESTING v24 SIMPLIFIED WORKFLOW (12 clips, progressive)")
    print("=" * 60)
    
    try:
        # Create engine
        engine = UltraRobustArchivalEngine(film_path, song_path)
        print(f"✓ Engine created successfully")
        print(f"✓ Source has audio: {engine.has_audio}")
        
        # Test simplified workflow
        print("\n📽️ Running simplified 3-step workflow...")
        success = engine.run_complete_pipeline(
            export_clips=True,
            max_scenes=12,
            beat_skip=2,  # Every other beat
            randomize=False,  # Progressive mode
            max_remix_clips=None,
            with_audio=True  # Should include audio in subclips
        )
        
        if success:
            print("✓ Pipeline completed successfully")
            
            # Check the results
            total_clips = sum(1 for s in engine.scene_data if s.get('has_clip', False))
            audio_clips = sum(1 for s in engine.scene_data if s.get('has_audio', False) and s.get('has_clip', False))
            
            print(f"\n📊 RESULTS:")
            print(f"   Total scenes processed: {len(engine.scene_data)}")
            print(f"   Clips created: {total_clips}")
            print(f"   Clips with audio: {audio_clips}")
            print(f"   Success rate: {audio_clips/total_clips*100:.1f}%" if total_clips > 0 else "   No clips created")
            
            # Show clip details
            print(f"\n📝 CLIP DETAILS:")
            for i, scene in enumerate(engine.scene_data[:12]):
                if scene.get('has_clip', False):
                    audio_status = "🔊 AUDIO" if scene.get('has_audio', False) else "🔇 NO AUDIO"
                    print(f"   Scene {scene['id']:2d} ({scene['start_timecode']}): {audio_status}")
            
            print(f"\n📁 Output: {engine.output_dir}/")
            print(f"   - analysis.html (interactive interface)")
            print(f"   - clips/ ({total_clips} subclips)")
            print(f"   - thumbnails/ ({len(engine.scene_data)} thumbnails)")
            if engine.song_path:
                print(f"   - remix_progressive.mp4 (music video)")
            
            return True
        else:
            print("✗ Pipeline failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simplified_workflow()
    if success:
        print("\n🎉 v24 SIMPLIFIED WORKFLOW TEST PASSED!")
        print("The new 3-step workflow is working correctly!")
    else:
        print("\n❌ v24 SIMPLIFIED WORKFLOW TEST FAILED!")
        sys.exit(1)