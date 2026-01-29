#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup script for ગુજરાતી પાઈથન (Gujarati Python)

A Python programming environment with complete Gujarati syntax and keywords.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="gujarati-python",
    version="1.0.1",
    author="Ritesh Rana",
    author_email="contact@riteshrana.engineer",
    description="Python programming with complete Gujarati syntax and keywords",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ambicuity/gujarati-python",
    packages=find_packages(),
    py_modules=["cli", "મુખ્ય"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Software Development :: Localization",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",

        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "gujarati-python=cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/ambicuity/gujarati-python/issues",
        "Source": "https://github.com/ambicuity/gujarati-python",
        "Documentation": "https://github.com/ambicuity/gujarati-python/tree/main/ડોક્સ",
    },
    keywords="gujarati python programming language localization",
    include_package_data=True,
    zip_safe=False,
)