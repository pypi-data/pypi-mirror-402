"""
Setup script for wintouch - Windows Touch Injection API for Python

Build with:
    python setup.py build_ext --inplace

Install with:
    pip install .
"""

import sys
from setuptools import setup, Extension

if sys.platform != "win32" and sys.platform != "cygwin":
    print("Warning: wintouch only works on Windows")
    ext_modules = []
else:
    ext_modules = [
        Extension(
            "_wintouch",
            sources=["src/_wintouch/module.c"],
            libraries=["user32"],
            define_macros=[
                ("UNICODE", "1"),
                ("_UNICODE", "1"),
            ],
        )
    ]

setup(
    ext_modules=ext_modules,
)
