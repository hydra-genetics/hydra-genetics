#!/usr/bin/env python

from setuptools import setup, find_packages
from pathlib import Path

version = "0.0.4"


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="hydra-genetics",
    version=version,
    description="Helper tools for use with hydra-genetics pipelines.",
    long_description=long_description,
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
    license='GPL-3',
    entry_points={"console_scripts": ["hydra-genetics=hydra_genetics.__main__:run"]},
    install_requires=[
        'pandas==1.3.1',
        'click==7.1.2',
        'jinja2==3.0.1',
        'rich==10.9.0',
        'gitpython'
    ],
    setup_requires=["twine>=1.11.0", "setuptools>=38.6."],
    packages=find_packages(exclude=("docs")),
    include_package_data=True,
    zip_safe=False,
)
