# <img src="images/hydragenetics.png" width=40 /> hydra-genetics/{{ short_name }}

#### {{ description }}

![Lint](https://github.com/hydra-genetics/{{ short_name }}/actions/workflows/lint.yaml/badge.svg?branch=develop)
![Snakefmt](https://github.com/hydra-genetics/{{ short_name }}/actions/workflows/snakefmt.yaml/badge.svg?branch=develop)
![snakemake dry run](https://github.com/hydra-genetics/{{ short_name }}/actions/workflows/snakemake-dry-run.yaml/badge.svg?branch=develop)
![integration test](https://github.com/hydra-genetics/{{ short_name }}/actions/workflows/integration.yaml/badge.svg?branch=develop)

![pycodestyle](https://github.com/hydra-genetics/{{ short_name }}/actions/workflows/pycodestyle.yaml/badge.svg?branch=develop)
![pytest](https://github.com/hydra-genetics/{{ short_name }}/actions/workflows/pytest.yaml/badge.svg?branch=develop)

[![License: GPL-3](https://img.shields.io/badge/License-GPL3-yellow.svg)](https://opensource.org/licenses/gpl-3.0.html)

## :speech_balloon: Introduction

The module consists of alignment  ....

## :heavy_exclamation_mark: Dependencies

In order to use this module, the following dependencies are required:

[![hydra-genetics](https://img.shields.io/badge/hydragenetics-v1.3.0-blue)](https://github.com/hydra-genetics/)
[![pandas](https://img.shields.io/badge/pandas-1.3.1-blue)](https://pandas.pydata.org/)
[![python](https://img.shields.io/badge/python-3.8-blue)
[![snakemake](https://img.shields.io/badge/snakemake-{{ min_snakemake_version }}-blue)](https://snakemake.readthedocs.io/en/stable/)
[![singularity](https://img.shields.io/badge/singularity-3.0.0-blue)](https://sylabs.io/docs/)

## :school_satchel: Preparations

### Sample data

Input data should be added to [`samples.tsv`](https://github.com/hydra-genetics/{{ short_name }}/blob/develop/config/samples.tsv)
and [`units.tsv`](https://github.com/hydra-genetics/{{ short_name }}/blob/develop/config/units.tsv).
The following information need to be added to these files:

| Column Id | Description |
| --- | --- |
| **`samples.tsv`** |
| sample | unique sample/patient id, one per row |
| **`units.tsv`** |
| sample | same sample/patient id as in `samples.tsv` |
| type | data type identifier (one letter), can be one of **T**umor, **N**ormal, **R**NA |
| platform | type of sequencing platform, e.g. `NovaSeq` |
| machine | specific machine id, e.g. NovaSeq instruments have `@Axxxxx` |
| flowcell | identifer of flowcell used |
| lane | flowcell lane number |
| barcode | sequence library barcode/index, connect forward and reverse indices by `+`, e.g. `ATGC+ATGC` |
| fastq1/2 | absolute path to forward and reverse reads |
| adapter | adapter sequences to be trimmed, separated by comma |

## :white_check_mark: Testing

The workflow repository contains a small test dataset `.tests/integration` which can be run like so:

```bash
$ cd .tests/integration
$ snakemake -s ../../Snakefile --configfiles ../../config/config.yaml config/config.yaml -j1 --use-singularity
```
`../../config/config.yaml` is the original config-file, while `config/config.yaml` is the test config. By defining two config-files the latter overwrites any overlapping variables in the first config-file.
## :rocket: Usage

To use this module in your workflow, follow the description in the
[snakemake docs](https://snakemake.readthedocs.io/en/stable/snakefiles/modularization.html#modules).
Add the module to your `Snakefile` like so:

```bash
module prealignment:
    snakefile:
        github(
            "{{ short_name }}",
            path="workflow/Snakefile",
            tag="1.0.0",
        )
    config:
        config


use rule * from {{ short_name }} as {{ short_name }}_*
```

### Output files

The following output files should be targeted via another rule:

| File | Description |
|---|---|
| `{{ short_name }}/PATH/FILE` | DESCRIPTION |

## :judge: Rule Graph
![rule_graph_reference](images/rulegraph.svg)