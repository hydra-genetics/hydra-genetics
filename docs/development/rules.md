# Snakemake rules
A rule describes a task and is the backbone of a Snakemake pipeline. In hydra-genetics we have set up a format for rules and their names.
## Create a rule template
Using the **hydra-genetics tool** it is very easy to create a new rule template following the hydra-genetics standard.
## Installation
Install hydra-genetics as described in [Installation](../installation.md).
## Make a rule skeleton
The hydra-genetics tools will set up a rule skeleton and place the rule in module_name/workflow/rules/new_rule.smk.
```bash
hydra-genetics create-rule -c picard_mark_duplicates -t picard -m alignment -a my_name -e name@email.com [OPTIONS]
```
| **Option** | **Description** |
|--------|-------------|
| -c, --command TEXT | command that will be run, will be used to name the rule (with `--script` it is the full rule name) [required] |
| -t, --tool TEXT | tool that will be used to run the command, if provided it will be used during the naming of the rule, ex samtools. <br/> With `--script` it only selects the .smk file |
| -m, --module TEXT | name module/workflow where rule will be added. Expected folder structure is module_name/workflow/, <br/> the rule will be added to a subfolder named rules, env.yaml to a subfolder named envs. [required] |
| -a, --author TEXT | Name of the main author(s) [required] |
| -e, --email TEXT | E-mail(s) of the main author(s) [required] |
| -o, --outdir TEXT | Output directory for where module is located (default: current dir) |
| --script | Create a rule that runs a Python script, see [Script rules](#script-rules) |
| --help | Show help message |

### Script rules
With `--script` the rule runs `workflow/scripts/<command>.py` through `script:` instead of a wrapper. The rule is named
exactly after `--command`, and `--tool` (optional) only chooses which `.smk` file the rule is added to. Stub files
`workflow/scripts/<command>.py` and `workflow/scripts/test_<command>.py` are created; the command fails without writing
anything if either already exists. The command must be a valid Python name.
```bash
hydra-genetics create-rule -c cnv_report -m cnv -a my_name -e name@email.com --script
hydra-genetics create-rule -c cnv_json -t cnv_report -m cnv -a my_name -e name@email.com --script
```
This gives the rules `cnv_report` and `cnv_json` in `workflow/rules/cnv_report.smk`, using
`workflow/scripts/cnv_report.py` and `workflow/scripts/cnv_json.py`.

## Example rule (`workflow/rules/example_rule.smk`)
All parts of the example rule should always be present, with `wrapper/script/shell/run` replaced by one of the execution types.
```
rule example_rule:
    input:
      input1="module/example_rule/{sample}_{type}.suffix1",
    output:
      output1=temp("module/example_rule/{sample}_{type}.suffix2"),
    params:
      extra=config.get("example_rule", {}).get("extra", ""),
    log:
      "module/example_rule/{sample}_{type}.suffix2.log"
    benchmark:
      repeat("module/example_rule/{sample}_{type}.suffix2.benchmark.tsv", config.get("example_rule", {}).get("benchmark_repeats", 1),)
    threads: config.get("example_rule", {}).get("threads", config["default_resources"]["threads"])
    resources:
      mem_mb=config.get("example_rule", {}).get("mem_mb", config["default_resources"]["mem_mb"]),
      mem_per_cpu=config.get("example_rule", {}).get("mem_per_cpu", config["default_resources"]["mem_per_cpu"]),
      partition=config.get("example_rule", {}).get("partition", config["default_resources"]["partition"]),
      threads=config.get("example_rule", {}).get("threads", config["default_resources"]["threads"]),
      time=config.get("example_rule", {}).get("time", config["default_resources"]["time"]),
    container:
        config.get("example_rule", {}).get("container", config["default_container"])
    message:
        "{rule}: Do stuff on {input.input1}"
    wrapper/script/shell/run:
        "Some run command"
```
