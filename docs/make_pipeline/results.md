# How to specify results files

## Rule all
The rule all specifies the result files from the pipeline. It is defined in the `Snakefile` before any modules are
included, since the modules also contain an `all` rule:
```
rule all:
    input:
        compile_output_file_list,
```

## Output files specified in a yaml file
The result files are defined in a yaml file, `config/output_files.yaml` in a pipeline created with hydra-genetics. The
file is pointed out by the `output` key in `config.yaml`:
```yaml
output: "config/output_files.yaml"
```
The file is read and validated against `workflow/schemas/output_files.schema.yaml` in `common.smk`:
```python
with open(config["output"]) as output:
    if config["output"].endswith("json"):
        output_spec = json.load(output)
    elif config["output"].endswith("yaml") or config["output"].endswith("yml"):
        output_spec = yaml.safe_load(output.read())

validate(output_spec, schema="../schemas/output_files.schema.yaml")
```
Note that a json file with the same structure is also accepted, but yaml is the format used by the pipeline template.

An example of the file:
```yaml
directory: "results"
files:
  - name: "bam"
    input: "alignment/samtools_merge_bam/{sample}_{type}.bam"
    output: "dna/bam/{sample}_{type}.bam"
  - name: "bai"
    input: "alignment/samtools_merge_bam/{sample}_{type}.bam.bai"
    output: "dna/bam/{sample}_{type}.bam.bai"
  - name: "multiqc html"
    input: null
    output: "qc/multiqc.html"
```

| Key | Explanation |
|-----|-------------|
| directory | Optional, the directory the result files are placed in (default: `./`). |
| files | List of result files, required. |
| name | Descriptive name of the result file, required. It is also used to name the copy rule for the file. |
| input | Path to the file that should be copied to the output directory, required. The wildcards `{sample}` and `{type}` can be used. If the value is `null` no copy rule is created and Snakemake has to find another rule that generates the file at `output`. |
| output | Path of the result file relative to `directory`, required. The wildcards `{sample}` and `{type}` can be used. |
| types | Optional list of sample types (`N`, `T` or `R`) the file is meant for. The key is allowed by the schema, but it is not used by the function in the pipeline template, see below. |

## compile_output_file_list function
The rule all calls the function `compile_output_file_list`, defined in `common.smk`, which uses the specification
above to create the list of all files that the pipeline should generate. The function in the pipeline template looks
like this:
```python
def compile_output_file_list(wildcards):
    outdir = pathlib.Path(output_spec.get("directory", "./"))
    output_files = []

    for f in output_spec["files"]:
        # Please remember to add any additional values down below
        # that the output strings should be formatted with.
        outputpaths = set(
            [
                f["output"].format(sample=sample, type=unit_type)
                for sample in get_samples(samples)
                for unit_type in get_unit_types(units, sample)
            ]
        )

        for op in outputpaths:
            output_files.append(outdir / Path(op))

    return output_files
```
If a result file should only be created for some sample types, or if the paths contain other wildcards, for example
a caller, the function has to be extended to filter on `f["types"]` and to format the strings with the extra values.

## Generate copy file rules
It is recommended to use a copy rule for each result file. In this way, result files will be copied individually and
not as a bulk, which improves performance for reruns. The copy rules are generated programmatically in `common.smk`
by the function `generate_copy_rules(output_spec)`, which is called once after it is defined.

For each entry in `files` with an `input` that is not `null` the function creates a rule that copies `input` to
`directory`/`output`. The rule is named `_copy_` followed by `name`, converted to lower case with every group of
non-word characters replaced by an underscore, e.g. the name `"multiqc html"` results in the rule `_copy_multiqc_html`.

The resources and the container of the copy rules can be configured in `config.yaml` and `resources.yaml` using the
key `_copy`, with the values in `default_resources` and `default_container` as defaults:
```yaml
_copy:
  container: "docker://hydragenetics/common:0.1.9"
  mem_mb: 1024
  threads: 1
```
See the function in the generated `workflow/rules/common.smk` for the full code.
