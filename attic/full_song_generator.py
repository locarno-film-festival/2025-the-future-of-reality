#!/usr/bin/env python3
"""
Full Song Duration Progressive Generator
Ensures the output matches the full song length while covering the entire movie
"""

from progressive_sampling_generator import ProgressiveSamplingGenerator

def create_full_song_music_video(video_file="movie.mp4", audio_file="song.mp3", output_file="full_song_journey.mp4"):
    """
    Create a music video that uses the ENTIRE song duration and covers the ENTIRE movie
    """
    
    print("🎵 FULL SONG PROGRESSIVE MUSIC VIDEO")
    print("=" * 50)
    print("Goal: Use every beat to create a complete journey through your movie!")
    print()
    
    # Create generator
    generator = ProgressiveSamplingGenerator(video_file, audio_file, output_file)
    
    # Step 1: Analyze the files first to show what we're working with
    print("🔍 ANALYZING YOUR FILES...")
    scenes = generator.detect_scenes()
    beats, tempo = generator.analyze_audio_beats()
    
    if not scenes or not beats:
        print("❌ Could not analyze files")
        return False
    
    total_beats = len(beats)
    song_duration = generator.audio_duration
    movie_duration = scenes[-1]['end'] / 60  # Convert to minutes
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"   🎵 Song: {song_duration/60:.1f} minutes, {total_beats} beats at {tempo:.0f} BPM")
    print(f"   🎬 Movie: {movie_duration:.1f} minutes, {len(scenes)} scenes")
    print(f"   🎯 Target: {total_beats} clips = {song_duration:.1f} seconds (FULL SONG)")
    
    # Step 2: Create the full song mapping
    print(f"\n🚀 CREATING FULL SONG MAPPING...")
    mapping = generator.create_progressive_mapping(
        max_clips=None,  # Use ALL beats - this is the key!
        sampling_method="smart_random"
    )
    
    if not mapping:
        print("❌ Failed to create mapping")
        return False
    
    print(f"✅ Created {len(mapping)} mappings (should be {total_beats-1})")
    
    # Step 3: Generate video clips
    print(f"\n🎬 GENERATING ALL VIDEO CLIPS...")
    clips = generator.generate_video_clips(max_clips=None)  # Use ALL clips
    
    if not clips:
        print("❌ Failed to generate clips")
        return False
    
    # Step 4: Verify we're using the full duration
    total_clip_duration = sum(clip.duration for clip in clips)
    print(f"✅ Generated {len(clips)} clips")
    print(f"📏 Total duration: {total_clip_duration:.1f} seconds")
    print(f"🎵 Song duration: {song_duration:.1f} seconds")
    
    duration_match = abs(total_clip_duration - song_duration) < 2.0  # Within 2 seconds
    if duration_match:
        print("✅ Duration matches song length!")
    else:
        print(f"⚠️ Duration mismatch: {abs(total_clip_duration - song_duration):.1f}s difference")
    
    # Step 5: Render the full video
    print(f"\n🎥 RENDERING FULL SONG VIDEO...")
    success = generator.render_music_video()
    
    if success:
        print(f"\n🎊 FULL SONG MUSIC VIDEO COMPLETE!")
        print(f"📁 File: {output_file}")
        print(f"⏱️ Duration: {total_clip_duration:.1f} seconds (full song)")
        print(f"🎬 Movie coverage: Beginning to end")
        print(f"🎵 Song coverage: Complete ({total_beats} beats)")
        
        # Calculate coverage stats
        unique_scenes = len(set(mapping_item['scene']['id'] for mapping_item in mapping))
        coverage_percent = (unique_scenes / len(scenes)) * 100
        
        print(f"\n📊 COVERAGE ANALYSIS:")
        print(f"   Unique scenes used: {unique_scenes}/{len(scenes)} ({coverage_percent:.1f}%)")
        print(f"   Sampling density: {len(clips)/len(scenes):.1f} clips per scene")
        print(f"   Movie journey: Complete beginning-to-end progression")
        
        return True
    else:
        print("❌ Rendering failed")
        return False

def create_optimized_full_song_video(video_file="movie.mp4", audio_file="song.mp3"):
    """
    Create an optimized version that ensures maximum movie coverage
    """
    
    print("🎯 OPTIMIZED FULL SONG VIDEO")
    print("=" * 40)
    print("Maximizing both song length AND movie coverage...")
    print()
    
    generator = ProgressiveSamplingGenerator(video_file, audio_file, "optimized_full_song.mp4")
    
    # Analyze first
    scenes = generator.detect_scenes()
    beats, tempo = generator.analyze_audio_beats()
    
    if not scenes or not beats:
        return False
    
    total_beats = len(beats)
    total_scenes = len(scenes)
    
    print(f"📊 Working with {total_beats} beats and {total_scenes} scenes")
    
    # Use ALL beats for full song duration
    success = generator.generate_progressive_music_video(
        max_clips=None,  # CRITICAL: Use all beats
        sampling_method="smart_random"
    )
    
    if success:
        print(f"\n✅ OPTIMIZED VERSION COMPLETE!")
        print(f"📁 File: optimized_full_song.mp4") 
        print(f"⏱️ Duration: Full song length")
        print(f"🎬 Coverage: Maximum movie sampling")
    
    return success

def compare_durations(video_file="movie.mp4", audio_file="song.mp3"):
    """
    Show the difference between limited clips vs full song
    """
    
    print("📊 DURATION COMPARISON")
    print("=" * 30)
    
    generator = ProgressiveSamplingGenerator(video_file, audio_file)
    scenes = generator.detect_scenes()
    beats, tempo = generator.analyze_audio_beats()
    
    if not scenes or not beats:
        return
    
    song_duration = generator.audio_duration
    total_beats = len(beats)
    
    print(f"🎵 Your song: {song_duration:.1f} seconds, {total_beats} beats")
    print()
    
    # Show different clip limits and their resulting durations
    test_clips = [50, 100, 200, 400, total_beats-1]
    
    for clips in test_clips:
        if clips >= total_beats:
            clips = total_beats - 1
            
        beat_duration = song_duration / total_beats
        estimated_duration = clips * beat_duration
        coverage = (clips / (total_beats-1)) * 100
        
        if clips == total_beats - 1:
            print(f"🎯 {clips} clips = {estimated_duration:.1f}s ({coverage:.0f}% - FULL SONG)")
        else:
            print(f"   {clips} clips = {estimated_duration:.1f}s ({coverage:.0f}% of song)")

def main():
    """
    Main function with options
    """
    
    print("🎵 FULL SONG DURATION MUSIC VIDEO GENERATOR")
    print("=" * 55)
    print()
    print("Choose option:")
    print("1. Create full song music video (recommended)")
    print("2. Create optimized full song video") 
    print("3. Compare different durations")
    print("4. Quick full song test")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        create_full_song_music_video()
    elif choice == "2":
        create_optimized_full_song_video()
    elif choice == "3":
        compare_durations()
    elif choice == "4":
        # Quick test with current files
        generator = ProgressiveSamplingGenerator("movie.mp4", "song.mp3", "quick_full_song.mp4")
        print("🚀 Quick full song test...")
        success = generator.generate_progressive_music_video(max_clips=None)  # Full song
        if success:
            print("✅ Quick test complete! Check quick_full_song.mp4")
    else:
        print("Creating full song video by default...")
        create_full_song_music_video()

if __name__ == "__main__":
    main()
