# coding: utf-8

import typing
import pandas
import snakemake


def get_sample(samples: pandas.DataFrame, wildcards: snakemake.io.Wildcards) -> pandas.Series:
    """
    function used to extract one sample(row) from sample.tsv
    Args:
        samples: DataFrame generate by importing a file following schema defintion
               found in pre-alignment/workflow/schemas/samples.schema.tsv
        wildcards: wildcards object with at least the following wildcard names
               sample
    Returns:
        Series containing data of the selected row
    Raises:
        raises an exception (KeyError) if no sample can be extracted from the Dataframe
    """
    return samples.loc[(wildcards.sample)].dropna()


def get_samples(samples: pandas.DataFrame) -> typing.List[str]:
    """
    function used to extract all sample found in samples.tsv
    Args:
        units: DataFrame generate by importing a file following schema defintion
               found in pre-alignment/workflow/schemas/units.schema.tsv
    Returns:
        List of strings with all sample names
    """
    return [sample.Index for sample in samples.itertuples()]
