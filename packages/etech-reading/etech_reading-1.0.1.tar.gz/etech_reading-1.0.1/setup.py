#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup configuration for eTech Reading package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="etech-reading",
    version="1.0.1",
    author="eOS",
    author_email="eOS@eTech.com",
    description="Fast Reading System using RSVP Technology",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eOS/etech-reading",
    project_urls={
        "Bug Tracker": "https://github.com/eOS/etech-reading/issues",
        "Documentation": "https://github.com/eOS/etech-reading#readme",
        "Source Code": "https://github.com/eOS/etech-reading",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Education",
        "Topic :: Education",
        "Topic :: Text Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "PyQt5>=5.15.0",
        "PyQtWebEngine>=5.15.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "etech-reading=etech_reading.reader:main",
        ],
    },
    keywords="reading speed rsvp rapid-serial-visual-presentation text-analysis",
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)
