#!/usr/bin/env python3
"""Compatibility shim for legacy build workflows.

All project metadata lives in ``pyproject.toml``. Keeping this lightweight script
ensures that tools which still invoke ``setup.py`` continue to function.
"""

from setuptools import setup  # type: ignore[import]


if __name__ == "__main__":
    setup()
