#!/usr/bin/env python3
"""
Compare regular (with repeats) vs no-repeat music video generation
"""

def compare_repeat_vs_no_repeat():
    """Create both versions to show the difference"""
    
    print("⚖️ REPEAT vs NO-REPEAT COMPARISON")
    print("=" * 45)
    print("Creating both versions to demonstrate the difference...")
    print()
    
    # Version 1: Regular (allows repeats)
    print("1️⃣ REGULAR VERSION (allows scene repeats):")
    from progressive_sampling_generator import ProgressiveSamplingGenerator
    
    regular_generator = ProgressiveSamplingGenerator(
        "movie.mp4", "song.mp3", "with_repeats.mp4"
    )
    
    regular_success = regular_generator.generate_progressive_music_video(
        max_clips=100,  # Test with 100 clips
        sampling_method="smart_random"
    )
    
    # Version 2: No-repeat
    print("\n2️⃣ NO-REPEAT VERSION (each scene used once):")
    from no_repeat_generator import NoRepeatProgressiveGenerator
    
    no_repeat_generator = NoRepeatProgressiveGenerator(
        "movie.mp4", "song.mp3", "no_repeats.mp4"
    )
    
    no_repeat_success = no_repeat_generator.generate_no_repeat_music_video(
        max_clips=100,
        strategy="progressive_unique"
    )
    
    if regular_success and no_repeat_success:
        print("\n🎊 BOTH VERSIONS CREATED!")
        print("📁 Compare these files:")
        print("   📄 with_repeats.mp4 (may have repeated scenes)")
        print("   📄 no_repeats.mp4 (guaranteed unique scenes)")
        print()
        print("🔍 Differences you should notice:")
        print("   • No-repeat version feels more like a complete movie journey")
        print("   • Regular version might repeat favorite/random scenes")
        print("   • No-repeat ensures you see more of the film's variety")
    
    return regular_success and no_repeat_success

def test_different_strategies():
    """Test different no-repeat strategies"""
    
    print("🎛️ TESTING DIFFERENT NO-REPEAT STRATEGIES")
    print("=" * 50)
    
    from no_repeat_generator import NoRepeatProgressiveGenerator
    
    strategies = [
        ("progressive_unique", "Progressive through movie, no repeats"),
        ("smart_distribution", "Even distribution across movie"),
        ("priority_sampling", "Best scenes first, then fill")
    ]
    
    for strategy, description in strategies:
        print(f"\n🎯 Testing: {strategy}")
        print(f"   {description}")
        
        generator = NoRepeatProgressiveGenerator(
            "movie.mp4", "song.mp3", f"no_repeat_{strategy}.mp4"
        )
        
        success = generator.generate_no_repeat_music_video(
            max_clips=50,  # Shorter for testing
            strategy=strategy
        )
        
        if success:
            print(f"✅ {strategy} completed successfully")
        else:
            print(f"❌ {strategy} failed")
    
    print(f"\n🎊 ALL STRATEGIES TESTED!")
    print(f"📁 Compare these approaches:")
    for strategy, _ in strategies:
        print(f"   📄 no_repeat_{strategy}.mp4")

def analyze_scene_usage():
    """Analyze how scenes are used in different approaches"""
    
    print("📊 SCENE USAGE ANALYSIS")
    print("=" * 30)
    print("Let's see how many unique scenes each approach uses...")
    print()
    
    from no_repeat_generator import NoRepeatProgressiveGenerator
    
    # Test with different clip counts
    clip_counts = [50, 100, 200, 400]
    
    for clips in clip_counts:
        print(f"🎯 Testing with {clips} clips:")
        
        generator = NoRepeatProgressiveGenerator("movie.mp4", "song.mp3")
        
        # Just do the analysis without rendering
        scenes = generator.detect_scenes()
        beats, tempo = generator.analyze_audio_beats()
        
        if scenes and beats:
            total_scenes = len(scenes)
            total_beats = len(beats) - 1
            actual_clips = min(clips, total_beats)
            
            # Calculate theoretical uniqueness
            if actual_clips <= total_scenes:
                uniqueness = 100.0
                repeated_scenes = 0
            else:
                uniqueness = (total_scenes / actual_clips) * 100
                repeated_scenes = actual_clips - total_scenes
            
            print(f"   Available scenes: {total_scenes}")
            print(f"   Requested clips: {actual_clips}")
            print(f"   Uniqueness rate: {uniqueness:.1f}%")
            if repeated_scenes > 0:
                print(f"   Scenes that must repeat: {repeated_scenes}")
            print()

def quick_no_repeat_test():
    """Quick test of the no-repeat system"""
    
    print("⚡ QUICK NO-REPEAT TEST")
    print("=" * 30)
    
    from no_repeat_generator import NoRepeatProgressiveGenerator
    
    generator = NoRepeatProgressiveGenerator(
        "movie.mp4", "song.mp3", "quick_no_repeat.mp4"
    )
    
    print("🎯 Creating music video with no repeated scenes...")
    success = generator.generate_no_repeat_music_video(
        max_clips=None,  # Full song
        strategy="progressive_unique"
    )
    
    if success:
        print("\n🎉 SUCCESS!")
        print("📁 Your no-repeat music video: quick_no_repeat.mp4")
        print("🎯 Every scene in this video is unique!")
    else:
        print("❌ Test failed")

def main():
    """Main menu"""
    
    print("🎬 NO-REPEAT MUSIC VIDEO TESTER")
    print("=" * 40)
    print("Eliminate repeated scenes for better variety!")
    print()
    print("Choose test:")
    print("1. Quick no-repeat test (recommended)")
    print("2. Compare repeat vs no-repeat versions")
    print("3. Test different no-repeat strategies")
    print("4. Analyze scene usage patterns")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        quick_no_repeat_test()
    elif choice == "2":
        compare_repeat_vs_no_repeat()
    elif choice == "3":
        test_different_strategies()
    elif choice == "4":
        analyze_scene_usage()
    else:
        print("Running quick test by default...")
        quick_no_repeat_test()

if __name__ == "__main__":
    main()
