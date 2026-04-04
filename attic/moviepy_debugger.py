#!/usr/bin/env python3
"""
MoviePy Debug Script
Comprehensive debugging to figure out what's wrong with MoviePy
"""

import sys
import os
import subprocess
import importlib.util

def check_python_environment():
    """Check which Python environment we're using"""
    print("🐍 PYTHON ENVIRONMENT ANALYSIS")
    print("=" * 50)
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path[:3]}...")  # First 3 paths
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        print(f"   Virtual env: {sys.prefix}")
    else:
        print("⚠️  Using system Python (not in virtual environment)")
    
    print()

def check_pip_packages():
    """Check what pip thinks is installed"""
    print("📦 PIP PACKAGE ANALYSIS")
    print("=" * 50)
    
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, timeout=30)
        
        lines = result.stdout.split('\n')
        moviepy_found = False
        related_packages = []
        
        for line in lines:
            if 'moviepy' in line.lower():
                moviepy_found = True
                print(f"✅ Found: {line.strip()}")
            elif any(pkg in line.lower() for pkg in ['imageio', 'opencv', 'numpy', 'ffmpeg']):
                related_packages.append(line.strip())
        
        if not moviepy_found:
            print("❌ MoviePy not found in pip list")
        
        print("\n📋 Related packages:")
        for pkg in related_packages[:5]:  # Show first 5
            print(f"   {pkg}")
            
    except Exception as e:
        print(f"❌ Error checking pip: {e}")
    
    print()

def check_moviepy_installation():
    """Check if moviepy files actually exist"""
    print("🔍 MOVIEPY INSTALLATION ANALYSIS")
    print("=" * 50)
    
    # Check if moviepy package exists
    spec = importlib.util.find_spec("moviepy")
    if spec is None:
        print("❌ MoviePy package not found by Python")
        return False
    
    print(f"✅ MoviePy package found at: {spec.origin}")
    
    # Check if the package directory exists
    if spec.submodule_search_locations:
        package_dir = spec.submodule_search_locations[0]
        print(f"📁 Package directory: {package_dir}")
        
        # Check what's inside the moviepy directory
        if os.path.exists(package_dir):
            contents = os.listdir(package_dir)
            print(f"📂 Directory contents: {contents[:5]}...")  # First 5 items
            
            # Check for editor.py specifically
            editor_path = os.path.join(package_dir, 'editor.py')
            if os.path.exists(editor_path):
                print("✅ editor.py found")
            else:
                print("❌ editor.py missing!")
                
            # Check for __init__.py
            init_path = os.path.join(package_dir, '__init__.py')
            if os.path.exists(init_path):
                print("✅ __init__.py found")
                with open(init_path, 'r') as f:
                    init_content = f.read()[:200]  # First 200 chars
                    print(f"📄 __init__.py preview: {init_content}...")
            else:
                print("❌ __init__.py missing!")
        else:
            print("❌ Package directory doesn't exist!")
    
    print()
    return True

def test_moviepy_imports():
    """Test different ways of importing moviepy"""
    print("🧪 MOVIEPY IMPORT TESTING")
    print("=" * 50)
    
    # Test 1: Basic moviepy import
    try:
        import moviepy
        print(f"✅ import moviepy - SUCCESS")
        print(f"   Version: {getattr(moviepy, '__version__', 'unknown')}")
        print(f"   Location: {moviepy.__file__}")
    except ImportError as e:
        print(f"❌ import moviepy - FAILED: {e}")
        return False
    except Exception as e:
        print(f"⚠️  import moviepy - ERROR: {e}")
    
    # Test 2: Editor import
    try:
        import moviepy.editor
        print(f"✅ import moviepy.editor - SUCCESS")
        print(f"   Location: {moviepy.editor.__file__}")
    except ImportError as e:
        print(f"❌ import moviepy.editor - FAILED: {e}")
        return False
    except Exception as e:
        print(f"⚠️  import moviepy.editor - ERROR: {e}")
        return False
    
    # Test 3: Specific classes
    try:
        from moviepy.editor import VideoFileClip
        print("✅ VideoFileClip import - SUCCESS")
    except ImportError as e:
        print(f"❌ VideoFileClip import - FAILED: {e}")
    except Exception as e:
        print(f"⚠️  VideoFileClip import - ERROR: {e}")
    
    # Test 4: Effects imports (version-dependent)
    try:
        from moviepy.video.fx.fadein import FadeIn
        print("✅ FadeIn import (v2.0+) - SUCCESS")
    except ImportError:
        print("⚠️  FadeIn import (v2.0+) - Not available (probably v1.x)")
    except Exception as e:
        print(f"⚠️  FadeIn import - ERROR: {e}")
    
    print()
    return True

def suggest_fixes():
    """Suggest potential fixes based on what we found"""
    print("🔧 SUGGESTED FIXES")
    print("=" * 50)
    
    print("Try these fixes in order:")
    print()
    
    print("1. Complete reinstall:")
    print("   pip uninstall moviepy -y")
    print("   pip install moviepy")
    print()
    
    print("2. Install with dependencies:")
    print("   pip install moviepy[optional]")
    print()
    
    print("3. Install dependencies separately:")
    print("   pip install imageio imageio-ffmpeg")
    print("   pip install moviepy")
    print()
    
    print("4. Use conda (often more reliable):")
    print("   conda install -c conda-forge moviepy")
    print()
    
    print("5. Install specific version:")
    print("   pip install 'moviepy==1.0.3'  # Stable older version")
    print("   # OR")
    print("   pip install 'moviepy>=2.0.0'  # Latest version")
    print()
    
    print("6. Check for conflicts:")
    print("   pip check")
    print("   pip list | grep -i movie")
    print()
    
    print("7. Fresh virtual environment:")
    print("   python -m venv fresh_env")
    print("   source fresh_env/bin/activate  # Linux/Mac")
    print("   # OR")
    print("   fresh_env\\Scripts\\activate  # Windows")
    print("   pip install moviepy")

def run_comprehensive_debug():
    """Run all debug tests"""
    print("🚨 MOVIEPY COMPREHENSIVE DEBUGGER")
    print("=" * 60)
    print()
    
    check_python_environment()
    check_pip_packages()
    
    # If basic package check fails, don't bother with imports
    if not check_moviepy_installation():
        print("🛑 MoviePy not properly installed - skipping import tests")
        suggest_fixes()
        return False
    
    success = test_moviepy_imports()
    
    if not success:
        suggest_fixes()
    else:
        print("🎉 MoviePy appears to be working!")
        print("If you're still getting errors, the issue might be in your specific script.")
    
    return success

def quick_fix_attempt():
    """Try to automatically fix common issues"""
    print("🔄 ATTEMPTING AUTOMATIC FIX")
    print("=" * 50)
    
    try:
        # Try complete reinstall
        print("Uninstalling moviepy...")
        subprocess.run([sys.executable, '-m', 'pip', 'uninstall', 'moviepy', '-y'], 
                      capture_output=True, timeout=60)
        
        print("Installing moviepy with dependencies...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'moviepy', 'imageio-ffmpeg'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Reinstallation completed")
            
            # Test the install
            try:
                import moviepy.editor
                print("✅ MoviePy now working!")
                return True
            except ImportError:
                print("❌ Still not working after reinstall")
                return False
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Auto-fix failed: {e}")
        return False

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Run comprehensive debug (recommended)")
    print("2. Try automatic fix")
    print("3. Both")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        run_comprehensive_debug()
    elif choice == "2":
        if quick_fix_attempt():
            print("\n🎉 Fix successful! Try running your original script now.")
        else:
            print("\n🔧 Auto-fix failed. Running debug to help manual fix...")
            run_comprehensive_debug()
    elif choice == "3":
        run_comprehensive_debug()
        print("\n" + "="*60)
        if quick_fix_attempt():
            print("\n🎉 Fix successful! Try running your original script now.")
        else:
            print("\n❌ Auto-fix also failed. See suggested fixes above.")
    else:
        print("Running comprehensive debug by default...")
        run_comprehensive_debug()
