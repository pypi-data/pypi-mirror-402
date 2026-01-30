"""Setup configuration for noveum-sdk.

This file provides setuptools compatibility.
All configuration is in pyproject.toml following PEP 621.
"""

from setuptools import find_packages, setup  # type: ignore[import-untyped]

# Read dependencies from pyproject.toml (handled automatically by setuptools>=61.0.0)
# This file exists for backward compatibility and editable installs
setup(
    packages=find_packages(exclude=["tests*", "doc*"]),
    package_data={"noveum_api_client": ["py.typed"]},
    include_package_data=True,
)
