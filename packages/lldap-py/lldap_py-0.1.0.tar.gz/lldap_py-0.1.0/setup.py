#!/usr/bin/env python3
"""Setup script for lldap-py package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lldap-py",
    version="0.1.0",
    author="Lucas Sylvester",
    description="Python tool for managing LLDAP servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/luca2618/lldap-py",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "toml>=0.10.2",
        "click>=8.0.0",
        "ldap3>=2.9.0",
    ],
    extras_require={'test': ['pytest']}
)
