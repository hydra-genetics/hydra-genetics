# -*- coding: UTF-8 -*-

from __future__ import print_function

__author__ = "Patrik Smeds"
__copyright__ = "Copyright 2022, Patrik Smeds"
__email__ = "patrik.smeds@scilifelab.uu.se"
__license__ = "GPL-3"


from pathlib import Path
import sys
import versioneer

if sys.version_info < (3, 8):
    print("At least Python 3.8 is required for hydra-genetics.\n", file=sys.stderr)
    exit(1)

try:
    from setuptools import setup, find_packages
except ImportError:
    print("Please install setuptools before installing hydra-genetics.", file=sys.stderr)
    exit(1)

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="hydra-genetics",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
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
        'pandas>=1.3.1',
        'click==7.1.2',
        'jinja2==3.0.1',
        'rich==10.9.0',
        'snakemake',
        'pysam',
        'gitpython',
        'pyaml'
    ],
    packages=find_packages(exclude=("docs")),
    include_package_data=True,
    zip_safe=False,
)
