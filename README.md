<p align="center">
<a href="https://hydra-genetics.readthedocs.io">https://hydra-genetics.readthedocs.io</a>
</p>

# <img src="images/hydragenetics.png" width=40 /> Hydra-genetics

Command line interface to create new modules/pipelines or adding a new rule to an existing project. Provides libraries used to make it easier for people not used to pandas to extract information from samples and units dataframes. These dataframes are generated from [units.tsv](https://github.com/hydra-genetics/tools/blob/develop/hydra_genetics/pipeline-template/workflow/schemas/units.schema.yaml) and [samples.tsv](https://github.com/hydra-genetics/prealignment/blob/develop/workflow/schemas/samples.schema.yaml) files which are used as input.

[![Lint and Test](https://github.com/hydra-genetics/tools/actions/workflows/main.yaml/badge.svg?branch=develop)](https://github.com/hydra-genetics/tools/actions/workflows/main.yaml)

![python](https://img.shields.io/badge/python-3.8-blue)

## Functions

* create
* reference


Example of how to generate a new project
```
 virtualenv -p python3.9 venv
 source venv/bin/activate
 pip install hydra-genetics
 hydra-genetics create-module -n snv -d "Collection of callers" -a "Patrik S" -e "p.s@mail.se" -g patrik -o snv
 # Create new smk file named "samtools.smk" with rule "samtools_rule2"
 hydra-genetics create-rule -c rule2 -t samtools -m snv -a test2 -e "test@test"
 # Add command to "samtools smk" file, rule name will be "samtools_rule3"
 hydra-genetics create-rule -c rule3 -t samtools -m snv -a test2 -e "test@test"

 # -t/--tool can be skipped for a single command tool, ex a script
 # this will create a smk file named "super_script.smk" with a rule "super_script"
 hydra-genetics create-rule -c rule3 -t samtools -m snv -a test2 -e "test@test"

 # Create input files
 hydra-genetics create-input-files -d path/dir1 -d path/dir2

 # Create singularity cache
 # all container specified in config.yaml will be fetched
 hydra-genetics singularity create-singularity-files  -o singularity_cache -c config.yaml

```
