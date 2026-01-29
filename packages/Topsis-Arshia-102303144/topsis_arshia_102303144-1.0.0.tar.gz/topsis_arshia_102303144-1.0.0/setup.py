from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Arshia-102303144",
    version="1.0.0",
    author="Arshia Anand",
    description="Python package for solving MCDM problems using TOPSIS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    install_requires=["pandas", "numpy", "openpyxl"],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)