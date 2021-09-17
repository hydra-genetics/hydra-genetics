# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

__author__ = "{author}"
__copyright__ = "Copyright 2021, {author}"
__email__ = "{email}"
__license__ = "GPL3"


rule {rule_name}:
    input:
        "INPUT_FILES",
    output:
        "{module}/{rule_name}/WILDCARDS_AND_FILE_NAME",
    params:
        #MORE_PARAMETERS
        extra=config.get("{rule_name}", {}).get("extra", ""),
    conda:
        "../envs/{rule_name}.yaml"
    log:
        "{module}/{rule_name}/WILDCARDS_AND_FILE_NAME.{rule_name}.log",
    benchmark:
        repeat(
            "{module}/{rule_name}/WILDCARDS_AND_FILE_NAME.{rule_name}..benchmark.tsv",
            config.get("benchmark", {}).get("repeats", 1),
        )
    container:
        config.get("singularity", {}).get("{rule_name}", config.get("singularity", {}).get("default", ""))
    wrapper:
        "0.78.0/bio/fastp"
