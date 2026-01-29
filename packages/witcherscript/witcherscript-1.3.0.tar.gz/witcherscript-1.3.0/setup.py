#!/usr/bin/env python3
"""
WitcherScript Setup Configuration
Enables: pip install witcherscript
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="witcherscript",
    use_scm_version=True,
    author="WitcherScript Contributors",
    description="A programming language inspired by The Witcher 3: Wild Hunt",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rwnicholas/WitcherScript",
    project_urls={
        "Bug Tracker": "https://github.com/rwnicholas/WitcherScript/issues",
        "Documentation": "https://github.com/rwnicholas/WitcherScript/blob/main/README.md",
        "Source Code": "https://github.com/rwnicholas/WitcherScript",
    },
    py_modules=["witcher", "witcher_interpreter"],
    entry_points={
        "console_scripts": [
            "witcher=witcher:main",
            "witcher_interpreter=witcher:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Education",
        "Topic :: Software Development :: Interpreters",
        "Topic :: System :: Shells",
    ],
    python_requires=">=3.6",
    keywords="programming language witcher interpreter game inspired",
    zip_safe=False,
    setup_requires=["setuptools_scm"],
)
