#!/usr/bin/env python

from setuptools import setup, find_packages

version = "0.1"

with open("README.md") as f:
    readme = f.read()

with open("LICENSE.md") as f:
    license = f.read()    
    
with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="hydra-genetics",
    version=version,
    description="Helper tools for use with hydra-genetics pipelines.",
    long_description=readme,
    long_description_content_type="text/markdown",
    keywords=[
        "hydra-genetics",
        "snakemake",
        "bioinformatics",
        "workflow",
        "pipeline",
        "clinical",
        "biology",
        "sequencing",
        "NGS",
        "next generation sequencing",
    ],
    author="Patrik Smeds",
    author_email="patrik.smeds@scilifelab.uu.se",
    url="https://github.com/hydra-genetics/tools",
    license=license,
    entry_points={"console_scripts": ["hydra-genetics=hydra_genetics.__main__:run"]},
    install_requires=required,
    setup_requires=["twine>=1.11.0", "setuptools>=38.6."],
    packages=find_packages(exclude=("docs")),
    include_package_data=True,
    zip_safe=False,
)
