# Input functions

Hydra Genetics contains helper functions to compile paths to BAM files depending on your pipeline configuration. These paths are used  by rules in other Hydra Genetics modules that require an aligned BAM file as input.

The functions are located in `hydra_genetics/utils/misc.py`.


## Aligned BAM files

Function `get_input_aligned_bam` compiles paths to aligned BAM files and their corresponding BAI index files based on workflow configuration. 

### Parameters

 - **wildcards**: A Snakemake Wildcards object that contains sample and type. These are used to construct file names.
 - **config**: A dictionary containing workflow configuration options. It may include:
   - **aligner**: Specifies which aligner was used (e.g., `minimap2`, `pbmm2`, etc.). If this is set, the function will construct path using these tools names.
 - **set_type** (optional): Override the type from wildcards. Must be `None`, `'N'`, `'T'`, or `'R'`. If `None` (default), uses `wildcards.type`.
 - **default_path** (optional): A fallback directory path used when no aligner is specified. Defaults to `"alignment/samtools_merge_bam"`.

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

#### Example: with set_type override

```python
wildcards = types.SimpleNamespace(sample="sample1", type="T")
config = {"aligner": "minimap2"}

# Override type to 'N' (normal)
bam_path, bai_path = get_input_aligned_bam(wildcards, config, set_type="N")

# Returns
(
    "alignment/minimap2_align/sample1_N.bam",
    "alignment/minimap2_align/sample1_N.bam.bai"
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

## Haplotagged/Phased BAM files

Function `get_input_haplotagged_bam` constructs the file paths for haplotagged/phased BAM and BAI index files, which may be required for downstream analyses (e.g., with structural variant callers like `severus`).

### Parameters

 - **wildcards**: A Snakemake Wildcards object that contains sample and type. These are used to construct file names.
 - **config**: A dictionary containing workflow configuration options. It may include:
   - **phaser**: Name of phasing/haplotagging tool used (e.g., `whatshap`, `hiphase`).
   - **haplotag_suffix**: Optional suffix for filenames from config.
 - **set_type** (optional): Override the type from wildcards. Must be `None`, `'N'`, `'T'`, or `'R'`. If `None` (default), uses `wildcards.type`.
 - **default_path** (optional): Default path for BAM files if no phaser is specified. Defaults to `"snv_indels/whatshap_haplotag"`.
 - **suffix** (optional): Suffix to append to the BAM file name. Default is `'haplotagged.bam'`.

### How it works

The function uses the `PHASED_BAM_PATHS` dictionary to map phaser/haplotagger names to their output directory paths. This dictionary contains predefined paths for common phasers:

```python
PHASED_BAM_PATHS = {
    "whatshap": "snv_indels/whatshap_haplotag",
    "hiphase": "snv_indels/hiphase"
}
```

1. **Phaser specified**: If the config dictionary includes a phaser:
   - First checks if the phaser exists in `PHASED_BAM_PATHS` and uses that custom path
   - If not in the dictionary, falls back to the pattern: `snv_indels/{phaser}`
   - Constructs BAM and BAI paths using the determined path prefix

2. **No phaser specified**: If no phaser is defined, the function uses the `default_path`.

3. **Suffix Handling**: If suffix is provided as an argument, it is used. Otherwise, the function checks for `haplotag_suffix` in config. If not specified in either location, the default suffix `'haplotagged.bam'` is used.

4. **Filename Construction**: 
   - With suffix: `{sample}_{type}.{suffix}.bam`
   - Without suffix: `{sample}_{type}.bam`

### Returns

A tuple containing:
 - Full path to the haplotagged BAM file
 - Full path to the corresponding BAI index file

### Examples

1. With phaser, no suffix
```python
wildcards = types.SimpleNamespace(sample="sample1", type="T")
config = {"phaser": "whatshap"}

bam_path, bai_path = get_input_haplotagged_bam(wildcards, config)

# Returns
(
    "snv_indels/whatshap_haplotag/sample1_T.bam",
    "snv_indels/whatshap_haplotag/sample1_T.bam.bai"
)
```

2. With phaser and suffix
```python
wildcards = types.SimpleNamespace(sample="sample1", type="T")
config = {"phaser": "hiphase", "haplotag_suffix": "phased"}

bam_path, bai_path = get_input_haplotagged_bam(wildcards, config)

# Returns
(
    "snv_indels/hiphase/sample1_T.phased.bam",
    "snv_indels/hiphase/sample1_T.phased.bam.bai"
)
```

3. With set_type override
```python
wildcards = types.SimpleNamespace(sample="sample1", type="N")
config = {"phaser": "whatshap"}

# Override type to 'T' (tumor)
bam_path, bai_path = get_input_haplotagged_bam(wildcards, config, set_type="T")

# Returns
(
    "snv_indels/whatshap_haplotag/sample1_T.bam",
    "snv_indels/whatshap_haplotag/sample1_T.bam.bai"
)
```

4. No phaser specified (uses default)
```python
wildcards = types.SimpleNamespace(sample="sample1", type="T")
config = {}

bam_path, bai_path = get_input_haplotagged_bam(wildcards, config)

# Returns
(
    "snv_indels/whatshap_haplotag/sample1_T.bam",
    "snv_indels/whatshap_haplotag/sample1_T.bam.bai"
)
```

## Customizing Phased BAM Paths

The following phasers have predefined paths in `PHASED_BAM_PATHS`:

- **whatshap** → `snv_indels/whatshap_haplotag`
- **hiphase** → `snv_indels/hiphase`

Any other phaser name will use the default pattern: `snv_indels/{phaser}`

You can override or extend the `PHASED_BAM_PATHS` dictionary in your `common.smk` or workflow file:

### Option 1: Update the existing dictionary (recommended)

```python
from hydra_genetics.utils import misc

# Add custom phasers or override existing ones
misc.PHASED_BAM_PATHS.update({
    "custom_phaser": "my/custom/phased/path",
    "whatshap": "different/whatshap/location",  # Override existing
    "hapcut2": "snv_indels/hapcut2"
})
```

### Option 2: Replace the entire dictionary

```python
from hydra_genetics.utils import misc

# Replace with completely custom paths
misc.PHASED_BAM_PATHS = {
    "whatshap": "custom/whatshap/path",
    "hiphase": "custom/hiphase/path",
    "my_phaser": "tools/my_phaser/output"
}
```

**Note**: Modifications must be made using the module reference (`misc.PHASED_BAM_PATHS`) for changes to take effect in the helper functions.

## set_type Parameter

Both `get_input_aligned_bam` and `get_input_haplotagged_bam` support the `set_type` parameter to override the type from wildcards. This is useful when you need to explicitly specify a sample type different from what's in the wildcards. It can be used for rules requiring both T (tumor) and N (normal) BAM files for a sample, enabling paired tumor-normal analysis workflows.

**Valid values:**
- `None` (default): Uses `wildcards.type`
- `'N'`: Normal/control sample
- `'T'`: Tumor sample
- `'R'`: RNA sample

**Example use case 1:** A rule that needs tumor BAM files but wildcards contains mixed types:

```python
rule my_rule:
    input:
        tumor_bam = lambda wildcards: get_input_aligned_bam(
            wildcards, 
            config, 
            set_type="T"  # Always get tumor BAM
        )[0]
```

**Example use case 2:** A rule requiring both tumor and normal BAM files for paired analysis:

```python
rule somatic_variant_calling:
    input:
        tumor_bam = lambda wildcards: get_input_aligned_bam(
            wildcards, 
            config, 
            set_type="T"  # Get tumor BAM
        )[0],
        normal_bam = lambda wildcards: get_input_aligned_bam(
            wildcards, 
            config, 
            set_type="N"  # Get normal BAM
        )[0]
    output:
        vcf = "variants/{sample}.somatic.vcf"
    shell:
        "variant_caller --tumor {input.tumor_bam} --normal {input.normal_bam} -o {output.vcf}"
```

