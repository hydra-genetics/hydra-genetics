# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

__author__ = "{{ author }}"
__copyright__ = "Copyright {{ year }}, {{ author }}"
__email__ = "{{ email }}"
__license__ = "GPL-3"


rule {{ name }}:
    input:
        "...",
    output:
        "{{ module_name }}/{{ name }}/{sample}_{type}.output.txt"
    params:
        extra=config.get("{{ name }}", {}).get("extra", ""),
    log:
        "{{ module_name }}/{{ name }}/{sample}_{type}.output.log"
    benchmark:
        repeat(
            "{{ module_name }}/{{ name }}/{sample}_{type}.output.benchmark.tsv", config.get("{{ name }}", {}).get("benchmark_repeats", 1)
        )
    threads: config.get("{{ name }}", {}).get("threads", config["default_resources"]["threads"])
    resources:
        threads=config.get("{{ name }}", {}).get("threads", config["default_resources"]["threads"]),
        time=config.get("{{ name }}", {}).get("time", config["default_resources"]["time"]),
        mem_mb=config.get("{{ name }}", {}).get("mem_mb", config["default_resources"]["mem_mb"]),
        mem_per_cpu=config.get("{{ name }}", {}).get("mem_per_cpu", config["default_resources"]["mem_per_cpu"]),
        partition=config.get("{{ name }}", {}).get("partition", config["default_resources"]["partition"]),
    container:
        config.get("{{ name }}", {}).get("container", config["default_container"])
    conda:
        "../envs/{{ name }}.yaml"
    message:
       "{rule}: Do stuff on {{ module_name }}/{rule}/{wildcards.sample}_{wildcards.type}.input"
    wrapper:
        "..."
