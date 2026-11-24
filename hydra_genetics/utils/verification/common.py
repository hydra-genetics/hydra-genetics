"""
Shared helpers for the verification comparators: statuses, tolerances, result dicts and file reading.
"""

import gzip
import json
import math
import os
import re

import yaml

# Statuses of a comparison between a reference and a candidate file
IDENTICAL = "identical"
WITHIN_TOLERANCE = "within_tolerance"
DIFFERENT = "different"
MISSING = "missing"
ERROR = "error"
COMPARISON_STATUSES = [IDENTICAL, WITHIN_TOLERANCE, DIFFERENT, MISSING, ERROR]

# Statuses of a known (true positive) variant check
FOUND = "found"
NOT_FOUND = "not_found"
FAILED_EXPECTATION = "failed_expectation"
NOT_CHECKED = "not_checked"
KNOWN_VARIANT_STATUSES = [FOUND, NOT_FOUND, FAILED_EXPECTATION, NOT_CHECKED, ERROR]

# Statuses that do not require a review
PASSING_STATUSES = {IDENTICAL, WITHIN_TOLERANCE, FOUND}

# Values in a tolerance specification that mean "exact match"
EXACT_TOLERANCES = (None, "=", "==", "exact", "")

NUMBER_REGEX = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
NAN_STRINGS = {"nan", "NaN", "NAN"}

# Relative slack used for numeric tolerances, covers float32 values written by pysam/htslib
RELATIVE_EPSILON = 1e-6


class VerificationError(Exception):
    """An anticipated problem with the input data, reported as status 'error' instead of failing."""


class SpecLoader(yaml.SafeLoader):
    """
    YAML loader that accepts a bare '=' as a value (as in 'chrom: =').

    PyYAML resolves a plain '=' to the YAML 'value' tag, which safe_load can not construct.
    """


SpecLoader.add_constructor("tag:yaml.org,2002:value", lambda loader, node: loader.construct_scalar(node))


def load_yaml(path):
    """Load a yaml file with SpecLoader."""
    with open(path) as fh:
        return yaml.load(fh, Loader=SpecLoader)


def open_text(path):
    """Open a plain or gzip compressed text file."""
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic == b"\x1f\x8b":
        return gzip.open(path, "rt")
    return open(path)


def read_lines(path):
    """Read all lines of a (gzipped) text file without line endings."""
    with open_text(path) as fh:
        return fh.read().splitlines()


def column_id(column):
    """Column identifiers are compared as strings, so that integer column ids from yaml work."""
    return str(column)


def parse_number(value):
    """Return value as float if it is a plain number (or NaN), otherwise None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if NUMBER_REGEX.match(text):
            return float(text)
        if text in NAN_STRINGS:
            return float("nan")
    return None


def normalise_tolerance(tolerance):
    """
    Convert a tolerance from the spec into a dict.

    - None, '=', 'exact': exact match
    - a number: absolute tolerance
    - 'N%': relative tolerance in percent
    - 'unordered': lists (separated by , & | or ;) are equal regardless of order
    - 'ignore': the column is not compared
    """
    if isinstance(tolerance, bool):
        raise VerificationError("invalid tolerance: {}".format(tolerance))
    if tolerance in EXACT_TOLERANCES:
        return {"type": "exact"}
    if isinstance(tolerance, (int, float)):
        return {"type": "absolute", "value": float(tolerance)}
    if isinstance(tolerance, str):
        text = tolerance.strip()
        if text in ("unordered", "ignore"):
            return {"type": text}
        if text.endswith("%") and parse_number(text[:-1]) is not None:
            return {"type": "relative", "value": float(text[:-1])}
        if parse_number(text) is not None:
            return {"type": "absolute", "value": float(text)}
    raise VerificationError("invalid tolerance: {}".format(tolerance))


def describe_tolerance(tolerance):
    """Human readable text of a normalised tolerance."""
    if tolerance["type"] == "absolute":
        return "+/- {:g}".format(tolerance["value"])
    if tolerance["type"] == "relative":
        return "+/- {:g}%".format(tolerance["value"])
    return tolerance["type"]


def _split_list(value):
    return sorted(v.strip() for v in re.split(r"[,&|;]", value))


def compare_values(reference, candidate, tolerance):
    """
    Compare two values (strings, numbers, None or tuples of those) using a normalised tolerance.

    :return: IDENTICAL, WITHIN_TOLERANCE or DIFFERENT
    """
    if isinstance(reference, tuple) or isinstance(candidate, tuple):
        reference = reference if isinstance(reference, tuple) else (reference,)
        candidate = candidate if isinstance(candidate, tuple) else (candidate,)
        if tolerance["type"] == "unordered":
            reference, candidate = tuple(sorted(map(str, reference))), tuple(sorted(map(str, candidate)))
        if len(reference) != len(candidate):
            return DIFFERENT
        statuses = [compare_values(r, c, tolerance) for r, c in zip(reference, candidate)]
        if DIFFERENT in statuses:
            return DIFFERENT
        return WITHIN_TOLERANCE if WITHIN_TOLERANCE in statuses else IDENTICAL
    if reference == candidate or str(reference) == str(candidate):
        return IDENTICAL
    if tolerance["type"] == "unordered" and reference is not None and candidate is not None:
        return WITHIN_TOLERANCE if _split_list(str(reference)) == _split_list(str(candidate)) else DIFFERENT
    if tolerance["type"] not in ("absolute", "relative"):
        return DIFFERENT
    ref_number, cand_number = parse_number(reference), parse_number(candidate)
    if ref_number is None or cand_number is None:
        return DIFFERENT
    if math.isnan(ref_number) or math.isnan(cand_number):
        return IDENTICAL if math.isnan(ref_number) and math.isnan(cand_number) else DIFFERENT
    if ref_number == cand_number:
        return IDENTICAL
    difference = abs(ref_number - cand_number)
    largest = max(abs(ref_number), abs(cand_number))
    if tolerance["type"] == "absolute":
        allowed = tolerance["value"]
    else:
        allowed = tolerance["value"] / 100.0 * largest
    return WITHIN_TOLERANCE if difference <= allowed + RELATIVE_EPSILON * largest else DIFFERENT


def parse_columns(columns):
    """
    Parse the 'columns' setting of a table spec into an ordered dict of column id -> normalised tolerance.

    Accepts a list of single key dicts ([{chrom: =}, {AF: 0.01}]), a list of names or a dict.
    """
    parsed = {}
    if columns is None:
        return parsed
    if isinstance(columns, dict):
        columns = [{k: v} for k, v in columns.items()]
    for item in columns:
        if isinstance(item, dict):
            for name, tolerance in item.items():
                parsed[column_id(name)] = normalise_tolerance(tolerance)
        else:
            parsed[column_id(item)] = normalise_tolerance(None)
    return parsed


def json_safe(value):
    """Make a value JSON serialisable: NaN/inf become strings, tuples become lists, keys become strings."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def shorten(value, length=300):
    """Shorten long strings shown in difference lists."""
    if isinstance(value, str) and len(value) > length:
        return value[:length] + "..."
    return value


class Result(object):
    """Collects counts, differences and messages for one comparison."""

    def __init__(self, comparator, reference, candidate, settings=None, max_differences=100):
        self.data = {
            "kind": "comparison",
            "comparator": comparator,
            "status": IDENTICAL,
            "reference": reference,
            "candidate": candidate,
            "counts": {},
            "differences": [],
            "differences_total": 0,
            "truncated": False,
            "messages": [],
            "settings": json_safe(settings or {}),
        }
        self.max_differences = max_differences

    def count(self, name, number=1):
        self.data["counts"][name] = self.data["counts"].get(name, 0) + number

    def set_count(self, name, number):
        self.data["counts"][name] = number

    def message(self, text):
        if text not in self.data["messages"]:
            self.data["messages"].append(text)

    def difference(self, entry):
        """Add a difference, entry['status'] decides whether it makes the comparison different."""
        status = entry.get("status", DIFFERENT)
        if status == DIFFERENT:
            self.data["status"] = DIFFERENT
        elif status == WITHIN_TOLERANCE and self.data["status"] == IDENTICAL:
            self.data["status"] = WITHIN_TOLERANCE
        self.data["differences_total"] += 1
        if len(self.data["differences"]) < self.max_differences:
            self.data["differences"].append(json_safe({k: shorten(v) for k, v in entry.items()}))
        else:
            self.data["truncated"] = True

    def set_status(self, status):
        self.data["status"] = status

    def finish(self):
        return self.data


def check_files(result, reference, candidate):
    """Set status MISSING and return False if one of the files does not exist."""
    missing = [name for name, path in (("reference", reference), ("candidate", candidate)) if not path or not os.path.isfile(path)]
    for name in missing:
        result.message("{} file not found: {}".format(name, reference if name == "reference" else candidate))
    if missing:
        result.set_status(MISSING)
        return False
    return True


def run_comparison(result, function):
    """Run function(); a VerificationError sets status ERROR and is recorded as a message."""
    try:
        function()
    except VerificationError as e:
        result.set_status(ERROR)
        result.message(str(e))
    return result.finish()


def write_json(data, path):
    """Write a result dict as JSON."""
    with open(path, "w") as fh:
        json.dump(json_safe(data), fh, indent=2, sort_keys=False)
        fh.write("\n")


def read_json(path):
    with open(path) as fh:
        return json.load(fh)
