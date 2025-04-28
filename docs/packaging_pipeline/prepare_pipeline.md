# Preparing a pipeline for packaging

This is a one-time effort in order to make the pipeline compatible with a restricted cluster. Here we use the **Miarka** cluster as an example but can easily be changed to another cluster with some modifications.

## Make reference file configs
These .yaml files are used for reference file download and packaging. Save files under config/references/. Example `config/references/references.hg19.yaml`. Files may be located on the local file system (see padded_regions in the examples below)  or hosted online (see svdb_query in the examples below).

### Examples
File on local cluster
```yaml
padded_regions: # The naming does not really matter, it just makes it easier to manage
  checksum: 1e4a414eac6c0da831afa475d97e9aae
  path: hastings/hg38_exome_comp_spikein_v2.0.2_targets_sorted.re_annotated.sorted_20bp_pad.bed # This should match what is written in the config files after the {{REFERENCE_DATA}}
  type: file
  url: file:/data/ref_data/wp3/hastings/hg38_exome_comp_spikein_v2.0.2_targets_sorted.re_annotated.sorted_20bp_pad.bed
```

File in github repo
```yaml
annotate_cnv:
  cnv_amp_genes:
    path: GMS560/cnv/cnv_amp_genes_240307.bed
    checksum: daa4bd789c9beb84bf1c02e125dd1fd6
    type: file
    url: https://github.com/genomic-medicine-sweden/Twist_Solid_pipeline_files/raw/v0.6.0/cnv/cnv_amp_genes_240307.bed
```

File on web (figshare in this case)
```yaml
svdb_query:
  db_string:
    checksum: 076f3a9bec5e9941eb4bbbf4594c0037
    path: GMS560/PoN/SVDB/all_TN_292_svdb_0.8_20220505.vcf
    type: file
    url: https://figshare.scilifelab.se/ndownloader/files/40882898
```

Compressed file with lots of files

```bash
# use this command to generate md5sums for files in directory and sub-directories
find -type f -exec md5sum '{}' \; > md5sum.txt
```

```yaml
star-fusion:
  genome_path:
    compressed_checksum: 3c747d7a80220e20b15bd2e16ca0a2ed
    path: ref_data/star-fusion
    type: folder
    content_checksum:
      GRCh37_gencode_v19_CTAT_lib_Mar012021.plug-n-play/ctat_genome_lib_build_dir/ref_annot.gtf.gene_spans: 09bf85ad5d2499ed52662ba1f92381c0 # you need the md5sums for all files
      GRCh37_gencode_v19_CTAT_lib_Mar012021.plug-n-play/ctat_genome_lib_build_dir/ref_annot.prot_info.dbm: 196bf70e87eb0c5640bbebc425319e01
    url: https://figshare.scilifelab.se/ndownloader/files/42084318

fusioncatcher:
  genome_path:
    compressed_checksum: 5006482f5b6b78c99e80330d2d69a239
    path: ref_data/fusioncatcher
    type: folder
    url:
      https://figshare.scilifelab.se/ndownloader/files/42061230: 5f4968cf58a28bfe661ee3d1207259c6
      https://figshare.scilifelab.se/ndownloader/files/42061233: ad677c79617e36f85592b45918a10f21
      https://figshare.scilifelab.se/ndownloader/files/42061242: b4a57d1a48b12e3302fa7d12e6ac6347
      https://figshare.scilifelab.se/ndownloader/files/42061248: 1280e3204b6990b825c762ac14e4446a
    content_checksum:
      human_v102/ucsc_genes_header.txt : 9aa055ae6c632068ddc0f4c60ad9c82f
      human_v102/synonyms.txt : dbaea5a7e374e110b4fbb57c2bea3063
      human_v102/exons_header.txt : 5bdb1d9e7484f7f9ac4666545ad41088
      human_v102/shield_against_pseudo-genes.txt : ae05c5a3a1fc94c8d78442e5f539a47d
```

## Modifying configs and profile for a new cluster

### Resource

Make a copy of the resources file and make adapt the new resource file to match the new clusters system setup, ex:
 - partition(s)
 - number of cores
 - memory

```bash
cp config/resource.yaml config/resource.miarka.yaml
```

Miarka has 6144 Mb per core on the CPU nodes so update all memory requirements to match this. 

If GPU is used change partition to **gpu** and memory_per_cpu to 5000 Mb and the gres command to either:

    * --gres=gres:gpu:2       # 2 GPUs on either GPU node
    * --gres=gres:gpu:l40s:2  # 2 GPUs on the node with l40 cards
    * --gres=gres:gpu:a100:2  # 2 GPUs on the node with a100 cards

```yaml
default_resources:
  threads: 1
  time: "12:00:00"
  mem_mb: 6144
  mem_per_cpu: 6144
  partition: "core"

bwa_mem:
  mem_mb: 122880
  mem_per_cpu: 6144
  threads: 8

pbrun_fq2bam:
  gres: "--gres=gres:gpu:l40s:2"
  mem_mb: 240000
  mem_per_cpu: 5000
  partition: "gpu"
  threads: 48
```

### Config files

Make a new config files where all file paths point to the reference directory. Example of new config `config/config.data.hg19.miarka.yaml`.
```yaml
# Add the following line at the top with the actual absolute path (example /proj/ngi2024001/nobackup/bin/wp1_gms560/design_and_ref_files)
REFERENCE_DATA: "<EXTRACT_PATH>/>PIPELINE_SHORT_NAME>/design_and_ref_files"

# Adjust config so that all reference files have the {{REFERENCE_DATA}} variable
# Add potential subfolder so that they match the paths found in the reference yaml files
reference:
  coverage_bed: "{{REFERENCE_DATA}}/hastings/refseq_select_mane_20230828.bed"
  design_bed: "{{REFERENCE_DATA}}/hastings/hg38_exome_comp_spikein_v2.0.2_targets_sorted.re_annotated.sorted.bed"
```

Adjust the main config file to point at the hydra-genetics modules
```yaml
# Add the following line
hydra_local_path: "{EXTRACT_PATH}/{PIPELINE_SHORT_NAME}/{TAG_OR_BRANCH}/hydra-genetics"
```

Add path to local singularities in the main config.yaml file 
```bash
# config/config.yaml
# Build new python environment if needed and install requirements
python3.11 -m venv python_venv/
pip install -r requirements.txt
# Activate python environment if not already active
source python_venv/bin/activate
cp config/config.yaml config/config.yaml.copy
hydra-genetics prepare-environment container-path-update -c config/config.yaml.copy -n config/config.yaml -p ${PATH_TO_apptainer_cache}
```

The path to the apptainer cache can also be given once at the top of the config, much like the REFERENCE_DATA variable.
```
PIPELINE_VERSION: v0.7.0
REFERENCE_DATA: /proj/ngi2024001/nobackup/bin/wp3_te/design_and_ref_files
APPTAINER_CACHE: /proj/ngi2024001/nobackup/bin/wp3_te/{{PIPELINE_VERSION}}/apptainer_cache

hydra_local_path: /proj/ngi2024001/nobackup/bin/wp3_te/{{PIPELINE_VERSION}}/hydra-genetics

default_container: '{{APPTAINER_CACHE}}/hydragenetics__common_1.11.1.sif'

```

### Profile

Make a new profile and adjust it to the computer cluster 
```bash
cp profile/marvin/config.yaml profile/miarka/config.yaml
```

```yaml
# profiles/miarka/config.yaml
# Example
jobs: 100
keep-going: True
restart-times: 1
rerun-incomplete: True
max-jobs-per-second: 100
max-status-checks-per-second: 100
use-singularity: True
drmaa: "-p {resources.partition} -t {resources.time} -n {resources.threads} --mem={resources.mem_mb} --mem-per-cpu={resources.mem_per_cpu} {resources.gres} -J {rule} -A ngi2024001 -e slurm/{rule}_%j.err -o slurm/{rule}_%j.out --nodes=1-1"
default-resources: [gres="", ]
drmaa-log-dir: "slurm"
singularity-args: "-e --cleanenv -B /proj -B $HOME --nv"
singularity-prefix: "/proj/ngi2024001/nobackup/bin/<PIPELINE_SHORT_NAME>/<TAG_OR_BRANCH>/apptainer_cache/"
wrapper-prefix: "git+file://proj/ngi2024001/bin/<PIPELINE_SHORT_NAME>/<TAG_OR_BRANCH>/snakemake-wrappers/"
```

## Modify Snakemake module import
To be able to use a local git file module imports must use the `get_module_snakefile()` function (instead of `github()`).

```py
module alignment:
    snakefile:
        get_module_snakefile( # Modify this line for all module imports
            config,
            "hydra-genetics/alignment",
            path="workflow/Snakefile",
            tag=config["modules"]["alignment"],
        )
    config:
        config
```

## Modify common.smk
Add these line in `rules/common.smk`:

```py
from hydra_genetics.utils.misc import get_module_snakefile # Needed for local git
from hydra_genetics.utils.misc import replace_dict_variables # Used by hydra genetics to obtain the file paths to the files in the config

config = replace_dict_variables(config) # Add this after the imports
```

## Add build script to pipeline

Add the build script `build/build_conda.sh` found in `https://github.com/hydra-genetics/hydra-genetics` to the pipeline. This can be placed in a subdirectory of your pipeline call build
