from setuptools import setup, find_packages

setup(
    name="bioshield-integration",
    version="2.1.1",
    author="Emerlad Compass",
    author_email="emerladcompass@gmail.com",
    description="Unified Intelligence Framework with Enhanced Pathogen Risk Assessment",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/emerladcompass/BioShield-Integration",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "pyyaml>=6.0",
    ],
)
