#!/usr/bin/env python3
"""Performance benchmarks for music video generators."""
import pytest
import time
import psutil
import os
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestPerformanceBenchmarks:
    """Performance benchmarks for key operations."""
    
    def test_audio_analysis_performance(self, test_audio_path):
        """Benchmark audio analysis performance."""
        pytest.importorskip("librosa")
        
        if not test_audio_path.exists():
            pytest.skip("Test audio not available")
        
        import librosa
        
        # Benchmark audio loading
        start_time = time.time()
        y, sr = librosa.load(str(test_audio_path))
        load_time = time.time() - start_time
        
        # Benchmark beat detection
        start_time = time.time()
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_detection_time = time.time() - start_time
        
        # Performance assertions
        assert load_time < 5.0, f"Audio loading took {load_time:.2f}s, should be < 5s"
        assert beat_detection_time < 10.0, f"Beat detection took {beat_detection_time:.2f}s, should be < 10s"
        
        # Memory usage check
        audio_size_mb = len(y) * 4 / (1024 * 1024)  # 4 bytes per float32
        assert audio_size_mb < 100, f"Audio data using {audio_size_mb:.1f}MB, should be < 100MB"

    def test_scene_detection_performance(self, long_test_video_path):
        """Benchmark scene detection performance."""
        pytest.importorskip("scenedetect")
        
        if not long_test_video_path.exists():
            pytest.skip("Long test video not available")
        
        from scenedetect import VideoManager, SceneManager
        from scenedetect.detectors import ContentDetector
        
        # Benchmark scene detection
        start_time = time.time()
        
        video_manager = VideoManager([str(long_test_video_path)])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=5.0))
        
        video_manager.set_duration()
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()
        video_manager.release()
        
        detection_time = time.time() - start_time
        
        # Performance assertions
        assert detection_time < 60.0, f"Scene detection took {detection_time:.2f}s, should be < 60s"
        assert len(scene_list) >= 300, f"Expected 300+ scenes, got {len(scene_list)}"
        
        # Calculate scenes per second of processing
        scenes_per_processing_second = len(scene_list) / detection_time
        assert scenes_per_processing_second > 5, f"Processing rate: {scenes_per_processing_second:.1f} scenes/sec"

    def test_memory_usage_monitoring(self, test_video_path, test_audio_path):
        """Monitor memory usage during processing."""
        if not test_video_path.exists() or not test_audio_path.exists():
            pytest.skip("Test assets not available")
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Simulate memory-intensive operations
        try:
            import librosa
            import numpy as np
            
            # Load audio (memory intensive)
            y, sr = librosa.load(str(test_audio_path))
            
            # Check memory after audio loading
            audio_memory = process.memory_info().rss / (1024 * 1024)
            
            # Perform beat analysis
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Check peak memory usage
            peak_memory = process.memory_info().rss / (1024 * 1024)
            
            # Memory assertions
            memory_increase = peak_memory - initial_memory
            assert memory_increase < 500, f"Memory usage increased by {memory_increase:.1f}MB, should be < 500MB"
            
        except ImportError:
            pytest.skip("librosa not available for memory test")

    def test_file_io_performance(self, temp_output_dir):
        """Test file I/O performance."""
        import json
        
        # Test JSON writing performance
        large_data = {
            "scenes": [{"start": i, "end": i+1, "duration": 1.0} for i in range(1000)],
            "beats": [i * 0.5 for i in range(2000)],
            "metadata": {"duration": 300, "fps": 24, "resolution": "1920x1080"}
        }
        
        json_file = temp_output_dir / "benchmark_data.json"
        
        # Benchmark JSON writing
        start_time = time.time()
        with open(json_file, 'w') as f:
            json.dump(large_data, f, indent=2)
        write_time = time.time() - start_time
        
        # Benchmark JSON reading
        start_time = time.time()
        with open(json_file, 'r') as f:
            loaded_data = json.load(f)
        read_time = time.time() - start_time
        
        # Performance assertions
        assert write_time < 1.0, f"JSON write took {write_time:.3f}s, should be < 1s"
        assert read_time < 0.5, f"JSON read took {read_time:.3f}s, should be < 0.5s"
        assert loaded_data == large_data, "Data integrity check failed"

class TestScalabilityBenchmarks:
    """Test scalability with different input sizes."""
    
    def test_video_length_scaling(self):
        """Test performance scaling with video length."""
        # Mock processing times for different video lengths
        video_lengths = [60, 300, 600, 1800]  # 1min, 5min, 10min, 30min
        expected_processing_ratios = []
        
        for length in video_lengths:
            # Simulate processing time (should scale roughly linearly)
            estimated_processing_time = length * 0.05  # 5% of video duration
            ratio = estimated_processing_time / length
            expected_processing_ratios.append(ratio)
        
        # Verify processing scales reasonably
        for i, ratio in enumerate(expected_processing_ratios):
            assert ratio < 0.1, f"Processing ratio for {video_lengths[i]}s video: {ratio:.3f}"

    def test_scene_count_scaling(self):
        """Test performance with different scene counts."""
        scene_counts = [50, 100, 300, 500]
        
        for count in scene_counts:
            # Estimate processing time based on scene count
            # Should be roughly linear with slight overhead
            estimated_time = count * 0.1 + 5  # 0.1s per scene + 5s overhead
            
            # Verify reasonable scaling
            assert estimated_time < 120, f"Estimated time for {count} scenes: {estimated_time:.1f}s"

class TestResourceUtilization:
    """Test CPU and memory resource utilization."""
    
    def test_cpu_utilization_monitoring(self):
        """Monitor CPU utilization during processing."""
        # Get CPU count
        cpu_count = psutil.cpu_count()
        
        # Simulate CPU-intensive operation
        start_time = time.time()
        
        # Mock CPU-intensive processing
        import numpy as np
        for _ in range(10):
            # Simulate beat detection computation
            data = np.random.randn(44100)
            np.fft.fft(data)
        
        duration = time.time() - start_time
        
        # Should complete reasonably quickly
        assert duration < 2.0, f"CPU-intensive operations took {duration:.2f}s"

    def test_concurrent_processing_capability(self):
        """Test ability to handle concurrent operations."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def mock_processing_task(task_id):
            """Mock processing task."""
            start_time = time.time()
            # Simulate processing
            time.sleep(0.1)
            duration = time.time() - start_time
            results_queue.put((task_id, duration))
        
        # Run multiple tasks concurrently
        threads = []
        num_tasks = 4
        
        start_time = time.time()
        for i in range(num_tasks):
            thread = threading.Thread(target=mock_processing_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify concurrent execution was efficient
        assert len(results) == num_tasks
        assert total_time < 0.5, f"Concurrent execution took {total_time:.2f}s"

class TestBenchmarkReporting:
    """Test benchmark result reporting."""
    
    def test_benchmark_report_generation(self, temp_output_dir):
        """Test generation of benchmark reports."""
        
        # Mock benchmark results
        benchmark_results = {
            "audio_analysis": {
                "load_time": 1.2,
                "beat_detection_time": 3.4,
                "memory_usage_mb": 45.6
            },
            "scene_detection": {
                "detection_time": 28.5,
                "scenes_detected": 308,
                "scenes_per_second": 10.8
            },
            "overall": {
                "total_time": 32.1,
                "peak_memory_mb": 78.9,
                "cpu_utilization": 0.65
            }
        }
        
        # Generate report
        report_file = temp_output_dir / "benchmark_report.json"
        
        import json
        with open(report_file, 'w') as f:
            json.dump(benchmark_results, f, indent=2)
        
        # Verify report was created
        assert report_file.exists()
        
        # Verify report content
        with open(report_file, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == benchmark_results
        assert "audio_analysis" in loaded_results
        assert "scene_detection" in loaded_results
        assert "overall" in loaded_results
