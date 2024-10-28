import git
import hashlib
import logging
import os
import re
import subprocess
import yaml

from datetime import datetime
from snakemake.common import is_local_file


def _create_container_name_version_string(image_information):
    if image_information.endswith(".sif"):
        container_name_and_version = re.search(r"__([A-Za-z0-9-]+)_([A-Za-z0-9.-]+)\.sif$", image_information)
        if container_name_and_version:
            return "_".join(container_name_and_version.groups())
        else:
            container_name = re.search(r"([A-Za-z0-9-]+)\.sif$", image_information)
            if container_name:
                return "_".join([container_name.groups()[0], "NoVersion"])
            else:
                raise Exception(f"Unable to extract container name from {image_information}")
    else:
        container_name_and_version = re.search("/([A-Za-z0-9-_.]+):[ ]*([A-Za-z0-9-_.]+)$", image_information)
        if container_name_and_version:
            return "_".join(container_name_and_version.groups())
        else:
            container_name = re.search("/([A-Za-z0-9-]+)$", image_information)
            if container_name:
                return "_".join([container_name.groups()[0], "NoVersion"])
            else:
                raise Exception(f"Unable to extract container name from {image_information}")


def add_version_files_to_multiqc(config, file_list):
    if "multiqc" in config.keys():
        for report in config["multiqc"]["reports"]:
            config["multiqc"]["reports"][report]["qc_files"] += file_list
    else:
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not find key multiqc in configuration.")


def _touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, "a").close()


def get_container_prefix(workflow):
    """
    Function used to fetch singularity cache location
    """

    if hasattr(workflow, "use_singularity"):
        # Fetch singularity prefix for snakemake version with version less
        # then 8
        if hasattr(workflow, "singularity_prefix"):
            return workflow.singularity_prefix
        else:
            return ".snakemake/singularity"
    elif hasattr(workflow, "deployment_settings"):
        # Fetch singularity prefix for snakemake version with equal to 8.0 or newer
        if workflow.deployment_settings.apptainer_prefix is None:
            return ".snakemake/singularity"
        else:
            return workflow.deployment_settings.apptainer_prefix
    return None


def get_software_version_from_labels(image_path):
    """
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

    """
    cmd = ["singularity", "inspect", image_path]
    software_version_list = []
    for row in subprocess.check_output(cmd).decode().split("\n"):

        if not row.startswith("org.") and not row.startswith("maintainer") and not row.startswith("license"):
            software_version = re.match("^([A-Za-z0-9-_.]+): ([a-z0-9.]+)$", row)
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
    """
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
    """
    if is_local_file(container):
        return container

    md5hash = hashlib.md5()
    md5hash.update(container.encode())
    return os.path.join(singularity_prefix_path, f"{md5hash.hexdigest()}.simg")


def use_container(workflow):
    """
    Function used to check if containers are used,
    """
    if hasattr(workflow, "use_singularity"):
        # For snakemake with version less then 8
        return True
    elif hasattr(workflow, "deployment_settings") and workflow.deployment_settings.deployment_method:
        # For snakemake with version 8 or newer
        from snakemake.settings import DeploymentMethod

        if DeploymentMethod.APPTAINER in workflow.deployment_settings.deployment_method:
            return True
        else:
            return False
    else:
        return False


def add_software_version_to_config(config, workflow, fail_missing_versions=True):
    """
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
    """
    container_cache = get_container_prefix(workflow)

    def _add_software_version(config, version_dict):
        logger = logging.getLogger(__name__)
        version_found = []
        software_version_key = "software_versions"
        for key, value in config.items():
            if isinstance(value, dict):
                config[key], version_dict = _add_software_version(value, version_dict)
            elif key in ["container", "default_container"]:
                if key == "default_container":
                    software_version_key = f"default_container_software_versions"
                image_path = get_image_path(value, container_cache)
                if os.path.isfile(image_path):
                    version_found += get_software_version_from_labels(image_path)
                    name_and_version = _create_container_name_version_string(value)

                    if not version_found:
                        if fail_missing_versions:
                            raise Exception(f"could not extract software versions from {image_path}, {value}")
                        else:
                            logger.warning(f"could not extract software versions from {image_path}, {value}")
                            name = name_and_version.split("_")[0]
                            version = "_".join(name_and_version.split("_")[1:])
                            version_found = [[name, version], ("NOTE", "version extract from image name and not labels")]
                else:
                    if fail_missing_versions:
                        raise Exception(f"could not locate local file {image_path} for {value}")
                    else:
                        logger.warning(f"could not locate local file {image_path} for {value}")
        if version_found:
            config[software_version_key] = {s: v for s, v in version_found}
            if "version" in config[software_version_key]:
                del config[software_version_key]["version"]
            version_dict[name_and_version] = config[software_version_key]
        return config, version_dict

    return _add_software_version(config, {})


def export_software_version_as_file(
    software_dict, directory="versions/software", file_name="softwares_mqc_versions.yaml", date_string=None
):
    """
    Print software version to file (should be same as filename in touch_software_version_file). Requires a dict with key software_info which
    should contain a dict with software names and versions.

    Parameters:
    -----------
    software_dict: dict
       dict with key software_info, ex {software_info: {'common_1.3': {'samtools': '1.3', 'picard': '1.6'}}}
    directory: str
       path where files will be written
    file_name: str
       file name to use for software logging
    date_string: str
       a string that will be added to the folder name to make it unique
    """
    if date_string is None:
        date_string = datetime.now().strftime("%Y%m%d")
    if directory is not None and len(directory) > 0:
        date_string = f"_{date_string}"
    directory = f"{directory}{date_string}"
    if len(directory) > 0 and not os.path.isdir(directory):
        os.makedirs(directory)
    output_file = os.path.join(directory, f"{file_name}")
    with open(output_file, "w") as writer:
        writer.write(yaml.dump(software_dict))
        for name in software_dict:
            notification = software_dict[name].pop("NOTE", None)
            if notification is not None:
                writer.write(f"# {notification}")
    return output_file


def touch_software_version_file(config, directory="versions/software", file_name="softwares_mqc_versions.yaml", date_string=None):
    """
    To be able to pass a proper file list to multiqc the version files need to exist before the dag graph
    is built. And before the dag graph is built we can not guarantee that all images exist on the file system,
    and therefor we can not use export_software_version_as_file to directly create the actual version files.
    This function will create all files (empty) that export_software_version_as_file will create.
    NOTE: you need to have the same parameter as with export_software_version_as_file

    Parameters:
    -----------
    config: dict
       dict with config file # not used?
    directory: str
       path where files will be written
    file_name: str
       file name to use for software version logging
    date_string: str
       a string that will be added to the folder name to make it unique
    """

    if date_string is None:
        date_string = datetime.now().strftime("%Y%m%d")
    if directory is not None and len(directory) > 0:
        date_string = f"_{date_string}"
        directory = f"{directory}{date_string}"
    if len(directory) > 0 and not os.path.isdir(directory):
        os.makedirs(directory)
    output_file = os.path.join(directory, f"{file_name}")
    _touch(output_file)

    if not file_name.endswith("mqc_versions.yaml"):
        logger = logging.getLogger(__name__)
        logger.warning(f"{file_name} is not going to be recognized by MultiQC. Should end with mqc_versions.yaml")
    return output_file


def get_pipeline_version(workflow, pipeline_name="pipeline"):
    """
    Will return the pipelines tag name and commit hex.

    Parameters:
    -----------
    workflow: object
        workflow object from snakemake that contain a basedir attribute

    Return
    ------
    dict with pipeline version and commit, ex {'pipeline_name': {'version': 'v1', 'pipeline_commit': 'achgk2...kacaa'}}
    """
    logger = logging.getLogger(__name__)

    def _find_root_repo(path):
        if path is None or os.path.dirname(str(path)) == str(path):
            return None
        elif os.path.isdir(str(os.path.join(str(path), ".git"))):
            return path
        else:
            return _find_root_repo(os.path.dirname(path))

    repo_path = _find_root_repo(getattr(workflow, "basedir"))

    if not repo_path:
        logger.warning("Pipeline directory is not a git repo")
        return {pipeline_name: {"version": None, "commit_id": None}}

    # Initialize a Git repo object
    repo = git.Repo(repo_path)

    # Get the currently checked out commit
    head_commit = repo.head.commit

    # Iterate through all tags and find the one pointing to the HEAD commit
    pipeline_version = None
    for tag in repo.tags:
        if tag.commit == head_commit:
            pipeline_version = tag.name
            break
    if pipeline_version is None:
        try:
            pipeline_version = repo.active_branch
        except TypeError as e:
            logger.warning("Unable to get version (from tags) or an active_branch")

    return {pipeline_name: {"version": str(pipeline_version), "commit_id": str(head_commit)}}


def export_pipeline_version_as_file(
    pipeline_version_dict, directory="versions/software", file_name_ending="mqc_versions.yaml", date_string=None
):
    """
    Print pipeline version to a file. Requires a dict with key pipeline_info which
    should contain a dict with software names and versions.

    Parameters:
    -----------
    pipeline_version_dict: dict
       dict with key pipeline_version_dict, ex {pipeline_name: {'version': '1.3', 'commit_id': 'ac8ac8t73'}}
    directory: str
       path where files will be written
    file_name_ending: str
       a string that will be combined with the software name version key
    date_string: str
       a string that will be added to the folder name to make it unique
    """
    if date_string is None:
        date_string = datetime.now().strftime("%Y%m%d")
    if directory is not None and len(directory) > 0:
        date_string = f"_{date_string}"
    directory = f"{directory}{date_string}"
    if len(directory) > 0 and not os.path.isdir(directory):
        os.makedirs(directory)
    output_file_list = []
    for pipeline_name in pipeline_version_dict:
        output_file = os.path.join(
            directory, f"{pipeline_name}__{pipeline_version_dict[pipeline_name]['version']}_{file_name_ending}"
        )
        output_file_list.append(output_file)
        with open(output_file, "w") as writer:
            writer.write(yaml.dump({pipeline_name: pipeline_version_dict[pipeline_name]["version"]}))
    return output_file_list


def touch_pipeline_version_file_name(
    pipeline_version_dict, directory="versions/software", file_name_ending="mqc_versions.yaml", date_string=None
):
    """
    Function used to create empty version file for pipeline version. This
    function is a bit redundant and export_pipeline_version_as_file could be used,
    since this function isn't dependent on singularity images which
    export_software_version_as_file is. But the function exist to have a similar workflow
    for both pipeline and software. NOTE: you need to have same parameters into
    touch_pipeline_version_file_name as to export_pipeline_version_as_file.

    Parameters:
    -----------
    pipeline_version_dict: dict
       dict with key pipeline_version_dict, ex {pipeline_name: {'version': '1.3', 'commit_id': 'ac8ac8t73'}}
    directory: str
       path where files will be written
    file_name_ending: str
       a string that will be combined with the software name version key
    date_string: str
       a string that will be added to the folder name to make it unique
    """
    if date_string is None:
        date_string = datetime.now().strftime("%Y%m%d")
    if directory is not None and len(directory) > 0:
        date_string = f"_{date_string}"
    directory = f"{directory}{date_string}"
    if len(directory) > 0 and not os.path.isdir(directory):
        os.makedirs(directory)

    output_file_list = []
    for pipeline_name in pipeline_version_dict:
        output_file = os.path.join(
            directory, f"{pipeline_name}__{pipeline_version_dict[pipeline_name]['version']}_{file_name_ending}"
        )
        output_file_list.append(output_file)
        _touch(output_file)
    return output_file_list
