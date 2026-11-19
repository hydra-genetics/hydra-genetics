"""
Comparison of two BAM/CRAM files, streamed record by record with pysam.
"""

import hashlib
import itertools

import pysam

from hydra_genetics.utils.verification.common import (
    DIFFERENT, Result, VerificationError, check_files, run_comparison,
)

# Header lines that contain command lines, paths and versions
VOLATILE_HEADER_TAGS = ("@PG", "@CO")
MASK_64 = (1 << 64) - 1


def _record_text(record, tags):
    text = record.to_string()
    if not tags:
        text = "\t".join(text.split("\t")[:11])
    return text


def _header_lines(alignment_file):
    return [line for line in str(alignment_file.header).splitlines() if line and not line.startswith(VOLATILE_HEADER_TAGS)]


def _open(path, threads, reference_fasta):
    try:
        return pysam.AlignmentFile(path, check_sq=False, threads=threads, reference_filename=reference_fasta)
    except (OSError, ValueError) as e:
        raise VerificationError("could not open {}: {}".format(path, e))


def compare_bam(reference, candidate, settings=None, max_differences=100, threads=1):
    """
    Compare two BAM (or CRAM) files.

    Settings:
      - sort: compare records regardless of order (default false), e.g. for STAR output
      - tags: include optional tags in the comparison (default true)
      - header: compare header lines (default false); @PG and @CO lines are always ignored
      - reference_fasta: fasta file needed to read CRAM files

    Records are compared as SAM text. An order sensitive digest and an order insensitive digest (sum of 64 bit
    record hashes) are computed for both files; differing records are listed in order sensitive mode only.

    :return: result dict, see the verification documentation
    """
    settings = dict(settings or {})
    result = Result("bam", reference, candidate, settings, max_differences)
    tags = settings.get("tags", True)

    def run():
        if not check_files(result, reference, candidate):
            return
        ref_file = _open(reference, threads, settings.get("reference_fasta"))
        cand_file = _open(candidate, threads, settings.get("reference_fasta"))
        if settings.get("header", False):
            ref_lines, cand_lines = _header_lines(ref_file), _header_lines(cand_file)
            for line in [line for line in ref_lines if line not in cand_lines]:
                result.difference({"key": "header", "type": "only_in_reference", "line": line, "status": DIFFERENT})
            for line in [line for line in cand_lines if line not in ref_lines]:
                result.difference({"key": "header", "type": "only_in_candidate", "line": line, "status": DIFFERENT})
        digests = {"reference": hashlib.sha256(), "candidate": hashlib.sha256()}
        multisets = {"reference": 0, "candidate": 0}
        counts = {"reference": 0, "candidate": 0}
        differing_positions = 0
        records = itertools.zip_longest(ref_file.fetch(until_eof=True), cand_file.fetch(until_eof=True))
        for index, (ref_record, cand_record) in enumerate(records):
            texts = {}
            for label, record in (("reference", ref_record), ("candidate", cand_record)):
                if record is None:
                    continue
                text = _record_text(record, tags)
                texts[label] = text
                encoded = text.encode()
                digests[label].update(encoded + b"\n")
                multisets[label] = (multisets[label] + int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big")) & MASK_64
                counts[label] += 1
            if texts.get("reference") != texts.get("candidate"):
                differing_positions += 1
                if not settings.get("sort", False):
                    result.difference({"key": "record {}".format(index + 1), "type": "record",
                                       "reference": texts.get("reference"), "candidate": texts.get("candidate"),
                                       "status": DIFFERENT})
        ref_file.close()
        cand_file.close()
        result.set_count("reference_records", counts["reference"])
        result.set_count("candidate_records", counts["candidate"])
        result.set_count("differing_positions", differing_positions)
        same_order = digests["reference"].digest() == digests["candidate"].digest()
        same_records = multisets["reference"] == multisets["candidate"] and counts["reference"] == counts["candidate"]
        result.data["digests"] = {
            "reference": {"ordered": digests["reference"].hexdigest(), "unordered": "{:016x}".format(multisets["reference"])},
            "candidate": {"ordered": digests["candidate"].hexdigest(), "unordered": "{:016x}".format(multisets["candidate"])},
        }
        if settings.get("sort", False):
            if not same_records:
                result.difference({"key": "records", "type": "record_set",
                                   "reference": "{} records".format(counts["reference"]),
                                   "candidate": "{} records".format(counts["candidate"]), "status": DIFFERENT})
                result.message("the record sets differ; individual records are not listed when sort is true")
        elif not same_order and same_records:
            result.message("the files contain the same records in a different order, set 'sort: true' to accept this")

    return run_comparison(result, run)
