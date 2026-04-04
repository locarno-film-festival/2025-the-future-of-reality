#!/usr/bin/env python3
"""
Create a 3-minute test audio file with varying rhythms and beats.
Changes every minute: 120 BPM -> 60 BPM -> 90 BPM
"""
import numpy as np
import scipy.io.wavfile as wav
from scipy import signal
import os


def generate_beat_pattern(bpm, duration, sample_rate=44100):
    """
    Generate a beat pattern at specified BPM for given duration.

    Args:
        bpm: Beats per minute
        duration: Duration in seconds
        sample_rate: Audio sample rate

    Returns:
        numpy array of audio samples
    """
    # Calculate beat interval
    beat_interval = 60.0 / bpm  # seconds per beat

    # Total samples
    total_samples = int(duration * sample_rate)
    audio = np.zeros(total_samples)

    # Generate beat positions
    beat_times = np.arange(0, duration, beat_interval)

    # Create different tones for variety
    frequencies = [220, 330, 440, 550]  # Different bass/mid frequencies

    for i, beat_time in enumerate(beat_times):
        if beat_time >= duration:
            break

        # Calculate sample position
        sample_pos = int(beat_time * sample_rate)

        # Choose frequency based on beat position for variety
        freq = frequencies[i % len(frequencies)]

        # Generate a short beat sound (kick drum-like)
        beat_duration = 0.1  # 100ms beat
        beat_samples = int(beat_duration * sample_rate)

        if sample_pos + beat_samples < total_samples:
            # Create beat sound - combination of low frequency and click
            t = np.linspace(0, beat_duration, beat_samples)

            # Low frequency component (kick drum)
            kick = 0.7 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 20)

            # High frequency click component
            click = 0.3 * np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 50)

            # Combine
            beat_sound = kick + click

            # Apply envelope
            envelope = np.exp(-t * 10)
            beat_sound *= envelope

            # Add to main audio
            end_pos = min(sample_pos + beat_samples, total_samples)
            audio_slice_len = end_pos - sample_pos
            audio[sample_pos:end_pos] += beat_sound[:audio_slice_len]

    return audio


def generate_background_tone(frequency, duration, sample_rate=44100):
    """Generate a background tone/melody."""
    t = np.linspace(0, duration, int(duration * sample_rate))

    # Create a varying tone
    base_freq = frequency
    modulation = 0.1 * np.sin(2 * np.pi * 0.5 * t)  # Slow modulation

    tone = 0.2 * np.sin(2 * np.pi * base_freq * (1 + modulation) * t)

    # Add some harmonics for richness
    tone += 0.1 * np.sin(2 * np.pi * base_freq * 2 * (1 + modulation) * t)
    tone += 0.05 * np.sin(2 * np.pi * base_freq * 3 * (1 + modulation) * t)

    return tone


def create_test_audio(output_path="test-assets/test_audio.wav", total_duration=180):
    """
    Create a 3-minute test audio with varying BPM.

    Args:
        output_path: Path to save the audio file
        total_duration: Total duration in seconds (180 = 3 minutes)
    """
    print("Creating test audio with varying BPM patterns...")

    # Parameters
    sample_rate = 44100
    segment_duration = total_duration / 3  # 60 seconds each
    bpm_sequence = [120, 60, 90]  # BPM for each minute

    # Background tone frequencies for each segment
    bg_frequencies = [110, 130, 150]  # Different background tones

    audio_segments = []

    for i, bpm in enumerate(bpm_sequence):
        print(f"Generating segment {i+1}: {bpm} BPM, {bg_frequencies[i]} Hz background")

        # Generate beat pattern
        beats = generate_beat_pattern(bpm, segment_duration, sample_rate)

        # Generate background tone
        background = generate_background_tone(
            bg_frequencies[i], segment_duration, sample_rate
        )

        # Combine beats and background
        segment = beats + background

        # Normalize to prevent clipping
        segment = segment / np.max(np.abs(segment)) * 0.8

        audio_segments.append(segment)

        print(
            f"Segment {i+1} complete: {len(segment)} samples, duration: {len(segment)/sample_rate:.1f}s"
        )

    # Concatenate all segments
    print("Concatenating audio segments...")
    final_audio = np.concatenate(audio_segments)

    # Final normalization
    final_audio = final_audio / np.max(np.abs(final_audio)) * 0.9

    # Convert to 16-bit integer
    final_audio_int = (final_audio * 32767).astype(np.int16)

    # Save as WAV file
    print(f"Saving audio to {output_path}...")
    wav.write(output_path, sample_rate, final_audio_int)

    print(f"Test audio created successfully: {output_path}")
    print(
        f"Duration: {len(final_audio_int)/sample_rate:.1f} seconds ({len(final_audio_int)/sample_rate/60:.1f} minutes)"
    )
    print(f"BPM sequence: {' -> '.join(map(str, bpm_sequence))}")
    print(f"Sample rate: {sample_rate} Hz")


if __name__ == "__main__":
    create_test_audio()
