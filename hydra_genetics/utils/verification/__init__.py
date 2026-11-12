"""
Verification of hydra-genetics results between two pipeline versions.

Comparators take a reference and a candidate file plus the settings of one 'files' entry of the verification
spec, and return a JSON serialisable result dict. See docs/verification.md.
"""

from hydra_genetics.utils.verification.bam import compare_bam
from hydra_genetics.utils.verification.common import (
    COMPARISON_STATUSES, KNOWN_VARIANT_STATUSES, SpecLoader, VerificationError, load_yaml, write_json,
)
from hydra_genetics.utils.verification.known_variants import check_known_variants
from hydra_genetics.utils.verification.report import render_report, summarise_results, write_summary_tsv
from hydra_genetics.utils.verification.table import compare_table
from hydra_genetics.utils.verification.text import compare_text
from hydra_genetics.utils.verification.vcf import compare_vcf

COMPARATORS = {
    "vcf": compare_vcf,
    "bam": compare_bam,
    "table": compare_table,
    "text": compare_text,
}

# File types that can be given in the spec and the comparator used for them
TYPES = {"vcf": "vcf", "bam": "bam", "cram": "bam", "table": "table", "json": "table", "html": "table", "text": "text"}


def infer_type(path, settings=None):
    """The 'type' of a files entry: the setting if given, otherwise from the file extension (None if unknown)."""
    settings = settings or {}
    if settings.get("type"):
        return settings["type"]
    lower = path.lower()
    for ending, file_type in ((".vcf", "vcf"), (".vcf.gz", "vcf"), (".bam", "bam"), (".cram", "cram"), (".tsv", "table"),
                              (".csv", "table"), (".json", "json"), (".html", "html"), (".htm", "html")):
        if lower.endswith(ending):
            return file_type
    return None


def compare_file(reference, candidate, settings=None, max_differences=100, threads=1):
    """Compare two files with the comparator chosen by infer_type."""
    settings = dict(settings or {})
    file_type = infer_type(candidate, settings)
    if file_type not in TYPES:
        raise VerificationError("unknown file type '{}' for {}, set 'type' to one of {}".format(
            file_type, candidate, ", ".join(sorted(TYPES))))
    comparator = TYPES[file_type]
    if file_type in ("json", "html"):
        settings.setdefault("source", file_type)
    if comparator == "bam":
        return compare_bam(reference, candidate, settings, max_differences, threads=threads)
    return COMPARATORS[comparator](reference, candidate, settings, max_differences)


__all__ = [
    "COMPARATORS", "COMPARISON_STATUSES", "KNOWN_VARIANT_STATUSES", "SpecLoader", "TYPES", "VerificationError",
    "check_known_variants", "compare_bam", "compare_file", "compare_table", "compare_text", "compare_vcf", "infer_type",
    "load_yaml", "render_report", "summarise_results", "write_json", "write_summary_tsv",
]
