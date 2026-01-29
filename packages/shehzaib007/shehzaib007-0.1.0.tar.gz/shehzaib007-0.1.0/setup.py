"""
Setup configuration for shehzaib007 package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="shehzaib007",
    version="0.1.0",
    author="Shehzaib",
    author_email="your_email@example.com",
    description="A simple utility package with basic math and string operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/shehzaib007",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    keywords="math string operations utility",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/shehzaib007/issues",
        "Source": "https://github.com/yourusername/shehzaib007",
    },
)
