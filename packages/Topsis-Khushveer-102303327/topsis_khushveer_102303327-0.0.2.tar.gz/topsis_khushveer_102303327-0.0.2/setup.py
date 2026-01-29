from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Khushveer-102303327",
    version="0.0.2",
    author="Khushveer Kaur",
    author_email="kkaur3_be23@thapar.edu",
    description="TOPSIS implementation as a command line tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main",
        ],
    },
    python_requires=">=3.7",
)
