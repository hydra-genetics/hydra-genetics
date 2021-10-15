# coding: utf-8

import yaml


def load_resources(config, file: str = "resources.yaml") -> dict:
    """
        helper function used to load resources.yaml file and update config
        with the information without replacing the current content.
    """
    from hydra_genetics.utils.misc import merge
    with open(file) as file:
        return merge(config, yaml.load(file, Loader=yaml.FullLoader))
