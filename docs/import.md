# Importing (`Snakemake`)
Importing modules and rules into the pipeline is done in the `Snakemake` file.  
## Importing pipeline specific rules
```
include: "rules/common.smk"
```
## Rule all
The **rule all** in the `Snakemake` file specifies the output files of the pipeline and should preferably be a function
defined in `common.smk`.
```
rule all:
    input:
        unpack(compile_output_list),
```
## Importing modules
The alignment module and all its rules is imported using the following command:
```
module alignment:
    snakefile:
        github(
            "hydra-genetics/alignment", # module
            path="workflow/Snakefile",  # path to the Snakefile
            tag="v0.1.0",               # release version to use, can also be github tag
        )
    config:
        config                          # forward the config file of the module (see Snakemake documentation)


use rule * from alignment as alignment_*
```
## Importing specific rules
Instead of importing all rule it is possible to only import specific rules:
```
use rule bwa_mem from alignment as alignment_bwa_mem
```
## Modifying imported rules
Sometimes it is necessary to modify the parts of the rule imported from hydra-genetics.
Here the input part of the rule is changed:
```
use rule picard_mark_duplicates from alignment as alignment_picard_mark_duplicates with:
  input:
    "alignment/samtools_merge_bam/{sample}_{type}_{chr}.bam",
```
It is also possible to modify wildcard constraints that is set in the module:
```
use rule picard_mark_duplicates from alignment as alignment_picard_mark_duplicates with:
  wildcard_constraints:
    type="T|N",
```
## Rule orders
When two rules imported from different modules have the same input it is not possible for Snakemake to
decide on which rule to use. This is solved by using rule orders in the `Snakemake` file.
```
ruleorder: snv_indels_bgzip > misc_bgzip
```
