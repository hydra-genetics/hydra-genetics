#!/usr/bin/env python
"""Creates a hydra-core pipeline matching the current
organization's specification based on a template.
"""

from datetime import date
import git
import glob
import gzip
import logging
import jinja2
import json
import pathlib
import os
import re
import shutil
import sys
import hydra_genetics

log = logging.getLogger(__name__)


class PipelineCreate(object):
    """Creates a hydra-genetics pipeline.
    Args:
        name (str): Name for the pipeline.
        description (str): Description for the pipeline.
        author (str): Authors name
        email (str): Authors email
        version (str): Version flag. Semantic versioning only. Defaults to `1.0dev`.
        snakemake_version (str): min snakemake version
        git_user: (str) username on github
        no_git (bool): Prevents the creation of a local Git repository for the pipeline. Defaults to False.
        force (bool): Overwrites a given workflow directory with the same name. Defaults to False.
            May the force be with you.
        outdir (str): Path to the local output directory.
    """
    def __init__(self, name, description, author, email, version="0.0.1", min_snakemake_version="6.10.0",
                 git_user=None, no_git=False, force=False, outdir=None):
        self.short_name = name.lower().replace(r"/\s+/", "-").replace("hydra-genetics/", "").replace("/", "-")
        self.name = f"{self.short_name}"
        self.description = description
        self.author = author
        self.email = email
        self.version = version
        self.min_snakemake_version = min_snakemake_version
        self.git_user = git_user
        self.no_git = no_git
        self.force = force
        self.year = date.today().year
        self.outdir = outdir
        if not self.outdir:
            self.outdir = os.path.join(os.getcwd(), self.name)

    def init_pipeline(self):
        """Creates the hydra_genetics pipeline."""
        log.info(f"Creating pipeline: {self.short_name}")
        if os.path.exists(self.outdir):
            if self.force:
                log.warning(f"Output directory '{self.outdir}' exists - continuing as --force specified")
            else:
                log.error(f"Output directory '{self.outdir}' exists!")
                log.info("Use -f / --force to overwrite existing files")
                sys.exit(1)
        else:
            os.makedirs(self.outdir)

        env = jinja2.Environment(
           loader=jinja2.PackageLoader("hydra_genetics", "pipeline-template"), keep_trailing_newline=True
        )

        template_dir = os.path.join(os.path.dirname(__file__), "../pipeline-template")
        object_attrs = vars(self)
        template_files = list(pathlib.Path(template_dir).glob("**/*"))
        ignore_strs = [".pyc", "__pycache__", ".pyo", ".pyd", ".DS_Store", ".egg", ".snakemake"]
        log.info("Adding folder and files")
        for template_fn_path_obj in template_files:
            template_fn_path = str(template_fn_path_obj)
            if any([s in template_fn_path for s in ignore_strs]):
                log.debug(f"Ignoring '{template_fn_path}' in jinja2 template creation")
                continue

            template_fn = os.path.relpath(template_fn_path, template_dir)
            output_path = os.path.join(self.outdir, template_fn)

            if os.path.isdir(template_fn_path_obj):
                log.debug(f"Creating directory: '{output_path}'")
                if os.path.exists(output_path):
                    if self.force:
                        log.warning(f"Output directory '{output_path}' exists - continuing as --force specified")
                    else:
                        log.error(f"Output directory '{output_path}' exists!")
                        log.info("Use -f / --force to overwrite existing files")
                        sys.exit(1)
                else:
                    os.makedirs(output_path)
                continue

            log.debug(f"Rendering template file: '{template_fn}'")

            if template_fn.endswith(".png"):
                shutil.copy(os.path.join(template_dir, template_fn), output_path)
            else:
                j_template = env.get_template(template_fn)
                rendered_output = j_template.render(object_attrs)

                # Write to the pipeline output file
                with open(output_path, "w") as fh:
                    log.debug(f"Writing to output file: '{output_path}'")
                    fh.write(rendered_output)

        if not self.no_git:
            self.git_init_pipeline()

    def git_init_pipeline(self):
        """Initialises the new pipeline as a Git repository and submits first commit."""
        log.info("Initialising pipeline git repository")
        repo = git.Repo.init(self.outdir, initial_branch='main')
        repo.git.add(A=True)
        repo.index.commit(f"initial template build from hydra-genetics/tools, version {hydra_genetics.__version__}")
        # Add TEMPLATE branch to git repository
        repo.git.branch("develop")
        log.info(
            "Done. Remember to add a remote and push to GitHub:\n"
            f"[white on grey23] cd {self.outdir} \n"
            " git remote add origin git@github.com:USERNAME/REPO_NAME.git \n"
            " git push --all origin                                       "
        )


class RuleCreate(object):
    """Creates a hydra-genetics rule.
    Args:
        command (str): Name of the rule, command that will be run.
        tool (str): tool that will be used to run the command, ex samtools (optional)
        module (str): Name of module where rule will be added.
        author (str): Authors name
        email (str): Authors email
        outdir (str): Path to the local output directory.

        if a tool and command are both provided the rule will be named tool_command
    """
    def __init__(self, command, module, author, email, tool=None, outdir=None):
        self.command = command
        self.tool = tool
        self.module_name = module
        self.author = author
        self.email = email
        self.year = date.today().year

        if not outdir:
            self.outdir = os.getcwd()
        else:
            self.outdir = os.path.abspath(outdir)

    def init_rule(self):
        """Creates the hydra_genetics rule."""
        outdir = os.path.normpath(os.path.join(self.outdir, self.module_name))
        if not os.path.exists(outdir):
            outdir_temp = outdir
            outdir = os.path.join(os.path.dirname(self.outdir), self.module_name)
            if not os.path.exists(outdir):
                log.error(f"Can not find module directory, tried with:\n'{outdir_temp}'\n'{outdir}'")
                exit(1)
        outdir_workflow = os.path.join(outdir, "workflow")
        # Rule path
        output_rules = os.path.join(outdir_workflow, "rules")

        # Schema path
        output_schemas = os.path.join(outdir_workflow, "schemas")
        output_schemas_config = os.path.join(output_schemas, "config.schema.yaml")
        output_schemas_resources = os.path.join(output_schemas, "resources.schema.yaml")
        output_schemas_rule = os.path.join(output_schemas, "rules.schema.yaml")

        # Docs software path
        output_docs_software = os.path.join(outdir, "docs", "softwares.md")

        if not os.path.exists(output_rules):
            log.error(f"Can not find output directory '{output_rules}'")
            sys.exit(2)
        self.append_rule = False
        self.name = self.command
        if self.tool is None:
            self.filename_rulename = f"{self.name}__{self.name}"
            log.info(f"Creating rule: '{output_rules}/{self.name}.smk'")
            output_rule = os.path.join(output_rules, f"{self.name}.smk")
        else:
            self.name = f"{self.tool}_{self.name}"
            self.filename_rulename = f"{self.tool}__{self.name}"
            if os.path.exists(os.path.join(output_rules, f"{self.tool}.smk")):
                log.info(f"Adding entry {self.name} to smk '{outdir}/{self.tool}.smk'")
                output_rule = os.path.join(output_rules, f"{self.tool}.smk")
                self.append_rule = True
            else:
                log.info(f"Creating smk file: '{output_rules}/{self.tool}.smk' with rule {self.name}")
                output_rule = os.path.join(output_rules, f"{self.tool}.smk")
        if os.path.exists(output_rule) and self.tool is None:
            log.error(f"Rule already exists '{output_rule}'")
            sys.exit(4)

        if not os.path.exists(output_schemas):
            log.info(f"Creating schema folder {output_schemas}")
            os.mkdir(output_schemas)

        if not os.path.exists(output_schemas_config):
            log.info(f"Creating config schema file {output_schemas_config}")
            self.append_schema_config = False
        else:
            log.info(f"Appending to config schema file {output_schemas_config}")
            self.append_schema_config = True

        if not os.path.exists(output_schemas_resources):
            log.info(f"Creating resources schema file {output_schemas_resources}")
            self.append_schema_resources = False
        else:
            log.info(f"Appending to resources schema file {output_schemas_resources}")
            self.append_schema_resources = True

        if not os.path.exists(output_schemas_rule):
            log.info(f"Creating rule schema file {output_schemas_rule}")
            self.append_schema_rule = False
        else:
            log.info(f"Appending to rule schema file {output_schemas_rule}")
            self.append_schema_rule = True

        if not os.path.exists(output_docs_software):
            log.info(f"Creating docs file {output_docs_software}")
            self.append_docs_software = False
            parent_dir = os.path.dirname(output_docs_software)
            if not os.path.exists(parent_dir):
                os.mkdir(parent_dir)
        else:
            log.info(f"Appending to docs file {output_docs_software}")
            self.append_docs_software = True

        env = jinja2.Environment(
            loader=jinja2.PackageLoader("hydra_genetics", "rule-template"), keep_trailing_newline=True
        )
        template_dir = os.path.join(os.path.dirname(__file__), "../rule-template")
        rename_files = {
            "skeleton_rule.smk": output_rule,
        }
        object_attrs = vars(self)
        template_files = list(pathlib.Path(template_dir).glob("**/*"))
        ignore_strs = [".pyc", "__pycache__", ".pyo", ".pyd", ".DS_Store", ".egg", ".snakemake"]
        if self.append_rule:
            with open(output_rule, 'r') as lines:
                for line in lines:
                    if self.name in line:
                        log.error(f"rule {self.name} already found in file {output_rule}")
                        exit(6)
        log.info("Adding folder and files")
        for template_fn_path_obj in template_files:
            template_fn_path = str(template_fn_path_obj)
            if any([s in template_fn_path for s in ignore_strs]):
                log.debug(f"Ignoring '{template_fn_path}' in jinja2 template creation")
                continue

            template_fn = os.path.relpath(template_fn_path, template_dir)
            if template_fn.endswith(".smk"):
                output_path = output_rules
                self.append = self.append_rule
            elif template_fn.endswith("config.schema.yaml"):
                output_path = output_schemas_config
                self.append = self.append_schema_config
            elif template_fn.endswith("rules.schema.yaml"):
                output_path = output_schemas_rule
                self.append = self.append_schema_rule
            elif template_fn.endswith("resources.schema.yaml"):
                output_path = output_schemas_resources
                self.append = self.append_schema_resources
            elif template_fn.endswith(".md"):
                output_path = output_docs_software
                self.append = self.append_docs_software

            if template_fn in rename_files:
                output_path = os.path.join(outdir, rename_files[template_fn])

            log.info(f"Rendering template file: '{template_fn}' at {output_path}")
            j_template = env.get_template(template_fn)
            rendered_output = j_template.render(object_attrs, trim_blocks=False)

            if os.path.exists(output_path):
                with open(output_path, "r+") as fh:
                    lines = fh.readlines()
                    line_number = 0
                    for line in lines:
                        if line.startswith('required:'):
                            break
                        else:
                            line_number += 1
                    fh.seek(0)
                    lines.insert(line_number, rendered_output)
                    log.info(f"Appending to output file: '{output_path}'")
                    fh.writelines(lines)
            else:
                # Write to the content to a new file
                with open(output_path, "w") as fh:
                    log.info(f"Writing to new output file: '{output_path}'")
                    fh.write(rendered_output)
        snakefile = os.path.join(outdir_workflow, "Snakefile")
        with open(snakefile, 'r+') as fh:
            lines = fh.readlines()
            line_number = 0
            for line in lines:
                line_number += 1
                if line.startswith('include: "rules/common.smk"'):
                    break
            else:
                log.error(f"Could not find 'include: ../rules/common.smk' entry in Snakefile '{snakefile}'")
                sys.exit(1)
            fh.seek(0)
            if self.tool is not None and not self.append_rule:
                lines.insert(line_number, str(f"include: \"rules/{self.tool}.smk\"\n"))
            elif self.tool is None:
                lines.insert(line_number, str(f"include: \"rules/{self.command}.smk\"\n"))

            fh.writelines(lines)


class CreateInputFiles(object):
    """Creates a hydra-genetics input files samples.tsv and units.tsv.
    Args:
        directories (str): Path to dir that should be search.
        outdir (str): Path to the local output directory.
    """
    def __init__(self,
                 directory,
                 outdir=None,
                 post_file_modifier=None,
                 platform="Illumina",
                 sample_type="T",
                 sample_regex=r"^([A-Za-z0-9-]+)_.*\.fastq.gz",
                 read_number_regex="_(R[12]{1})[_.]{1}",
                 adapters="AGATCGGAAGAGCACACGTCTGAACTCCAGTCA,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
                 data_json=None,
                 data_columns=None,
                 tc=1.0,
                 force=False,
                 default_barcode=None,
                 validate_run_information=False,
                 ask_for_input=False,
                 occurrences_warning_th=0.9,
                 number_of_reads=200,
                 every_n_reads=1000):
        self.directory = directory
        self.outdir = outdir
        self.post_file_modifier = post_file_modifier
        self.platform = platform
        self.sample_type = sample_type
        self.sample_regex = sample_regex
        self.read_number_regex = read_number_regex
        self.adapters = adapters
        self.data_json = data_json
        self.data_columns = data_columns
        self.tc = tc
        self.force = force
        self.default_barcode = default_barcode
        self.validate_run_information = validate_run_information
        self.ask_for_input = ask_for_input
        self.occurrences_warning_th = occurrences_warning_th
        self.number_of_reads = number_of_reads
        self.every_n_reads = every_n_reads

        if not self.outdir:
            self.outdir = os.getcwd()

    def init(self):
        """Creates the hydra_genetics pipeline input files."""
        log.info(f"Searching for fastq-files:")
        file_dict = {}
        data_json = {}
        data_columns = {}
        if self.data_json and self.data_columns:
            data_json = json.load(open(self.data_json))
            for sample in data_json['samples']:
                if 'settings' in data_json['samples'][sample]:
                    data_json['samples'][sample]['settings'] = json.loads(data_json["samples"][sample]["settings"])
            data_columns = json.load(open(self.data_columns))
            if 'units' in data_columns:
                data_columns['units'] = dict(map(lambda v: (v.split(":")[0].split(".")[-1],
                                                            (v.split(":")[1], v.split(":")[0].split("."))),
                                                 data_columns['units']))
            if 'samples' in data_columns:
                data_columns['samples'] = dict(map(lambda v: (v.split(":")[0].split(".")[-1],
                                                              (v.split(":")[1], v.split(":")[0].split('.'))),
                                                   data_columns['samples']))
        elif self.data_json or self.data_columns:
            log.error("Both --data-json and --data-columns need to be specified at the same time, not only one of them.")
        for d in self.directory:
            dir_files_found = 0
            log.info(f"Dir: %s" % d)
            for f in glob.glob('%s/**/*.fastq.gz' % d, recursive=True):
                if "Undetermined" in f:
                    continue
                temp_filename = os.path.basename(f)
                try:
                    samplename = re.search(self.sample_regex, temp_filename).group(1)
                    read = re.search(self.read_number_regex, temp_filename).group(1)
                    first_part = re.split(self.read_number_regex, temp_filename)[0]
                    log.debug("sample name: {}, read part: {}".format(samplename, read))
                    if samplename not in file_dict:
                        file_dict[samplename] = {}
                    if first_part not in file_dict[samplename]:
                        file_dict[samplename][first_part] = {}
                    if read in file_dict[samplename][first_part]:
                        raise Exception(
                                    "Trying to add read (%s) for sample %s multiple times\n%s\n%s" %
                                    (read, samplename, f, file_dict[samplename][first_part][read]))
                    file_dict[samplename][first_part][read] = f
                    dir_files_found += 1
                    log.info("    found: %s" % f)
                except AttributeError:
                    log.debug("Couldn't extract sample name from: %s" % temp_filename)
            if dir_files_found == 0:
                log.warning("No fastq files found in '{}', "
                            "please make sure regex '{}' matches your file names!, and '{}' matches read number".
                            format(d, self.sample_regex, self.read_number_regex))
                exit(1)
            else:
                log.info("{} fastq files found".format(dir_files_found))
        result_dict = {}
        if self.validate_run_information:
            log.info("NOTE: fastq file will be parsed until end, could take some time for big files")
        log.info("Processing  found files, extracting run information and validation number of found reads:".format(str(f)))
        for sample in file_dict:
            for files in file_dict[sample]:
                if len(file_dict[sample][files]) % 2 != 0:
                    raise ValueError("Uneven number of files found:\n{}".format(str(file_dict[sample][files])))
                for read_number, f in file_dict[sample][files].items():
                    log.info("\t - {} for run information".format(str(f)))
                    machine_id, flowcell, lane_id, barcode = extract_run_information(f,
                                                                                     self.default_barcode,
                                                                                     self.number_of_reads,
                                                                                     self.every_n_reads,
                                                                                     self.occurrences_warning_th,
                                                                                     self.validate_run_information,
                                                                                     self.ask_for_input)
                    no_index_counter = 0
                    if sample in result_dict:
                        if flowcell in result_dict[sample]:
                            if barcode in result_dict[sample][flowcell]:
                                if lane_id in result_dict[sample][flowcell][barcode]:
                                    if 'reads' in result_dict[sample][flowcell][barcode][lane_id]:
                                        if read_number in result_dict[sample][flowcell][barcode][lane_id]['reads']:
                                            dup_file = result_dict[sample][flowcell][barcode][lane_id]['reads'][read_number]
                                            raise ValueError("sample, flowcell, lane and read number combination "
                                                             "found multiple times: sample {}"
                                                             " flowcell {} barcode {} lane {} read {}:\n - {}".
                                                             format(sample,
                                                                    flowcell,
                                                                    barcode,
                                                                    lane_id,
                                                                    read_number,
                                                                    "\n - ".join([f, dup_file])))
                                        else:
                                            result_dict[sample][flowcell][barcode][lane_id]['reads'][read_number] = f
                                    else:
                                        result_dict[sample][flowcell][barcode][lane_id]['reads'] = {read_number: f}
                                        result_dict[sample][flowcell][barcode][lane_id]['machine'] = machine_id
                                        result_dict[sample][flowcell][barcode][lane_id]['barcode'] = barcode
                                else:
                                    result_dict[sample][flowcell][barcode][lane_id] = {'reads': {read_number: f},
                                                                                       'machine': machine_id,
                                                                                       'barcode': barcode}
                            else:
                                result_dict[sample][flowcell][barcode] = {lane_id: {'reads': {read_number: f},
                                                                                    'machine': machine_id,
                                                                                    'barcode': barcode}}
                        else:
                            result_dict[sample][flowcell] = {barcode: {lane_id: {'reads': {read_number: f},
                                                                                 'machine': machine_id,
                                                                                 'barcode': barcode}}}
                    else:
                        result_dict[sample] = {flowcell: {barcode: {lane_id: {'reads': {read_number: f},
                                                                              'machine': machine_id,
                                                                              'barcode': barcode}}}}

        def extract_value(field, default, data):
            head, *tail = field
            if head not in data:
                return default
            if tail:
                return extract_value(tail, default, data[head])
            else:
                return data[head]

        samples_file_name = "samples.tsv"
        if self.post_file_modifier is not None:
            samples_file_name = "samples_{}.tsv".format(self.post_file_modifier)
        if os.path.isfile(samples_file_name):
            if not self.force:
                log.warn("File exists {} and force wasn't used".format(samples_file_name))
                exit(1)
            else:
                log.warn("File exists {} overwriting!!!".format(samples_file_name))
        with open(samples_file_name, "w") as output:
            header = ["sample"]
            if data_columns and "samples" in data_columns:
                header += data_columns["samples"].keys()
            elif self.tc:
                header.append('tumor_content')
            output.write("\t".join(header))
            for sample, data in sorted(file_dict.items()):
                row_data = [sample]
                if data_columns and "samples" in data_columns:
                    for _, value in data_columns['samples'].items():
                        row_data.append(extract_value(value[1][2:], value[0], data_json['samples'][sample]))
                elif self.tc:
                    row_data.append(self.tc)
                output.write("\n{}".format("\t".join(map(lambda x: str(x), row_data))))
        units_file_name = "units.tsv"
        if self.post_file_modifier is not None:
            units_file_name = "units_{}.tsv".format(self.post_file_modifier)
        if os.path.isfile(units_file_name):
            if not self.force:
                log.warn("File exists {} and force wasn't used".format(units_file_name))
                exit(1)
            else:
                log.warn("File exists {} overwriting!!!".format(units_file_name))

        with open(units_file_name, "w") as output:
            extra_header_columns = []
            if 'units' in data_columns:
                extra_header_columns = list(data_columns['units'].keys())
                if 'type' in extra_header_columns:
                    extra_header_columns.remove("type")
                if 'platform' in extra_header_columns:
                    extra_header_columns.remove("platform")
                if 'adapter' in extra_header_columns:
                    extra_header_columns.remove("adapter")
            output.write("\t".join(["sample", "type", "platform", "barcode", "machine",
                                    "flowcell", "lane", "fastq1", "fastq2", "adapter"] + extra_header_columns))
            for sample in sorted(result_dict):
                for flowcell in sorted(result_dict[sample]):
                    for barcode in sorted(result_dict[sample][flowcell]):
                        for lane, data in sorted(result_dict[sample][flowcell][barcode].items()):
                            if len(data['reads'].keys()) != 2:
                                raise ValueError("Incorrect number of fastq-files: {}:\n - {}".format(
                                    len(data['reads'].keys()), "\n - ".join(
                                        "{}: {}".format(k, data['reads'][k]) for k in data['reads'])))
                            sample_type = self.sample_type
                            s_type = sample_type
                            s_platform = self.platform
                            s_adapters = self.adapters
                            extra_data = []
                            if data_json and 'units' in data_columns:
                                extra_columns = list(data_columns['units'].keys())
                                if 'type' in extra_columns:
                                    value = data_columns['units']['type']
                                    s_type = extract_value(value[1][2:], value[0], data_json['samples'][sample])
                                    extra_columns.remove('type')
                                if 'platform' in extra_columns:
                                    value = data_columns['units']['platform']
                                    s_platform = extract_value(value[1][2:], value[0], data_json['samples'][sample])
                                    extra_columns.remove('platform')
                                if 'adapter' in extra_columns:
                                    value = data_columns['units']['adapter']
                                    extra_columns.remove('adapter')
                                    s_adapters = extract_value(value[1][2:], value[0], data_json['samples'][sample])
                                for column in extra_columns:
                                    value = data_columns['units'][column]
                                    extra_data.append(extract_value(value[1][2:], value[0], data_json['samples'][sample]))
                            elif self.tc:
                                header.append('tumor_content')

                            output.write("\n"+"\t".join([sample,
                                                         s_type,
                                                         s_platform,
                                                         data['barcode'],
                                                         data['machine'],
                                                         flowcell,
                                                         "L" + lane.rjust(3, '0'),
                                                         str(data['reads']["1"]),
                                                         str(data['reads']["2"]),
                                                         s_adapters] + extra_data))


def extract_run_information(file_path, default_barcode=None, number_of_reads=200, every_n_reads=1000, warning_threshold=0.9,
                            compare_first_and_last_read=False, ask_for_input=False):
    """
    extract information from provided fastq.gz file and creates a consensus create_barcode

    :param file_path: path to fastq.gz file
    :type file_path: string
    :param default_barcode: barcode string used when a barcode can not be extracted
    :type default_barcode: string
    :param number_of_reads: number of reads that will be used to create consensus barcode
    :type number_of_reads: integer
    :param: warning_threshold: raise a warning for char with lower occurences this value
    :type warning_threshold: float
    :param compare_first_and_last_read: compare first read with last read to detect merged lanes or flowcells

    :return: (machine_id, flowcell_id, lane, consensus_barcode)
    :rtype: tuple
    """

    def extract_barcode(line):
        """
        extract barcode from read name

        :param line: readname, ex @A00687:159:HLCNMDRXY:1:2101:2320:1000:GCC+AGG 1:N:0:CGCTCTAT+TTGCAACG
        :type line: string

        :return: barcode from read name
        :rtype: string
        """
        return re.sub('[12/]+$', '', line.decode("utf-8").split(":")[-1])

    def count_bases(data, barcode, length):
        """
        iterate over barcode and increate data counter

        :param data: data structure representing each position in the barcode,
                     ex [[{'A': 0, 'C': 0, 'G': 0, 'T': 0, 'N': 0, '+': 0} ...]
        :typa data: list of dicts
        :param barcode: barcode added to data structure, ex ACGT+GTCA
        :type barcode: string
        :param length: length of barcode

        :return: updated version of data structure
        :rtype: list of dicts
        """
        for i in range(length):
            if barcode[i] == 'A':
                data[i]['A'] += 1
            elif barcode[i] == 'C':
                data[i]['C'] += 1
            elif barcode[i] == 'G':
                data[i]['G'] += 1
            elif barcode[i] == 'T':
                data[i]['T'] += 1
            elif barcode[i] == 'N':
                data[i]['N'] += 1
            elif barcode[i] == '+':
                data[i]['+'] += 1
        return data

    def extract_run_informatio(line):
        """
        extract information from read name

        :param line: read name, ex @A00687:159:HLCNMDRXY:1:2101:2320:1000:GCC+AGG 1:N:0:CGCTCTAT+TTGCAACG
        :return tuple with (machine_id, flowcell_id, lane)
        :rtype: tuple
        """
        columns = line.decode("utf-8").split(":")
        return (columns[0], columns[2], columns[3])

    def create_barcode(data, length, number_of_reads, warning_threshold=0.9):
        """
        from data a barcode will be generate. Warnings will be raised for consensus chars that have a lower occurences then
        the provided threshold.

        :param data: data structure representing each position in the barcode,
                     ex [[{'A': 0, 'C': 0, 'G': 0, 'T': 0, 'N': 0, '+': 0} ...]
        :typa data: list of dicts
        :param length: length of barcode
        :type length: integer
        :param number_of_reads: number of reads that have been use to create data
        :type number_of_reads: integer
        :param: warning_threshold: raise a warning for char with lower occurences this value
        :type warning_threshold: float

        :return: consensus barcode
        :rtype: string
        """
        barcode = ""
        for i in range(length):
            max_base = max(data[i], key=data[i].get)
            if list(data[i].values()).count(data[i][max_base]) > 1:
                raise Exception("Multiple base with same occurences: {}. UNABLE to handle exiting!".format(data[i]))
            max_base_n = data[i][max_base]
            if max_base_n / number_of_reads < warning_threshold:
                logging.warning('Consesuns base {} occurences {:.1%} at position {} in barcode, file {}'.
                                format(max_base, max_base_n / number_of_reads, i, file_path))
            barcode += max_base
        return barcode

    def ask_user_for_input(message, question):
        """
        Function used to ask user for input, retries once if no input is given.
        """
        counter = 2
        user_input = ''
        print(message)
        while counter > 0 and len(user_input) == 0:
            user_input = input(question).rstrip()
            counter -= 1
        if len(user_input) == 0:
            raise Exception("No input entered!!!")
        if '_' in user_input:
            logging.warning("Replacing all occurences of '_' with '-' in {}".format(user_input))
            user_input = user_input.replace("_", "-")
        return user_input

    def skip_read_information(reader_it):
        """
        used to skip read sequence and quality lines
        """
        next(reader_it)
        next(reader_it)
        next(reader_it)

    with gzip.open(file_path, "rb") as reader:
        counter = number_of_reads
        every = every_n_reads  # only look at every n read
        reader_it = iter(reader)
        # Parse first read
        line = next(reader_it).rstrip()
        # Extract machine id, flowcell and lane
        machine_id, flowcell_id, lane = extract_run_informatio(line)
        barcode = extract_barcode(line)
        if not re.match('^[A-Z-+]+$', barcode):
            if default_barcode is not None:
                return (machine_id, flowcell_id, lane, default_barcode)
            else:
                raise Exception("Undable to extract barcode from read name and no default barcode specified")
        skip_read_information(reader_it)
        counter -= 1
        length = len(barcode)
        # data structure used to store counts for each barcode
        data = [{'A': 0, 'C': 0, 'G': 0, 'T': 0, 'N': 0, '+': 0} for i in range(length)]
        data = count_bases(data, barcode, length)
        last_read = line
        for line in reader_it:
            if every == 0:
                every = every_n_reads
                line = line.rstrip()
                last_read = line
                data = count_bases(data, extract_barcode(line), length)
                skip_read_information(reader_it)
                counter -= 1
                if counter == 0:
                    break
                continue
            else:
                line = line.rstrip()
                last_read = line
                skip_read_information(reader_it)
                every -= 1
        if counter > 0:
            logging.warning("Could only select {} reads of {} from fastq file {} for evaluation!".
                            format(number_of_reads - counter, number_of_reads, file_path))
        if compare_first_and_last_read:
            if counter == 0:
                for last_read in reader_it:
                    skip_read_information(reader_it)
            data = count_bases(data, extract_barcode(last_read), length)
            last_machine_id, last_flowcell_id, last_lane = extract_run_informatio(last_read)
            if last_machine_id != machine_id:
                if ask_for_input:
                    last_machine_id = ask_user_for_input("Multiple machines found in fastq file, {} and {}\n".
                                                         format(last_machine_id, machine_id),
                                                         "Enter machine id that should be used:")
                else:
                    raise Exception("Multiple machines found in fastq file, {} and {}".format(last_machine_id, machine_id))
            if last_flowcell_id != flowcell_id:
                if ask_for_input:
                    last_flowcell_id = ask_user_for_input("Multiple flowcells found in fastq file, {} and {}".
                                                          format(last_flowcell_id, flowcell_id),
                                                          "Enter flowcell id that should be used:")
                else:
                    raise Exception("Multiple flowcells found in fastq file, {} and {}".format(last_flowcell_id, flowcell_id))
            if last_lane != lane:
                logging.warning("First read and last read have different lane numbers {} vs {}, lane will be set to 0!".
                                format(last_lane, lane))
            return (last_machine_id, last_flowcell_id, "0", create_barcode(data, length, number_of_reads - counter, warning_threshold))
        return (machine_id, flowcell_id, lane, create_barcode(data, length, number_of_reads - counter, warning_threshold))
