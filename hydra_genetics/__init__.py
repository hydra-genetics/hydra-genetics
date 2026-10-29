#!/usr/bin/env python
"""
    Main hydra-genetics module file.

"""
from packaging.version import Version
from ._version import __version__


def min_version(version):
    """Require minimum hydra-genetics version, raise workflow error if not met."""
    if Version(__version__) < Version(version):
        from .exceptions import HydraGeneticsVersionError
        raise HydraGeneticsVersionError(
            "Expecting hydra-genetics version {} or higher (you are currently using {}).".format(
                version, __version__
            )
        )


def max_version(version):
    """Set maximum hydra-genetics version, raise workflow error if not met."""
    if Version(__version__) > Version(version):
        from .exceptions import HydraGeneticsVersionError
        raise HydraGeneticsVersionError(
            "Expecting hydra-genetics version {} or less (you are currently using {}).".format(
                version, __version__
            )
        )
