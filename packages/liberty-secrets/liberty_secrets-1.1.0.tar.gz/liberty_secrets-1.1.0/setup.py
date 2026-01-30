#!/usr/bin/env python3
"""Setup script for Liberty - Hardware-Bound Secrets Manager"""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="liberty-secrets",
    version="1.1.0",
    author="Liberty Contributors",
    description="Hardware-bound secret management. No more .env files in Git.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/liberty",
    py_modules=["liberty"],
    install_requires=[
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "liberty=liberty:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.7",
)
