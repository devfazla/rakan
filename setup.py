"""
RAKAN - Local AI Development Platform
Setup configuration for pip installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="rakan",
    version="0.1.0",
    author="DevFazla",
    author_email="devfazla@devfazla.com",
    description="RAKAN - A modular, portable, local-first AI coding assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/devfazla/rakan",
    project_urls={
        "Bug Reports": "https://github.com/devfazla/rakan/issues",
        "Source": "https://github.com/devfazla/rakan",
        "Website": "https://devfazla.com",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "web": ["fastapi>=0.95.0", "uvicorn>=0.21.0", "websockets>=11.0"],
        "gpu": ["GPUtil>=1.4.0"],
        "windows": ["winshell>=0.6", "pywin32>=305"],
    },
    entry_points={
        "console_scripts": [
            "rakan=cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "rakan": [
            "config/*.yaml",
            "rakan_ascii.txt",
            "web/*.html",
        ],
    },
    zip_safe=False,
)