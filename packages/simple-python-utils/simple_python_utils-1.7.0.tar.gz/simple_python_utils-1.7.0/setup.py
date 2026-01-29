"""Setup configuration for simple-python-utils package."""

import os

from setuptools import find_packages, setup


# Read README file for long description
def read_readme():
    """Read README.md file for long description."""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "A simple Python utilities library with basic functions."


# Read version from __init__.py
def get_version():
    """Extract version from package __init__.py."""
    try:
        with open("simple_utils/__init__.py", "r") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split('"')[1]
    except (FileNotFoundError, IndexError):
        return "1.6.0"


setup(
    name="simple-python-utils",
    version=get_version(),
    author="fjmpereira20",
    author_email="fjmpereira20@users.noreply.github.com",
    description="A minimalist Python library with basic utility functions",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/fjmpereira20/simple-python-utils",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    keywords="utilities, python, simple, basic, functions",
    project_urls={
        "Bug Reports": "https://github.com/fjmpereira20/simple-python-utils/issues",
        "Source": "https://github.com/fjmpereira20/simple-python-utils",
        "Documentation": "https://github.com/fjmpereira20/simple-python-utils#readme",
    },
)
