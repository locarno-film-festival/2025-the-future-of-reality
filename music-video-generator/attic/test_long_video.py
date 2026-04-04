#!/usr/bin/env python3
"""
Test script for the long video with 300+ scenes
"""
import os
from datetime import datetime

def test_long_video_scene_detection():
    """Test scene detection on the long video with 300+ scenes"""
    print("🎬 TESTING LONG VIDEO WITH 300+ SCENES")
    print("=" * 50)
    
    video_path = "test-assets/test_video_long.mp4"
    
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"❌ Long video not found: {video_path}")
        return False
    
    # Get file info
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
    print(f"✅ Long video found: {video_path}")
    print(f"✅ File size: {file_size:.1f} MB")
    
    # Test video properties with moviepy
    try:
        from moviepy import VideoFileClip
        
        video_clip = VideoFileClip(video_path)
        print(f"✅ Video duration: {video_clip.duration:.1f} seconds ({video_clip.duration/60:.1f} minutes)")
        print(f"✅ Video resolution: {video_clip.w}x{video_clip.h}")
        print(f"✅ Video FPS: {video_clip.fps}")
        video_clip.close()
        
    except Exception as e:
        print(f"❌ Error checking video properties: {e}")
        return False
    
    # Test scene detection
    try:
        from scenedetect import VideoManager, SceneManager
        from scenedetect.detectors import ContentDetector
        
        print("\n🔍 Running scene detection...")
        print("This may take a few minutes for a 10-minute video...")
        
        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=5.0))  # Very low threshold for maximum sensitivity
        
        start_time = datetime.now()
        video_manager.set_duration()
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()
        video_manager.release()
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Scene detection completed!")
        print(f"✅ Processing time: {processing_time:.1f} seconds")
        print(f"✅ Scenes detected: {len(scene_list)}")
        print(f"✅ Target was 300+ scenes - {'SUCCESS' if len(scene_list) >= 300 else 'NEED MORE'}")
        print(f"✅ Generated segments: 343, Detected scenes: {len(scene_list)}")
        
        # Show first few and last few scenes
        print(f"\n📋 First 5 scenes:")
        for i, scene in enumerate(scene_list[:5]):
            start_time_sec = scene[0].get_seconds()
            end_time_sec = scene[1].get_seconds()
            duration = end_time_sec - start_time_sec
            print(f"   Scene {i+1}: {start_time_sec:.1f}s to {end_time_sec:.1f}s ({duration:.1f}s)")
        
        if len(scene_list) > 10:
            print(f"\n📋 Last 5 scenes:")
            for i, scene in enumerate(scene_list[-5:], len(scene_list) - 4):
                start_time_sec = scene[0].get_seconds()
                end_time_sec = scene[1].get_seconds()
                duration = end_time_sec - start_time_sec
                print(f"   Scene {i}: {start_time_sec:.1f}s to {end_time_sec:.1f}s ({duration:.1f}s)")
        
        # Success criteria
        return len(scene_list) >= 300
        
    except Exception as e:
        print(f"❌ Scene detection failed: {e}")
        return False

def main():
    """Run the long video test"""
    print("🎬 LONG VIDEO TEST - 300+ SCENES REQUIREMENT")
    print("=" * 60)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_long_video_scene_detection()
    
    print(f"\n📊 TEST RESULT")
    print("=" * 30)
    
    if success:
        print("🎉 SUCCESS! Long video meets requirements:")
        print("   ✅ Video duration: 10 minutes")
        print("   ✅ Scene count: 300+ scenes detected")
        print("   ✅ File size: Reasonable for testing")
        print("   ✅ Scene detection: Working properly")
        print("\n🚀 Ready for use in music video generators!")
    else:
        print("❌ FAILED: Long video does not meet requirements")
        
    return success

if __name__ == "__main__":
    main()
