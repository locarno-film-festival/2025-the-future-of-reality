#!/usr/bin/env python3
"""
Test script for progressive sampling music video generation
"""

from progressive_sampling_generator import ProgressiveSamplingGenerator

def test_all_methods():
    """Test different progressive sampling methods"""
    
    # Create generator
    generator = ProgressiveSamplingGenerator("movie.mp4", "song.mp3")
    
    print("🎬 Testing Progressive Sampling Methods")
    print("=" * 60)
    
    # Method 1: Smart Random (Recommended)
    print("\n1️⃣ SMART RANDOM SAMPLING")
    print("Random selection within progressive time windows")
    generator.output_path = "progressive_smart_random.mp4"
    generator.generate_progressive_music_video(
        max_clips=100,  # ~40 seconds at 152 BPM
        sampling_method="smart_random"
    )
    
    # Method 2: Weighted Random  
    print("\n2️⃣ WEIGHTED RANDOM SAMPLING")
    print("Prioritizes longer/more important scenes")
    generator.output_path = "progressive_weighted.mp4"
    generator.generate_progressive_music_video(
        max_clips=100,
        sampling_method="weighted_random"
    )
    
    # Method 3: Even Distribution
    print("\n3️⃣ EVEN DISTRIBUTION SAMPLING")
    print("Evenly spaced samples across the movie")
    generator.output_path = "progressive_even.mp4"
    generator.generate_progressive_music_video(
        max_clips=100,
        sampling_method="even_distribution"
    )
    
    print("\n🎊 ALL PROGRESSIVE VIDEOS CREATED!")
    print("Compare these three approaches:")
    print("   📁 progressive_smart_random.mp4")
    print("   📁 progressive_weighted.mp4") 
    print("   📁 progressive_even.mp4")

def test_different_lengths():
    """Test different video lengths"""
    
    generator = ProgressiveSamplingGenerator("movie.mp4", "song.mp3")
    
    print("\n🎬 Testing Different Lengths")
    print("=" * 40)
    
    # Short preview (30 seconds)
    print("\n⚡ 30-second preview")
    generator.output_path = "progressive_30sec.mp4"
    generator.generate_progressive_music_video(
        max_clips=76,  # ~30 seconds at 152 BPM
        sampling_method="smart_random"
    )
    
    # Medium (1 minute)
    print("\n🎯 1-minute highlight")
    generator.output_path = "progressive_1min.mp4"
    generator.generate_progressive_music_video(
        max_clips=152,  # ~1 minute at 152 BPM
        sampling_method="smart_random"
    )
    
    # Full song
    print("\n🎵 Full song length")
    generator.output_path = "progressive_full_song.mp4"
    generator.generate_progressive_music_video(
        max_clips=650,  # Almost full song
        sampling_method="smart_random"
    )
    
    print("\n🎊 ALL LENGTHS CREATED!")

def quick_progressive_test():
    """Quick test with your exact setup"""
    
    generator = ProgressiveSamplingGenerator("movie.mp4", "song.mp3", "progressive_journey.mp4")
    
    print("🚀 QUICK PROGRESSIVE TEST")
    print("=" * 40)
    print("Creating a movie journey that goes from beginning to end...")
    print("but randomly samples scenes from each portion!")
    
    success = generator.generate_progressive_music_video(
        max_clips=None,  # About 80 seconds
        sampling_method="smart_random"
    )
    
    if success:
        print("\n🎉 SUCCESS!")
        print("🎬 Your progressive music video: progressive_journey.mp4")
        print("\nThis video takes you on a journey through your entire movie,")
        print("but samples randomly from each time period to match your song!")
    else:
        print("❌ Something went wrong")

if __name__ == "__main__":
    # Choose what to run:
    
    print("Choose test:")
    print("1. Quick progressive test (recommended)")
    print("2. Test all sampling methods")
    print("3. Test different lengths")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        quick_progressive_test()
    elif choice == "2":
        test_all_methods()
    elif choice == "3":
        test_different_lengths()
    else:
        print("Running quick test by default...")
        quick_progressive_test()
