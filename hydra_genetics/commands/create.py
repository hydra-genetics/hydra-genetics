#!/usr/bin/env python
"""Creates a hydra-core pipeline matching the current
organization's specification based on a template.
"""

from datetime import date
import git
import glob
import logging
import jinja2
import pathlib
import os
import re
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
    def __init__(self, name, description, author, email, version="0.0.1", min_snakemake_version="6.8.0",
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
        repo = git.Repo.init(self.outdir)
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
        name (str): Name for the pipeline.
        module (str): Name of module where rule will be added.
        author (str): Authors name
        email (str): Authors email
        outdir (str): Path to the local output directory.
    """
    def __init__(self, name, module, author, email, outdir=None):
        self.name = name
        self.module_name = module
        self.author = author
        self.email = email
        self.year = date.today().year
        self.outdir = outdir

        if not self.outdir:
            self.outdir = os.getcwd()

    def init_rule(self):
        """Creates the hydra_genetics rule."""
        log.info(f"Creating rule: {self.outdir}/{self.module_name}/workflow/rules/{self.name}.smk")
        outdir = os.path.join(self.outdir, self.module_name, "workflow")
        output_rules = os.path.join(self.outdir, self.module_name, "workflow", "rules")
        output_envs = os.path.join(self.outdir, self.module_name, "workflow", "envs")
        if not os.path.exists(output_rules):
            log.error(f"Can not find output directory '{output_rules}'")
            sys.exit(1)
        if not os.path.exists(output_envs):
            log.error(f"Can not find output directory '{output_envs}' exists!")
            sys.exit(1)
        output_rule = os.path.join(output_rules, f"{self.name}.smk")
        output_env = os.path.join(output_envs, f"{self.name}.yaml")
        if os.path.exists(output_rule):
            log.error(f"Rule already exists '{output_rule}'")
            sys.exit(1)
        if os.path.exists(output_env):
            log.error(f"env file already exists '{output_env}'")
            sys.exit(1)
        env = jinja2.Environment(
            loader=jinja2.PackageLoader("hydra_genetics", "rule-template"), keep_trailing_newline=True
        )
        template_dir = os.path.join(os.path.dirname(__file__), "../rule-template")
        rename_files = {
           "skeleton_env.yaml": os.path.join("envs", f"{self.name}.yaml"),
           "skeleton_rule.smk": os.path.join("rules", f"{self.name}.smk"),
        }
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
            output_path = os.path.join(outdir, template_fn)
            if template_fn in rename_files:
                output_path = os.path.join(outdir, rename_files[template_fn])

            log.debug(f"Rendering template file: '{template_fn}'")
            j_template = env.get_template(template_fn)
            rendered_output = j_template.render(object_attrs)

            # Write to the pipeline output file
            with open(output_path, "w") as fh:
                log.debug(f"Writing to output file: '{output_path}'")
                fh.write(rendered_output)
        snakefile = os.path.join(outdir, "Snakefile")
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
            lines.insert(line_number, str(f"include: \"rules/{self.name}.smk\"\n"))
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
                 run="RUN",
                 sample_type="T",
                 sample_regex="^([A-Za-z0-9-]+)_S[0-9]+_R[12]{1}_001.fastq.gz",
                 read_number_regex="^[A-Za-z0-9-]+_S[0-9]+_(R[12]{1})_001.fastq.gz",
                 lane_identifier="_(L[0-9]+)_",
                 adapters="AGATCGGAAGAGCACACGTCTGAACTCCAGTCA,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
                 tc=1.0,
                 force=False):
        self.directory = directory
        self.outdir = outdir
        self.post_file_modifier = post_file_modifier
        self.run = run
        self.platform = platform
        self.sample_type = sample_type
        self.sample_regex = sample_regex
        self.read_number_regex = read_number_regex
        self.lane_identifier = lane_identifier
        self.adapters = adapters
        self.tc = tc
        self.force = force

        if not self.outdir:
            self.outdir = os.getcwd()

    def init(self):
        """Creates the hydra_genetics rule."""
        log.info(f"Searching for fastq-files:")
        file_dict = {}
        platform = self.platform
        sample_type = self.sample_type
        run = self.run
        run_is_regex = True if re.search(".*[(].+[)].*", run) else False
        for d in self.directory:
            dir_files_found = 0
            log.info(f"Dir: %s" % d)
            for f in glob.glob('%s/**/*.fastq.gz' % d, recursive=True):
                if "Undetermined" in f:
                    continue
                temp_filename = os.path.basename(f)
                try:
                    run_value = run
                    if run_is_regex:
                        run_value = re.search(run, f)
                        if run_value:
                            run_value = run_value.group(1)
                        else:
                            raise ValueError("Unable to extract run info from:\n{}\nwith regex: {}".format(temp_filename, run))
                    samplename = re.search(self.sample_regex, temp_filename).group(1)
                    read = re.search(self.read_number_regex, temp_filename).group(1)
                    if run_value not in file_dict:
                        file_dict[run_value] = {}
                    if samplename in file_dict[run_value]:
                        if read in file_dict[run_value][samplename]:
                            raise Exception(
                                    "Trying to add read (%s) for sample %s multiple times\n%s\n%s" %
                                    (read, samplename, f, file_dict[samplename][read]))
                        file_dict[run_value][samplename].append(f)
                        dir_files_found += 1
                    else:
                        file_dict[run_value][samplename] = [f]
                        dir_files_found += 1
                    log.info("    found: %s" % f)
                except AttributeError:
                    log.debug("Couldn't extract sample name from: %s" % temp_filename)
            if dir_files_found == 0:
                log.warning("No fastq files found in '{}', "
                            "please make sure regex '{}' matches your file names!".format(d, self.sample_regex))
            else:
                log.info("{} fastq files found".format(dir_files_found))

        def lane_identifier(x): return self.lane_identifier

        if re.search(".*[(].+[)].*", self.lane_identifier):
            def lane_identifier(x): return re.search(self.lane_identifier, x).group(1)

        lane = lane_identifier

        for run_key in file_dict:
            for sample in file_dict[run_key]:
                if len(file_dict[run_key][sample]) % 2 != 0:
                    raise ValueError("Uneven number of files found:\n{}".format(str(file_dict[run_key][sample])))
                lane_dict = dict()
                no_index_counter = 0
                for f in file_dict[run_key][sample]:
                    read_number = re.search(self.read_number_regex, f).group(1)
                    lane_id = lane(f)
                    if lane_id in lane_dict:
                        if read_number in lane_dict[lane_id]:
                            raise ValueError(
                                "s index and read number combination found multiple times: index {} read {}:\n - {}".format(
                                     lane_id,
                                     read_number,
                                     "\n - ".join(
                                         [f, lane_dict[lane_id][read_number]])))
                        lane_dict[lane_id][read_number] = f
                    else:
                        lane_dict[lane_id] = {read_number: f}
                file_dict[run_key][sample] = lane_dict
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
            output.write("\t".join(["sample", "TC"]))
            for run_key, data in sorted(file_dict.items()):
                for sample, sample_info in sorted(data.items()):
                    output.write("\n{}".format("\t".join([sample, str(self.tc)])))
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
            output.write("\t".join(["sample", "type", "platform", "run", "lane", "fastq1", "fastq2", "adapter"]))
            for run_key, values in sorted(file_dict.items()):
                for sample, data in sorted(file_dict[run_key].items()):
                    for lane in data:
                        if len(data[lane].keys()) != 2:
                            raise ValueError("Incorrect number of fastq-files: {}:\n - {}".format(
                                len(data[sample][lane].keys()), "\n - ".join(
                                    "{}: {}".format(k, data[lane][k]) for k in data[lane])))
                        output.write("\n"+"\t".join([sample, self.sample_type, self.platform, run_key, lane,
                                     str(data[lane]["1"]),
                                     str(data[lane]["2"]),
                                     self.adapters]))
