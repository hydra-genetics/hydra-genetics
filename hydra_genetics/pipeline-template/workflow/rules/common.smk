__author__ = "{{ author }}"
__copyright__ = "Copyright {{ year }}, {{ author }}"
__email__ = "{{ email }}"
__license__ = "GPL-3"

import itertools
import numpy as np
import pathlib
import pandas as pd
import yaml
from snakemake.utils import validate
from snakemake.utils import min_version

from hydra_genetics.utils.resources import load_resources
from hydra_genetics.utils.samples import *
from hydra_genetics.utils.units import *

min_version("{{ min_snakemake_version }}")

### Set and validate config file

if not workflow.overwrite_configfiles:
    "At least one config file must be passed using --configfile/--configfiles, by command line or a profile!"


validate(config, schema="../schemas/config.schema.yaml")
config = load_resources(config, config["resources"])
validate(config, schema="../schemas/resources.schema.yaml")


### Read and validate samples file

samples = pd.read_table(config["samples"], dtype=str).set_index("sample", drop=False)
validate(samples, schema="../schemas/samples.schema.yaml")

### Read and validate units file

units = (
    pandas.read_table(config["units"], dtype=str)
    .set_index(["sample", "type", "flowcell", "lane", "barcode"], drop=False)
    .sort_index()
)

validate(units, schema="../schemas/units.schema.yaml")

with open(config["output"]) as output:
    if config["output"].endswith("json"):
        output_spec = json.load(output)
    elif config["output"].endswith("yaml") or config["output"].endswith("yml"):
        output_spec = yaml.safe_load(output.read())

validate(output_spec, schema="../schemas/output_files.schema.yaml")


### Set wildcard constraints
wildcard_constraints:
    sample="|".join(samples.index),
    type="N|T|R",


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


def generate_copy_rules(output_spec):
    output_directory = pathlib.Path(output_spec.get("directory", "./"))
    rulestrings = []

    for f in output_spec["files"]:
        if f["input"] is None:
            continue

        rule_name = "_copy_{}".format("_".join(re.split(r"\W+", f["name"].strip().lower())))
        input_file = pathlib.Path(f["input"])
        output_file = output_directory / pathlib.Path(f["output"])

        mem_mb = config.get("_copy", {}).get("mem_mb", config["default_resources"]["mem_mb"])
        mem_per_cpu = config.get("_copy", {}).get("mem_per_cpu", config["default_resources"]["mem_per_cpu"])
        partition = config.get("_copy", {}).get("partition", config["default_resources"]["partition"])
        threads = config.get("_copy", {}).get("threads", config["default_resources"]["threads"])
        time = config.get("_copy", {}).get("time", config["default_resources"]["time"])
        copy_container = config.get("_copy", {}).get("container", config["default_container"])

        rule_code = "\n".join(
            [
                f'@workflow.rule(name="{rule_name}")',
                f'@workflow.input("{input_file}")',
                f'@workflow.output("{output_file}")',
                f'@workflow.log("logs/{rule_name}_{output_file.name}.log")',
                f'@workflow.container("{copy_container}")',
                '@workflow.conda("../envs/copy_results_files.yaml")',
                f'@workflow.resources(time="{time}", threads={threads}, mem_mb="{mem_mb}", '
                f'mem_per_cpu={mem_per_cpu}, partition="{partition}")',
                f'@workflow.shellcmd("{copy_container}")',
                "@workflow.run\n",
                f"def __rule_{rule_name}(input, output, params, wildcards, threads, resources, "
                "log, version, rule, conda_env, container_img, singularity_args, use_singularity, "
                "env_modules, bench_record, jobid, is_shell, bench_iteration, cleanup_scripts, "
                "shadow_dir, edit_notebook, conda_base_path, basedir, runtime_sourcecache_path, "
                "__is_snakemake_rule_func=True):",
                '\tshell("(cp {input[0]} {output[0]}) &> {log}", bench_record=bench_record, '
                "bench_iteration=bench_iteration)\n\n",
            ]
        )

        rulestrings.append(rule_code)

    exec(compile("\n".join(rulestrings), "copy_result_files", "exec"), workflow.globals)


generate_copy_rules(output_spec)
