# <img src="images/hydragenetics.png" width=40 /> hydra-genetics

A command-line tool that helps you create modules and pipelines, or add rules to an existing project. It can also generate the `samples.tsv` and `units.tsv` input files from FASTQ or BAM files with the `create-input-files` command. Their expected format is defined by the [units](https://github.com/hydra-genetics/hydra-genetics/blob/develop/hydra_genetics/pipeline-template/workflow/schemas/units.schema.yaml) and [samples](https://github.com/hydra-genetics/hydra-genetics/blob/develop/hydra_genetics/pipeline-template/workflow/schemas/samples.schema.yaml) schemas.

Full documentation is available at [hydra-genetics.readthedocs.io](https://hydra-genetics.readthedocs.io/en/latest/).

[![Lint and Test](https://github.com/hydra-genetics/hydra-genetics/actions/workflows/main.yaml/badge.svg?branch=develop)](https://github.com/hydra-genetics/hydra-genetics/actions/workflows/main.yaml)

[![build mkdocs](https://github.com/hydra-genetics/hydra-genetics/actions/workflows/test-build-mkdocs.yaml/badge.svg)](https://github.com/hydra-genetics/hydra-genetics/actions/workflows/test-build-mkdocs.yaml)

![python](https://img.shields.io/badge/python-%3E%3D3.8%2C%3C%3D3.11-blue)

## Installation

```bash
# using virtualenv and pip
virtualenv -p python3.9 venv
source venv/bin/activate
pip install hydra-genetics

# using pixi
pixi init
pixi add --pypi hydra-genetics
pixi add --pypi "setuptools<81"  # needed for all imports to work
```

## Examples

```bash
# Create a new module
hydra-genetics create-pipeline -n snv -d "Collection of callers" -a "Patrik S" -e "p.s@mail.se" -g patrik -o snv

# Create a new smk file named "samtools.smk" with rule "samtools_rule2"
hydra-genetics create-rule -c rule2 -t samtools -m snv -a test2 -e "test@test"
# Add a rule to the existing "samtools.smk" file, the rule name will be "samtools_rule3"
hydra-genetics create-rule -c rule3 -t samtools -m snv -a test2 -e "test@test"

# -t/--tool can be skipped for a single-command tool, e.g. a script
# this will create a smk file named "super_script.smk" with a rule "super_script"
hydra-genetics create-rule -c super_script -m snv -a test2 -e "test@test"

# Create input files
hydra-genetics create-input-files -d path/dir1 -d path/dir2 -p Illumina

# Create singularity cache
# all containers specified in config.yaml will be included
hydra-genetics prepare-environment create-singularity-files -o singularity_cache -c config.yaml
```
