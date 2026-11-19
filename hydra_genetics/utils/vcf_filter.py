"""
VCF filter expressions used by hydra-genetics.

The expression engine (``create_variant_filter`` and ``create_convert_expression_function``) is moved
unchanged from the hydra-genetics filtering module (workflow/scripts/filter_vcf.py) so that other
modules can share it. See the filtering module documentation for the expression syntax.
"""

import logging
import re

from hydra_genetics.utils.io import utils


def is_float(element) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False


def _and_function(v1, v2): return v1 and v2


def _or_function(v1, v2): return v1 or v2


def _parse_helper(f_iterator):
    """
    function used to parse a string with parenthesis and create a nested fail_filter_list

    :param f_iterator: filter string that will be parsed
    :type f_iterator: string iterator

    :return: return a nested list
    """
    data = []
    filter_string = ''
    for item in f_iterator:
        if item == '(':
            result, closing_parantes = _parse_helper(f_iterator)
            if len(result) == 1:
                result = result[0]
            data.append(result)
            if not closing_parantes:
                raise SyntaxError("Missing closing parantes!")
        elif item == ')':
            if len(filter_string) != 0:
                data.append(filter_string)
            return data, True
        else:
            filter_string += item
            if filter_string.startswith(' or '):
                data.append(_or_function)
                result, p_found = _parse_helper(f_iterator)
                if len(result) == 1:
                    result = result[0]
                data.append(result)
                return data, p_found
            elif filter_string.startswith(' and '):
                data.append(_and_function)
                result, p_found = _parse_helper(f_iterator)
                if len(result) == 1:
                    result = result[0]
                data.append(result)
                return data, p_found
            elif filter_string.endswith(' or '):
                data.append(filter_string[:-4])
                data.append(_or_function)
                result, p_found = _parse_helper(f_iterator)
                if len(result) == 1:
                    result = result[0]
                data.append(result)
                return data, p_found
            elif filter_string.endswith(' and '):
                data.append(filter_string[:-5])
                data.append(_and_function)
                result, p_found = _parse_helper(f_iterator)
                if len(result) == 1:
                    result = result[0]
                data.append(result)
                return data, p_found
    if len(filter_string) != 0:
        data.append(filter_string)
    return data, False


def _convert_string(data, process_function):
    """
    converts a nested list of string into functions
    :params data: data structure with string
    :type list: nested list with strings
    :params process_function: function used to convert string to lambda function
    :type list: function

    :return: nested list with lambda functions
    """
    if isinstance(data, str):
        return process_function(data)
    elif isinstance(data, list):
        if len(data) == 3:
            return [_convert_string(data[0], process_function), data[1], _convert_string(data[2], process_function)]
        elif len(data) == 1:
            return _convert_string(data[0], process_function)
        else:
            raise Exception("Unhandled data structure case {}, unexpected number of items {}!".format(data, len(data)))
    else:
        raise Exception("Unhandled data structure case {}\ntype: {}\nlength: {}".format(data, type(data), len(data)))


def _evaluate_expression(data, variant):
    """
    function used to evaluate variant using a nested list of functions

    :param data: a nested list with functions that will be evaluated
    :type data: nested list
    :param variant: variant that will be evaluated
    :type process_function: a function
    :param

    :return: boolean
    """
    if callable(data):
        return data(variant)
    elif isinstance(data, list):
        if len(data) == 3:
            return data[1](_evaluate_expression(data[0], variant), _evaluate_expression(data[2], variant))
        elif len(data) == 1:
            return _evaluate_expression(data[0], variant)
        else:
            raise Exception("Unhandled data structure case {}, unexpected number of items {}!".format(data, len(data)))
    else:
        raise Exception("Unhandled data structure case {}!".format(data))


def create_variant_filter(filter, string_parser):
    data, _ = _parse_helper(iter(filter))
    data = _convert_string(data, string_parser)
    return lambda variant: _evaluate_expression(data, variant)


def create_convert_expression_function(annotation_extractors):
    """
    :param annotation_extractors: dict with functions that can extract annotations
    :type annotation_extractors: dict
    """

    def na_handling_helper(na_handling, expression):
        if na_handling == "NA_TRUE":
            return True
        elif na_handling == "NA_FALSE":
            return False
        elif na_handling == "NA_ERROR":
            raise ValueError("Couldn't evaluate {} due to missing value".format(expression))

    def regex_compare(regex_exist, value, expression=""):
        if value is None:
            value = ""
        if "!exist" in expression:
            return re.search(regex_exist, value) is None
        else:
            return re.search(regex_exist, value) is not None

    def compare_data(comparison, value1, value2, index1=None, index2=None, na_handling="NA_FALSE", expression=""):
        if isinstance(value1, float):
            if value2 is None:
                return na_handling_helper(na_handling, expression)
            if index2 is not None:
                value2 = value2[index2]
            return comparison(value1, float(value2))
        elif isinstance(value2, float):
            if value1 is None:
                return na_handling_helper(na_handling, expression)
            if index1 is not None:
                value1 = value1[index1]
            return comparison(float(value1), value2)
        else:
            if index2 is not None:
                value2 = value2[index2]
            if index1 is not None:
                value1 = value1[index1]
            if value1 == '-' and value2 is None:
                value2 = '-'
            if value2 == '-' and value1 is None:
                value1 = '-'
            if value1 is None or value2 is None:
                return na_handling_helper(na_handling, expression)
            return comparison(value1, value2)

    def convert_to_expression(expression):
        """
        Valid format of expression is:
        - DATA_SOURCE:NA_HANDLING(OPTIONAL):FIELD:COLUMN(OPTIONAL) [<|>|=|!=] VALUE
        - VALUE [<|>|=|!=] DATA_SOURCE:NA_HANDLING(OPTIONAL):FIELD:COLUMN(OPTIONAL)
        - exist[regex, DATA_SOURCE:NA_HANDLING(OPTIONAL):FIELD:COLUMN]
        - !exist[regex, DATA_SOURCE:NA_HANDLING(OPTIONAL):FIELD:COLUMN]

        DATA_SOURCE:
         - VEP
         - FORMAT
         - INFO
         - QUAL

        NA_HANDLING:
         - NA_TRUE: when None is found the expression will return True and filter variant
         - NA_FALSE: when None is found the expression will return False and not filter variant
         - NA_ERROR: when None is found the an error will be raised if value not found
        Default will be NA_FALSE, i.e a filter will not remove variant

        FIELD, any field in info, format or vep string

        COLUMN, used to extract value from tuple

        :params expression
        :type expression: string
        """
        comparison = {
            ">": lambda value1, value2: value1 > value2,
            "<": lambda value1, value2: value1 < value2,
            "=": lambda value1, value2: value1 == value2,
            "!=": lambda value1, value2: value1 != value2
        }

        # Extract information about how None values should be handled during filtering
        regex_na_handling = r"(VEP|FORMAT|INFO|QUAL):(NA_TRUE|NA_FALSE|NA_ERROR):"
        na_handling = re.search(regex_na_handling, expression)
        if na_handling:
            na_handling = na_handling.groups()[1]
            # Remove NA handling information from expression
            expression = re.sub(r"(NA_TRUE|NA_FALSE|NA_ERROR):", '', expression)
        else:
            na_handling = "NA_FALSE"
        regex_string = "[ ]*(VEP|FORMAT|INFO):([A-Za-z0-9_.]+):*([0-9]*)"

        if "exist[" in expression:
            # Handle exist expression
            # Example "exist[XM_[0-9]+, VEP:Feature]"
            exist_statment, regex_exist, field = re.search(r"([!]{0,1}exist)\[(.+),[ ]*(.+)\]", expression).groups()
            source, field, index = re.search(regex_string, field).groups()
            if len(index) > 0:
                def get_value(variant):
                    return annotation_extractors[source](variant, field)[int(index)]
            else:
                def get_value(variant):
                    value = annotation_extractors[source](variant, field)
                    if isinstance(value, tuple):
                        value = ",".join(value)
                    return value
            return lambda variant: regex_compare(regex_exist, get_value(variant), expression)
        elif "QUAL" in expression.strip():
            data = re.split("[ ]([<>=!]+)[ ]", expression)
            if "QUAL" in data[0]:
                value = float(data[2])
                return lambda variant: compare_data(
                                                        comparison[data[1]],
                                                        annotation_extractors["QUAL"](variant),
                                                        value,
                                                        na_handling=na_handling,
                                                        expression=expression
                                                    )
            elif "QUAL" in data[2]:
                value = float(data[0])
                return lambda variant: compare_data(
                                                        comparison[data[1]],
                                                        value,
                                                        annotation_extractors["QUAL"](variant),
                                                        na_handling=na_handling,
                                                        expression=expression
                                                    )

        else:
            # Handle comparison expression
            # Example "FORMAT:NA_TRUE:SB_mutect2:1 > 400"
            data = re.split("[ ]([<>=!]+)[ ]", expression)
            if len(data) != 3:
                raise Exception("Invalid expression: " + expression)

            if "VEP:" in data[0] or "FORMAT:" in data[0] or "INFO:" in data[0]:
                source, field, index = re.search(regex_string, data[0]).groups()
                if len(index) == 0:
                    index = None
                else:
                    index = int(index)
                try:
                    data[2] = data[2].rstrip(" ").lstrip(" ")
                    value2 = float(data[2])
                    return lambda variant: compare_data(
                                                            comparison[data[1]],
                                                            annotation_extractors[source](variant, field),
                                                            value2, index1=index, na_handling=na_handling,
                                                            expression=expression
                                                        )
                except ValueError:
                    return lambda variant: compare_data(
                                                            comparison[data[1]],
                                                            annotation_extractors[source](variant, field),
                                                            data[2], index1=index, na_handling=na_handling,
                                                            expression=expression
                                                        )
            elif "VEP:" in data[2] or "FORMAT:" in data[2] or "INFO:" in data[2]:
                source, field, index = re.search(regex_string, data[2]).groups()
                if len(index) == 0:
                    index = None
                else:
                    index = int(index)
                try:
                    data[0] = data[0].rstrip(" ").lstrip(" ")
                    value1 = float(data[0])
                    return lambda variant: compare_data(
                                                            comparison[data[1]],
                                                            value1,
                                                            annotation_extractors[source](variant, field),
                                                            index2=index, na_handling=na_handling,
                                                            expression=expression
                                                        )
                except ValueError:
                    return lambda variant: compare_data(
                                                            comparison[data[1]],
                                                            data[0],
                                                            annotation_extractors[source](variant, field),
                                                            index2=index, na_handling=na_handling,
                                                            expression=expression
                                                        )
            else:
                raise Exception("Could not find comparison field in: " + expression)

    return convert_to_expression


def select_sample_index(samples, sample_name_regex):
    """
    Select the sample column that FORMAT expressions should read.

    Same behaviour as the filtering module: a single regex match is used, more than one match is an error,
    and without a match the first sample is used if the file has only one sample.

    :param samples: sample names in VCF column order
    :type samples: list of strings
    :param sample_name_regex: regex used to find the sample
    :type sample_name_regex: string

    :return: index of the selected sample
    """
    log = logging.getLogger(__name__)
    sample_index = 0
    number_of_matches = 0
    for index, name in enumerate(samples):
        if sample_name_regex and re.search(sample_name_regex, name):
            sample_index = index
            number_of_matches += 1
    if number_of_matches > 1:
        raise Exception("More then one sample match regex")
    if number_of_matches == 0 and len(samples) > 1:
        raise Exception("More then one sample and no regex")
    if number_of_matches == 0:
        log.info(f"Using default index: {sample_index}, nothing found using regex {sample_name_regex}")
    return sample_index


def get_vep_fields(header):
    """
    Return a dict mapping VEP (CSQ) field names to their index, or None if the header has no CSQ field.

    :param header: header of a pysam VariantFile
    """
    for record in header.records:
        if record.type == "INFO" and record.get('ID') == "CSQ":
            # pysam keeps the quotes of the description, strip them so that the last field name is usable
            fields = record['Description'].split("Format: ")[1].split('">')[0].rstrip('"').split("|")
            return {v: c for c, v in enumerate(fields)}
    return None


def create_annotation_extractors(variant_file, sample_index):
    """
    Create the annotation extractors used by create_convert_expression_function: VEP (only if the header
    has a CSQ field), FORMAT (for the selected sample), INFO and QUAL.

    :param variant_file: an opened pysam VariantFile
    :param sample_index: index of the sample used for FORMAT expressions
    :type sample_index: int

    :return: dict with extractor functions
    """
    annotation_extractor = {}
    vep_fields = get_vep_fields(variant_file.header)
    if vep_fields is not None:
        annotation_extractor["VEP"] = utils.get_annotation_data_vep(vep_fields)
    annotation_extractor['FORMAT'] = utils.get_annotation_data_format(sample_index)
    annotation_extractor['INFO'] = utils.get_annotation_data_info
    annotation_extractor['QUAL'] = lambda variant: None if variant.qual == '.' else variant.qual
    return annotation_extractor


def create_filter_from_vcf(variant_file, expression, sample_name_regex=None, sample_index=None):
    """
    Build a filter function (variant -> bool) for an opened VCF.

    :param variant_file: an opened pysam VariantFile
    :param expression: hydra filter expression, e.g. "FORMAT:AF:0 < 0.01"
    :param sample_name_regex: regex used to select the FORMAT sample (ignored if sample_index is given)
    :param sample_index: explicit sample index

    :return: function returning True when the expression is true for a variant
    """
    if sample_index is None:
        sample_index = select_sample_index(list(variant_file.header.samples), sample_name_regex)
    extractors = create_annotation_extractors(variant_file, sample_index)
    return create_variant_filter(expression, create_convert_expression_function(extractors))
