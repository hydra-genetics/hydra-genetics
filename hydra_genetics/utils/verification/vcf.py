"""
Comparison of two VCF files.
"""

import logging
import re
from collections import OrderedDict

import pysam

from hydra_genetics.utils.vcf_filter import create_filter_from_vcf, get_vep_fields, select_sample_index
from hydra_genetics.utils.verification.common import (
    DIFFERENT, Result, VerificationError, check_files, normalise_tolerance, parse_columns, run_comparison,
)
from hydra_genetics.utils.verification.records import compare_records

FIXED_COLUMNS = ["chrom", "pos", "id", "ref", "alt", "qual", "filter"]
FIELD_GROUPS = ["FORMAT", "INFO", "VEP"]

# Header lines that change between runs of the same pipeline version (dates, paths, command lines, versions)
VOLATILE_HEADER_LINES = [
    r"^##fileDate=",
    r"^##VEP=",
    r"^##VEP-command-line=",
    r"Command(Line)?=",
    r"^##commandline=",
    r"^##reference=",
    r"^##source=",
    r"Version=",
    r"^##tumor_sample=",
    r"^##normal_sample=",
    r"^##SVDB",
]


def parse_vcf_columns(columns):
    """
    Parse the 'columns' setting of a VCF spec into an ordered dict column -> tolerance.

    Fixed columns are given by name (chrom, pos, id, ref, alt, qual, filter); FORMAT, INFO and VEP fields are
    given as lists under a FORMAT:, INFO: or VEP: item, e.g. [{chrom: =}, {FORMAT: [{AF: 0.01}]}].
    """
    if columns is None:
        return None
    if isinstance(columns, dict):
        columns = [{k: v} for k, v in columns.items()]
    parsed = OrderedDict()
    for item in columns:
        items = item.items() if isinstance(item, dict) else [(item, None)]
        for name, value in items:
            if name in FIELD_GROUPS:
                for field, tolerance in parse_columns(value or []).items():
                    parsed["{}:{}".format(name, field)] = tolerance
            elif str(name).lower() in FIXED_COLUMNS:
                parsed[str(name).lower()] = normalise_tolerance(value)
            else:
                raise VerificationError("unknown VCF column '{}', use one of {} or a FORMAT/INFO/VEP group".format(
                    name, ", ".join(FIXED_COLUMNS)))
    return parsed


def _normalise(value):
    """Convert a pysam value into a string or a tuple of strings."""
    if isinstance(value, tuple):
        return tuple(_normalise(v) for v in value)
    if value is None:
        return "."
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return "{:.7g}".format(value)
    return str(value)


def _select_sample(variant_file, settings):
    samples = list(variant_file.header.samples)
    if not samples:
        return None
    sample = settings.get("sample")
    if isinstance(sample, int) and not isinstance(sample, bool):
        if sample >= len(samples):
            raise VerificationError("sample index {} out of range, samples: {}".format(sample, ", ".join(samples)))
        return sample
    if isinstance(sample, str):
        if sample not in samples:
            raise VerificationError("sample '{}' not found, samples: {}".format(sample, ", ".join(samples)))
        return samples.index(sample)
    try:
        return select_sample_index(samples, settings.get("sample_name_regex"))
    except Exception as e:
        raise VerificationError("could not select sample ({}), set 'sample' or 'sample_name_regex'".format(e))


class VcfReader(object):
    """Reads records of one VCF file as (key, values) using the selected columns."""

    def __init__(self, path, settings, columns, result, label):
        self.path, self.settings, self.columns, self.result, self.label = path, settings, columns, result, label
        self.variant_file = pysam.VariantFile(path)
        self.header_text = str(self.variant_file.header)
        self.sample_index = _select_sample(self.variant_file, settings)
        self.vep_fields = get_vep_fields(self.variant_file.header)
        self.info_ids = set(self.variant_file.header.info.keys())
        self.format_ids = set(self.variant_file.header.formats.keys())
        self.filter = None
        if settings.get("filter"):
            self.filter = create_filter_from_vcf(self.variant_file, settings["filter"], sample_index=self.sample_index or 0)
        if columns is not None:
            for column in columns:
                group, _, field = column.partition(":")
                if group == "INFO" and field not in self.info_ids:
                    result.message("{}: INFO field {} is not defined in the header".format(label, field))
                elif group == "FORMAT" and field not in self.format_ids:
                    result.message("{}: FORMAT field {} is not defined in the header".format(label, field))
                elif group == "VEP" and (self.vep_fields is None or field not in self.vep_fields):
                    result.message("{}: VEP field {} is not defined in the CSQ header".format(label, field))

    def _value(self, record, column):
        group, _, field = column.partition(":")
        if column == "chrom":
            return record.chrom
        if column == "pos":
            return str(record.pos)
        if column == "id":
            return _normalise(record.id)
        if column == "ref":
            return record.ref
        if column == "alt":
            return ",".join(record.alts or ("."))
        if column == "qual":
            return _normalise(record.qual)
        if column == "filter":
            return ";".join(record.filter.keys()) or "."
        if group == "INFO":
            if field not in self.info_ids:
                return None
            return _normalise(record.info.get(field))
        if group == "FORMAT":
            if self.sample_index is None or field not in self.format_ids:
                return None
            return _normalise(record.samples[self.sample_index].get(field))
        if group == "VEP":
            if self.vep_fields is None or field not in self.vep_fields or "CSQ" not in record.info:
                return None
            transcripts = record.info["CSQ"]
            value = transcripts[0].split("|")[self.vep_fields[field]] if transcripts else ""
            return value or "."
        raise VerificationError("unknown column {}".format(column))

    def _all_columns(self, record):
        columns = list(FIXED_COLUMNS)
        columns += ["INFO:{}".format(k) for k in record.info.keys()]
        if self.sample_index is not None:
            columns += ["FORMAT:{}".format(k) for k in record.format.keys()]
        return columns

    def records(self):
        records, dropped = [], 0
        for record in self.variant_file:
            if self.filter is not None:
                try:
                    if self.filter(record):
                        dropped += 1
                        continue
                except (TypeError, ValueError, KeyError, IndexError) as e:
                    raise VerificationError(
                        "{}: could not evaluate filter '{}' on {}:{} ({}); fields with several values need an index, "
                        "e.g. FORMAT:AF:0".format(self.label, self.settings["filter"], record.chrom, record.pos, e))
            key = (record.chrom, record.pos, record.ref, ",".join(record.alts or (".")))
            columns = self.columns if self.columns is not None else self._all_columns(record)
            values = {}
            for column in columns:
                value = self._value(record, column)
                if value is not None:
                    values[column] = value
            records.append((key, values))
        self.result.set_count("{}_filtered_out".format(self.label), dropped)
        return records


def header_lines(header_text, ignore_patterns):
    patterns = [re.compile(p) for p in VOLATILE_HEADER_LINES + list(ignore_patterns or [])]
    return [line for line in header_text.splitlines() if line.startswith("##") and not any(p.search(line) for p in patterns)]


def compare_vcf(reference, candidate, settings=None, max_differences=100):
    """
    Compare two VCF files (plain or bgzipped).

    Settings:
      - columns: columns to compare with tolerances (see parse_vcf_columns); default: every field, exact
      - filter: hydra filter expression, variants for which it is true are removed from both files
      - sample / sample_name_regex: sample used for FORMAT fields (index or name / regex), default: the only sample
      - header: compare header lines (default false); volatile lines are always ignored
      - header_ignore: extra regexes of header lines to ignore

    Records are matched on chrom, pos, ref and alt.

    :return: result dict, see the verification documentation
    """
    settings = dict(settings or {})
    result = Result("vcf", reference, candidate, settings, max_differences)

    def run():
        if not check_files(result, reference, candidate):
            return
        columns = parse_vcf_columns(settings.get("columns"))
        try:
            readers = [VcfReader(reference, settings, columns, result, "reference"),
                       VcfReader(candidate, settings, columns, result, "candidate")]
        except (OSError, ValueError) as e:
            raise VerificationError("could not open VCF: {}".format(e))
        if settings.get("header", False):
            ref_lines, cand_lines = [header_lines(r.header_text, settings.get("header_ignore")) for r in readers]
            for line in [line for line in ref_lines if line not in cand_lines]:
                result.difference({"key": "header", "type": "only_in_reference", "line": line, "status": DIFFERENT})
            for line in [line for line in cand_lines if line not in ref_lines]:
                result.difference({"key": "header", "type": "only_in_candidate", "line": line, "status": DIFFERENT})
        logging.getLogger(__name__).info("comparing %s and %s", reference, candidate)
        compare_records(result, readers[0].records(), readers[1].records(), columns,
                        format_key=lambda key: "{}:{} {}>{}".format(*key))

    return run_comparison(result, run)
