#!/usr/bin/env python3
"""Setup configuration for music_video_generator package."""
from setuptools import setup, find_packages

setup(
    name="music_video_generator",
    version="2.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "librosa",
        "scenedetect[opencv]",
        "numpy",
        "matplotlib",
        "opencv-python",
    ],
    author="Music Video Generator Team",
    description="AI-driven music video generation from archival film footage",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
