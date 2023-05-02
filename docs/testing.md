# Testing

## Current tests
- [pycodestyle](https://pycodestyle.pycqa.org/en/latest/): (--max-line-length 130)
- [snakefmt](https://github.com/snakemake/snakefmt): (line-length 130)
- [snakemake](https://snakemake.readthedocs.io/en/stable/executing/cli.html?highlight=lint#UTILITIES) --lint: (line-length 130)
- [snakemake dry-run](https://snakemake.readthedocs.io/en/stable/executing/cli.html#useful-command-line-arguments)
- execution test with small dataset
- integration test with complete dataset after merging to develop or main on some modules which also tests compatibility between dependent modules.

The small execution tests will make sure that the pipeline actually can be executed, i.e run and generate data. The integration test with complete data set will also evaluate the generated result to make sure that results does not change, if it's not deliberately.

## Small integration test
* A small (KB to a few MB if necessary) dataset for testing is to be included and placed under .tests/integration/.
* Original input should be contained in the input directory while references, such as fasta-files or databases, should go into reference. If output from previous modules is necessary, the path structure of these files should be adapted.
* For configuration, add an appropriate config.yaml, resources.yaml as well as tsv-files.
* If the module offers different routes, include configuration for each of them.
* To avoid committing output from the test runs, add output file patterns to your .gitignore:
```
.snakemake
*.log
*.benchmark.tsv
```

## Testing locally
To avoid failing actions, try to check the different testing regimes locally on your machine:
```bash
python3.9 -m venv ~/path/venv/
source ~/path/venv/bin/activate
pip install -r requirements.test.txt
pip install -r requirements.txt
snakefmt --compact-diff
pycodestyle --max-line-length=130 --statistics workflow/scripts
python -m pytest workflow/scripts/python_script_test.py
cd .tests/integration
snakemake --lint -s ../../workflow/Snakefile
snakemake -n -s ../../workflow/Snakefile
snakemake -s ../../workflow/Snakefile -j 1 --use-singularity
```
