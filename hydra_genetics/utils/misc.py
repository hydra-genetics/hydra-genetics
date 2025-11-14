# coding: utf-8

from collections.abc import Mapping
from copy import deepcopy
import os
import yaml
import re
from datetime import datetime
from snakemake.sourcecache import GithubFile, LocalGitFile, WorkflowError


def get_module_snakefile(config, repo, path, tag):
    ''' return a complete snakefile path, either pointing to github or a local repo'''
    if 'hydra_local_path' in config:
        repo_path = os.path.join(config['hydra_local_path'], repo)
        if not os.path.exists(repo_path):
            ' Remove possible organization part from repo path '
            repo_path_v2 = os.path.join(config['hydra_local_path'], os.sep.join(repo.split(os.sep)[1:]))
            if not os.path.exists(repo_path_v2):
                raise FileNotFoundError(f"Repo folder {repo_path} or {repo_path_v2} doesn't exist!")
            else:
                repo_path = repo_path_v2
        if not os.path.isdir(repo_path):
            raise FileNotFoundError(f"{repo_path} isn't a folder!")
        return LocalGitFile(repo_path, path=path, tag=tag)
    else:
        return GithubFile(repo, path=path, tag=tag)


def merge(dict1, dict2):
    ''' Return a new dictionary by merging two dictionaries recursively. '''

    result = deepcopy(dict1)
    for key, value in dict2.items():
        if isinstance(value, Mapping):
            result[key] = merge(result.get(key, {}), value)
        else:
            result[key] = deepcopy(dict2[key])
    return result


def extract_chr(file, filter_out=["chrM"]):
    chr = None
    if os.path.exists(file):
        with open(file) as lines:
            chr = [line.split("\t")[0] for line in lines]
        return [c for c in chr if c not in filter_out]
    return [""]


def replace_dict_variables(config):
    '''
        Make it possible to defina a variable in a  vaue string using ´{{}}´,
        ex {{PROJECT_VARIABLE}}. PROJECT_VARIABLE must exist as a variable
        in the yaml file and will be used to replace all occurences of
        {{PROJECT_VARAIBLE}} in the yaml file.
    '''
    def update_dict(temp_config):
        for k in temp_config:
            if type(temp_config[k]) is dict:
                temp_config[k] = update_dict(temp_config[k])
            elif type(temp_config[k]) is str:
                match = re.findall(r'\{\{([A-Za-z0-9_]+)\}\}', temp_config[k])
                for m in match:
                    temp_config[k] = temp_config[k].replace("{{" + m + "}}", config[m])
            elif type(temp_config[k]) is list:
                for i in range(len(temp_config[k])):
                    if type(temp_config[k][i]) is str:
                        match = re.findall(r'\{\{([A-Za-z0-9_]+)\}\}', temp_config[k][i])
                        for m in match:
                            temp_config[k][i] = temp_config[k][i].replace("{{" + m + "}}", config[m])
        return temp_config
    return update_dict(config)


def export_config_as_file(config, output_file="config", directory="versions", date_string=None):
    if date_string is None:
        date_string = datetime.now().strftime('%Y%m%d--%H-%M-%S')
    if directory is not None and len(directory) > 0:
        date_string = f"_{date_string}"
    if output_file is not None:
        output_file = f"{output_file}{date_string}.yaml"
    if directory is not None:
        output_file = os.path.join(directory, output_file)
    if len(directory) > 0 and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(output_file, 'w') as writer:
        writer.write(yaml.dump(config))


def get_input_aligned_bam(wildcards, config, default_path="alignment/samtools_merge_bam"):
    """
    Compile the paths to input aligned BAM and BAI files for the workflow.

    This function determines the appropriate BAM file path based on the configuration
    and workflow parameters.

    Args:
        wildcards (snakemake.io.Wildcards): Wildcards object containing sample and type information.
        config (dict): Configuration dictionary with possible keys:
            - aligner (str or None): The aligner used for generating the BAM file.
        default_path (str): Default path for BAM files if no specific configuration is provided.

    Returns:
        tuple: A tuple containing the alignment BAM file path and its BAI index file path.
    """
    try:
        if config.get("aligner") is not None:
            # Use aligner to compile the paths
            aligner = config.get("aligner")
            alignment_path = f"alignment/{aligner}_align/{wildcards.sample}_{wildcards.type}.bam"
            index_path = f"alignment/{aligner}_align/{wildcards.sample}_{wildcards.type}.bam.bai"
        else:
            # no aligner, use the default path
            alignment_path = f"{default_path}/{wildcards.sample}_{wildcards.type}.bam"
            index_path = f"{alignment_path}.bai"

        return alignment_path, index_path

    except KeyError as e:
        raise WorkflowError(f"Missing required wildcards: {e}")


def get_input_haplotagged_bam(wildcards, config, default_path="alignment/samtools_merge_bam", suffix=None):
    """
    Compile paths to haplotagged BAM/BAI files (may be required for downstream analyses with e.g. cnvkit_batch)
    This function determines the appropriate BAM file path based on the configuration. suffix can be provided
    either as a function argument or in the config file under the key 'haplotag_suffix'.

    For backward compatibility, if only wildcards and config are provided, the function will default to using the
    default path and return 'alignment/samtools_merge_bam/{sample}_{type}.bam'.

    Args:
        wildcards (snakemake.io.Wildcards): Wildcards object containing sample and type information.
        config (dict): config with or without 'haplotag_path' key.
        default_path (str): Default path for BAM files if no specific configuration is provided.
        suffix (str): Suffix to append to the BAM file name (default is None).
    Returns:
        tuple: A tuple containing the alignment BAM file path and its BAI index file path.

    """
    try:
        sample_name = getattr(wildcards, "sample")
        sample_type = getattr(wildcards, "type")
    except AttributeError as e:
        raise WorkflowError(f"Missing required wildcards: {e}")

    haplotag_path = config.get("haplotag_path", None)
    path_to_input_bam = haplotag_path if haplotag_path is not None else default_path

    # check for suffix in the config
    if suffix is None:
        suffix = config.get("haplotag_suffix", None)

    if suffix:  # This will be False for None and ''
        file_name = f"{sample_name}_{sample_type}.{suffix}.bam"
    else:
        file_name = f"{sample_name}_{sample_type}.bam"

    bam_path = os.path.join(path_to_input_bam, file_name)
    bai_path = f"{bam_path}.bai"

    return bam_path, bai_path
