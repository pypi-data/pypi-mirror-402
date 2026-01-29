from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Pranav-102303194", 
    version="1.0.0",
    author="Pranav",
    author_email="pranavvaish20@gmail.com", 
    description="A Python package to implement TOPSIS for MCDM.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PranavVaish/Topsis-Pranav-102303194",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'topsis=topsis_pranav_102303194.topsis:main',
        ],
    },
)