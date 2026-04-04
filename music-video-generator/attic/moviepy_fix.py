#!/bin/bash
# MoviePy 2.x Fix Script

echo "🔧 Fixing MoviePy 2.x installation..."

# Method 1: Complete clean install with correct version
echo "Step 1: Complete cleanup and reinstall"
pip uninstall moviepy -y
pip cache purge
pip install --no-cache-dir "moviepy>=2.0.0"

echo "Step 2: Test MoviePy 2.x imports"
python -c "
import moviepy
print('MoviePy version:', moviepy.__version__)

# Test new MoviePy 2.x import structure
try:
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
    print('✅ New import structure works!')
except ImportError as e:
    print('❌ New imports failed:', e)

# Test if old editor module exists
try:
    import moviepy.editor
    print('✅ Legacy editor module available')
except ImportError:
    print('⚠️ Legacy editor module not available (expected in 2.x)')
"

echo "Step 3: Install alternative stable version if needed"
echo "If the above failed, trying stable 1.x version..."
pip uninstall moviepy -y
pip install "moviepy==1.0.3"

echo "Step 4: Final test"
python -c "
try:
    import moviepy.editor as mp
    print('✅ MoviePy working with version:', mp.__version__)
    print('VideoFileClip available:', hasattr(mp, 'VideoFileClip'))
except Exception as e:
    print('❌ Still failing:', e)
"
