from setuptools import setup, find_packages

setup(
    name="Topsis-Anjani-102303480",
    version="1.0.0",
    packages=find_packages(),
    description="TOPSIS implementation in Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Anjani Agarwal",
    install_requires=[
        "numpy",
        "pandas"
    ],
)
