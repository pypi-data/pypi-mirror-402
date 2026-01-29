from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="topsis-sayyam-102303147",
    version="0.1.0",
    author="Sayyam Wadhwa",
    author_email="sayyam.wad@gmail.com",
    description="A command-line Python package implementing the TOPSIS method for multi-criteria decision making.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sayyam-wad/topsis-sayyam-102303147",
    license="MIT",
    py_modules=["topsis"],
    install_requires=[
        "numpy",
        "pandas",
    ],
    classifiers=[
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Education",
    "Topic :: Scientific/Engineering",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent",
],

    python_requires=">=3.8",
)
