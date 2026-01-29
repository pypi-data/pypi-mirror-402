"""
Backwards-compatible setup.py for older pip versions.
Modern installations use pyproject.toml.
"""
from setuptools import setup, find_packages

setup(
    name="kita",
    version="1.0.1",
    packages=find_packages(),
    install_requires=["requests>=2.25.0"],
    python_requires=">=3.8",
)
