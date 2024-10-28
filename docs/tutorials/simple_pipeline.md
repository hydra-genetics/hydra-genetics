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

Local installations:

* Python => 3.8 (with pip and venv) but < 3.10 (otherwise there are compatibility issues with the *core* module of the `click` package)
* Singularity >= 3.8.6 or Apptainer
* graphviz

<hr />

## Setup environment
```bash
python3.8 -m venv hackaton_venv
source hackaton_venv/bin/activate
pip install hydra-genetics==3.0.0
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

Look through the generated files.

### Optional: Add a remote repository

Note the hidden *.git* subdirectory in the `simple-pipeline` directory: with the `hydra-genetics create-pipeline` command, the skeleton pipeline is created with Git version control that is set up, however the pipeline's repository does not have any remote repository defined.
The user may add a remote repository.

<hr />

### Download test data
Download fastq and reference files from [google drive](https://drive.google.com/drive/folders/1PEw05fKo-P-vJHl9y6U0Y82M1s5LdOjb)

```
# gdown need to be installed
pip install gdown

# Download reference data
gdown https://drive.google.com/drive/folders/1lWUAg83k0H3RtEoI6Rr3flCPpFTQ5p57?usp=share_link -O reference --folder

# Download fastq files
gdown https://drive.google.com/drive/folders/1X1tRvHp6bKGESBixD2hpbmIL0CWeaEe2?usp=share_link -O fastq_data --folder
```

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

**Hint**: type `hydra-genetics create-input-files --help` to display all (default) options that are available and figure out what should be added.

Check out the input files created in the directory *simple_pipeline*: `samples.tsv` and `units.tsv`. 

The contents of the file `samples.tsv` should be 
```
sample	tumor_content
HD827sonic-testing1	1.0
HD827sonic-testing2	1.0
HD827sonic-testing3	1.0
```

In the file `units.tsv`, all samples should be of type "T" and sequenced on  Illumina platform.

### Config file for the simple pipeline
Upon creation, the config file for the pipeline is minimalistic as it should suit any pipeline.

The simple pipeline in this tutorial is supposed to trim the fastq files and then output merged and sorted BAM files.
The modules *prealignment* and *alignment* will used for this purpose. The config requirements for these modules are also necessary in the newly created pipeline.
Look at the schemas, example configs, and documentation for *prealignment* and *alignment* to find out what needs to be added in the config (`config/config.yaml`) of *simple-pipeline*. Recall that one should look at the versions of the repositories *prealignment* and *alignment* with the correct tag. 

* `prealignment/config/config.yaml`
* `alignment/config/config.yaml`
* `prealignment/workflow/schemas/config.schemas.yaml`
* `alignment/workflow/schemas/config.schemas.yaml`

Any requirement in `simple-pipeline/workflow/schemas/config.schemas.yaml`  must be met in `simple-pipeline/config/config.yaml` by adding the relevant section.

**Hint**: Furthermore, some configurations that are found in `alignment/config/config.yaml` and in `prealignment/config/config.yaml` are necessary in order to run the simple pipeline, even if those are not specified as "required" in any of the schemas of the 2 modules. These necessary configurations in `config/config.yaml` are specifications for:

- paths to the fasta and fai files used as reference data,
- name of the trimmer software and location of the Docker container with this tool,
- location of the Docker container with the tool bwa-mem as well as the paths to the reference files required by this tool,
- location of the Docker container with the tool Picard.

### Run pipeline
Install required programs (snakemake, …):
```bash
pip install -r requirements.txt
```

<br />

#### Dry run

Make sure workflow can execute using dry-run. Here we specify what output file we expect in the command line and the pipeline is stopped once the file `alignment/samtools_merge_bam/HD827sonic-testing1_T.bam` has been created (partial execution).
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -n \
      --configfile config/config.yaml \
      --until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam
```

<br />

#### (Actual) partial run

Run the pipeline until reads alignment is completed for the sample *HD827sonic-testing1*.
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -c1 \
      --singularity-args "-B path/to/fastq_and_reference_files/" \
      --configfile config/config.yaml \
      --until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam
```

**NB**: if Apptainer is used as local installation instead of Singularity, no binding arguments are needed. Run the following command instead:

```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -c1 \
      --configfile config/config.yaml \
      --until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam
```

<br />

Modify `config/output_files.yaml` so that you don’t have to include “--until alignment/samtools_merge_bam/HD827sonic-testing1_T.bam”  in your shell command, remove the *alignment* folder and (dry-)run the pipeline again.

**NB**: per default in hydra-genetics, all files are set to temporary and deleted upon completion of the pipeline, that in order to keep a clean directory and to avoid memory issues due to too many files. Therefore, the files that the user wants to keep as output must be copied. This can be explicitly specified in `config/output_files.yaml`.

#### Full run

Modify then the input and output paths so that all samples in `samples.tsv` are also processed without hard coding the file path. Run the pipeline again.
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -c1 \
      --singularity-args "-B path/to/fastq_and_reference_files/" \
      --configfile config/config.yaml
```

**Hint**: wildcards can be used in the YAML files if they are defined in the .smk file that uses the YAML file.

**NB**: if Apptainer is used as local installation instead of Singularity, the same remark as previously applies:
```bash
snakemake -s workflow/Snakefile \
      --use-singularity \
      -c1 \
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
When using the hydra-genetics create-pipeline and create-rule readthedocs documentation is already prepared for you. All you need to do is update the schemas. Follow the instruction to view a local copy of your current documentation and then update it.

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
Update the descriptions in the schemas and the software documentation page will update with this new information. (Might need restart of server). Look at `docs/softwares.md` to see the code that generates the documentation.  
Schemas:

* `simple_pipeline/workflow/schemas/rule.schema.yaml` #Description of the rule input and output
* `simple_pipeline/workflow/schemas/config.schema.yaml` #Description of the configurations (params, container, ...)
* `simple_pipeline/workflow/schemas/resources.schema.yaml` #Description of the computer resources (modify if extra resources are needed)
