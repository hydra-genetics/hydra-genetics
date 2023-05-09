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

<hr />

## Pre-requirements:

* Python => 3.8 (with pip and venv)
* Singularity >= 3.8.6
* graphviz

<hr />

## Download test data
Download fastq and reference files from [google drive](https://drive.google.com/drive/folders/1PEw05fKo-P-vJHl9y6U0Y82M1s5LdOjb)

```
# gdown need to be installed
pip install gdown

# Download reference data
gdown https://drive.google.com/drive/folders/1lWUAg83k0H3RtEoI6Rr3flCPpFTQ5p57?usp=share_link -O reference_data --folder 

# Download fastq files
gdown https://drive.google.com/drive/folders/1X1tRvHp6bKGESBixD2hpbmIL0CWeaEe2?usp=share_link -O fastq_data --folder 
```

<hr />

## Setup environment
```bash
python3 -m venv hackaton_venv
source hackaton_venv/bin/activate
pip install hydra-genetics==1.2.0
```

<hr />

## Create pipeline

### Create skeleton pipeline
```bash
hydra-genetics create-pipeline \
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
The below command will not find anything due to how the files are named. First, try the command and the try to modify it by adding --read-number-regex "modified_regex" to match the file names.  
```bash
hydra-genetics create-input-files \
   -d path/to/fastq/ \
   --every 2 \
   --nreads 10
```

Check out the input files created: `samples.tsv` and `units.tsv`.

### Config pipeline
The pipeline is supposed to trim the fastq files and then output merged and sorted bamfiles.  
Look at the schemas, example configs and documentation for prealignment and alignment to find out what is required to be added in the config (`config/config.yaml`).

* `prealignment/config/config.yaml`
* `alignment/config/config.yaml`
* `prealignment/workflow/schemas/config.schemas.yaml`
* `alignment/workflow/schemas/config.schemas.yaml`

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
      --singularity-args "-B path/to/fastq_and_reference_files/"
      --configfile config/config.yaml \
      --until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam
```
<br />
Modify workflow/rules/common.smk so that you don’t have to include “--until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam”  in your shell command and also so that all samples in samples.tsv are run without hard coding the file path. Run again.
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -c1 \
      --singularity-args "-B path/to/fastq_and_reference_files/"
      --configfile config/config.yaml
```

### Make a rulegraph
Make a rulegraph of your pipeline, look at the figure and enjoy your success!
```bash
snakemake -s workflow/Snakefile --configfile config/config.yaml --until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam --rulegraph | dot -Tsvg > images/rulegraph.svg
```

<hr />

## Code testing
Before making a pull-request to a hydra-genetics module or pipeline it is recommended to run a number of tests locally.  
Install test programs:
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

<hr />

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
      --singularity-args "-B path/to/fastq_and_reference_files/"
      --configfile config/config.yaml
```

<hr />

## Add documentation
When using the hydra-genetics create-pipeline and create-rule readthedocs documentation is already prepared for you. All you need to do is update the schemas. Follow the instruction to view a local copy of your corrent documentation and then update it.

### Install local mkdocs server and plugins
```bash
pip install -r docs/requirements.txt
```

### Start server
```bash
mkdocs serve
```

### View documentation in browser
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Update schemas
Update the descriptions in the schemas and the software documetantion page will update with this new information. (Might need restart of server). Look at `docs/softwares.md` to see the code that generates the documentation.  
Schemas:

* `simple_pipeline/workflow/schemas/rule.schema.yaml` #Description of the rule input and output
* `simple_pipeline/workflow/schemas/config.schema.yaml` #Description of the configurations (params, container, ...)
* `simple_pipeline/workflow/schemas/resources.schema.yaml` #Description of the computer resources (modify if extra resources are needed)
