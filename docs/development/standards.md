# Code standards
Here the standards and conventions are defined on how to write rules, configs, and other code in the hydra-genetics framework.

## Documentation
### README
Each module and pipeline should include a README with the following parts:

* Short description
* Github action badges
* Introduction on what the module should be used for
* Dependencies as badges
* Section about input data and reference files
* How to run the test dataset (if possible)
* Rule graph which is contained in images/rulegraph.svg.

### readthedocs
Each module and pipeline are recommended to have a more in depth documentation using [readthedocs](https://readthedocs.org/).

## Snakemake rules

* Rules should be placed in the workflow/rules directory.
* Use only small letters and connect words with underscore (e.g. picard_mark_duplicates).
* Use alphabetical order when applicable.
* For structure, all rules that use the same tool (e.g. picard) should be added to the same rule file named tool.smk. Rule names should be tool name followed by command, for example picard_collect_wgs_metrics.
* Rules that produce new output should place this file in module/rule/ while rules that only modify an output file (bgzip, annotate) should place the file in the input directory under the same name as the input with a descriptive but short suffix module/input_rule/input_file.suffix.
* Input and Output files/directories should get a reasonable tag (specific suffix, e.g. vcf, bam, is preferred), such as:
```
input:
    vcf=”module/input_rule/{sample}.vcf”,
```
* The name of the main output file (e.g. .bam, .vcf) will also be used for naming the log and benchmark files of a rule, only adding .log and .benchmark.tsv in the end, respectively.
* Output files should be marked with the temp() directive in order to save space. Use a rule that copies final results files to a results folder.
* When accessing values in the config object they should be retrieved with the get directive while also setting a sensible default:
```
sorting=config.get("bwa_mem", {}).get("sort", "samtools"),
```
* For all rules, threads and resources (mem_mb, mem_per_cpu, partition, threads, time) should be specified having the default pointing to default_resources in the config object.
```
threads=config.get("bwa_mem", {}).get("threads", config["default_resources"]["threads"]),
```
* Container images are used for execution. Containers should be located at dockerHub and [docker images](https://hub.docker.com/search?q=hydragenetics) provided by hydra-genetics should be used. New containers are added and uploaded via the docker module.
* All rules should contain a message for logging starting with the rule name followed by a colon and a brief description of what is done and on which file.
```
message:
      "{rule}: align fastq files {input.reads} using bwa mem"
```
* Last but not least, the execution needs to be specified which can either be shell, run, script or wrapper. We prefer to use official wrappers if they exist. Otherwise, the command should be specified or a script file referenced. The command should be split in several lines, each starting and ending with quotes, for each new flag. Don’t forget to include logging.

## common.smk
This is a general rule taking care of any actions that are not directly connected with running a specific program.
### Set up
On the top, include a snakemake version check, import of config, resources, tsv-files and respective checks:
```
min_version("6.0.0")

configfile: "config.yaml"

validate(config, schema="../schemas/config.schema.yaml")
config = load_resources(config, config["resources"])
validate(config, schema="../schemas/resources.schema.yaml")

samples = pd.read_table(config["samples"], dtype=str).set_index("sample", drop=False)
validate(samples, schema="../schemas/samples.schema.yaml")

units = pandas.read_table(config["units"], dtype=str).set_index(["sample", "type", "run", "lane"], drop=False).sort_index()
validate(units, schema="../schemas/units.schema.yaml")

wildcard_constraints:
    sample="|".join(samples.index),
    unit="N|T|R",
```
### Functions
The next part should comprise necessary functions used by rules, input or parameters. There are a number of functions available in hydra-genetics/tools which should be used where possible.
### Output
The bottom should be the function compile_output_list which programmatically generates a list of all necessary output files for the module to be targeted in the all rule defined in the `Snakemake` file. See further [Result files](results.md).

## Scripts
* Scripts in python (at least 3.8.0) or R (at 4.0.0) should be placed in the scripts directory.
* Try to keep your names concise and use only lowercase and underscores.
* Scripts should comprise of functions (DRY) which are called in your main function like so:
```python
	if __name__ == "__main__":
		…
```
* Logging is to be included - anything from info to warnings and errors to make troubleshooting easier.
* Unit tests are mandatory, putting them in scriptname_test.py files. Refer to the section unit tests for details.

## Unit tests
Unit tests use the unittest library and should be defined as TestCases. In the class, define your test function.
We are using table-driven testing by exploiting the functionality of dataclasses. All edge cases should be defined in a list of TestCase and subsequently looped through to test the function output and compare it to the expected result:
```python
import unittest
from dataclasses import dataclass
from my_script import my_function

class TestInsertSize(unittest.TestCase):
	def test_my_function(self):
		@dataclass
        	class TestCase:
            		name: str
            		input: str
            		expected: str

        		testcases = [
                		TestCase(
                    			name="Successful test",
                    			input=”input string”,
                    			expected="expected string",
                		),
        		]

        	for case in testcases:
            		actual = my_function(case.input)
            		self.assertEqual(
                		case.expected,
                		actual,
                		"failed test '{}': expected {}, got {}".format(
                    			case.name, case.expected, actual
                		),
            		)
```
## Config
The modules use a `config.yaml` file to tie all file and other dependencies as well as parameters for different rules together.
To make configuration easier, add an example to the config folder. See further [pipeline configuration](config.md).

## `sample.tsv` and `units.tsv`
The files `samples.tsv` and `units.tsv` store all sample meta data needed to run pipelines that uses hydra-genetics.
These can be automatically generated from the `.fastq`-files by the hydra-genetics help tool, see [create sample files](create_sample_files.md).

## Schemas
For `config.yaml`, `resources.yaml` and input tsv-files (`samples.tsv` and `units.tsv`), appropriate schemas should be included in workflow/schemas/.
* Each entry defined should include a type and description.
* Use the *required* keyword for stanzas that are absolutely necessary for the whole module, e.g. resources, samples and units.
* To make configuration easier, add examples to the config folder.
An example schema for the `config.yaml`:
```yaml
$schema: "http://json-schema.org/draft-04/schema#"
description: snakemake configuration file
type: object
properties:
  resources:
    type: string
    description: path to resources.yaml file

  samples:
    type: string
    description: path to samples.tsv file

  units:
    type: string
    description: path to units.tsv file

  default_container:
    type: string
    description: name or path to a default docker/singularity container

  bwa_mem_merge:
    type: object
    description: parameters for merging of bam files, directly after alignment step
    properties:
      benchmark_repeats:
        type: integer
        description: set number of times benchmark should be repeated
      container:
        type: string
        description: name or path to docker/singularity container
      extra:
        type: string
        description: parameters that should be forwarded
```
An example schema for the `unit.tsv`:
```
$schema: "http://json-schema.org/draft-04/schema#"
description: row represents one dataset
properties:
  sample:
    type: string
    description: sample id
  type:
    type: string
    description: type of sample data Tumor, Normal, RNA (N|T|R)
    pattern: "^(N|T|R)$"
  flowcell:
    type: string
    description: flowcell id
  fastq1:
    type: string
    description: absolute path to R1 fastq file
  fastq2:
    type: string
    description: absolute path to R2 fastq file
required:
  - sample
  - type
  - flowcell
  - fastq1
  - fastq2
```

## Github
The following branches are used: main, develop (default), feature, bugfix and release branches. Branches are merged into main and then into main follwoing a new release. Read more about gitflow: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
https://lucamezzalira.com/2014/03/10/git-flow-vs-github-flow/  

* Code contribution should be kept small, be done via pull-request.
* Use commit tags and meaningful commit messages to make it easier for the reviewer to understand the purpose of your contribution. sgc is a nice CLI that will guide you when committing staged changes. You need to get npm or yarn though.
* If possible try to squash commits before doing the first pull-request and reformat the commit messages
* All contributions should be reviewed before being incorporated in the code base, by at least 2 persons for main and 1 for develop.

### Continuous Integration/Actions
To ensure the quality of the code submitted, we include github actions that are automatically run when pull requests are generated or merged into develop/main. These need to finish successfully. These tasks include integration tests (snakemake dry run and run on test data with both conda and singularity), unit tests (pytest) and linting/formatting (snakemake lint, pycodestyle and snakefmt). See further [testing](testing.md).

### Releases
For versioning, we follow the semantic versioning standard: Major.Minor.Patch. Release versioning can be set up automatically by using [release-please](https://github.com/googleapis/release-please).
