
# Tools

Python tool with helper functions for setting up new pipeline and preparing reference data

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
