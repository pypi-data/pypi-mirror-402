import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="topsis-gaurav-102303493",
    version="1.0.5",
    description="A Python package implementing the TOPSIS method for multi-criteria decision making.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Gaurav Prakash Srivastava",
    author_email="gsrivastava_be23@thapar.edu",
    license="MIT",
    packages=["topsis"],
    install_requires=[
        "pandas",
        "numpy",
        "argparse",
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis.__main__:main",
        ]
    }
)