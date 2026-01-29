from setuptools import setup, find_packages

setup(
    name="pycan-research",
    version="1.0.0",
    author="Balaga Raghuram",
    description="Comprehensive Python library for cancer research",
    long_description="AI/ML tools for cancer detection and analysis",
    packages=find_packages(),
    install_requires=["numpy>=1.20.0", "scikit-learn>=1.0.0"],
    python_requires=">=3.8",
)
