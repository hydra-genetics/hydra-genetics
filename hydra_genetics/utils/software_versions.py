import hashlib
import logging
import os
import re
import subprocess
import yaml

from datetime import datetime
from snakemake.common import is_local_file


def get_container_prefix(workflow):
    '''
    Function used to fetch singularity cache location
    '''

    if hasattr(workflow, 'use_singularity'):
        # Fetch singularity prefix for snakemake version with version less
        # then 8
        if hasattr(workflow, 'singularity_prefix'):
            return workflow.singularity_prefix
        else:
            return ".snakemake/singularity"
    elif hasattr(workflow, 'deployment_settings'):
        # Fetch singularity prefix for snakemake version with equal to 8.0 or newer
        if workflow.deployment_settings.apptainer_prefix is None:
            return ".snakemake/singularity"
        else:
            return workflow.deployment_settings.apptainer_prefix
    return None


def get_software_version_from_labels(image_path):
    '''
    Function used to create a list of software version used in a singularity image,
    usually created from a docker image. The software name and version will be extracted
    from labels that have been set in the container.  The expected format is
    ([A-Za-z0-9-_.]+): ([0-9.]+)$, where the first section is the software name
    and second part is the version. In the dockerfile the labels could look like this
    LABEL gatk4=4.11.0

    Parameters
    ----------
    image_path: str
       path to the image that will be inspected

    Returns:
    --------
    list of tuples where each tuple consist of software name and software version.

    '''
    cmd = ["singularity", "inspect", image_path]
    software_version_list = []
    for row in subprocess.check_output(cmd).decode().split("\n"):
        if not row.startswith("org.label-schema") and not row.startswith("maintainer"):
            software_version = re.match("^([A-Za-z0-9-_.]+): ([0-9.]+)$", row)
            if software_version:
                software_version_list.append(software_version.groups())
    return software_version_list


def get_deffile(image_path):
    """
    Function used to extract from which docker image the singularity image was created.

    Parameters
    ----------
    image_path: str
       path to the image that will be inspected

    Returns
    -------
    docker image name "org/name:version or None if information couldn't be found.

    """
    cmd = ["singularity", "inspect", image_path]
    for row in subprocess.check_output(cmd).decode().split("\n"):
        if row.startswith("org.label-schema.usage.singularity.deffile.from"):
            return row.split(": ")[1]
    return None


def get_image_path(container, singularity_prefix_path):
    '''
    Function used to return a path to singularity a image. If it's a local file, .i.e
    a path to a file on the file system the path will be returned without modifications. If it's
    a singularity image that has been downloaded by snakemake the function will create
    the snakemake generated image name and path, which is the singularity prefix as storage
    location followed by a hashname (generated from the provided docker image name and location).

    Parameters
    ----------
    container: str
        either a path to a local file or image name and type, ex docker://hydragenetics/bcbio-vc:0.2.6
    :singularity_prefix_path: str
        storage path of singularity/apptainer images

    Returns
    -------
    str: path to locally store image
    '''
    if is_local_file(container):
        return container

    md5hash = hashlib.md5()
    md5hash.update(container.encode())
    return os.path.join(singularity_prefix_path, f"{md5hash.hexdigest()}.simg")


def use_container(workflow):
    '''
    Function used to check if containers are used,
    '''
    if hasattr(workflow, 'use_singularity'):
        # For snakemake with version less then 8
        return True
    elif hasattr(workflow, 'deployment_settings') and workflow.deployment_settings.deployment_method:
        # For snakemake with version 8 or newer
        from snakemake.settings import DeploymentMethod
        if DeploymentMethod.APPTAINER in workflow.deployment_settings.deployment_method:
            return True
        else:
            return False
    else:
        return False


def add_software_version_to_config(config, workflow, fail_missing_versions=True):
    '''
    Function that will look through the config dict to locate
    container definitions. When container information is found the
    softwares version will be extracted and added to the config.

    Parameters:
    config: dict
        snakemake dict object
    workflow: object
        snakemake workflow object
    fail_missing_versions: boolean
        if set to true an error will be raised if a container is specified
        and versions can't be extracted.

    Returns:
    a config where software_verions have been added
    '''
    container_cache = get_container_prefix(workflow)

    def _add_software_version(config, version_dict):

        def _create_container_name_version_string(image_informaiton):
            return "__".join(re.search(".+/([A-Za-z0-9-_.]+):[ ]*([A-Za-z0-9.-_]+$)", value).groups())

        logger = logging.getLogger(__name__)
        version_found = []
        for key, value in config.items():
            if isinstance(value, dict):
                config[key], version_dict = _add_software_version(value, version_dict)
            elif key in ["container", "default_container"]:
                image_path = get_image_path(value, container_cache)
                if os.path.isfile(image_path):
                    version_found += get_software_version_from_labels(image_path)
                    if not is_local_file(value):
                        name_and_version = _create_container_name_version_string(value)
                    else:
                        name_and_version = _create_container_name_version_string(get_software_version_from_labels(value))

                    if not version_found:
                        if fail_missing_versions:
                            raise Exception("could not extract software versions from {image_path}")
                        else:
                            logger.warning(f"could not extract software versions from {image_path}")
                            version_found = [name_and_version.split("__"), ('NOTE', 'version extract from image name and not labels')]
                else:
                    if fail_missing_versions:
                        raise Exception(f"could not locate local file {image_path} for {value}")
                    else:
                        logger.warning(f"could not locate local file {image_path} for {value}")
        if version_found:
            config['software_versions'] = {s: v for s, v in version_found}
            version_dict[name_and_version] = config['software_versions']
        return config, version_dict
    return _add_software_version(config, {})


def export_software_version_as_files(software_dict, directory="software_versions", file_name_ending="mqv_versions.yaml"):
    """
    Print software version to files. Requires a dict with key software_info which
    should contain a dict with software names and versions.

    Parameters:
    -----------
    config: dict
       dict with key software_info, ex {software_info: {'common_1.3': {'samtools': '1.3', 'picard': '1.6'}}}
    directory: str
       path where files will be written
    file_name_ending: str
       a string that will be combined with the software name version key
    """
    directory = f"{directory}_{datetime.now().strftime('%Y%m%d--%H-%M-%S')}.yaml"
    if not os.path.isdir(directory):
        os.mkdir(directory)
    for name in software_dict:
        with open(os.path.join(directory, f"{name}_{file_name_ending}"), 'w') as writer:
            notification = software_dict[name].pop('NOTE', None)
            writer.write(yaml.dump(software_dict[name]))
            if notification is not None:
                writer.write(f"# {notification}")
