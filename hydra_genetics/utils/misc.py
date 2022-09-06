# coding: utf-8

from collections.abc import Mapping
from copy import deepcopy
import os
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
        return LocalGitFile(os.path.join(config['hydra_local_path'], repo), path=path, tag=tag)
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
