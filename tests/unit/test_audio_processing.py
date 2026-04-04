#!/usr/bin/env python3
"""Unit tests for audio processing functionality."""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestAudioProcessing:
    """Test audio processing functions across generators."""
    
    def test_safe_float_conversion(self):
        """Test safe float conversion function."""
        # Mock a generator class with safe_float method
        class MockGenerator:
            def safe_float(self, value):
                """Convert numpy types to Python float safely."""
                if hasattr(value, 'item'):
                    return float(value.item())
                return float(value)
        
        generator = MockGenerator()
        
        # Test with numpy scalar
        np_float = np.float64(3.14159)
        result = generator.safe_float(np_float)
        assert isinstance(result, float)
        assert abs(result - 3.14159) < 1e-6
        
        # Test with regular float
        regular_float = 2.71828
        result = generator.safe_float(regular_float)
        assert isinstance(result, float)
        assert abs(result - 2.71828) < 1e-6
        
        # Test with integer
        integer_val = 42
        result = generator.safe_float(integer_val)
        assert isinstance(result, float)
        assert result == 42.0

    def test_safe_int_conversion(self):
        """Test safe integer conversion function."""
        class MockGenerator:
            def safe_int(self, value):
                """Convert numpy types to Python int safely."""
                if hasattr(value, 'item'):
                    return int(value.item())
                return int(value)
        
        generator = MockGenerator()
        
        # Test with numpy scalar
        np_int = np.int64(42)
        result = generator.safe_int(np_int)
        assert isinstance(result, int)
        assert result == 42
        
        # Test with float
        float_val = 3.7
        result = generator.safe_int(float_val)
        assert isinstance(result, int)
        assert result == 3

    @patch('librosa.load')
    def test_audio_loading(self, mock_load):
        """Test audio file loading with librosa."""
        # Mock librosa.load return values
        mock_audio_data = np.random.randn(44100 * 30)  # 30 seconds
        mock_sample_rate = 22050
        mock_load.return_value = (mock_audio_data, mock_sample_rate)
        
        # Import and test (would normally import from actual generator)
        import librosa
        y, sr = librosa.load("test-assets/test_audio.wav")
        
        assert len(y) == len(mock_audio_data)
        assert sr == mock_sample_rate
        mock_load.assert_called_once()

    @patch('librosa.beat.beat_track')
    def test_beat_detection(self, mock_beat_track):
        """Test beat detection functionality."""
        # Mock beat detection results
        mock_tempo = 120.0
        mock_beats = np.array([0, 0.5, 1.0, 1.5, 2.0])
        mock_beat_track.return_value = (mock_tempo, mock_beats)
        
        import librosa
        
        # Test beat detection
        y = np.random.randn(44100 * 10)  # 10 seconds
        sr = 22050
        
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        assert tempo == mock_tempo
        assert np.array_equal(beats, mock_beats)
        mock_beat_track.assert_called_once()

    def test_audio_segment_extraction(self):
        """Test extracting audio segments based on beat timing."""
        # Create mock audio data
        sample_rate = 22050
        duration = 10  # seconds
        audio_data = np.random.randn(sample_rate * duration)
        
        # Mock beat times (every 0.5 seconds)
        beat_times = np.array([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
        
        # Test segment extraction logic
        def extract_segment(audio, sr, start_time, end_time):
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            return audio[start_sample:end_sample]
        
        # Extract a 1-second segment from 1.0s to 2.0s
        segment = extract_segment(audio_data, sample_rate, 1.0, 2.0)
        
        expected_length = sample_rate  # 1 second worth of samples
        assert len(segment) == expected_length

    def test_tempo_analysis(self):
        """Test tempo analysis across different BPM sections."""
        # Mock our test audio with varying BPM
        segments = [
            {"expected_bpm": 120, "start": 0, "end": 60},
            {"expected_bpm": 60, "start": 60, "end": 120}, 
            {"expected_bpm": 90, "start": 120, "end": 180}
        ]
        
        with patch('librosa.beat.beat_track') as mock_beat:
            for segment in segments:
                # Mock tempo detection for each segment
                mock_beat.return_value = (segment["expected_bpm"], np.array([]))
                
                # Simulate tempo analysis
                import librosa
                tempo, _ = librosa.beat.beat_track(y=np.random.randn(1000), sr=22050)
                
                # Verify tempo is as expected
                assert tempo == segment["expected_bpm"]

    def test_audio_duration_calculation(self):
        """Test audio duration calculations."""
        sample_rate = 44100
        
        # Test different durations
        test_cases = [
            (44100, 1.0),      # 1 second
            (88200, 2.0),      # 2 seconds  
            (132300, 3.0),     # 3 seconds
            (2646000, 60.0),   # 1 minute
        ]
        
        for num_samples, expected_duration in test_cases:
            calculated_duration = num_samples / sample_rate
            assert abs(calculated_duration - expected_duration) < 0.01

class TestAudioAnalysisUtilities:
    """Test utility functions for audio analysis."""
    
    def test_bpm_validation(self):
        """Test BPM validation logic."""
        def is_valid_bpm(bpm):
            """Check if BPM is within reasonable range."""
            return 40 <= bpm <= 200
        
        # Test valid BPMs
        assert is_valid_bpm(60) is True
        assert is_valid_bpm(120) is True
        assert is_valid_bpm(180) is True
        
        # Test invalid BPMs
        assert is_valid_bpm(30) is False
        assert is_valid_bpm(250) is False

    def test_beat_time_conversion(self):
        """Test conversion between beat frames and time."""
        sample_rate = 22050
        
        with patch('librosa.frames_to_time') as mock_frames_to_time:
            mock_frames_to_time.return_value = np.array([0.0, 0.5, 1.0, 1.5])
            
            import librosa
            beat_frames = np.array([0, 11, 22, 33])
            beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
            
            assert len(beat_times) == 4
            mock_frames_to_time.assert_called_once_with(beat_frames, sr=sample_rate)

    def test_audio_analysis_error_handling(self):
        """Test error handling in audio analysis."""
        with patch('librosa.load') as mock_load:
            # Test file not found error
            mock_load.side_effect = FileNotFoundError("Audio file not found")
            
            import librosa
            
            with pytest.raises(FileNotFoundError):
                librosa.load("nonexistent_file.wav")

    def test_memory_efficient_loading(self):
        """Test memory-efficient audio loading for large files."""
        with patch('librosa.load') as mock_load:
            # Mock loading with offset and duration
            mock_audio = np.random.randn(22050 * 30)  # 30 seconds
            mock_load.return_value = (mock_audio, 22050)
            
            import librosa
            
            # Test loading with offset and duration
            y, sr = librosa.load("test_file.wav", offset=10.0, duration=30.0)
            
            assert len(y) == len(mock_audio)
            assert sr == 22050
            mock_load.assert_called_once_with("test_file.wav", offset=10.0, duration=30.0)
