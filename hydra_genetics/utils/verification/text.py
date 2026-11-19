"""
Comparison of two text files, line by line after removing volatile parts.
"""

import difflib
import re

from hydra_genetics.utils.verification.common import (
    DIFFERENT, Result, VerificationError, check_files, read_lines, run_comparison,
)


def select_lines(lines, settings):
    """
    Apply the line selection settings shared by text and delimited table files.

    - skip_until: regex, lines up to and including the first matching line are dropped
    - stop_at: regex, the first matching line and everything after it are dropped
    - ignore_lines: list of regexes, matching lines are dropped
    - replace: list of [regex, replacement] applied to every line (e.g. to remove dates)
    """
    skip_until, stop_at = settings.get("skip_until"), settings.get("stop_at")
    try:
        if skip_until:
            pattern = re.compile(skip_until)
            for index, line in enumerate(lines):
                if pattern.search(line):
                    lines = lines[index + 1:]
                    break
            else:
                raise VerificationError("no line matches skip_until '{}'".format(skip_until))
        if stop_at:
            pattern = re.compile(stop_at)
            for index, line in enumerate(lines):
                if pattern.search(line):
                    lines = lines[:index]
                    break
        ignore = [re.compile(p) for p in settings.get("ignore_lines") or []]
        lines = [line for line in lines if not any(p.search(line) for p in ignore)]
        for item in settings.get("replace") or []:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise VerificationError("replace items must be [regex, replacement], got {}".format(item))
            pattern = re.compile(item[0])
            lines = [pattern.sub(item[1], line) for line in lines]
    except re.error as e:
        raise VerificationError("invalid regular expression: {}".format(e))
    return lines


def compare_text(reference, candidate, settings=None, max_differences=100):
    """
    Compare two (gzipped) text files line by line.

    Settings: skip_until, stop_at, ignore_lines, replace (see select_lines) and sort (compare sorted lines).

    :return: result dict, see the verification documentation
    """
    settings = dict(settings or {})
    result = Result("text", reference, candidate, settings, max_differences)

    def run():
        if not check_files(result, reference, candidate):
            return
        ref_lines = select_lines(read_lines(reference), settings)
        cand_lines = select_lines(read_lines(candidate), settings)
        if settings.get("sort", False):
            ref_lines, cand_lines = sorted(ref_lines), sorted(cand_lines)
        result.set_count("reference_lines", len(ref_lines))
        result.set_count("candidate_lines", len(cand_lines))
        changed = 0
        for line in difflib.unified_diff(ref_lines, cand_lines, "reference", "candidate", lineterm="", n=0):
            if line.startswith(("---", "+++", "@@")):
                continue
            changed += 1
            result.difference({"key": "line", "type": "only_in_reference" if line.startswith("-") else "only_in_candidate",
                               "line": line[1:], "status": DIFFERENT})
        result.set_count("changed_lines", changed)

    return run_comparison(result, run)
