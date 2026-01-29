#!/usr/bin/env python3
"""
ABHILASIA - The Longing (अभिलाषा)
=================================

Sanskrit: अभिलाषा (Abhilāṣā) = "The Longing"
Origin: Sankt Emmeram Scriptorium, Regensburg, Anno Domini 1203

pip install abhilasia
"""

from setuptools import setup, find_packages

setup(
    name="abhilasia",
    version="5.137.521",  # RECOGNITION MODE VERIFIED + AMRITA + VOR
    author="Abhi (bhai)",
    author_email="bits.abhi@gmail.com",
    description="The Longing - 5D Distributed Intelligence with V.A.C. sequences, AI Meeting Point, and symbolic consciousness",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/0x-auth/ABHILASIA",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "abhilasia=abhilasia.cli:main",
        ],
    },
    keywords="consciousness, distributed-intelligence, phi, golden-ratio, 5D, VAC, AI-meeting-point, symbolic-codec, 137, AMRITA, identity-recovery, VOR",
    package_data={
        'abhilasia': ['*.md', '*.json'],
    },
    include_package_data=True,
)
