from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Aryaman-102303622",
    version="1.0.1",                # Updated version for next upload
    author="Aryaman",
    author_email="aryaman@example.com",
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