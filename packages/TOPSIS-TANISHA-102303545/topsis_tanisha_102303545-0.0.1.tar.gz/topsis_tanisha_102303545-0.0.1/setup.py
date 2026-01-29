import os
from setuptools import setup, find_packages

this_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="TOPSIS-TANISHA-102303545",
    version="0.0.1",
    author="Tanisha Dua",
    author_email="tanisha.dua244@gmail.com",
    description="A Python package implementing the TOPSIS decision making method",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy", "openpyxl"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_tanisha.topsis:main"
        ]
    },
    python_requires=">=3.8",
)


