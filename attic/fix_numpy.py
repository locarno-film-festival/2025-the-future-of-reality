#!/bin/bash
# Fix librosa numpy compatibility issue

echo "🔧 Fixing librosa/numpy compatibility..."

# The error is caused by numpy 1.26+ being incompatible with older librosa
# Let's fix this with compatible versions

echo "Method 1: Update librosa to latest version"
pip install --upgrade librosa

echo "Testing librosa after upgrade..."
python -c "
import librosa
import numpy as np
print('librosa version:', librosa.__version__)
print('numpy version:', np.__version__)

# Test the specific function that was failing
try:
    import librosa
    y, sr = librosa.load(librosa.ex('brahms'))  # Use example file
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    print('✅ librosa beat tracking works!')
except Exception as e:
    print('❌ librosa still failing:', e)
"

echo "If that failed, trying Method 2: Downgrade numpy"
echo "This is more aggressive but often works..."

# Only run if first method failed
if [ $? -ne 0 ]; then
    echo "Downgrading numpy to compatible version..."
    pip install "numpy<1.25"
    
    echo "Testing again..."
    python -c "
    import librosa
    import numpy as np
    print('librosa version:', librosa.__version__)
    print('numpy version:', np.__version__)
    
    try:
        import librosa
        y, sr = librosa.load(librosa.ex('brahms'))
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        print('✅ librosa working with downgraded numpy!')
    except Exception as e:
        print('❌ Still failing:', e)
    "
fi

echo "Method 3: Use conda instead (most reliable)"
echo "If pip versions keep conflicting, conda manages dependencies better:"
echo ""
echo "conda install -c conda-forge librosa"
echo ""
echo "This automatically installs compatible versions of all dependencies."
