"""
Checks of known (true positive) variants in candidate result files.
"""

import os
import re

import pysam

from hydra_genetics.utils.vcf_filter import create_filter_from_vcf
from hydra_genetics.utils.verification.common import (
    ERROR, FAILED_EXPECTATION, FOUND, NOT_CHECKED, NOT_FOUND, VerificationError, column_id, json_safe, parse_number,
)
from hydra_genetics.utils.verification.table import read_table
from hydra_genetics.utils.verification.vcf import _select_sample


def _matches(cell, wanted):
    """True if a table cell matches a value from 'match' (exact text, equal number or {regex: ...})."""
    if cell is None:
        return False
    if isinstance(wanted, dict):
        if "regex" in wanted:
            return re.search(wanted["regex"], cell) is not None
        raise VerificationError("match values must be a value or {{regex: ...}}, got {}".format(wanted))
    if str(wanted) == cell:
        return True
    wanted_number, cell_number = parse_number(wanted), parse_number(cell)
    return wanted_number is not None and cell_number is not None and wanted_number == cell_number


def _meets(cell, requirement):
    """Return (ok, reason) for one 'expect' requirement: {min, max, equals, regex} or a plain value."""
    if not isinstance(requirement, dict):
        requirement = {"equals": requirement}
    if cell is None:
        return False, "missing"
    reasons = []
    for name, limit in requirement.items():
        if name == "equals":
            if not _matches(cell, limit):
                reasons.append("!= {}".format(limit))
        elif name == "regex":
            if re.search(limit, cell) is None:
                reasons.append("does not match {}".format(limit))
        elif name in ("min", "max"):
            value = parse_number(cell)
            if value is None:
                reasons.append("not a number")
            elif name == "min" and value < float(limit):
                reasons.append("< {}".format(limit))
            elif name == "max" and value > float(limit):
                reasons.append("> {}".format(limit))
        else:
            raise VerificationError("unknown expectation '{}', use min, max, equals or regex".format(name))
    return not reasons, "; ".join(reasons)


def _check_table(expectation, path, settings, result):
    _, rows = read_table(path, dict(settings))
    match = {column_id(k): v for k, v in (expectation.get("match") or {}).items()}
    expect = {column_id(k): v for k, v in (expectation.get("expect") or {}).items()}
    candidates = [row for row in rows if all(_matches(row.get(c), v) for c, v in match.items())]
    if not candidates:
        result["status"] = NOT_FOUND
        result["details"] = "no row matches {}".format(match) if match else "the table is empty"
        return
    failures = []
    for row in candidates:
        checks = {c: _meets(row.get(c), r) for c, r in expect.items()}
        if all(ok for ok, _ in checks.values()):
            result["status"] = FOUND
            result["observed"] = {c: row.get(c) for c in list(match) + list(expect)}
            return
        failures.append((row, checks))
    row, checks = failures[0]
    result["status"] = FAILED_EXPECTATION
    result["observed"] = {c: row.get(c) for c in list(match) + list(expect)}
    result["details"] = "; ".join("{} {}".format(c, reason) for c, (ok, reason) in checks.items() if not ok)


def _check_vcf(expectation, path, settings, result):
    variant = expectation.get("variant") or {}
    if "chrom" not in variant or "pos" not in variant:
        raise VerificationError("variant needs at least chrom and pos")
    variant_file = pysam.VariantFile(path)
    sample_index = _select_sample(variant_file, settings)
    records = []
    for record in variant_file:
        if record.chrom != str(variant["chrom"]) or record.pos != int(variant["pos"]):
            continue
        if "ref" in variant and record.ref != str(variant["ref"]):
            continue
        if "alt" in variant and str(variant["alt"]) not in (record.alts or ()):
            continue
        records.append(record)
    if not records:
        result["status"] = NOT_FOUND
        result["details"] = "no record at {}:{}".format(variant["chrom"], variant["pos"])
        return
    result["observed"] = {"record": str(records[0]).rstrip("\n")[:500]}
    expression = expectation.get("expression")
    if not expression:
        result["status"] = FOUND
        return
    check = create_filter_from_vcf(variant_file, expression, sample_index=sample_index or 0)
    for record in records:
        try:
            if check(record):
                result["status"] = FOUND
                result["observed"] = {"record": str(record).rstrip("\n")[:500]}
                return
        except (TypeError, ValueError, KeyError, IndexError) as e:
            raise VerificationError("could not evaluate '{}' ({}); fields with several values need an index, "
                                    "e.g. FORMAT:AF:0".format(expression, e))
    result["status"] = FAILED_EXPECTATION
    result["details"] = "expression '{}' is false".format(expression)


def check_known_variants(expectations, files):
    """
    Check that known variants are present in candidate result files.

    :param expectations: list of dicts with keys sample, type, variant_type, description, file and either
        variant: {chrom, pos, ref, alt} plus an optional hydra filter 'expression' that must be true (VCF files),
        or match: {column: value or {regex: ...}} plus expect: {column: {min, max, equals, regex}} (tables)
    :param files: dict file name -> {"path": ..., "comparator": "vcf" or "table", "settings": {...}}; the settings
        of the files entry are used to read the file (sep, header, records, sample, ...)

    :return: list of result dicts with status found, not_found, failed_expectation, not_checked or error
    """
    results = []
    for expectation in expectations:
        result = {
            "kind": "known_variant",
            "sample": expectation.get("sample"),
            "type": expectation.get("type"),
            "variant_type": expectation.get("variant_type"),
            "description": expectation.get("description", ""),
            "file": expectation.get("file"),
            "path": None,
            "status": NOT_CHECKED,
            "observed": {},
            "details": "",
            "expectation": json_safe(expectation),
        }
        results.append(result)
        target = files.get(expectation.get("file"))
        if target is None:
            result["details"] = "no file entry named '{}'".format(expectation.get("file"))
            continue
        result["path"] = target["path"]
        if not os.path.isfile(target["path"]):
            result["details"] = "file not found: {}".format(target["path"])
            continue
        try:
            if target.get("comparator") == "vcf":
                _check_vcf(expectation, target["path"], target.get("settings") or {}, result)
            elif target.get("comparator") in ("table", "json", "html"):
                _check_table(expectation, target["path"], target.get("settings") or {}, result)
            else:
                result["details"] = "known variants can not be checked in {} files".format(target.get("comparator"))
        except VerificationError as e:
            result["status"] = ERROR
            result["details"] = str(e)
        result["observed"] = json_safe(result["observed"])
    return results
