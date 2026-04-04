#!/usr/bin/env python3
"""
Comprehensive test runner for the music video project.
Runs all tests and provides detailed reporting.
"""
import subprocess
import sys
import os
import time
from pathlib import Path
from datetime import datetime


def check_dependencies():
    """Check that all required dependencies are installed."""
    print("🔍 CHECKING DEPENDENCIES")
    print("=" * 40)

    required_modules = [
        ("pytest", "pytest"),
        ("librosa", "librosa"),
        ("moviepy", "moviepy"),
        ("scenedetect", "scenedetect"),
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
    ]

    missing = []
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} (missing)")
            missing.append(package_name)

    if missing:
        print(f"\n❌ Missing dependencies: {missing}")
        print("Install with: pip install -r requirements.txt")
        return False

    print("✅ All dependencies available")
    return True


def check_test_assets():
    """Check that test assets are available."""
    print("\n🎬 CHECKING TEST ASSETS")
    print("=" * 40)

    required_assets = [
        "test-assets/test_video.mp4",
        "test-assets/test_audio.wav",
        "test-assets/test_video_long.mp4",
    ]

    missing = []
    for asset in required_assets:
        if Path(asset).exists():
            size = Path(asset).stat().st_size / (1024 * 1024)  # MB
            print(f"✅ {asset} ({size:.1f} MB)")
        else:
            print(f"❌ {asset} (missing)")
            missing.append(asset)

    if missing:
        print(f"\n❌ Missing test assets: {missing}")
        print("Generate with:")
        print("  python create_test_video.py")
        print("  python create_test_audio.py")
        return False

    print("✅ All test assets available")
    return True


def run_test_category(category, description):
    """Run a specific test category."""
    print(f"\n{description}")
    print("=" * len(description))

    cmd = ["python", "-m", "pytest", f"tests/{category}/", "-v", "--tb=short"]

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time

    if result.returncode == 0:
        print(f"✅ {description} PASSED ({duration:.1f}s)")
        return True, duration
    else:
        print(f"❌ {description} FAILED ({duration:.1f}s)")
        print("STDOUT:", result.stdout[-500:])  # Last 500 chars
        print("STDERR:", result.stderr[-500:])  # Last 500 chars
        return False, duration


def run_coverage_report():
    """Generate test coverage report."""
    print("\n📊 GENERATING COVERAGE REPORT")
    print("=" * 40)

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Coverage report generated")
        print("📁 HTML report: htmlcov/index.html")

        # Extract coverage percentage from output
        output_lines = result.stdout.split("\n")
        for line in output_lines:
            if "TOTAL" in line and "%" in line:
                print(f"📈 {line.strip()}")

        return True
    else:
        print("❌ Coverage report failed")
        print("STDERR:", result.stderr[-300:])
        return False


def run_linting_checks():
    """Run code quality checks."""
    print("\n🔍 RUNNING CODE QUALITY CHECKS")
    print("=" * 40)

    checks = [
        (
            ["flake8", ".", "--max-line-length=88", "--extend-ignore=E203,W503"],
            "Flake8 linting",
        ),
        (["python", "-m", "black", "--check", "--diff", "."], "Black formatting"),
    ]

    all_passed = True

    for cmd, description in checks:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_passed = False

    return all_passed


def main():
    """Run complete test suite."""
    print("🎬🎵 MUSIC VIDEO PROJECT - COMPREHENSIVE TEST RUNNER")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    overall_start = time.time()

    # 1. Check dependencies
    if not check_dependencies():
        return 1

    # 2. Check test assets
    if not check_test_assets():
        return 1

    # 3. Run linting checks
    print("\n🔧 CODE QUALITY PHASE")
    linting_passed = run_linting_checks()

    # 4. Run test categories
    print("\n🧪 TESTING PHASE")
    test_categories = [
        ("unit", "🧪 UNIT TESTS"),
        ("integration", "🔗 INTEGRATION TESTS"),
        ("performance", "⚡ PERFORMANCE BENCHMARKS"),
    ]

    results = {}
    for category, description in test_categories:
        passed, duration = run_test_category(category, description)
        results[category] = {"passed": passed, "duration": duration}

    # 5. Generate coverage report
    coverage_passed = run_coverage_report()

    # 6. Summary
    total_duration = time.time() - overall_start

    print(f"\n📊 FINAL RESULTS")
    print("=" * 40)
    print(f"⏱️  Total execution time: {total_duration:.1f}s")

    # Test results summary
    passed_tests = sum(1 for r in results.values() if r["passed"])
    total_tests = len(results)

    print(f"\n🎯 Test Results: {passed_tests}/{total_tests} categories passed")
    for category, result in results.items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"   {status} {category.upper()} ({result['duration']:.1f}s)")

    print(f"\n🔧 Code Quality: {'✅ PASS' if linting_passed else '❌ FAIL'}")
    print(f"📊 Coverage Report: {'✅ GENERATED' if coverage_passed else '❌ FAILED'}")

    # Overall status
    all_passed = passed_tests == total_tests and linting_passed and coverage_passed

    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED! Ready for commit/deployment.")
        print(f"✅ Code quality: Excellent")
        print(f"✅ Test coverage: Generated (see htmlcov/index.html)")
        print(f"✅ Performance: Benchmarked")
        return 0
    else:
        print(
            f"\n❌ SOME TESTS FAILED. Please review and fix issues before committing."
        )
        failed_categories = [cat for cat, res in results.items() if not res["passed"]]
        if failed_categories:
            print(f"   Failed categories: {failed_categories}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
