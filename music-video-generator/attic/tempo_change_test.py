#!/usr/bin/env python3
"""
Test script for songs with tempo changes like "The Chain"
"""

from adaptive_tempo_generator import AdaptiveTempoGenerator

def test_adaptive_tempo():
    """Test the adaptive tempo generator"""
    
    print("🎵 ADAPTIVE TEMPO TEST")
    print("=" * 40)
    print("Perfect for songs like 'The Chain' with tempo changes!")
    print()
    
    # Create generator
    generator = AdaptiveTempoGenerator(
        video_path="movie.mp4",
        audio_path="song.mp3",  # Your "Chain" or other tempo-changing song
        output_path="adaptive_tempo_chain.mp4"
    )
    
    print("🎯 This will:")
    print("   • Detect tempo changes throughout the song")
    print("   • Adapt scene selection based on tempo")
    print("   • Create faster cuts during fast sections")
    print("   • Use longer, more contemplative scenes during slow parts")
    print("   • Show tempo analysis visualization")
    print()
    
    # Generate with high sensitivity to tempo changes
    success = generator.generate_adaptive_music_video(
        max_clips=None,         # Full song duration
        sensitivity="high",     # Very responsive to tempo changes
        threshold=30.0,         # Scene detection sensitivity
        visualize=True          # Show tempo analysis chart
    )
    
    if success:
        print("\n🎉 SUCCESS!")
        print("🎬 Your adaptive tempo music video: adaptive_tempo_chain.mp4")
        print("📊 Check the tempo analysis chart that was generated")
        print("\nYou should notice:")
        print("   • Slow, contemplative cuts during quiet parts")
        print("   • Fast, energetic cuts during the bass line section")
        print("   • Smooth transitions between tempo sections")
    else:
        print("❌ Generation failed")

def compare_adaptive_vs_regular():
    """Compare adaptive tempo vs regular progressive sampling"""
    
    print("⚖️ ADAPTIVE VS REGULAR COMPARISON")
    print("=" * 45)
    print("Creating both versions to see the difference...")
    print()
    
    # 1. Regular progressive (ignores tempo changes)
    print("1️⃣ Creating regular progressive version...")
    from progressive_sampling_generator import ProgressiveSamplingGenerator
    
    regular_generator = ProgressiveSamplingGenerator(
        "movie.mp4", "song.mp3", "regular_progressive_chain.mp4"
    )
    
    regular_success = regular_generator.generate_progressive_music_video(
        max_clips=None,
        sampling_method="smart_random"
    )
    
    # 2. Adaptive tempo version
    print("\n2️⃣ Creating adaptive tempo version...")
    adaptive_generator = AdaptiveTempoGenerator(
        "movie.mp4", "song.mp3", "adaptive_tempo_chain.mp4"
    )
    
    adaptive_success = adaptive_generator.generate_adaptive_music_video(
        max_clips=None,
        sensitivity="high",
        visualize=True
    )
    
    if regular_success and adaptive_success:
        print("\n🎊 BOTH VERSIONS CREATED!")
        print("📁 Compare these files:")
        print("   📄 regular_progressive_chain.mp4 (ignores tempo changes)")
        print("   📄 adaptive_tempo_chain.mp4 (adapts to tempo changes)")
        print("\n🎯 In the adaptive version, you should notice:")
        print("   • Different pacing that matches the song's energy")
        print("   • Faster cuts during high-energy sections")
        print("   • More contemplative scenes during slow parts")

def analyze_song_tempo_only():
    """Just analyze the tempo without creating video"""
    
    print("🔍 TEMPO ANALYSIS ONLY")
    print("=" * 30)
    print("Analyzing your song's tempo changes...")
    print()
    
    generator = AdaptiveTempoGenerator("movie.mp4", "song.mp3")
    
    # Just do tempo analysis
    tempo_segments, tempo_changes = generator.analyze_adaptive_tempo()
    
    if tempo_segments:
        # Generate visualization
        generator.visualize_tempo_analysis("song_tempo_analysis.png")
        
        print(f"\n📊 TEMPO ANALYSIS RESULTS:")
        print(f"   Global tempo: {generator.global_tempo:.1f} BPM")
        print(f"   Tempo segments analyzed: {len(tempo_segments)}")
        print(f"   Significant tempo changes: {len(tempo_changes)}")
        
        if tempo_changes:
            print(f"\n🔄 Tempo changes detected:")
            for change in tempo_changes:
                print(f"   {change['time']:.1f}s: {change['old_tempo']:.0f} → {change['new_tempo']:.0f} BPM")
        else:
            print(f"\n📊 No significant tempo changes detected")
            print(f"   (Your song might have consistent tempo)")
        
        print(f"\n📈 Tempo visualization saved as: song_tempo_analysis.png")
    else:
        print("❌ Could not analyze tempo")

def test_different_sensitivities():
    """Test different sensitivity levels"""
    
    print("🎛️ SENSITIVITY LEVEL TEST")
    print("=" * 35)
    print("Creating videos with different tempo sensitivity levels...")
    print()
    
    sensitivities = ["low", "medium", "high"]
    
    for sensitivity in sensitivities:
        print(f"🎯 Creating {sensitivity} sensitivity version...")
        
        generator = AdaptiveTempoGenerator(
            "movie.mp4", "song.mp3", 
            f"adaptive_{sensitivity}_sensitivity.mp4"
        )
        
        success = generator.generate_adaptive_music_video(
            max_clips=100,  # Shorter for quick testing
            sensitivity=sensitivity,
            visualize=False  # Skip visualization for speed
        )
        
        if success:
            print(f"✅ {sensitivity} sensitivity version complete")
        else:
            print(f"❌ {sensitivity} sensitivity version failed")
    
    print(f"\n🎊 ALL SENSITIVITY TESTS COMPLETE!")
    print(f"📁 Compare these files:")
    print(f"   📄 adaptive_low_sensitivity.mp4")
    print(f"   📄 adaptive_medium_sensitivity.mp4") 
    print(f"   📄 adaptive_high_sensitivity.mp4")

def main():
    """Main menu"""
    
    print("🎵 ADAPTIVE TEMPO MUSIC VIDEO TESTER")
    print("=" * 45)
    print("Perfect for songs with tempo changes!")
    print()
    print("Choose test:")
    print("1. Create adaptive tempo music video (recommended)")
    print("2. Compare adaptive vs regular progressive")
    print("3. Analyze song tempo only (no video)")
    print("4. Test different sensitivity levels")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_adaptive_tempo()
    elif choice == "2":
        compare_adaptive_vs_regular()
    elif choice == "3":
        analyze_song_tempo_only()
    elif choice == "4":
        test_different_sensitivities()
    else:
        print("Running adaptive tempo test by default...")
        test_adaptive_tempo()

if __name__ == "__main__":
    main()
