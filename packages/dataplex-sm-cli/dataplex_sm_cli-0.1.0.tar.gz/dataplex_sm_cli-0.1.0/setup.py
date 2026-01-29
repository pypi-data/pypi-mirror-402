#!/usr/bin/env python
"""Setup script for dataplex-sm-cli package."""

from setuptools import setup, find_packages

setup(
    name="dataplex-sm-cli",
    version="0.1.0",
    description="A CLI tool for Dataplex Semantic Model operations",
    author="Sachin Rungta",
    author_email="sachin.rungta@example.com",
    url="https://github.com/Sachin-Rungta/dataplex-sm-cli",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "dataplex-sm=dataplex_sm_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
