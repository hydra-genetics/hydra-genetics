# Python environment
To run and test pipelines and modules created using hydra-genetics a python virtual environment is needed.
## Create python environment
Create a new [python environment](https://docs.python.org/3/library/venv.html):
```
python3 -m venv /path/to/new/virtual/environment
```
## Install hydra-genetics
Activate the virtual environment and install hydra-genetics tools and other requirements.
The `requirements.txt` should be located directly in the module or pipeline folder, see .
```
cd hydra-genetics_module
source /path/to/new/virtual/environment/bin/activate
pip install -r requirements.txt
pip install hydra_genetics
```
## Install tests
```
pip install -r requirements.test.txt
```
