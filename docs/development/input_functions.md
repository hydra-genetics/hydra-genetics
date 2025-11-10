# Input functions

Hydra Genetics contains helper functions to compile paths to BAM files depending on your pipeline configuration. These paths are used  by rules in other Hydra Genetics modules that require an aligned BAM file as input.

The functions are located in `hydra_genetics/utils/misc.py`.


## Aligned BAM files

Function `get_input_aligned_bam` compiles paths to aligned BAM files and their corresponding BAI index files based on workflow configuration. 

### Parameters

 - **wildcards**: A Snakemake Wildcards object that contains sample and type. These are used to construct file names.
 - **config**: A dictionary containing workflow configuration options. It may include:
   - **aligner**: Specifies which aligner was used (e.g., `minimap2`, `pbmm2`, etc.). If this is set, the function will construct path using these tools names.
- **default_path** (optional): A fallback directory path used when no aligner is specified. Defaults to `"alignment/samtools_merge_bam"`, which is equivalent to choosing bwa as the aligner

### How it works

1. **Aligner specified**: If the config dictionary includes an aligner, the function assumes you're working with long-read data and constructs the correct BAM and BAI paths using this aligner in the path.

2. **No aligner specified**: If no aligner is defined, the function constructs the file paths using the `default_path` and the `wildcards.sample` and `wildcards.type` values.

#### Returns

A tuple containing:

 - The full path to the BAM file
 - The full path to the corresponding BAI index file

#### Example: no aligner

```
wildcards = types.SimpleNamespace(sample="sample1", type="rna")
config = {}

bam_path, bai_path = get_input_aligned_bam(wildcards, config)

# Returns:
(
    "alignment/samtools_merge_bam/sample1_rna.bam",
    "alignment/samtools_merge_bam/sample1_rna.bam.bai"
)
```

#### Example: with aligner

```
wildcards = types.SimpleNamespace(sample="sample1", type="rna")
config = {"aligner": "pbmm2"}

bam_path, bai_path = get_input_aligned_bam(wildcards, config)

# Returns
(
    "alignment/pbmm2/sample1_rna.bam",
    "alignment/pbmm2/sample1_rna.bam.bai"
)
```

## Haplotagged BAM files

Function `get_input_haplotagged_bam` constructs the file paths for haplotagged BAM and BAI index files, which may be required for downstream analyses (e.g., with `cnvkit_batch`). It supports flexible configuration and backward compatibility.

### Parameters

 - **wildcards**: A Snakemake Wildcards object that contains sample and type. These are used to construct file names.
 - **config**: A dictionary containing workflow configuration options. It may include:
   - **haplotag_path**: custom path to haplotagged BAMs
   - **haplotag_suffix**: optional suffix for filenames, if not provided no suffix is used.
 - **default_path**: A path used if `haplotag_path` is not provided. Defaults to `"alignment/samtools_merge_bam"`.
 - **suffix**: Optional suffix to append to the BAM filename. Default is `None`.

### How it works

1. **Wildcard Extraction**: Retrieves sample and type from the wildcards object. If missing, raises a `WorkflowError`.

2. **Path Resolution**: Uses `haplotag_path` from config if available. Falls back to `default_path` if not.

3. **Suffix Handling**: If suffix is provided as an argument, it is used. Otherwise, the function checks for `haplotag_suffix` in config, if it not specified, no suffix is used.

4. **Filename Construction**: With suffix: `sample_type.suffix.bam`; Without suffix: `sample_type.bam`

5. **Returns**: A tuple of:
   - Full path to the BAM file
   - Full path to the corresponding BAI index file

### Examples

1. No suffix, default path
```
wildcards = types.SimpleNamespace(sample="sample1", type="rna")
config = {}

bam_path, bai_path = get_input_haplotagged_bam(wildcards, config)

# Returns
(
    "alignment/samtools_merge_bam/sample1_rna.bam",
    "alignment/samtools_merge_bam/sample1_rna.bam.bai"
)
```

2. Suffix from config, default path
```
wildcards = types.SimpleNamespace(sample="sample1", type="rna")
config = {"haplotag_suffix": "haplotagged"}

bam_path, bai_path = get_input_haplotagged_bam(wildcards, config)

# Returns
(
    "alignment/samtools_merge_bam/sample1_rna.haplotagged.bam",
    "alignment/samtools_merge_bam/sample1_rna.haplotagged.bam.bai"
)
```

3. No suffix, custom path
```
wildcards = types.SimpleNamespace(sample="sample1", type="rna")
config = {"haplotag_path": "custom/path"}

bam_path, bai_path = get_input_haplotagged_bam(wildcards, config)

# Returns
(
    "custom/path/sample1_rna.bam",
    "custom/path/sample1_rna.bam.bai"
)
```

## List of valid aligners

- **pbmm2**

- **minimap2**

Leaving aligner **blank** is equivalent to choosing duplicate marked bwa bam file
