# coding: utf-8

from collections.abc import Mapping
from copy import deepcopy


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
    with open(file) as lines:
        chr = [line.split("\t")[0] for line in lines]
    return [c for c in chr if c not in filter_out]
