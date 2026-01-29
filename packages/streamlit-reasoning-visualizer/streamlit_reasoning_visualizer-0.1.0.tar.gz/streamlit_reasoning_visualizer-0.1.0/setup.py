"""
Backward-compatible setup script for streamlit-reasoning-visualizer.

This file exists for compatibility with older pip versions that don't fully
support pyproject.toml. The actual configuration is in pyproject.toml.
"""
from setuptools import setup, find_packages
import os

# Read the README for long description
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A Streamlit component to visualize LLM reasoning processes"

setup(
    name="streamlit-reasoning-visualizer",
    version="0.1.0",
    author="Ketan Mahandule",
    description="A Streamlit component to visualize LLM reasoning processes with collapsible thought sections and rich markdown/LaTeX rendering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ketanmahandule/streamlit-reasoning-visualizer",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    package_data={
        "reasoning_visualizer": [
            "frontend/build/**/*",
            "frontend/build/*",
        ],
    },
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "build>=1.0.0",
            "twine>=4.0.0",
        ],
        "example": [
            "ollama>=0.1.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: User Interfaces",
    ],
)
