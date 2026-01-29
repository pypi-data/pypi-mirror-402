from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="topsis-akshatbhatnagar-102303158",
    version="1.0.2",  # <--- INCREMENTED VERSION
    author="Akshat Bhatnagar",
    author_email="abhatnagar_be23@thapar.edu",
    description="A Python package for TOPSIS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            # The part before ':' must match your new lowercase folder name exactly
            'topsis=topsis_akshatbhatnagar_102303158.topsis:main',
        ],
    },
)
