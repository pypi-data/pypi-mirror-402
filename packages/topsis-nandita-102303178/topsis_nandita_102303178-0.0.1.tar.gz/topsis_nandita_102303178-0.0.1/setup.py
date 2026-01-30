from setuptools import setup, find_packages

setup(
    name="topsis-nandita-102303178",
    version="0.0.1",
    author="Nandita",
    author_email="nnandita1_be23@thapar.edu",
    description="TOPSIS implementation as a Python package",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_nandita_102303178.topsis:main"
        ]
    }
)
