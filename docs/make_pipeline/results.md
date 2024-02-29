# How to specify results files

## Rule all
The rule all specifies the result files from the pipeline and is defined last in the `Snakemake` file:
```
rule all:
    input:
        unpack(compile_output_list),
```

## compile_output_list function
The rule calls upon the function *compile_output_list* defined in `common.smk` which uses a json-file to define the output files. An example of the function is shown below:
```python
def compile_output_list(wildcards):
    output_files = []
    types = set([unit.type for unit in units.itertuples()])
    for output in output_json:                                                            
        output_files += set(
            [
                output.format(sample=sample, type=unit_type, caller=caller)
                for sample in get_samples(samples)
                for unit_type in get_unit_types(units, sample)
                if unit_type in set(output_json[output]["types"]).intersection(types)
                for caller in config["bcbio_variation_recall_ensemble"]["callers"]
            ]
        )
    return list(set(output_files))
```

## Output files specified in json format
The output_json is specified in the `common.smk` which look up the actual file in `config.yaml`:
```python
with open(config["output"]) as output:
    output_json = json.load(output)
```
In our example the output_json file looks like this:
```
{
  "bam_dna/{sample}_{type}.bam": {"name": "_result_bam", "file": "alignment/samtools_merge_bam/{sample}_{type}.bam", "types": ["T", "N"]},
  "bam_dna/{sample}_{type}.bam.bai": {"name": "_result_bai", "file": null, "types": ["T", "N"]},
  "results/dna/vcf/{sample}_{type}.annotated.vcf.gz": {"name": "_result_annotated_vcf", "file": "annotation/background_annotation/{sample}_{type}.background_annotation.vcf.gz", "types": ["T", "N"]},
  "results/rna/qc/multiqc_RNA.html": {"name": "_result_multiqc_rna_html", "file": "qc/multiqc/multiqc_RNA.html", "types": ["R"]}
}
```

## Generate copy file rules
It is recommended to use a copy rule for each output file. In this way, result files will be copied individually and not as a bulk which improves performance for reruns. These rules can be generated programmatically in `common.smk` for example by the following function:
```python
def generate_copy_code(workflow, output_json):
    code = ""
    for result, values in output_json.items():
        if values["file"] is not None:
            input_file = values["file"]
            output_file = result
            rule_name = values["name"]
            mem_mb = config.get("_copy", {}).get("mem_mb", config["default_resources"]["mem_mb"])
            mem_per_cpu = config.get("_copy", {}).get("mem_mb", config["default_resources"]["mem_mb"])
            partition = config.get("_copy", {}).get("partition", config["default_resources"]["partition"])
            threads = config.get("_copy", {}).get("threads", config["default_resources"]["threads"])
            time = config.get("_copy", {}).get("time", config["default_resources"]["time"])
            copy_container = config.get("_copy", {}).get("container", config["default_container"])
            result_file = os.path.basename(output_file)
            code += f'@workflow.rule(name="{rule_name}")\n'
            code += f'@workflow.input("{input_file}")\n'
            code += f'@workflow.output("{output_file}")\n'
            code += f'@workflow.log("logs/{rule_name}_{result_file}.log")\n'
            code += f'@workflow.container("{copy_container}")\n'
            code += f'@workflow.conda("../env/copy_result.yaml")\n'
            code += f'@workflow.resources(time = "{time}", threads = {threads}, mem_mb = {mem_mb}, mem_per_cpu = {mem_per_cpu}, partition = "{partition}")\n'
            code += '@workflow.shellcmd("cp {input} {output}")\n\n'
            code += "@workflow.run\n"
            code += (
                f"def __rule_{rule_name}(input, output, params, wildcards, threads, resources, log, version, rule, "
                "conda_env, container_img, singularity_args, use_singularity, env_modules, bench_record, jobid, is_shell, "
                "bench_iteration, cleanup_scripts, shadow_dir, edit_notebook, conda_base_path, basedir, runtime_sourcecache_path, "
                "__is_snakemake_rule_func=True):\n"
                '\tshell ( "(cp {input[0]} {output[0]}) &> {log}" , bench_record=bench_record, bench_iteration=bench_iteration)\n\n'
            )
    exec(compile(code, "result_to_copy", "exec"), workflow.globals)


generate_copy_code(workflow, output_json)
```
