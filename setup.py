"""
Setup file for CME Gap Analyzer (optional - for package installation).
"""

from setuptools import setup, find_packages

setup(
    name="cme-gap-analyzer",
    version="0.1.0",
    description="Analyze CME gaps in Bitcoin price data",
    author="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "requests>=2.31.0",
        "pytz>=2023.3",
    ],
    python_requires=">=3.8",
)

