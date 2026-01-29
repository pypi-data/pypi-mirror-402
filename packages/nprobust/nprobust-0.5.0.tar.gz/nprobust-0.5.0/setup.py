"""
Setup script for nprobust package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nprobust",
    version="0.5.0",
    author="Translated from R by Calonico, Cattaneo, and Farrell",
    description="Nonparametric Robust Estimation and Inference Methods",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nppackages/nprobust",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "plotting": ["matplotlib>=3.4.0"],
        "dev": [
            "pytest>=6.0",
            "matplotlib>=3.4.0",
        ],
    },
)
