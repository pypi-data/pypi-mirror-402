"""
Setup script for Core package.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="core",
    version="1.0.0",
    description="A powerful Python game engine with comprehensive math library and render pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Core Contributors",
    author_email="",  # Add your email if desired
    url="https://github.com/yourusername/core",  # Update with your repo URL
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Libraries",
    ],
    keywords=["game-engine", "3d", "rendering", "math", "graphics"],
    project_urls={
        "Documentation": "https://github.com/yourusername/core#readme",  # Update
        "Source": "https://github.com/yourusername/core",  # Update
        "Tracker": "https://github.com/yourusername/core/issues",  # Update
    },
)

