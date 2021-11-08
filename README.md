
# Tools

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
 hydra-genetics create-rule -n rule2 -m snv -a test2 -e "test@test"
```
