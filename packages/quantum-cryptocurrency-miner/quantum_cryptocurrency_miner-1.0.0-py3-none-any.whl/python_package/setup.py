#!/usr/bin/env python3
"""
Setup script for the Python CMake Integration package.
This is primarily for reference - the actual building is handled by CMake.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Python bindings for C++ functionality built with CMake"

# Read version from __init__.py
def get_version():
    init_path = os.path.join(os.path.dirname(__file__), '__init__.py')
    with open(init_path, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return "1.0.0"

setup(
    name="python-cmake-integration",
    version=get_version(),
    author="CMake Python Integration Team",
    author_email="team@example.com",
    description="Python bindings for C++ functionality built with CMake",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/python-cmake-integration",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core requirements - none for the C++ module
    ],
    extras_require={
        "numpy": ["numpy>=1.19.0"],
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme",
            "myst-parser",
        ],
    },
    entry_points={
        "console_scripts": [
            "python-cmake-info=python_cmake_package:print_module_info",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="cmake python c++ integration numpy performance",
    project_urls={
        "Bug Reports": "https://github.com/example/python-cmake-integration/issues",
        "Source": "https://github.com/example/python-cmake-integration",
        "Documentation": "https://python-cmake-integration.readthedocs.io/",
    },
)