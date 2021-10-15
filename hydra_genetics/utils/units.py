# coding: utf-8

import pandas
import snakemake
import warnings


def get_unit(units: pandas.DataFrame, wildcards: snakemake.io.Wildcards) -> pandas.Series:
    """
    function used to extract one unit(row) from units.tsv
    Args:
        units: DataFrame generate by importing a file following schema defintion
               found in pre-alignment/workflow/schemas/units.schema.tsv
        wildcards: wildcards object with at least the following wildcard names
               sample, type, run, and lane
    Returns:
        Series containing data of the selected row
    Raises:
        raises an exception (KeyError) if no unit can be extracted from the Dataframe
    """
    unit = units.loc[(wildcards.sample, wildcards.type, wildcards.run, wildcards.lane)].dropna()
    return unit


def get_fastq_file(units: pandas.DataFrame, wildcards: snakemake.io.Wildcards, read_pair: str = "fastq1") -> str:
    """
    function used to extract path for one unit(row) from units.tsv
    Args:
        units: DataFrame generate by importing a file following schema defintion
               found in pre-alignment/workflow/schemas/units.schema.tsv
        wildcards: wildcards object with at least the following wildcard names
               sample, type, run, and lane
        read_pair: fast1 or fastq2
    Returns:
        path for fastq file as a str
    Raises:
        raises an exception (KeyError) if no unit can be extracted from the Dataframe
    """
    unit = get_unit(units, wildcards)
    if read_pair not in ["fastq1", "fastq2"]:
        raise ValueError("Incorrect input value error {}: expected {} or {}".format(read_pair, "fastq1", "fastq2"))
    return unit[read_pair]


def get_fastq_adapter(units: pandas.DataFrame, wildcards: snakemake.io.Wildcards) -> str:
    """
    function used to extract adapters for one unit(row) from units.tsv
    Args:
        units: DataFrame generate by importing a file following schema defintion
               found in pre-alignment/workflow/schemas/units.schema.tsv
        wildcards: wildcards object with at least the following wildcard names
               sample, type, run, and lane
    Returns:
        return adapter with format seq1,seq2
    Raises:
        raises an exception (KeyError) if no unit can be extracted from the Dataframe
    """
    unit = get_unit(units, wildcards)
    return unit["adapter"]


def get_units(units: pandas.DataFrame, wildcards: snakemake.io.Wildcards, type: str = None) -> pandas.DataFrame:
    """
    function used to extract one or more units from units.tsv
    Args:
        units: DataFrame generate by importing a file following schema defintion
               found in pre-alignment/workflow/schemas/units.schema.tsv
        wildcards: wildcards object with at least the following wildcard names
               sample and type (optional, can also be passed as an argument).
        type: N,T or R
    Returns:
        all units from the DataFrame that can be filtereted out using sample name
        and unit type (N,T,R)
    Raises:
        raises an exception (KeyError) if no unit(s) can be extracted from the Dataframe
    """
    if type is None:
        files = units.loc[(wildcards.sample, wildcards.type)].dropna()
    else:
        files = units.loc[(wildcards.sample, type)].dropna()
    return [file for file in files.itertuples()]


def get_fastq_files(units: pandas.DataFrame, wildcards: snakemake.io.Wildcards, type: str = None):
    """
    function used to extract all fastq files for a sample with a sepecific type
    Args:
        units: DataFrame generate by importing a file following schema defintion
               found in pre-alignment/workflow/schemas/units.schema.tsv
        wildcards: wildcards object with at least the following wildcard names
               sample, read and type (optional, can also be passed as an argument).
        type: N,T or R
    Returns:
        all units from the DataFrame that can be filtereted out using sample name
        ,fastq (1 or 2) and type type (N,T,R)
    Raises:
        raises an exception (KeyError) if no unit(s) can be extracted from the Dataframe
    """
    return [getattr(file, wildcards.read) for file in get_units(units, wildcards, type)]


def get_unit_types(units: pandas.DataFrame, sample: str) -> set[str]:
    """
    function used to extract all types of units found for a sample in units.tsv (N,T,R)
    Args:
        units: DataFrame generate by importing a file following schema defintion
               found in pre-alignment/workflow/schemas/units.schema.tsv
        wildcards: wildcards object with at least the following wildcard names
               sample.
    Returns:
        set of type types ex set("N","T")
    Raises:
        raises an exception (KeyError) if no unit(s) can be extracted from the Dataframe
    """
    return set([u.type for u in units.loc[(sample,)].dropna().itertuples()])
