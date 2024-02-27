# coding: utf-8

from collections.abc import Mapping
from copy import deepcopy
import logging
import git
import os
import re
from snakemake.sourcecache import GithubFile, LocalGitFile


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


def get_pipeline_version(workflow):
    """
    Will return the pipelines tag name and commit hex.

    Parameters:
    -----------
    workflow: object
        workflow object from snakemake that contain a basedir attribute

    Return
    ------
    dict with pipeline version and commit, ex {'pipeline_version': 'v1', 'pipeline_commit': 'achgk2...kacaa'}
    """
    def _find_root_repo(path):
        if path is None:
            return None
        elif os.path.isdir(str(os.path.join(str(path), ".git"))):
            return path
        else:
            return _find_root_repo(os.path.dirname(path))
    repo_path = _find_root_repo(getattr(workflow, 'basedir'))

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
            logger = logging.getLogger(__name__)
            logger.warning("Unable to get version (from tags) or an active_branch")

    return {'pipeline_version': pipeline_version, 'pipeline_commit': head_commit}
