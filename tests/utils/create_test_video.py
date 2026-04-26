#!/usr/bin/env python3
"""
Create a test video with color screens that switch at random intervals.
"""
import random
import os
import subprocess
import numpy as np
import cv2


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
        (255, 255, 255),# White
        (0, 0, 0),      # Black
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
        (255, 192, 203),# Pink
        (0, 128, 0),    # Dark Green
        (128, 0, 0),    # Dark Red
        (0, 0, 128),    # Navy
        (128, 128, 0),  # Olive
        (255, 165, 0),  # Bright Orange
    ]

    fps = 24
    width, height = 320, 240
    temp_path = output_path + ".tmp.avi"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    print(f"Generating {duration} seconds of video...")

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

    current_time = 0
    scene_count = 0
    last_color = None

    while current_time < duration:
        # Random duration between 0.5 and 3 seconds for each color (to get 300+ scenes)
        clip_duration = random.uniform(0.5, 3.0)

        # Ensure we don't exceed total duration
        if current_time + clip_duration > duration:
            clip_duration = duration - current_time

        num_frames = int(clip_duration * fps)

        # Pick a different color than the last one
        color = random.choice(colors)
        while color == last_color and len(colors) > 1:
            color = random.choice(colors)
        last_color = color

        # Write frames (OpenCV uses BGR)
        frame = np.full((height, width, 3), color[::-1], dtype=np.uint8)
        for _ in range(num_frames):
            writer.write(frame)

        current_time += clip_duration
        scene_count += 1
        print(f"Added {color} clip, duration: {clip_duration:.1f}s, total: {current_time:.1f}s")

    writer.release()

    # Convert to mp4 with ffmpeg
    subprocess.run(
        ["ffmpeg", "-y", "-i", temp_path, "-c:v", "libx264", "-preset", "ultrafast", output_path],
        capture_output=True,
    )
    os.remove(temp_path)

    print(f"Test video created successfully: {output_path}")
    print(f"Duration: {duration} seconds ({duration/60:.1f} minutes)")
    print(f"Number of color segments: {scene_count}")


if __name__ == "__main__":
    create_test_video()
