#!/usr/bin/env python
"""Creates a hydra-core pipeline matching the current
organization's specification based on a template.
"""

from datetime import date
import git
import logging
import jinja2
import pathlib
import os
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
        self.name = f"hydra_genetics/{self.short_name}"
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
