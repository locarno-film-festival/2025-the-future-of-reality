#!/usr/bin/env python3
"""
Test the fixed adaptive tempo generator
"""

from fixed_adaptive_tempo_generator import FixedAdaptiveTempoGenerator

def quick_test():
    """Quick test of the fixed version"""
    
    print("🔧 TESTING FIXED ADAPTIVE TEMPO GENERATOR")
    print("=" * 50)
    print("This version handles the numpy formatting issues!")
    print()
    
    generator = FixedAdaptiveTempoGenerator(
        "movie.mp4", 
        "song.mp3", 
        "chain_adaptive_fixed.mp4"
    )
    
    print("🎯 Creating adaptive tempo music video...")
    print("   • Will detect tempo changes (if any)")
    print("   • Adapts scene pacing to match song energy")
    print("   • Uses full song duration")
    print()
    
    success = generator.generate_adaptive_music_video(
        max_clips=None,      # Full song duration
        sensitivity="high",  # Very responsive to tempo changes
        threshold=30.0       # Scene detection sensitivity
    )
    
    if success:
        print("\n🎉 FIXED VERSION SUCCESS!")
        print("📁 Your adaptive tempo music video: chain_adaptive_fixed.mp4")
        print()
        print("🎵 The video should:")
        print("   • Match the full song duration")
        print("   • Vary pacing based on tempo changes")
        print("   • Show faster cuts during energetic sections")
        print("   • Use longer scenes during slower parts")
    else:
        print("\n❌ Fixed version also failed - check your file paths")

if __name__ == "__main__":
    quick_test()
