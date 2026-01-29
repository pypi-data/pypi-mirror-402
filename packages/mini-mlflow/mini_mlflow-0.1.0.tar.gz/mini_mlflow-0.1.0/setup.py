"""
Setup script for mini-mlflow package.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="mini-mlflow",
    version="0.1.0",
    description="A minimal ML experiment tracker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Mini MLflow Contributors",
    license="MIT",
    python_requires=">=3.7",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    install_requires=[
        "pyyaml>=5.1",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=["mlflow", "machine-learning", "experiment-tracking", "ml", "tracking"],
    project_urls={
        "Homepage": "https://github.com/yourusername/mini-mlflow",
        "Documentation": "https://github.com/yourusername/mini-mlflow#readme",
        "Repository": "https://github.com/yourusername/mini-mlflow",
        "Issues": "https://github.com/yourusername/mini-mlflow/issues",
    },
)
