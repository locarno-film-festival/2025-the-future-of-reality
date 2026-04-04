#!/usr/bin/env python3
"""
Debug version to find out why bulletproof generator created all black screens
"""

from bulletproof_generator import BulletproofGenerator
import traceback

def debug_bulletproof_step_by_step():
    """Debug each step to see where it's going wrong"""
    
    print("🔍 DEBUGGING BULLETPROOF GENERATOR")
    print("=" * 45)
    print("Let's see where the black screens are coming from...")
    print()
    
    generator = BulletproofGenerator("movie.mp4", "song.mp3", "debug_test.mp4")
    
    # Step 1: Test scene detection
    print("1️⃣ TESTING SCENE DETECTION:")
    try:
        scenes = generator.detect_scenes(threshold=30.0)
        if scenes:
            print(f"✅ Scene detection working: {len(scenes)} scenes found")
            print(f"   First scene: {scenes[0]['start']:.1f}s to {scenes[0]['end']:.1f}s")
            print(f"   Last scene: {scenes[-1]['start']:.1f}s to {scenes[-1]['end']:.1f}s")
        else:
            print("❌ No scenes detected!")
            return
    except Exception as e:
        print(f"❌ Scene detection failed: {e}")
        traceback.print_exc()
        return
    
    # Step 2: Test beat analysis
    print("\n2️⃣ TESTING BEAT ANALYSIS:")
    try:
        beats, tempo = generator.analyze_audio_beats()
        if beats:
            print(f"✅ Beat analysis working: {len(beats)} beats at {tempo:.1f} BPM")
            print(f"   Duration: {generator.audio_duration:.1f} seconds")
        else:
            print("❌ No beats detected!")
            return
    except Exception as e:
        print(f"❌ Beat analysis failed: {e}")
        traceback.print_exc()
        return
    
    # Step 3: Test video loading
    print("\n3️⃣ TESTING VIDEO LOADING:")
    try:
        from moviepy.editor import VideoFileClip
        video = VideoFileClip("movie.mp4", verbose=False)
        print(f"✅ Video loads fine: {video.duration:.1f}s, {video.size}")
        video.close()
    except Exception as e:
        print(f"❌ Video loading failed: {e}")
        traceback.print_exc()
        return
    
    # Step 4: Test mapping creation (this is probably where it goes wrong)
    print("\n4️⃣ TESTING MAPPING CREATION:")
    try:
        mapping = generator.create_bulletproof_mapping(max_clips=10)  # Test with just 10 clips
        
        print(f"   Total mappings: {len(mapping)}")
        
        # Analyze mapping types
        types = {}
        for m in mapping:
            mtype = m['type']
            types[mtype] = types.get(mtype, 0) + 1
        
        print(f"   Mapping types: {types}")
        
        # Show first few mappings
        print("   First 5 mappings:")
        for i, m in enumerate(mapping[:5]):
            scene_info = f"Scene {m['scene']['id']}" if m['scene'] else "BLACK SCREEN"
            print(f"     Beat {i}: {m['type']} -> {scene_info}")
        
        if types.get('emergency_black', 0) > 0:
            print(f"\n🚨 FOUND THE PROBLEM: {types['emergency_black']} black screens!")
            print("   Reasons:")
            for reason in generator.fallback_reasons:
                print(f"     • {reason}")
        
    except Exception as e:
        print(f"❌ Mapping creation failed: {e}")
        traceback.print_exc()
        return
    
    # Step 5: Test single scene extraction
    print("\n5️⃣ TESTING SINGLE SCENE EXTRACTION:")
    try:
        from moviepy.editor import VideoFileClip
        video = VideoFileClip("movie.mp4", verbose=False)
        
        # Test extracting the first scene
        first_scene = scenes[0]
        test_clip = video.subclip(first_scene['start'], first_scene['end'])
        print(f"✅ Scene extraction works: {test_clip.duration:.1f}s clip")
        
        test_clip.close()
        video.close()
        
    except Exception as e:
        print(f"❌ Scene extraction failed: {e}")
        traceback.print_exc()
        return
    
    print("\n🎯 DIAGNOSIS COMPLETE!")

def create_fixed_bulletproof():
    """Create a fixed version that's less aggressive with black screens"""
    
    print("\n🔧 CREATING FIXED VERSION")
    print("=" * 30)
    
    from perfect_forward_generator import PerfectForwardGenerator
    
    # Use the perfect forward generator (which worked) as base
    generator = PerfectForwardGenerator("movie.mp4", "song.mp3", "fixed_bulletproof.mp4")
    
    success = generator.generate_perfect_music_video(max_clips=None)
    
    if success:
        print("✅ Fixed version created: fixed_bulletproof.mp4")
        print("   This should work without black screens!")
    else:
        print("❌ Even the fixed version failed")

def compare_working_vs_broken():
    """Compare the working perfect generator vs broken bulletproof"""
    
    print("\n⚖️ COMPARING WORKING VS BROKEN")
    print("=" * 40)
    
    # Test the working perfect generator
    print("1️⃣ Testing WORKING perfect generator:")
    from perfect_forward_generator import PerfectForwardGenerator
    
    working_gen = PerfectForwardGenerator("movie.mp4", "song.mp3", "working_test.mp4")
    
    try:
        working_gen.detect_scenes()
        working_gen.analyze_audio_beats()
        working_mapping = working_gen.create_guaranteed_forward_mapping(max_clips=10)
        
        print(f"   ✅ Working generator: {len(working_mapping)} mappings")
        
        types = {}
        for m in working_mapping:
            mtype = m.get('type', 'normal_scene')
            types[mtype] = types.get(mtype, 0) + 1
        print(f"   Mapping types: {types}")
        
    except Exception as e:
        print(f"   ❌ Working generator failed: {e}")
    
    # Test the broken bulletproof generator
    print("\n2️⃣ Testing BROKEN bulletproof generator:")
    broken_gen = BulletproofGenerator("movie.mp4", "song.mp3", "broken_test.mp4")
    
    try:
        broken_gen.detect_scenes()
        broken_gen.analyze_audio_beats()
        broken_mapping = broken_gen.create_bulletproof_mapping(max_clips=10)
        
        print(f"   Bulletproof generator: {len(broken_mapping)} mappings")
        
        types = {}
        for m in broken_mapping:
            mtype = m['type']
            types[mtype] = types.get(mtype, 0) + 1
        print(f"   Mapping types: {types}")
        
        if 'emergency_black' in types:
            print(f"   🚨 Black screen reasons:")
            for reason in broken_gen.fallback_reasons:
                print(f"     • {reason}")
        
    except Exception as e:
        print(f"   ❌ Bulletproof generator failed: {e}")

if __name__ == "__main__":
    # Run the debugging
    debug_bulletproof_step_by_step()
    
    # Compare working vs broken
    compare_working_vs_broken()
    
    # Create a fixed version
    create_fixed_bulletproof()
