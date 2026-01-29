from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="topsis_aryaman_102303622", 
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package to implement TOPSIS for MCDM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "pandas",
        "openpyxl"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_aryaman_102303622.topsis:main",
        ],
    },
)