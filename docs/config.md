# Pipeline configuration (`config.yaml`, `resources.yaml`)
Configuration of the pipeline is set up in the `config.yaml` file. Both general settings and rule specific settings are set here.
The `config.yaml` can also point to other config-files, such as a config for reasources `resources.yaml`.
## Basic setup
Basic setup for `config.yaml`:
```
resources: "config/resources.yaml"                          # resources parameters
samples: "samples.tsv"                                      # sample names
units: "units.tsv"                                          # sample file and meta info
output: "config/output_list.json"                           # rule all files (optional)
default_container: "docker://hydragenetics/common:0.1.9"    # default container
reference:                                                  # list of general references
  fasta: “reference_genome.fasta”
```
Basic setup for the `resources.yaml` for default resource usage:
```
default_resources:
  mem_mb: 6144        # total max memory
  mem_per_cpu: 6144   # memory per thread
  partition: "core"   # partition to us on the cluster (optional)
  threads: 1          # threads
  time: "4:00:00"     # wall time
```
## Rule parameters
Rules with configurable parameters can be set in `config.yaml` in the following way:
```
cnvkit_batch:
  container: "docker://hydragenetics/cnvkit:0.9.9"  # container
  normal_reference: "cnvkit_panel_of_normal.cnn"    # reference file
  method: "hybrid"                                  # program parameter
```
Rules with extra resource demands can be set in `resources.yaml` in the following way:
```
arriba:
  mem_mb: 30720
  mem_per_cpu: 6144
  threads: 5
  time: "8:00:00"
```
