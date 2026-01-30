import os
from setuptools import setup, find_packages

setup(
    name="fluxpy-ui",
    version="3.2.4",
    author="FluxPy Team",
    description="The Ultimate Universal Python UI Framework for Desktop, Web, and Mobile",
    long_description=open("README.md").read() if os.path.exists("README.md") else "FluxPy v3.1.0",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt6",
        "flask",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
