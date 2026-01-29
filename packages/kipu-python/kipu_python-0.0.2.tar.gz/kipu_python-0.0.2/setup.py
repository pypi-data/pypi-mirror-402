"""
Setup configuration for the Kipu API Python library
"""

from setuptools import setup, find_packages
import os
import re

# Read version from kipu/__init__.py without importing (avoids build isolation issues)
def get_version():
    init_path = os.path.join(os.path.dirname(__file__), 'kipu', '__init__.py')
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string in kipu/__init__.py")

__version__ = get_version()

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    with open(readme_path, 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="kipu-python",
    version=__version__,  # Dynamic version from kipu/__init__.py
    author="Rahul",
    author_email="rahul01110100@gmail.com",
    description="The Kipu Python library provides convenient access to the Kipu API (V3) from any Python 3.8+ application. The library includes HMAC SHA1 authentication, recursive JSON flattening capabilities and type definitions for most of the request params and response fields, and offers asynchronous clients powered by [asyncio].",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Rahulkumar010/kipu-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "pytest-asyncio>=0.18.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "pre-commit>=2.15.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.12.0",
            "myst-parser",
            "linkify-it-py",
        ],
    },
    entry_points={
        "console_scripts": [
            "kipu-cli=kipu.cli:main",
        ],
    },
    keywords=[
        "kipu", "healthcare", "api", "library", "medical", "ehr", "electronic-health-records",
        "hmac", "authentication", "async", "pandas", "recursive-json-flattening"
    ],
    project_urls={
        "Bug Reports": "https://github.com/Rahulkumar010/kipu-python/issues",
        "Source": "https://github.com/Rahulkumar010/kipu-python",
        "Documentation": "https://kipu-python.readthedocs.io/",
    },
    include_package_data=True,
    zip_safe=False,
)
