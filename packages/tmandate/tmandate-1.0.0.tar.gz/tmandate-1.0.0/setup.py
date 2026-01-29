from setuptools import setup, find_packages

setup(
    name="tmandate",
    version="1.0.0",
    author="TMANDATE",
    description="TMANDATE Python SDK",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
    ],
)