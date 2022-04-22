#!/usr/bin/env python
"""
    Main hydra_genetics module file.

"""

from . import _version
__version__ = _version.get_versions()['version']


def min_version(version):
    """Require minimum hydra-genetics version, raise workflow error if not met."""
    import pkg_resources

    if pkg_resources.parse_version(__version__) < pkg_resources.parse_version(version):
        from .exceptions import HydraGeneticsVersionError
        raise HydraGeneticsVersionError(
            "Expecting Hydra-Genetics version {} or higher (you are currently using {}).".format(
                version, __version__
            )
        )
