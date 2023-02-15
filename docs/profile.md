# Cluster profile
A profile contains cluster specific settings like which job scheduler is used and Snakemake settings for running the pipeline.
Below is an example profile for Snakemake run on a cluster with slurm, drmaa, and singularities. For more option see the [Snakemake](https://snakemake.readthedocs.io/en/stable/executing/cli.html) documentation.
```yaml
jobs: 100                                             # Max number of jobs running and in queue
keep-going: True                                      # When error, keep running jobs that are independent of this error
restart-times: 2                                      # When error, try to rerun twice
rerun-incomplete: True                                # When rerunning, automatically rerun incomplete jobs
use-singularity: True                                 # Run using singularity containers
configfile: "config/config.yaml"                      # Path to config file
singularity-args: "--cleanenv -B /data"               # Singularity arguments
singularity-prefix: "/data/singularity_cache/"        # Singularity cache
drmaa: " -t {resources.time} -n {resources.threads} --mem={resources.mem_mb} --mem-per-cpu={resources.mem_per_cpu} --mem-per-cpu={resources.mem_per_cpu} --partition={resources.partition} -J {rule} -e slurm_out/{rule}_%j.err -o slurm_out/{rule}_%j.out" # drmaa options
drmaa-log-dir: "slurm_out"                            # Directory for slurm output log files
default-resources: [threads=1, time="04:00:00", partition="low", mem_mb="3074", mem_per_cpu="3074"] # Default resources, overwritten by default values in resourses.yaml
```
To run a pipeline with a profile just specify the profile like this:
```bash
snakemake --profile profiles/
```
