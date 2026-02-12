#!/usr/bin/env python
"""
    Main hydra_genetics module file.

"""
from packaging.version import Version
from . import _version
__version__ = _version.get_versions()['version']


def min_version(version):
    """Require minimum hydra-genetics version, raise workflow error if not met."""
    if Version(__version__) < Version(version):
        from .exceptions import HydraGeneticsVersionError
        raise HydraGeneticsVersionError(
            "Expecting Hydra-Genetics version {} or higher (you are currently using {}).".format(
                version, __version__
            )
        )


def max_version(version):
    """Set maximum hydra-genetics version, raise workflow error if not met."""
    if Version(__version__) > Version(version):
        from .exceptions import HydraGeneticsVersionError
        raise HydraGeneticsVersionError(
            "Expecting Hydra-Genetics version {} or less (you are currently using {}).".format(
                version, __version__
            )
        )
