#!/usr/bin/env python3
"""
Test v23 with progressive mode and 12 clips to identify pattern
"""

import sys
import warnings
warnings.filterwarnings("ignore")

from ultraRobustArchivalToolv23 import UltraRobustArchivalEngine

def test_progressive_audio():
    """Test progressive mode with 12 clips to see audio pattern."""
    
    film_path = "movie.mp4"
    song_path = "song.m4a"
    
    print("🧪 TESTING v23 PROGRESSIVE MODE (12 clips)")
    print("=" * 50)
    
    try:
        # Create engine
        engine = UltraRobustArchivalEngine(film_path, song_path)
        print(f"✓ Engine created successfully")
        print(f"✓ Source has audio: {engine.has_audio}")
        
        # Test with 12 scenes in progressive mode
        print("\n📽️ Testing with 12 scenes in progressive order...")
        scenes = engine.analyze_and_export_scenes(
            export_clips=True,
            max_scenes=12,
            max_clip_duration=5,  # Short clips for quick test
            with_audio=True
        )
        
        if scenes:
            print(f"✓ Scene analysis completed: {len(scenes)} scenes")
            
            # Detailed analysis of each clip
            audio_clips = 0
            total_clips = 0
            clip_details = []
            
            for scene in scenes:
                if scene.get('has_clip', False):
                    total_clips += 1
                    has_audio = scene.get('has_audio', False)
                    if has_audio:
                        audio_clips += 1
                    
                    clip_details.append({
                        'id': scene['id'],
                        'has_audio': has_audio,
                        'timecode': scene['start_timecode']
                    })
                        
            print(f"✓ Total clips exported: {total_clips}")
            print(f"✓ Clips with audio: {audio_clips}")
            print(f"✓ Success rate: {audio_clips/total_clips*100:.1f}%")
            
            # Show pattern
            print("\n📊 CLIP ANALYSIS PATTERN:")
            for clip in clip_details:
                status = "🔊 AUDIO" if clip['has_audio'] else "🔇 NO AUDIO"
                print(f"   Scene {clip['id']:2d} ({clip['timecode']}): {status}")
            
            # Check for pattern
            audio_positions = [clip['id'] for clip in clip_details if clip['has_audio']]
            no_audio_positions = [clip['id'] for clip in clip_details if not clip['has_audio']]
            
            print(f"\n📈 PATTERN ANALYSIS:")
            print(f"   Audio clips at positions: {audio_positions}")
            print(f"   No audio clips at positions: {no_audio_positions}")
            
            if audio_clips == total_clips:
                print("🎉 SUCCESS! ALL clips have audio!")
            else:
                print(f"⚠ PARTIAL SUCCESS: {no_audio_positions} clips missing audio")
                
            # Create HTML
            success = engine.create_visualization_html()
            if success:
                print(f"✓ HTML created: {engine.output_dir}/analysis.html")
                return True
                
        else:
            print("✗ Scene analysis failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_progressive_audio()
    if success:
        print("\n🎉 v23 PROGRESSIVE TEST COMPLETED!")
    else:
        print("\n❌ v23 PROGRESSIVE TEST FAILED!")
        sys.exit(1)