import click
import logging
import os
import yaml


def create_docker_file_path(storage_path, container):
    return os.path.join(storage_path, container.replace('docker://', '').replace("/", "_").replace(":", "_") + ".sif")


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
    help="path to where singulariy files are stored",
)
def container_path_update(configfile, new_configfile, singularity_cache_path):
    with open(configfile, "r") as stream:
        try:
            yaml_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)

    for key in yaml_data:
        if 'container' in key:
            yaml_data[key] = create_docker_file_path(singularity_cache_path, yaml_data[key])
        elif isinstance(yaml_data[key], dict):
            if 'container' in yaml_data[key]:
                yaml_data[key]['container'] = create_docker_file_path(singularity_cache_path, yaml_data[key]['container'])

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
def create_singularity_files(configfile, output_folder):
    yaml_data = None
    with open(configfile, "r") as stream:
        try:
            yaml_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)

    containers = set()
    for key in yaml_data:
        if "container" in key:
            containers.add(yaml_data[key])
        elif isinstance(yaml_data[key], dict):
            if 'container' in yaml_data[key]:
                containers.add(yaml_data[key]['container'])

    if os.path.exists(output_folder):
        if os.path.isdir(output_folder):
            pass
        else:
            raise IOError(f"{output_folder} is not a folder")
    else:
        os.mkdir(output_folder)

    for container in containers:
        file_path = create_docker_file_path(output_folder, container)
        logging.info(f"Create singularity {file_path}")
        os.system(f"singularity build {file_path} {container}")
