# Pipeline packaging

Some systems don't allow access to internet making it impossible to use a pipeline that is dependent on resources hosted on the web, like docker hub and github. This is solved by packing the pipeline and all its dependencies.

## Package pipeline

### On local computer or unrestricted cluster
The following instructions on packaging the pipeline for an offline environment should be performed on your local computer or a cluster with internet access.

Use a build script that will package all files needed to run the pipeline:

 * The virtual environment
 * Github repositories (Pipeline, hydra-genetics modules, Snakemake-wrappers)
 * Singularities / Apptainers

### Preparations

Requires:

 - [conda](https://www.anaconda.com/docs/getting-started/miniconda/main)
 - [conda-pack](https://conda.github.io/conda-pack/)

```bash
# On Marvin conda can be loaded by
module load miniconda3
```

### Package and download all files with the build script
Set pipeline version and pipeline name which must match an existing version and name found on github
List all reference config files that should be used as arguments to the build script


```bash
# Example: TAG_OR_BRANCH="v0.18.3" PIPELINE_NAME="Twist_Solid" PIPELINE_GITHUB_REPO="https://github.com/genomic-medicine-sweden/Twist_Solid.git" bash build/build_conda.sh config/references/design_files.hg19.yaml -v config/references/novaseq.hg19.pon.yaml -v config/references/references.hg19.yaml
TAG_OR_BRANCH="vX.Y.X" PIPELINE_NAME="Your_pipeline_name" PIPELINE_GITHUB_REPO="pipeline_github_repo.git" bash build/build_conda.sh config/references/<file1>.yaml config/references/<file2>.yaml
```

## Resulting files and folders
The following files and folders have been created and need to be moved to your server:

1. file: design_and_ref_files.tar.gz
2. file: {PIPELINE_NAME}_{TAG_OR_BRANCH}.tar.gz
3. folder: singularity_cache 


## Copy pipeline package files

Copy the pipeline packaged files to the compute cluster.

```bash
# Miarka
rsync -Pav design_and_ref_files.tar.gz <USER>@<cluster>:<basepath>/${PIPELINE_SHORT_NAME}/
rsync -Pav ${PIPELINE_NAME}_${TAG_OR_BRANCH}.tar.gz apptainer_cache <USER>@<cluster>:<basepath>/${PIPELINE_SHORT_NAME}/${TAG_OR_BRANCH}/
```
