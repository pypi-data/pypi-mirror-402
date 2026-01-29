from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Vikas-102303451",
    version="1.0.0",
    author="Vikas Verma",
    author_email="vverma_be22@thapar.edu",
    description="A Python package for TOPSIS implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vikasverma/topsis", 
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'topsis=topsis_vikas.topsis:main',
        ],
    },
)
