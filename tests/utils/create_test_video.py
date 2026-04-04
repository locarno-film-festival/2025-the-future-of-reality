#!/usr/bin/env python3
"""
Create a 5-minute test video with color screens that switch at random intervals.
"""
import random
import numpy as np
from moviepy import ColorClip, concatenate_videoclips

def create_test_video(output_path="test-assets/test_video_long.mp4", duration=600):
    """
    Create a 10-minute video with random color screens and frequent scene changes.
    
    Args:
        output_path: Path to save the video
        duration: Total duration in seconds (600 = 10 minutes)
    """
    print("Creating test video with random color transitions...")
    
    # Define a palette of very distinct colors (RGB values) to ensure scene detection
    colors = [
        (255, 0, 0),    # Bright Red
        (0, 255, 0),    # Bright Green  
        (0, 0, 255),    # Bright Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 255, 255), # White
        (0, 0, 0),      # Black
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
        (255, 192, 203), # Pink
        (0, 128, 0),    # Dark Green
        (128, 0, 0),    # Dark Red
        (0, 0, 128),    # Navy
        (128, 128, 0),  # Olive
        (255, 165, 0),  # Bright Orange
    ]
    
    clips = []
    total_time = 0
    
    print(f"Generating {duration} seconds of video...")
    
    while total_time < duration:
        # Random duration between 0.5 and 3 seconds for each color (to get 300+ scenes)
        clip_duration = random.uniform(0.5, 3.0)
        
        # Ensure we don't exceed total duration
        if total_time + clip_duration > duration:
            clip_duration = duration - total_time
        
        # Random color
        color = random.choice(colors)
        
        # Create color clip
        clip = ColorClip(size=(1920, 1080), color=color, duration=clip_duration)
        clips.append(clip)
        
        total_time += clip_duration
        print(f"Added {color} clip, duration: {clip_duration:.1f}s, total: {total_time:.1f}s")
    
    # Concatenate all clips
    print("Concatenating clips...")
    final_video = concatenate_videoclips(clips)
    
    # Write video file
    print(f"Writing video to {output_path}...")
    final_video.write_videofile(output_path, fps=24, codec='libx264')
    
    print(f"Test video created successfully: {output_path}")
    print(f"Duration: {duration} seconds ({duration/60:.1f} minutes)")
    print(f"Number of color segments: {len(clips)}")

if __name__ == "__main__":
    create_test_video()
