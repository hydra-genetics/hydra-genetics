{% if append_rule == 0 -%}
__author__ = "{{ author }}"
__copyright__ = "Copyright {{ year }}, {{ author }}"
__email__ = "{{ email }}"
__license__ = "GPL-3"


{% else %}

{% endif -%}
rule {{ name }}:
    input:
        input1="...",
    output:
        output1="{{ module_name }}/{{ name }}/{sample}_{type}.output.txt",
    params:
        extra=config.get("{{ name }}", {}).get("extra", ""),
    log:
        "{{ module_name }}/{{ name }}/{sample}_{type}.output.log",
    benchmark:
        repeat(
            "{{ module_name }}/{{ name }}/{sample}_{type}.output.benchmark.tsv",
            config.get("{{ name }}", {}).get("benchmark_repeats", 1)
        )
    threads: config.get("{{ name }}", {}).get("threads", config["default_resources"]["threads"])
    resources:
        mem_mb=config.get("{{ name }}", {}).get("mem_mb", config["default_resources"]["mem_mb"]),
        mem_per_cpu=config.get("{{ name }}", {}).get("mem_per_cpu", config["default_resources"]["mem_per_cpu"]),
        partition=config.get("{{ name }}", {}).get("partition", config["default_resources"]["partition"]),
        threads=config.get("{{ name }}", {}).get("threads", config["default_resources"]["threads"]),
        time=config.get("{{ name }}", {}).get("time", config["default_resources"]["time"]),
    container:
        config.get("{{ name }}", {}).get("container", config["default_container"])
    message:
        "{rule}: do stuff on {input.input1}"
    wrapper:
        "..."
