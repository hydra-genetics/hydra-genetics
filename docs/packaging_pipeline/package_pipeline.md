# Pipeline packaging

Some system doesn't allow access to internet making it impossible to have a pipeline that are dependent on resource hosted on web, like docker hub and github. This is solved by packing the pipeline and all dependencies.

## On local computer or unrestricted cluster
Do these instructions on your local computer or a cluster with internet access.

## Package pipeline

Use a build script that will package all files needed to run the pipeline:

 * Environment
 * Github repositories (Pipeline, hydra-genetics modules, Snakemake-wrappers)
 * Singularities / Apptainers

### Preparations

Requires:

 - conda
 - conda-pack

```bash
# On Marvin conda can be loaded by 
module load miniconda3
```

### Package and download all files with the build script
Set pipeline version and pipeline name which must match version and name found on github
List all reference config files that should be used as arguments to the build script


```bash
# Example: TAG_OR_BRANCH="v0.18.3" PIPELINE_NAME="Twist_Solid" bash build/build_conda.sh config/references/design_files.hg19.yaml -v config/references/novaseq.hg19.pon.yaml -v config/references/references.hg19.yaml
TAG_OR_BRANCH="vX.Y.X" PIPELINE_NAME="Your_pipeline_name" bash build/build_conda.sh config/references/<file1>.yaml config/references/<file2>.yaml
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
rsync -Pav design_and_ref_files.tar.gz ${USER}@miarka1.uppmax.uu.se:/proj/ngi2024001/bin/${PIPELINE_SHORT_NAME}/
rsync -Pav ${PIPELINE_NAME}_${TAG_OR_BRANCH}.tar.gz apptainer_cache ${USER}@miarka1.uppmax.uu.se:/proj/ngi2024001/bin/${PIPELINE_SHORT_NAME}/${TAG_OR_BRANCH}/
```
