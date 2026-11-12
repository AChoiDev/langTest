"""Setup script for qbepy with CFFI extension."""

from setuptools import setup

setup(
    cffi_modules=["build_ffi.py:ffi"],
)
