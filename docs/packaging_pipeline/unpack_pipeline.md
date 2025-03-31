# On computer cluster

## Preparations
```bash
# Prepare variables in terminal
TAG_OR_BRANCH="vX.Y.Z" # eg TAG_OR_BRANCH="v0.18.3"
PIPELINE_NAME="Your_pipeline_name" # eg PIPELINE_NAME="Twist_Solid"
PIPELINE_SHORT_NAME="wpX_name" # wg PIPELINE_SHORT_NAME="wp1_gms560"
USER="username_on_remote_cluster"
```

## Uncompress files

Extract environment and repositories

```bash
# Miarka
cd /proj/ngi2024001/bin/${PIPELINE_SHORT_NAME}/${TAG_OR_BRANCH}/
tar -strip-components=1 -zxvf ${PIPELINE_NAME}_${TAG_OR_BRANCH}.tar.gz
mkdir venv && tar zxvf env.tar.gz -C venv/
source venv/bin/activate
```

Decompress reference files

```bash
# Miarka
cd /proj/ngi2024001/bin/${PIPELINE_SHORT_NAME}/
mkdir new_design_and_ref_files
tar -xvf design_and_ref_files.tar.gz -C new_design_and_ref_files
rsync -Pav new_design_and_ref_files/ design_and_ref_files/
```

## Validate reference files

Validate that all design and reference files exists and haven't changed

**OBS! Warnings for possible file PATH/hydra-genetics and missing tbi files in config can be ignored**

```bash
# Twist solid example for Miarka
hydra-genetics --debug references validate -c config/config.yaml -c config/config.data.hg19.yaml -v config/references/design_files.hg19.yaml -v config/references/nextseq.hg19.pon.yaml -v config/references/references.hg19.yaml -p /proj/ngi2024001/bin/${PIPELINE_SHORT_NAME}/
```

## Final adjustments of profile and start-scripts
* Set correct paths in the profile for singularity-prefix and wrapper-prefix if not already done.
* Update start-script to use the correct profile


## Run Pipeline

Run the pipeline as usual but with updated profile or updated start script.