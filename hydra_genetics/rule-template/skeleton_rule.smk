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
    threads: config.get("{{ name }}", config["default_resources"])["threads"]
    container:
        config.get("{{ name }}", {}).get("container", config["default_container"])
    conda:
        "../envs/{{ name }}.yaml"
    message:
       "{rule}: Do stuff on {{ module_name }}/{rule}/{wildcards.sample}_{wildcards.type}.input"
    wrapper:
        "..."
