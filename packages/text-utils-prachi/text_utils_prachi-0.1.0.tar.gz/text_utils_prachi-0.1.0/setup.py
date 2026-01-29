from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="text-utils-prachi",                 # PyPI project name (must be unique)
    version="0.1.0",                          # Version (cannot be reused on PyPI)
    author="Prachi Kabra",
    author_email="pythonwithprachi1213@gmail.com",
    description="A basic text utilities package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/prachikabra121/text_utils_prachi",
    packages=find_packages(),                 # Auto-detect packages
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
