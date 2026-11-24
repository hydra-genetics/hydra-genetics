"""
Comparison of keyed records, shared by the VCF and table comparators.
"""

from collections import OrderedDict

from hydra_genetics.utils.verification.common import DIFFERENT, IDENTICAL, compare_values, normalise_tolerance


def group_by_key(records):
    """Group (key, values) pairs by key, keeping file order; duplicate keys are paired in order later."""
    grouped = OrderedDict()
    for key, values in records:
        grouped.setdefault(key, []).append(values)
    return grouped


def compare_records(result, reference_records, candidate_records, columns, format_key=str):
    """
    Compare two lists of (key, values) records and add counts and differences to result.

    :param result: Result object
    :param reference_records: list of (key, dict column -> value)
    :param candidate_records: list of (key, dict column -> value)
    :param columns: ordered dict column -> normalised tolerance, or None to compare every column exactly
    :param format_key: function used to show a key in the difference list
    """
    reference, candidate = group_by_key(reference_records), group_by_key(candidate_records)
    result.set_count("reference_records", len(reference_records))
    result.set_count("candidate_records", len(candidate_records))
    for name in ("matched", "identical", "within_tolerance", "different", "only_in_reference", "only_in_candidate"):
        result.set_count(name, 0)
    duplicated = sum(1 for values in list(reference.values()) + list(candidate.values()) if len(values) > 1)
    if duplicated:
        result.message("{} keys occur more than once, duplicates are paired in file order".format(duplicated))
    exact = normalise_tolerance(None)
    for key in list(reference.keys()) + [k for k in candidate.keys() if k not in reference]:
        ref_rows, cand_rows = reference.get(key, []), candidate.get(key, [])
        for index in range(max(len(ref_rows), len(cand_rows))):
            if index >= len(cand_rows):
                result.count("only_in_reference")
                result.difference({"key": format_key(key), "type": "only_in_reference", "status": DIFFERENT})
                continue
            if index >= len(ref_rows):
                result.count("only_in_candidate")
                result.difference({"key": format_key(key), "type": "only_in_candidate", "status": DIFFERENT})
                continue
            result.count("matched")
            ref_values, cand_values = ref_rows[index], cand_rows[index]
            compared = columns
            if compared is None:
                compared = OrderedDict((c, exact) for c in list(ref_values) + [c for c in cand_values if c not in ref_values])
            record_status = IDENTICAL
            for column, tolerance in compared.items():
                if tolerance["type"] == "ignore":
                    continue
                missing = [n for n, v in (("reference", ref_values), ("candidate", cand_values)) if column not in v]
                if missing:
                    status = IDENTICAL if len(missing) == 2 else DIFFERENT
                    if status == DIFFERENT:
                        result.difference({"key": format_key(key), "type": "missing_column", "column": column,
                                           "reference": ref_values.get(column), "candidate": cand_values.get(column),
                                           "status": DIFFERENT})
                else:
                    status = compare_values(ref_values[column], cand_values[column], tolerance)
                    if status != IDENTICAL:
                        result.difference({"key": format_key(key), "type": "value", "column": column,
                                           "reference": ref_values[column], "candidate": cand_values[column],
                                           "status": status})
                if status == DIFFERENT or (status != IDENTICAL and record_status == IDENTICAL):
                    record_status = status
            result.count(record_status)
