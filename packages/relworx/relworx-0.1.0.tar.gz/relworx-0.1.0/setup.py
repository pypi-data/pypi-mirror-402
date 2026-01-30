#!/usr/bin/env python
"""Setup configuration for relworx package."""

from setuptools import setup, find_packages

setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
)
