# Installation
The hydra-genetics tools are distributed as the python package `hydra-genetics`. They are needed to create pipelines,
modules and rules, to create the sample files, and to run and test pipelines and modules created using hydra-genetics.
The package requires Python 3.8 or newer.

## Install hydra-genetics
### Using a virtual environment and pip
Create a new [python environment](https://docs.python.org/3/library/venv.html), activate it and install the package:
```bash
python3 -m venv /path/to/new/virtual/environment
source /path/to/new/virtual/environment/bin/activate
pip install hydra-genetics
```

### Using pixi
```bash
pixi init
pixi add --pypi hydra-genetics
pixi add --pypi "setuptools<81"
```
Note that `setuptools<81` is needed for all imports to work. The tools can then be run with `pixi run`, for example
`pixi run hydra-genetics --help`, or from a shell started with `pixi shell`.

To check the installation, run:
```bash
hydra-genetics --help
```

## Module and pipeline requirements
A module or pipeline created using hydra-genetics has a `requirements.txt` file, with the dependencies needed to run it,
and a `requirements.test.txt` file, with the dependencies needed to test it, located directly in its root folder.
Activate the virtual environment and install them using pip:
```bash
cd hydra-genetics_module
source /path/to/new/virtual/environment/bin/activate
pip install -r requirements.txt
pip install -r requirements.test.txt
```
`pixi init --import` requires an `environment.yml` file to set up the workspace. Such a file is not provided for
modules and pipelines (yet), so the dependencies can be installed one by one via `pixi add`.
