from setuptools import setup, find_packages

setup(
    name="cancerlab-pythonlibrary",
    version="1.0.0",
    author="Balaga Raghuram",
    author_email="your.email@example.com",
    description="Machine Learning library for cancer detection and analysis",
    long_description="A comprehensive Python package for cancer detection, classification, and analysis using ML algorithms.",
    long_description_content_type="text/plain",
    url="https://github.com/balagaraghuram/cancerlab_pythonlibrary",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scikit-learn>=1.0.0",
    ],
    keywords="cancer machine-learning healthcare medical-ai",
)
