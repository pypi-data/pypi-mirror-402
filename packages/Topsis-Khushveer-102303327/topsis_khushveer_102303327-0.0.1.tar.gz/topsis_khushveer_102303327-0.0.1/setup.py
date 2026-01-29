from setuptools import setup, find_packages

setup(
    name="Topsis-Khushveer-102303327",
    version="0.0.1",
    author="Khushveer Kaur",
    author_email="kkaur3_be23@thapar.edu",
    description="TOPSIS implementation as a command line tool",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main",
        ]
    },
)
