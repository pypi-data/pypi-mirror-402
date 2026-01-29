from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Lakshita-102303505",
    version="1.0.0",
    author="Lakshita Gupta",
    author_email="lakshitagupta0518@gmail.com",
    description="A Python package for TOPSIS multi-criteria decision analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Lakshita018/topsis",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "openpyxl>=3.0.0",
    ],
    entry_points={
        'console_scripts': [
            'topsis=Topsis_Lakshita_102303505.topsis:main',
        ],
    },
    keywords="topsis, multi-criteria decision analysis, mcdm, decision making",
    project_urls={
        "Bug Reports": "https://github.com/Lakshita018/topsis/issues",
        "Source": "https://github.com/Lakshita018/topsis",
    },
)
