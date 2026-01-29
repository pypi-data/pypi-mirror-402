from setuptools import setup, find_packages

setup(
    name="VIXRHeston",
    version="0.1.1",
    description="VIX term structure in the rough Heston model via Markovian approximation",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy",
        "scipy",
    ],
)