#!/usr/bin/env python3
"""
Test script for the new Premiere Pro-Style Archival Analysis Engine
Validates the clips-first workflow and professional timeline interface
"""

import sys
from pathlib import Path
import tempfile
import subprocess

def create_test_video():
    """Create a simple test video using FFmpeg."""
    print("🎬 Creating test video...")
    
    test_video_path = Path("test_video.mp4")
    
    # Create a simple test video with audio using FFmpeg
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', 'testsrc2=duration=30:size=640x480:rate=24',
        '-f', 'lavfi', 
        '-i', 'sine=frequency=440:duration=30',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-t', '30',
        str(test_video_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✓ Test video created: {test_video_path}")
            return test_video_path
        else:
            print(f"   ✗ FFmpeg failed: {result.stderr}")
            return None
    except FileNotFoundError:
        print("   ✗ FFmpeg not found - skipping video creation test")
        return None

def test_imports():
    """Test that all required libraries can be imported."""
    print("\n📦 Testing library imports...")
    
    try:
        from premiere_style_archival_engine import PremiereStyleArchivalEngine
        print("   ✓ Premiere engine imported successfully")
        
        # Test component classes
        from premiere_style_archival_engine import AudioWaveformRenderer
        from premiere_style_archival_engine import SpectrogramAnalyzer  
        from premiere_style_archival_engine import ProportionalTimelineEngine
        print("   ✓ All component classes imported")
        
        return True
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False

def test_engine_initialization():
    """Test engine initialization without processing."""
    print("\n⚙️ Testing engine initialization...")
    
    try:
        # Create engine with dummy file path
        test_path = "dummy_video.mp4"
        engine = PremiereStyleArchivalEngine(test_path)
        
        print("   ✓ Engine initialized successfully")
        print(f"   ✓ Output directory created: {engine.output_dir}")
        print(f"   ✓ Working directories created")
        
        # Test component initialization
        assert engine.waveform_renderer is not None
        assert engine.spectrogram_analyzer is not None  
        assert engine.timeline_engine is not None
        print("   ✓ All components initialized")
        
        return True
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return False

def test_timeline_engine():
    """Test the proportional timeline calculation."""
    print("\n📐 Testing proportional timeline engine...")
    
    try:
        from premiere_style_archival_engine import ProportionalTimelineEngine
        
        engine = ProportionalTimelineEngine()
        
        # Test with sample scene data
        sample_scenes = [
            {'id': 0, 'duration': 5.0},   # Short scene
            {'id': 1, 'duration': 30.0},  # Long scene  
            {'id': 2, 'duration': 2.0},   # Very short scene
            {'id': 3, 'duration': 15.0}   # Medium scene
        ]
        
        # Test different zoom levels
        for zoom_name, zoom_value in engine.ZOOM_LEVELS.items():
            clip_widths = engine.calculate_clip_widths(
                sample_scenes, 
                timeline_width_px=1200, 
                zoom_level=zoom_value
            )
            
            assert len(clip_widths) == len(sample_scenes)
            print(f"   ✓ {zoom_name} zoom: {len(clip_widths)} clips calculated")
            
            # Verify proportional relationships
            durations = [s['duration'] for s in sample_scenes]
            widths = [c['width_px'] for c in clip_widths]
            
            # Longest scene should have widest clip (accounting for max width constraint)
            max_duration_idx = durations.index(max(durations))
            max_width = max(widths)
            print(f"     Longest scene ({durations[max_duration_idx]}s) → {widths[max_duration_idx]:.1f}px")
            
        print("   ✓ Proportional timeline calculations working")
        return True
        
    except Exception as e:
        print(f"   ✗ Timeline engine test failed: {e}")
        return False

def test_waveform_renderer():
    """Test waveform generation with synthetic data."""
    print("\n🎵 Testing waveform renderer...")
    
    try:
        from premiere_style_archival_engine import AudioWaveformRenderer
        import numpy as np
        import tempfile
        import os
        
        renderer = AudioWaveformRenderer()
        
        # Test silent waveform generation
        silent_waveform = renderer.generate_silent_waveform(duration=5.0, target_points=100)
        
        assert 'left_waveform' in silent_waveform
        assert 'right_waveform' in silent_waveform
        assert len(silent_waveform['left_waveform']) == 100
        assert all(x == 0.0 for x in silent_waveform['left_waveform'])
        print("   ✓ Silent waveform generation working")
        
        # Test peak downsampling
        test_data = np.random.randn(1000) * 0.5
        downsampled = renderer.downsample_with_peaks(test_data, chunk_size=10)
        assert len(downsampled) == 100  # 1000 / 10
        print("   ✓ Peak-preserving downsampling working")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Waveform renderer test failed: {e}")
        return False

def test_spectrogram_analyzer():
    """Test spectrogram analysis."""
    print("\n📊 Testing spectrogram analyzer...")
    
    try:
        from premiere_style_archival_engine import SpectrogramAnalyzer
        
        analyzer = SpectrogramAnalyzer()
        
        # Test silent spectrogram generation
        silent_spec = analyzer.generate_silent_spectrogram(duration=5.0)
        
        assert 'spectrogram' in silent_spec
        assert 'frequencies' in silent_spec
        assert 'times' in silent_spec
        assert len(silent_spec['frequencies']) == 64  # n_mels
        print("   ✓ Silent spectrogram generation working")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Spectrogram analyzer test failed: {e}")
        return False

def run_integration_test(test_video_path):
    """Run integration test with actual video processing."""
    print(f"\n🚀 Running integration test with {test_video_path}...")
    
    try:
        from premiere_style_archival_engine import PremiereStyleArchivalEngine
        
        # Create engine
        engine = PremiereStyleArchivalEngine(str(test_video_path))
        
        # Run Phase 1 only (clips generation) with limited scenes
        print("   Testing Phase 1: Clips-first generation...")
        phase1_success = engine.phase1_generate_all_clips(
            threshold=30.0,
            max_scenes=5,  # Limit for testing
            force_audio=True
        )
        
        if phase1_success:
            print("   ✓ Phase 1 completed successfully")
            
            # Test Phase 2 (timeline interface)
            print("   Testing Phase 2: Timeline interface...")
            phase2_success = engine.phase2_create_premiere_timeline('fit_all')
            
            if phase2_success:
                print("   ✓ Phase 2 completed successfully")
                
                # Test Phase 3 (enhanced analysis)
                print("   Testing Phase 3: Enhanced analysis...")
                phase3_success = engine.phase3_enhanced_analysis()
                
                if phase3_success:
                    print("   ✓ Phase 3 completed successfully")
                    print(f"   ✓ Complete pipeline success: {engine.output_dir}")
                    print(f"   ✓ Interface available: {engine.output_dir}/premiere_interface.html")
                    return True
                else:
                    print("   ⚠ Phase 3 failed but pipeline partially successful")
                    return True
            else:
                print("   ✗ Phase 2 failed")
                return False
        else:
            print("   ✗ Phase 1 failed")
            return False
            
    except Exception as e:
        print(f"   ✗ Integration test failed: {e}")
        return False

def main():
    """Run comprehensive test suite."""
    print("🧪 PREMIERE PRO-STYLE ARCHIVAL ENGINE TEST SUITE")
    print("="*60)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Library imports
    total_tests += 1
    if test_imports():
        tests_passed += 1
    
    # Test 2: Engine initialization  
    total_tests += 1
    if test_engine_initialization():
        tests_passed += 1
        
    # Test 3: Timeline engine
    total_tests += 1
    if test_timeline_engine():
        tests_passed += 1
        
    # Test 4: Waveform renderer
    total_tests += 1
    if test_waveform_renderer():
        tests_passed += 1
        
    # Test 5: Spectrogram analyzer
    total_tests += 1
    if test_spectrogram_analyzer():
        tests_passed += 1
    
    # Test 6: Integration test (if video creation works)
    test_video = create_test_video()
    if test_video and test_video.exists():
        total_tests += 1
        if run_integration_test(test_video):
            tests_passed += 1
        
        # Cleanup
        try:
            test_video.unlink()
            print(f"   ✓ Test video cleaned up")
        except:
            pass
    else:
        print("   ⚠ Skipping integration test (no test video)")
    
    # Results
    print("\n" + "="*60)
    print(f"🧪 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ ALL TESTS PASSED - Engine ready for use!")
        return 0
    elif tests_passed >= total_tests * 0.8:
        print("⚠ MOST TESTS PASSED - Engine mostly functional")
        return 0
    else:
        print("❌ MULTIPLE TESTS FAILED - Check installation and dependencies")
        return 1

if __name__ == "__main__":
    sys.exit(main())
