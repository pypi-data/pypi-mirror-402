"""Setup configuration for TOON Converter."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="toon-token-optimizer",
    version="1.0.0",
    author="Prashant Dudami",
    author_email="prashant.dudami@gmail.com",
    description="Token Optimized Object Notation - Reduce LLM token usage by 40-60%",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/prashantdudami/toon-converter",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
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
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[],  # No external dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    keywords="llm, tokens, json, optimization, ai, gpt, claude, openai, anthropic",
)
