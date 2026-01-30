from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="topsis-nandita-102303178",
    version="0.0.2",
    author="Nandita",
    author_email="nnandita1_be23@thapar.edu",
    description="TOPSIS implementation as a Python package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_nandita_102303178.topsis:main"
        ]
    }
)
