#!/usr/bin/env python3
"""
Quick test version for audio functionality - limits to 20 scenes for faster testing
"""

import sys
from ultraRobustArchivalToolv21 import UltraRobustArchivalEngine

def main():
    """Quick test with limited scenes."""
    if len(sys.argv) < 3:
        print("Usage: python quick_audio_test.py <film.mp4> <song.m4a>")
        return
    
    film_path = sys.argv[1]
    song_path = sys.argv[2]
    
    # Create engine and run with limited scenes for quick testing
    engine = UltraRobustArchivalEngine(film_path, song_path)
    
    print("\n🧪 QUICK AUDIO TEST - LIMITED TO 20 SCENES")
    
    success = engine.run_complete_pipeline(
        export_clips=True,
        max_scenes=20,  # Limit to 20 scenes for quick test
        beat_skip=2,    # Every other beat
        randomize=True, # Random mode
        max_remix_clips=50,  # Limit remix clips
        with_audio=True # Enable audio
    )
    
    if success:
        print(f"\n✅ QUICK TEST COMPLETE!")
        print(f"📁 Check: {engine.output_dir}/analysis.html")
        print(f"🔍 Look for 🔊 icons indicating audio clips")
        print(f"🎬 Click on clips to test audio playback")
    else:
        print("\n❌ Quick test failed")

if __name__ == "__main__":
    main()