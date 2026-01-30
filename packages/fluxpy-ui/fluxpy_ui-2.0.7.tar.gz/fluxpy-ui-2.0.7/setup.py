from setuptools import setup, find_packages

setup(
    name="fluxpy-ui",
    version="2.0.7",
    author="FluxPy Team",
    description="An enterprise-grade modern desktop UI and Game framework for Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'fluxpy': ['assets/*'],
    },
    install_requires=[
        "PyQt6",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
