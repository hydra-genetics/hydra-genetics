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

The function uses the `ALIGNER_PATHS` dictionary to map aligner names to their output directory paths. This dictionary contains predefined paths for common aligners:

```python
ALIGNER_PATHS = {
    "minimap2": "alignment/minimap2_align",
    "pbmm2": "alignment/pbmm2_align",
    "vacmap": "alignment/vacmap_align",
    "star": "alignment/star",
    "parabricks_fq2bam": "parabricks/pbrun_fq2bam",
    "parabricks_fq2bam_recal": "parabricks/pbrun_fq2bam_recal",
    "parabricks_rna_fq2bam": "parabricks/pbrun_rna_fq2bam"
}
```

1. **Aligner specified**: If the config dictionary includes an aligner:
   - First checks if the aligner exists in `ALIGNER_PATHS` and uses that custom path
   - If not in the dictionary, falls back to the pattern: `alignment/{aligner}_align`
   - Constructs BAM and BAI paths using the determined path prefix

2. **No aligner specified**: If no aligner is defined, the function constructs the file paths using the `default_path` and the `wildcards.sample` and `wildcards.type` values.


#### Returns

A tuple containing:

 - The full path to the BAM file
 - The full path to the corresponding BAI index file

#### Example: no aligner

```python
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

```python
wildcards = types.SimpleNamespace(sample="sample1", type="rna")
config = {"aligner": "pbmm2"}

bam_path, bai_path = get_input_aligned_bam(wildcards, config)

# Returns
(
    "alignment/pbmm2_align/sample1_rna.bam",
    "alignment/pbmm2_align/sample1_rna.bam.bai"
)
```

## Customizing Aligner Paths

The following aligners have predefined paths in `ALIGNER_PATHS`:

- **minimap2** → `alignment/minimap2_align`
- **pbmm2** → `alignment/pbmm2_align`
- **vacmap** → `alignment/vacmap_align`
- **star** → `alignment/star`
- **parabricks_fq2bam** → `parabricks/pbrun_fq2bam`
- **parabricks_fq2bam_recal** → `parabricks/pbrun_fq2bam_recal`
- **parabricks_rna_fq2bam** → `parabricks/pbrun_rna_fq2bam`

However, you can override or extend the `ALIGNER_PATHS` dictionary in your `common.smk` or workflow file to support custom aligners or non-standard directory structures.

### Option 1: Update the existing dictionary (recommended)

Add or override specific aligner paths while keeping the defaults:

```python
from hydra_genetics.utils import misc

# Add custom aligners or override existing ones
misc.ALIGNER_PATHS.update({
    "custom_aligner": "my/custom/path",
    "minimap2": "my/different/minimap2/path",  # Override existing
    "bwa": "alignment/bwa_mem"
})
```

### Option 2: Replace the entire dictionary

Completely replace the dictionary with your own custom paths:

```python
from hydra_genetics.utils import misc

# Replace with completely custom paths
misc.ALIGNER_PATHS = {
    "bwa": "custom/bwa/location",
    "minimap2": "custom/minimap2/location",
    "my_aligner": "tools/my_aligner/output"
}
```

**Note**: Modifications must be made using the module reference (`misc.ALIGNER_PATHS`) for changes to take effect in the helper functions.


## Haplotagged BAM files

Function `get_input_haplotagged_bam` constructs the file paths for haplotagged BAM and BAI index files, which may be required for downstream analyses (e.g., with `cnvkit_batch`). It supports flexible configuration and backward compatibility.

### Parameters

 - **wildcards**: A Snakemake Wildcards object that contains sample and type. These are used to construct file names.
 - **config**: A dictionary containing workflow configuration options. It may include:
   - **haplotag_path**: custom path to haplotagged BAMs
   - **haplotag_suffix**: optional suffix for filenames, if not provided no suffix is used.
   - **aligner**: Specifies which aligner was used (e.g., `minimap2`, `pbmm2`, etc.). If `haplotag_path` is not provided, this is used to construct the base path as `alignment/{aligner}_align`.
   - **default_path**: A path used if `haplotag_path` and `aligner` are not provided. Defaults to `"alignment/samtools_merge_bam"`.
   - **suffix**: Optional suffix to append to the BAM filename. Default is `None`.

### How it works

1. **Wildcard Extraction**: Retrieves sample and type from the wildcards object. If missing, raises a `WorkflowError`.

2. **Path Resolution**: 
    - Uses `haplotag_path` from config if available. 
    - If `haplotag_path` is missing but `aligner` is specified in config, it constructs the path as `alignment/{aligner}_align`.
    - Falls back to `default_path` if neither are available.

3. **Suffix Handling**: If suffix is provided as an argument, it is used. Otherwise, the function checks for `haplotag_suffix` in config, if it not specified, no suffix is used.

4. **Filename Construction**: With suffix: `sample_type.suffix.bam`; Without suffix: `sample_type.bam`

5. **Returns**: A tuple of:
   - Full path to the BAM file
   - Full path to the corresponding BAI index file

### Examples

1. No suffix, default path
```python
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
```python
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
```python
wildcards = types.SimpleNamespace(sample="sample1", type="rna")
config = {"haplotag_path": "custom/path"}

bam_path, bai_path = get_input_haplotagged_bam(wildcards, config)

# Returns
(
    "custom/path/sample1_rna.bam",
    "custom/path/sample1_rna.bam.bai"
)
```

4. No suffix, aligner specified
```python
wildcards = types.SimpleNamespace(sample="sample1", type="rna")
config = {"aligner": "bwa-mem2"}

bam_path, bai_path = get_input_haplotagged_bam(wildcards, config)

# Returns
(
    "alignment/bwa-mem2_align/sample1_rna.bam",
    "alignment/bwa-mem2_align/sample1_rna.bam.bai"
)
```

