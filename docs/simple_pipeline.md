# Tutorial
This tutorial will guide you through making a pipeline that trim and then align fastq files. You will learn how to:

* Create a new hydra-genetics pipeline
* Add hydra-genetics modules
* Create input files based on the test data
* Configure the pipeline
* Run the pipeline
* Make a rulegraph of the pipeline
* Do code testing
* Add your own rule

## Pre-requirements:

* Python => 3.8 (with pip and venv)
* Singularity >= 3.8.6
* graphviz

## Download test data
Download fastq and reference files from [google drive](https://drive.google.com/drive/folders/1PEw05fKo-P-vJHl9y6U0Y82M1s5LdOjb)

## Setup environment
```bash
python3 -m venv hackaton_venv
source hackaton_venv/bin/activate
pip install hydra-genetics==1.0.0
```

## Create pipeline

### Create skeleton pipeline
```bash
hydra-genetics create-module \
    --name simple_pipeline \
    --description "A simple pipeline" \
    --author "Patrik Smeds" \
    --email patrik.smeds@scilifelab.uu.se \
    --git-user smeds
cd simple_pipeline
```

Look through the generated files

### Add hydra-genetics modules
Add the [prealignment module](https://github.com/hydra-genetics/prealignment) to `workflow/Snakefile` (use tag=”v1.1.0”). See instructions in the module README.  
Add the [alignment module](https://github.com/hydra-genetics/alignment) to `workflow/Snakefile` (use tag=”v0.4.0”). See instructions in the module README.  

### Create input files
```bash
hydra-genetics create-input-files \
   -d path/to/fastq/ \
   --every 2 \
   --nreads 10
```

The above command will not find anything due to how the files are named, try to modify --read-number-regex to match the file names.  
Check out the input files created: `samples.tsv` and `units.tsv`.

### Config pipeline
The pipeline is supposed to trim the fastq files and then output merged and sorted bamfiles.  
Look at the schemas, example configs and documentation for prealignment and alignment to find out what is required to be added in the config (`config/config.yaml`).

* `prealignment/workflow/schemas/config.schemas.yaml`
* `alignment/workflow/schemas/config.schemas.yaml`
* `prealignment/config/config.yaml`
* `alignment/config/config.yaml`

### Run pipeline
Install required programs (snakemake, …):
```bash
pip install -r requirements.txt
```

<br />
Make sure workflow can execute using dry-run. Here we specify what output file we expect in the command line.
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -n \
      --configfile config/config.yaml \
      --until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam
```
<br />
Run pipeline
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -c1 \
      --configfile config/config.yaml \
      --until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam
```
<br />
Modify workflow/rules/common.smk so that you don’t have to include “--until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam”  in your shell command and also so that all samples in samples.tsv are run without hard coding the file path. Run again.
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -c1 \
      --configfile config/config.yaml
```

### Make a rulegraph
Make a rulegraph of your pipeline, look at the figure and enjoy your success!
```bash
snakemake -s workflow/Snakefile --configfile config/config.yaml --rulegraph | dot -Tsvg > images/rulegraph.svg
```

### Code testing
Before making a pull-request to a hydra-genetics module or pipeline it is recommended to run a number of tests locally.  
Install test programs
```bash
pip install -r requirements.test.txt
```
<br />
Check syntax of snakemake rules
```bash
snakefmt --compact-diff -l 130 workflow/
```
<br />
Check syntax of python scripts
```bash
pycodestyle --max-line-length=130 --statistics workflow/scripts/
```
<br />
Run pytest for scripts with implemented tests
```bash
python -m pytest workflow/scripts/test_dummy.py
```
<br />
Run linting of the pipeline
```bash
snakemake --lint -s workflow/Snakefile --configfile config/config.yaml
```
<br />

## Add a rule
In this step we will add a new rule to the pipeline. The new rule should use a program of your choice from [picard](https://broadinstitute.github.io/picard/).  

### Create new rule template
```bash
hydra-genetics create-rule \
    --module simple_pipeline \
    --tool picard \
    --command program_name \
    --author "Patrik Smeds" \
    --email patrik.smeds@scilifelab.uu.se
```

### Modify rule
Modify ´simple_pipeline/workflow/rules/picard.smk´ so that the rule does what you what it to do.

### Update pipeline
Update the pipeline to use the new rule.  
The following files need to be modified:

* `simple_pipeline/workflow/rules/common.smk` #Add new output
* `simple_pipeline/workflow/Snakefile` #Check that the new rule is imported
* `simple_pipeline/config/config.yaml` #Check that the new rule with container and other options are added. Add more stuff if needed

### Run pipeline
Run the pipeline to generate the new output files.
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -c1 \
      --configfile config/config.yaml
```
