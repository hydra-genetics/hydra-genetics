#!/usr/bin/env python
"""Creates a hydra-core pipeline matching the current
organization's specification based on a template.
"""

import logging
import jinja2
import pathlib
import os
import sys

log = logging.getLogger(__name__)


class PipelineCreate(object):
    """Creates a hydra-core pipeline.
    Args:
        name (str): Name for the pipeline.
        description (str): Description for the pipeline.
        author (str): Authors name of the pipeline.
        version (str): Version flag. Semantic versioning only. Defaults to `1.0dev`.
        no_git (bool): Prevents the creation of a local Git repository for the pipeline. Defaults to False.
        force (bool): Overwrites a given workflow directory with the same name. Defaults to False.
            May the force be with you.
        outdir (str): Path to the local output directory.
    """
    def __init__(self, name, description, author, email, version="0.0.1", git_user=None, nogit=False, force=False, outdir=None):
        self.short_name = name.lower().replace(r"/\s+/", "-").replace("hydra_core/", "").replace("/", "-")
        self.name = f"hydra_core/{self.short_name}"
        self.description = description
        self.author = author
        self.email = email
        self.version = version
        self.git_user = git_user
        self.no_git = no_git
        self.force = force
        self.outdir = outdir
        if not self.outdir:
            self.outdir = os.path.join(os.getcwd(), self.name)

    def init_pipeline(self):
        """Creates the hydra_core pipeline."""

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
           loader=jinja2.PackageLoader("hydra_core", "pipeline-template"), keep_trailing_newline=True
        )

        template_dir = os.path.join(os.path.dirname(__file__), "../pipeline-template")
        object_attrs = vars(self)
        template_files = list(pathlib.Path(template_dir).glob("**/*"))
        template_files += list(pathlib.Path(template_dir).glob("*"))
        ignore_strs = [".pyc", "__pycache__", ".pyo", ".pyd", ".DS_Store", ".egg", ".snakemake"]

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
