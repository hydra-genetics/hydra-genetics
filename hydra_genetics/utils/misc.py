# coding: utf-8

import collections
from copy import deepcopy


def merge(dict1, dict2):
    ''' Return a new dictionary by merging two dictionaries recursively. '''

    result = deepcopy(dict1)
    print("Reuslt...")
    print(result)
    for key, value in dict2.items():
        print(key)
        if isinstance(value, collections.Mapping):
            result[key] = merge(result.get(key, {}), value)
        else:
            print("Add")
            result[key] = deepcopy(dict2[key])
    print("Reuslt...")
    print(result)
    return result
