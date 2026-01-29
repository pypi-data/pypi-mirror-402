
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="text_package",                 # PyPI project name (must be unique)
    version="0.1.0",                          # Version (cannot be reused on PyPI)
    author="Ashutosh Raj",
    author_email="asahu10m@gmail.com",
    description="A basic text utilities package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/asahu10m/python_package",
    packages=find_packages(),                 # Auto-detect packages
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
