import click
import logging
import os
import shutil
import subprocess
import sys
import yaml

from snakemake.common import is_local_file

from hydra_genetics.utils.software_versions import iter_container_entries


def create_docker_file_path(storage_path, container):
    return os.path.join(storage_path, container.replace('docker://', '').replace("/", "__").replace(":", "_") + ".sif")


@click.group("prepare-environment", short_help="prepare for singularity environment")
def environment():
    pass


@environment.command(short_help="update config with path to container cache")
@click.option(
    "-c",
    "--configfile",
    prompt="config.yaml path",
    required=True,
    type=str,
    help="config file used to find pipeline containers",
)
@click.option(
    "-n",
    "--new-configfile",
    prompt="path",
    required=True,
    type=str,
    help="path to update config file",
)
@click.option(
    "-p",
    "--singularity-cache-path",
    prompt="singularity cache path",
    required=True,
    type=str,
    help="path to where singularity files are stored",
)
def container_path_update(configfile, new_configfile, singularity_cache_path):
    with open(configfile, "r") as stream:
        try:
            yaml_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)

    for parent, key, value in iter_container_entries(yaml_data):
        if is_local_file(value):
            logging.info(f"Keeping {value}: already a local image")
            continue
        parent[key] = create_docker_file_path(singularity_cache_path, value)

    with open(new_configfile, 'w') as file:
        for key, value in yaml_data.items():
            file.write(yaml.dump({key: value}))
            file.write("\n")


@environment.command(short_help="update search path to reference files")
@click.option(
    "-c",
    "--configfile",
    prompt="config.yaml path",
    required=True,
    type=str,
    help="config file used to find pipeline containers",
)
@click.option(
    "-n",
    "--new-configfile",
    prompt="path",
    required=True,
    type=str,
    help="path to update config file",
)
@click.option(
    "--reference-path",
    multiple=True,
    prompt="path",
    required=True,
    type=str,
    help=(
        "format oldpath:newpath, will iterate over the provided config"
        " file and replace all occurrences of oldpath with new path"
    ),
)
def reference_path_update(configfile, new_configfile, reference_path):
    def process_yaml_data(yaml_data, reference_path):
        for key in yaml_data:
            if isinstance(yaml_data[key], dict):
                yaml_data[key] = process_yaml_data(yaml_data[key], reference_path)
            else:
                if isinstance(yaml_data[key], str):
                    for old_path, new_path in reference_path:
                        if old_path in yaml_data[key]:
                            yaml_data[key] = yaml_data[key].replace(old_path, new_path)
        return yaml_data
    reference_paths = [r.split(":") for r in reference_path]
    with open(configfile, "r") as stream:
        try:
            yaml_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)

    yaml_data = process_yaml_data(yaml_data, reference_paths)

    with open(new_configfile, 'w') as file:
        for key, value in yaml_data.items():
            file.write(yaml.dump({key: value}))
            file.write("\n")


@environment.command(short_help="create singularity containers")
@click.option(
    "-c",
    "--configfile",
    prompt="config.yaml path",
    required=True,
    type=str,
    help="config file used to find pipeline containers",
)
@click.option(
    "-o",
    "--output-folder",
    prompt="folder path",
    required=True,
    type=str,
    help="output folder where files will be stored",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="rebuild images that already exist in the output folder",
)
def create_singularity_files(configfile, output_folder, force):
    yaml_data = None
    with open(configfile, "r") as stream:
        try:
            yaml_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

    containers = sorted({value for _, _, value in iter_container_entries(yaml_data)})

    if os.path.exists(output_folder):
        if not os.path.isdir(output_folder):
            raise IOError(f"{output_folder} is not a folder")
    else:
        os.makedirs(output_folder)

    if containers and shutil.which("singularity") is None:
        logging.error("singularity could not be found on PATH")
        sys.exit(1)

    failed = []
    for container in containers:
        if is_local_file(container):
            logging.info(f"Skipping {container}: already a local image")
            continue
        file_path = create_docker_file_path(output_folder, container)
        if os.path.exists(file_path) and not force:
            logging.info(f"Skipping {file_path}: already exists, use --force to rebuild")
            continue
        command = ["singularity", "build"] + (["--force"] if force else []) + [file_path, container]
        logging.info(f"Create singularity {file_path}")
        if subprocess.run(command).returncode != 0:
            logging.error(f"Failed to build {file_path} from {container}")
            failed.append(container)

    if failed:
        logging.error("Failed to build singularity images for: " + ", ".join(failed))
        sys.exit(1)
