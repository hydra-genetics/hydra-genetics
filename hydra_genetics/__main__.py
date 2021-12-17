
import click
import logging
import os
import re
import sys

import hydra_genetics.utils
from hydra_genetics.commands.create import PipelineCreate, RuleCreate, CreateInputFiles
import rich.console
import rich.logging
import rich.traceback

# Set up logging as the root logger
# Submodules should all traverse back to this
log = logging.getLogger()


def rich_force_colors():
    """
    Check if any environment variables are set to force Rich to use coloured output
    """
    if os.getenv("GITHUB_ACTIONS") or os.getenv("FORCE_COLOR") or os.getenv("PY_COLORS"):
        return True
    return None


def run():
    # Set up rich stderr console
    stderr = rich.console.Console(stderr=True, force_terminal=rich_force_colors())

    # Set up the rich traceback
    rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)

    stderr.print("\u001b[36m" + r'  _  _  _  _  ____  ____   __         ___  ____  __ _  ____  ____  __  ___  ____ ',
                 highlight=False)
    stderr.print("\u001b[36m" + r' / )( \( \/ )(    \(  _ \ / _\  ___  / __)(  __)(  ( \(  __)(_  _)(  )/ __)/ ___) ',
                 highlight=False)
    stderr.print("\u001b[36m" + r' ) __ ( )  /  ) D ( )   //    \(___)( (_ \ ) _) /    / ) _)   )(   )(( (__ \___ \ ',
                 highlight=False)
    stderr.print("\u001b[36m" + r' \_)(_/(__/  (____/(__\_)\_/\_/      \___/(____)\_)__)(____) (__) (__)\___)(____/ ',
                 highlight=False)
    stderr.print("\u001b[36m hydra-core/tools version {}\033[0m\n\n".format(hydra_genetics.__version__), highlight=False)

    cli()


@click.group(help="CLI tool to prepare and initialize snakemake projects")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Print verbose output to the console.")
@click.option("-l", "--log-file", help="Save a verbose log to a file.", metavar="<filename>")
def cli(verbose, log_file):
    log.setLevel(logging.DEBUG)

    log.addHandler(
        rich.logging.RichHandler(
            level=logging.DEBUG if verbose else logging.INFO,
            console=rich.console.Console(stderr=True, force_terminal=rich_force_colors()),
            show_time=False,
            markup=True,
        )
    )

    if log_file:
        log_fh = logging.FileHandler(log_file, encoding="utf-8")
        log_fh.setLevel(logging.DEBUG)
        log_fh.setFormatter(logging.Formatter("[%(asctime)s] %(name)-20s [%(levelname)-7s]  %(message)s"))
        log.addHandler(log_fh)


def validate_wf_name_prompt(ctx, opts, value):
    """Force the workflow name to meet the hydra-core requirements"""
    if not re.match(r"^[a-z_]+$", value):
        click.echo("Invalid workflow name: must be lowercase without punctuation.")
        value = click.prompt(opts.prompt)
        return validate_wf_name_prompt(ctx, opts, value)
    return value


def validate_rule_name_prompt(ctx, opts, value):
    """Force the rule name to meet the hydra-core requirements"""
    if not re.match(r"^[a-z0-9_]+$", value):
        click.echo("Invalid workflow name: must be lowercase ('_' is allowed) without punctuation.")
        value = click.prompt(opts.prompt)
        return validate_rule_name_prompt(ctx, opts, value)
    return value


@cli.command(short_help="create bare bone project")
@click.option(
    "-n",
    "--name",
    prompt="Workflow Name",
    required=True,
    callback=validate_wf_name_prompt,
    type=str,
    help="The name of your new pipeline",
)
@click.option("-d", "--description", prompt=True, required=True, type=str, help="A short description of your pipeline")
@click.option("-a", "--author", prompt=True, required=True, type=str, help="Name of the main author(s)")
@click.option("-e", "--email", prompt=True, required=True, type=str, help="E-mail(s) of the main author(s)")
@click.option("--version", type=str, default="0.0.1", help="The initial version number to use")
@click.option("--min-snakemake-version", type=str, default="6.8.0", help="Min snakemake version")
@click.option("-g", "--git-user", prompt=True, required=True, help="User name of main git user(s)")
@click.option("--no-git", is_flag=True, default=False, help="Do not create git repo")
@click.option("-f", "--force", is_flag=True, default=False, help="Overwrite output directory if it already exists")
@click.option("-o", "--outdir", type=str, help="Output directory for new pipeline (default: pipeline name)")
def create_module(name, description, author, email, version, min_snakemake_version, git_user, no_git, force, outdir):
    pipeline = PipelineCreate(name, description, author, email, version, min_snakemake_version, git_user, no_git, force, outdir)
    pipeline.init_pipeline()


@cli.command(short_help="add rule to project")
@click.option(
    "-n",
    "--name",
    prompt="rule name",
    required=True,
    callback=validate_rule_name_prompt,
    type=str,
    help="name of rule that will be added",
)
@click.option(
    "-m",
    "--module",
    prompt="name of module/workflow",
    required=True,
    callback=validate_wf_name_prompt,
    type=str,
    help="name module/workflow where rule will be added. Expected folder structure is module_name/workflow/, "
         " the rule will be added to a subfolder named rules, env.yaml to a subfolder named envs.")
@click.option(
        "-a",
        "--author",
        prompt=True,
        required=True,
        type=str,
        help="Name of the main author(s)")
@click.option(
        "-e",
        "--email",
        prompt=True,
        required=True,
        type=str,
        help="E-mail(s) of the main author(s)")
@click.option(
        "-o",
        "--outdir",
        type=str,
        help="Output directory for where rule will be added (default: current dir)")
def create_rule(name, module, author, email, outdir):
    rule = RuleCreate(name, module, author, email, outdir)
    rule.init_rule()


@cli.command(short_help="create inpu-files, samples.tsv and units.tsv")
@click.option(
    "-d",
    "--directory",
    multiple=True,
    prompt="directory/directories",
    required=True,
    type=str,
    help="path to dir where fastq-files should be looked for.")
@click.option(
        "-o",
        "--outdir",
        type=str,
        help="Output directory for where rule will be added (default: current dir)")
@click.option(
        "-p",
        "--platform",
        type=str,
        help="Sequence platform that the data originate from, ex nextseq, miseq. Default Illumina",
        default="Illumina")
@click.option(
        "-r",
        "--run",
        type=str,
        help="Sequence run id, something used to identify where data originate from, ex data, flowcell id. Could also be a regex "
             "used to extract run id from file path (need to contain '(' and ')', ex \".*([0-9]+_[A_Z]+).*\".",
        default="RUN")
@click.option(
        "-l",
        "--lane-identifier",
        type=str,
        help="Identifier for lane, either a string or a regex that will extract lane identifier from file "
             "name, ex \"_(L[0-9]*)_\"",
        default="L000")
@click.option(
        "-t",
        "--sample-type",
        type=str,
        help="Sample type, N|T|R, default T",
        default="T")
@click.option(
        "-s",
        "--sample-regex",
        type=str,
        help="Regex used to extract sample from filename, default '([A-Za-z0-9-]+)_S[0-9]+_R[12]{1}_001.fastq.gz$'",
        default="^([A-Za-z0-9-]+)_S[0-9]+_(R[12]{1})_001.fastq.gz")
@click.option(
        "-n",
        "--read-number-regex",
        type=str,
        help="Regex used to extract read number from filename (note only number value), default '_R([1-2]{1})_001'",
        default="_R([12]{1})_")
@click.option(
        "-a",
        "--adapters",
        type=str,
        help="adapter sequence, comma sepearated",
        default="AGATCGGAAGAGCACACGTCTGAACTCCAGTCA,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT")
@click.option(
        "--post-file-modifier",
        type=str,
        help="add string to output files",
        default=None)
@click.option(
        "--force",
        help="overwrite existing files",
        is_flag=True)
@click.option(
        "--tc",
        help="tumor contet",
        type=float,
        default=1.0)
def create_input_files(directory, outdir, post_file_modifier, platform, run, sample_type,
                       sample_regex, read_number_regex, lane_identifier, adapters, tc, force):
    input_files = CreateInputFiles(directory, outdir, post_file_modifier, platform, run, sample_type,
                                   sample_regex, read_number_regex, lane_identifier, adapters, tc, force)
    input_files.init()


@cli.command(short_help="download reference data")
def referece_data():
    pass


if __name__ == "__main__":
    run()
