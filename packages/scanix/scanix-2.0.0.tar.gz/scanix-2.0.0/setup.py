#!/usr/bin/env python3
"""
Setup configuration for Scanix
Static Code Security Scanner
Developed by Riyad ODJOUADE (Ore)
"""

from setuptools import setup, find_packages
from pathlib import Path

# Lire le README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Lire requirements.txt
requirements = []
if (this_directory / "requirements.txt").exists():
    requirements = (this_directory / "requirements.txt").read_text().splitlines()
    requirements = [r.strip() for r in requirements if r.strip() and not r.startswith("#")]

setup(
    name="scanix",
    version="2.0.0",
    author="Riyad ODJOUADE",
    author_email="riyadodjouade@gmail.com",
    description="⚡ Fast and powerful static code security scanner - Détecte 25+ vulnérabilités OWASP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ore2025/scanix",
    project_urls={
        "Bug Tracker": "https://github.com/Ore2025/scanix/issues",
        "Documentation": "https://github.com/Ore2025/scanix#readme",
        "Source Code": "https://github.com/Ore2025/scanix",
    },
    packages=find_packages(exclude=["tests", "tests.*", "venv", "static"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Environment :: Console",
        "Natural Language :: French",
        "Natural Language :: English",
    ],
    keywords=[
        "security",
        "scanner",
        "static-analysis",
        "vulnerability",
        "owasp",
        "code-security",
        "sast",
        "security-scanner",
        "vulnerability-scanner",
        "sql-injection",
        "xss",
        "security-audit",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "scanix=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["*.yaml", "*.json"],
    },
    zip_safe=False,
    license="MIT",
)