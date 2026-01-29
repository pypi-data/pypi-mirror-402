"""
Setup configuration for mercury_package
A Python package for mercury pollution Monte Carlo simulation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="mercury-pollution-simulator",
    version="1.1.1",
    author="Henry Nunoo-Mensah",
    author_email="hnunoo-mensah@knust.edu.gh",
    description="Monte Carlo simulator for mercury pollution assessment with multiple model types (empirical, mechanistic, compartmental, simplified)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/henrynunoo-mensah/mercury-pollution-simulator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Environmental Science",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "openpyxl>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mercury-sim=mercury_package.cli:main",
        ],
    },
)
