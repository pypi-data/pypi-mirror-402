#!/usr/bin/env python
"""
Setup script for explodethosebits (etb).

This file exists for backward compatibility with older pip versions
and editable installs. The main configuration is in pyproject.toml.
"""

from skbuild import setup

setup(
    name="explodethosebits",
    description="ExplodeThoseBits - CUDA-Accelerated exhaustive bit-tree/bit-explosion analysis for digital forensics",
    author="Odin Glynn-Martin",
    license="MIT",
    packages=["etb"],
    package_dir={"etb": "python/etb"},
    python_requires=">=3.8",
    cmake_args=[
        "-DCMAKE_CUDA_ARCHITECTURES=90;100",
    ],
    cmake_install_dir="etb",
)
