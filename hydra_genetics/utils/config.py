# coding: utf-8

"""
Config accessors that fail loudly instead of yielding an empty string.

Rules have traditionally reached into the config with a chain of ``.get`` calls that
default to ``""``::

    fasta=config.get("reference", {}).get("fasta", ""),

That default is never a usable value. In an ``input:`` directive Snakemake aborts with a
``MissingInputException`` whose "affected files" list is empty, so the failure names
neither the input nor the config key. In a ``params:`` directive nothing is checked at
all and the job runs, interpolating the empty string into the shell command.

``get_config_value`` replaces that chain. Call it from an input or params function so
the lookup stays lazy: a workflow that never runs the rule does not have to configure
it, which is what the ``""`` default was relied on for.
"""

from snakemake.exceptions import WorkflowError


# Separates "no default given, so this entry is required" from a default of None, [] or
# "", each of which is a value a caller may legitimately want back.
_REQUIRED = object()


def _prefix(module):
    return f"{module}: " if module else ""


def get_config_value(config, *keys, default=_REQUIRED, expect=str, module=None):
    """
    Fetch a value from a config dict, failing with a message that names the missing entry.

    :param config: the Snakemake config dict to read from
    :type config: dict
    :param keys: successive keys to walk, e.g. ``"reference", "fasta"``
    :type keys: str
    :param default: value to return when the entry is absent or blank. Omit it to make
                    the entry required, in which case a missing or blank entry raises.
                    Pass ``default=[]`` for an input file the rule can run without:
                    Snakemake reads an empty list as "no file", which is what ``""``
                    was never able to express.
    :param expect: type the value must have, or ``None`` to skip the type check. With
                   the default ``str`` the value must also be non-blank.
    :type expect: type
    :param module: name of the calling module, used to prefix error messages so a
                   composed workflow says which module's config is at fault
    :type module: str

    :return: the configured value, or ``default`` when one was given and the entry is
             absent or unusable
    :raises snakemake.exceptions.WorkflowError: when a required entry is missing, blank,
             or of the wrong type
    """
    value = config
    for i, key in enumerate(keys):
        if not isinstance(value, dict) or key not in value:
            if default is not _REQUIRED:
                return default
            missing = ":".join(keys[: i + 1])
            raise WorkflowError(f"{_prefix(module)}missing config entry '{missing}', required by the rule being run")
        value = value[key]

    name = ":".join(keys)
    if expect is str:
        if not isinstance(value, str) or not value.strip():
            if default is not _REQUIRED:
                return default
            raise WorkflowError(f"{_prefix(module)}config entry '{name}' must be a non-empty string, got {repr(value)}")
    elif expect is not None:
        if not isinstance(value, expect):
            if default is not _REQUIRED:
                return default
            raise WorkflowError(
                f"{_prefix(module)}config entry '{name}' must be of type {expect.__name__}, got {repr(value)}"
            )

    return value


def config_accessor(config, module=None):
    """
    Bind :func:`get_config_value` to one config dict and one module tag.

    Binding once keeps the tag out of every call site. In a module's ``common.smk``::

        from hydra_genetics.utils.config import config_accessor

        get_config_value = config_accessor(config, module="alignment")

    after which rules call it with keys alone::

        fasta=lambda wildcards: get_config_value("reference", "fasta"),
        pon=lambda wildcards: get_config_value("cnvkit_batch", "normal_reference", default=[]),

    :param config: the Snakemake config dict the returned accessor reads from
    :type config: dict
    :param module: name of the module, used to prefix error messages. Leaving it unset
                   still produces working errors, only vaguer ones, so set it whenever
                   the module is included into a larger workflow.
    :type module: str

    :return: a callable taking ``*keys`` plus the ``default`` and ``expect`` keywords
    :rtype: callable
    """

    def _accessor(*keys, default=_REQUIRED, expect=str):
        return get_config_value(config, *keys, default=default, expect=expect, module=module)

    return _accessor
