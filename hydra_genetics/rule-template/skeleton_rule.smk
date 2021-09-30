# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

__author__ = "{{ author }}"
__copyright__ = "Copyright {{ year }}, {{ author }}"
__email__ = "{{ email }}"
__license__ = "GPL-3"

rule {{ rule_name }}:
    input:
        ...
    output:
        "{{ module_name }}/{{ rule_name }}/{sample}_{unit}.output.txt"
    params:
        extra=config.get("{{ rule_name }}", {}).get("extra", ""),
    log:
        "{{ module_name }}/{{ rule_name }}/{sample}_{unit}.output.log"
    benchmark:
       repeat("{{ module_name }}/{{ rule_name }}/{sample}_{unit}.output.benchmark.tsv", config.get("{{ rule_name }}", {}).get("benchmark_repeats", 1),)
    threads: # optional
       config.get("{{ rule_name }}", config["default_resources"])["threads"]
    container:
       config.get("{{ rule_name }}", {}).get("container", config["default_container"])
    conda:
       "../envs/{{ rule_name }}.yaml"
    message:
       "{rule}: Do stuff on {{ module_name }}//{rule}/{wildcards.sample}_{wildcards.unit}.input"
    wrapper:
        "..."
