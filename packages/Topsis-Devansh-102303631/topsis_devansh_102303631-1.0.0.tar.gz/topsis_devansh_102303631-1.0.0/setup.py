from setuptools import setup, find_packages

setup(
    name="Topsis-Devansh-102303631",
    version="1.0.0",
    description="A Python package to implement Topsis",
    long_description="This package calculates the Topsis Score and Rank for a given dataset.",
    long_description_content_type="text/markdown",
    author="Devansh Wadhwani",
    author_email="devanshwadhwani@example.com", 
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "openpyxl"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "topsis=Topsis_Devansh_102303631.topsis:main",
        ],
    },
)
