# Testing Guide for Music Video Project

This document provides comprehensive information about the testing infrastructure and procedures for the music video generation project.

## 🎯 Test Suite Overview

The project uses a comprehensive test suite with three levels of testing:

### Test Structure
```
tests/
├── unit/                 # Unit tests for individual functions
│   ├── test_audio_processing.py
│   └── test_scene_detection.py
├── integration/          # Integration tests for complete workflows
│   └── test_generators.py
├── performance/          # Performance benchmarks
│   └── test_benchmarks.py
├── fixtures/             # Test data and mocks
└── conftest.py          # Pytest configuration
```

## 🚀 Quick Start

### Install Development Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
# Run complete test suite
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/performance/   # Performance benchmarks only
```

### Set Up Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

## 📋 Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test individual functions and components in isolation.

**Audio Processing Tests** (`test_audio_processing.py`):
- Safe numpy type conversions (`safe_float`, `safe_int`)
- Audio loading with librosa
- Beat detection functionality
- Tempo analysis across BPM changes
- Memory-efficient audio handling

**Scene Detection Tests** (`test_scene_detection.py`):
- Scene manager initialization
- Content detector threshold settings
- Scene timing calculations
- Scene filtering and selection strategies
- Error handling for corrupted files

**Running Unit Tests**:
```bash
pytest tests/unit/ -v
```

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test complete workflows and generator integration.

**Generator Tests** (`test_generators.py`):
- UltraRobustArchivalTool integration
- Premiere-style engine workflow
- End-to-end pipeline simulation
- Configuration validation
- Output file verification

**Running Integration Tests**:
```bash
pytest tests/integration/ -v
```

### 3. Performance Benchmarks (`tests/performance/`)

**Purpose**: Monitor system performance and detect regressions.

**Benchmark Tests** (`test_benchmarks.py`):
- Audio analysis performance (< 10s for 3-minute audio)
- Scene detection performance (< 60s for 10-minute video)
- Memory usage monitoring (< 500MB increase)
- File I/O performance benchmarks
- Scalability testing with different input sizes

**Running Performance Tests**:
```bash
pytest tests/performance/ -v
```

## 🔧 Test Configuration

### Fixtures (conftest.py)

Available test fixtures:
- `test_video_path`: Path to 5-minute test video
- `test_audio_path`: Path to 3-minute test audio  
- `long_test_video_path`: Path to 10-minute video (300+ scenes)
- `temp_output_dir`: Temporary directory for test outputs
- `sample_generator_config`: Default generator configuration

### Test Assets

Required test assets in `test-assets/`:
- `test_video.mp4`: 5-minute video with color transitions
- `test_audio.wav`: 3-minute audio with varying BPM (120→60→90)
- `test_video_long.mp4`: 10-minute video with 300+ scenes

**Generate test assets**:
```bash
python create_test_video.py    # Creates test videos
python create_test_audio.py    # Creates test audio
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow (`.github/workflows/ci.yml`)

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Pipeline Steps**:
1. **Multi-Python Testing**: Tests on Python 3.9, 3.10, 3.11
2. **Dependency Installation**: Installs FFmpeg and all required packages
3. **Code Quality Checks**: Linting with flake8, formatting with black
4. **Test Execution**: Runs unit, integration, and performance tests
5. **Coverage Reporting**: Uploads coverage reports to Codecov
6. **Security Scanning**: Runs Bandit security analysis
7. **Quality Gate**: Enforces quality standards for PRs

### Pre-commit Hooks (`.pre-commit-config.yaml`)

**Automatic Checks Before Each Commit**:
- Code formatting (Black, isort)
- Linting (flake8)
- Security scanning (Bandit)
- **Custom Checks**:
  - Numpy safety patterns
  - Test asset availability
  - Unit test execution

**Setup Pre-commit**:
```bash
pip install pre-commit
pre-commit install
```

## 📊 Test Coverage

### Coverage Requirements
- Minimum 80% code coverage required
- Critical functions must have 95%+ coverage
- All generators must have integration tests

### Generating Coverage Reports
```bash
# HTML report (opens in browser)
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=. --cov-report=term-missing

# XML report (for CI)
pytest --cov=. --cov-report=xml
```

## 🎮 Running Specific Tests

### Test Selection Examples
```bash
# Run tests matching pattern
pytest -k "audio" -v

# Run tests for specific file
pytest tests/unit/test_audio_processing.py::TestAudioProcessing::test_beat_detection -v

# Run with specific markers
pytest -m "slow" -v        # Run slow tests only
pytest -m "not slow" -v    # Skip slow tests

# Run with output capture
pytest -s -v              # Show print statements

# Run with detailed failure info
pytest --tb=long -v       # Detailed tracebacks
```

### Test Markers
```python
@pytest.mark.slow          # Long-running tests
@pytest.mark.integration   # Integration tests
@pytest.mark.performance   # Performance benchmarks
@pytest.mark.skipif        # Conditional skipping
```

## 🛠️ Writing New Tests

### Test File Naming Convention
- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<workflow_name>.py` 
- Performance tests: `test_<benchmark_type>.py`

### Test Function Naming
- Descriptive names: `test_audio_loading_with_valid_file`
- Use underscores for readability
- Start with `test_` prefix

### Example Test Structure
```python
import pytest
from unittest.mock import patch, MagicMock

class TestNewFeature:
    """Test new feature functionality."""
    
    def test_basic_functionality(self, fixture_name):
        """Test basic feature operation."""
        # Arrange
        input_data = "test_input"
        
        # Act
        result = process_function(input_data)
        
        # Assert
        assert result is not None
        assert result.status == "success"
    
    @patch('external.library.function')
    def test_with_mocking(self, mock_function):
        """Test with external dependency mocked."""
        mock_function.return_value = "mocked_result"
        
        result = function_that_calls_external()
        
        assert result == "expected_result"
        mock_function.assert_called_once()
```

## 🚨 Test Failure Debugging

### Common Issues and Solutions

**ImportError: No module named 'X'**
```bash
pip install -r requirements.txt
```

**Test assets not found**
```bash
python create_test_video.py
python create_test_audio.py
```

**FFmpeg not available**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/
```

**Memory issues during tests**
```bash
# Run tests with memory monitoring
pytest --memprof tests/performance/
```

### Debugging Test Failures
```bash
# Run single failing test with maximum detail
pytest tests/unit/test_audio_processing.py::test_failing_function -vvv --tb=long --capture=no

# Run with pdb debugger
pytest --pdb tests/unit/test_audio_processing.py::test_failing_function
```

## 📈 Performance Monitoring

### Benchmark Expectations
- **Audio Analysis**: < 10 seconds for 3-minute audio
- **Scene Detection**: < 60 seconds for 10-minute video
- **Memory Usage**: < 500MB increase during processing
- **Scene Detection Rate**: > 5 scenes/second processing

### Performance Regression Detection
```bash
# Run performance tests and save results
pytest tests/performance/ --benchmark-save=baseline

# Compare against baseline
pytest tests/performance/ --benchmark-compare=baseline
```

## 🔍 Continuous Integration

### Pipeline Status
Check pipeline status at: `https://github.com/yourusername/music_video_project/actions`

### Pipeline Failure Investigation
1. Check the failing step in GitHub Actions
2. Look at detailed logs for error messages
3. Run the same test locally to reproduce
4. Fix the issue and push the correction

### Quality Gates
- All tests must pass
- Code coverage must be ≥ 80%
- No security vulnerabilities (Bandit scan)
- Code formatting must pass (Black, flake8)

## 📝 Test Maintenance

### Adding New Tests
1. Write test following naming conventions
2. Add appropriate fixtures if needed
3. Update this documentation if introducing new patterns
4. Ensure tests are fast (< 1s each for unit tests)

### Updating Test Assets
```bash
# Regenerate test assets when needed
python create_test_video.py     # Updates test videos
python create_test_audio.py     # Updates test audio

# Verify new assets work
python test_long_video.py       # Validate 300+ scenes
python acceptance_test.py       # Full acceptance test
```

### Regular Maintenance Tasks
- Review and update performance benchmarks monthly
- Update dependencies in requirements.txt quarterly
- Review test coverage reports to identify gaps
- Update CI/CD pipeline as needed

## 🎯 Best Practices

### Writing Effective Tests
1. **Test one thing at a time**: Each test should verify a single behavior
2. **Use descriptive names**: Test names should explain what they verify
3. **Mock external dependencies**: Use mocks for librosa, moviepy, etc.
4. **Clean up resources**: Use fixtures for temporary files/directories
5. **Assert meaningful conditions**: Don't just test that code runs

### Performance Testing Guidelines
1. **Set realistic benchmarks**: Based on typical hardware capabilities
2. **Test with different input sizes**: Verify scalability
3. **Monitor memory usage**: Prevent memory leaks
4. **Use consistent test environments**: Same hardware/OS when possible

### Integration Testing Tips
1. **Test complete workflows**: End-to-end functionality
2. **Use realistic test data**: Representative of actual usage
3. **Test error recovery**: How system handles failures
4. **Verify output quality**: Not just that files are created

## 🔧 Troubleshooting

### Common Test Environment Issues

**Permission Errors**:
```bash
chmod +x scripts/check_numpy_safety.py
```

**Module Import Errors**:
```python
# Add to test file if needed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

**Test Asset Generation Failures**:
```bash
# Check FFmpeg installation
ffmpeg -version

# Verify Python dependencies
python -c "import moviepy, librosa, scenedetect; print('All imports successful')"
```

For additional help, check the project issues or create a new issue with:
- Test failure output
- System information (OS, Python version)
- Steps to reproduce the problem
