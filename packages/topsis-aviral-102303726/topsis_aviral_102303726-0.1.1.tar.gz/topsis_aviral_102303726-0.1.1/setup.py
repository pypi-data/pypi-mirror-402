from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="topsis-aviral-102303726",
    version="0.1.1",  # change version
    description="TOPSIS implementation in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
)
