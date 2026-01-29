"""Setup configuration for MusicList for Soundiiz."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="musiclist-for-soundiiz",
    version="1.0.8",
    author="Luc Muss",
    author_email="lucmuss@users.noreply.github.com",
    description="Extract music file metadata for Soundiiz import",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lucmuss/musiclist-for-soundiiz",
    project_urls={
        "Bug Reports": "https://github.com/lucmuss/musiclist-for-soundiiz/issues",
        "Source": "https://github.com/lucmuss/musiclist-for-soundiiz",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "mutagen>=1.45.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "isort>=5.10.0",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "musiclist-for-soundiiz=musiclist_for_soundiiz.cli:main",
            "musiclist-for-soundiiz-gui=musiclist_for_soundiiz.gui:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="soundiiz music metadata audio playlist csv export",
)
