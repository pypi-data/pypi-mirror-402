from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Punya-102303567",
    version="1.0.0",
    author="Punya",
    author_email="punya@example.com",
    description="A Python package to implement TOPSIS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/punyey/assignment1_DS",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "topsis=Topsis_Punya_102303567.topsis:main",
        ],
    },
)
