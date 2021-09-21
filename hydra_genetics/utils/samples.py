# coding: utf-8

import typing
import pandas


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
