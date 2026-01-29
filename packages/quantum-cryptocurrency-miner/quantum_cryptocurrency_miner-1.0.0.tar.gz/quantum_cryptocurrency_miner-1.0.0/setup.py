#!/usr/bin/env python3
"""
Setup script for Quantum Cryptocurrency Miner
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="quantum-cryptocurrency-miner",
    version="1.0.0",
    author="Quantum Miner Team",
    author_email="team@quantum-miner.com",
    description="Next-generation quantum cryptocurrency mining system with distributed architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quantum-miner/quantum-cryptocurrency-miner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: System :: Distributed Computing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.17.0",
            "grafana-api>=1.0.3",
        ],
        "quantum": [
            "qiskit>=0.44.0",
            "cirq>=1.2.0",
            "pennylane>=0.32.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "quantum-miner=main:main",
            "quantum-miner-cli=cli:main",
            "prometheus-orchestrator=orchestrator:main",
        ],
    },
    include_package_data=True,
    package_data={
        "quantum-miner": [
            "web/*.html",
            "web/*.css",
            "web/*.js",
            "config/*.yaml",
            "config/*.yml",
            "config/*.conf",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/quantum-miner/quantum-cryptocurrency-miner/issues",
        "Source": "https://github.com/quantum-miner/quantum-cryptocurrency-miner",
        "Documentation": "https://quantum-miner.readthedocs.io/",
    },
)