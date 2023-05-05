__author__ = "{{ author }}"
__copyright__ = "Copyright {{ year }}, {{ author }}"
__email__ = "{{ email }}"
__license__ = "GPL-3"


rule dummy:
    output:
        OUTPUT1="{{ short_name }}/dummy/{sample}_{type}.dummy.txt"
    params:
        extra=config.get("dummy", {}).get("extra", ""),
    log:
        "{{ short_name }}/dummy/{sample}_{type}.output.log"
    benchmark:
       repeat("module/dummy/{sample}_{type}.output.benchmark.tsv", config.get("dummy", {}).get("benchmark_repeats", 1),)
    threads: # optional
       threads=config.get("dummy", {}).get("threads", config["default_resources"]["threads"]),
    resources:
        threads=config.get("dummy", {}).get("threads", config["default_resources"]["threads"]),
        time=config.get("dummy", {}).get("time", config["default_resources"]["time"]),
    container:
       config.get("dummy", {}).get("container", config["default_container"])
    message:
       "{rule}: Do stuff on module/{rule}/{wildcards.sample}_{wildcards.type}.input"
    shell:
        """
        touch {output}
        """
