"""Setup configuration for Number Guessing Game package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="number-guessing-game-bhimesh",
    version="1.0.2",
    author="bhimesh",
    author_email="your.email@example.com",
    description="An interactive number guessing game",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/number-guessing-game",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6",
)
