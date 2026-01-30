"""Setup configuration for LockStock Python SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lockstock",
    version="0.1.0",
    author="LockStock Team",
    author_email="hello@lockstock.dev",
    description="The TCP/IP of AI Agency - Cryptographic identity and memory for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lockstock/lockstock",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    keywords="ai agents identity authentication memory cryptography security",
    project_urls={
        "Bug Reports": "https://github.com/lockstock/lockstock/issues",
        "Source": "https://github.com/lockstock/lockstock",
        "Documentation": "https://docs.lockstock.dev",
    },
)
