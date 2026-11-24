"""
Summary of verification results and rendering of the review report.
"""

import csv
import datetime

from jinja2 import Environment, StrictUndefined

from hydra_genetics.utils.verification.common import (
    COMPARISON_STATUSES, KNOWN_VARIANT_STATUSES, PASSING_STATUSES, json_safe, read_json,
)

PASSED = "passed"
REVIEW_REQUIRED = "review_required"


def summarise_results(results, metadata=None):
    """
    Combine comparison and known variant results into one summary.

    :param results: list of result dicts or paths to result JSON files; a known variant result file holds a list
    :param metadata: dict shown in the report header (pipeline, versions, directories, spec, ...)

    :return: dict with metadata, verdict ('passed' when every comparison is identical or within tolerance and
        every known variant is found, otherwise 'review_required'), totals, files and known_variants
    """
    comparisons, known_variants = [], []
    for item in results:
        data = read_json(item) if isinstance(item, str) else item
        for entry in data if isinstance(data, list) else [data]:
            (known_variants if entry.get("kind") == "known_variant" else comparisons).append(entry)
    comparisons.sort(key=lambda r: (str(r.get("name")), str(r.get("sample")), str(r.get("type"))))
    known_variants.sort(key=lambda r: (str(r.get("sample")), str(r.get("type")), str(r.get("variant_type"))))
    totals = {
        "comparisons": {s: sum(1 for r in comparisons if r.get("status") == s) for s in COMPARISON_STATUSES},
        "known_variants": {s: sum(1 for r in known_variants if r.get("status") == s) for s in KNOWN_VARIANT_STATUSES},
    }
    passed = all(r.get("status") in PASSING_STATUSES for r in comparisons + known_variants)
    metadata = dict(metadata or {})
    metadata.setdefault("generated", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    return json_safe({
        "metadata": metadata,
        "verdict": PASSED if passed else REVIEW_REQUIRED,
        "totals": totals,
        "files": comparisons,
        "known_variants": known_variants,
    })


TSV_COLUMNS = ["check", "name", "sample", "type", "comparator", "status", "details", "reference", "candidate"]


def write_summary_tsv(summary, path):
    """Write one row per comparison and per known variant check."""
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(TSV_COLUMNS)
        for r in summary["files"]:
            details = "; ".join(r.get("messages", []))
            if r.get("differences_total"):
                details = "{} differences{}".format(r["differences_total"], "; " + details if details else "")
            writer.writerow(["comparison", r.get("name"), r.get("sample") or "", r.get("type") or "", r.get("comparator"),
                             r.get("status"), details, r.get("reference"), r.get("candidate")])
        for r in summary["known_variants"]:
            name = r.get("description") or r.get("variant_type")
            writer.writerow(["known_variant", name, r.get("sample"), r.get("type"), r.get("variant_type"),
                             r.get("status"), r.get("details"), "", r.get("path") or ""])


def render_report(summary, template, css_files=(), output=None):
    """
    Render the HTML review report with jinja2 (autoescaping on).

    :param summary: dict from summarise_results
    :param template: path to the jinja2 template; it receives summary, metadata, verdict, totals, files,
        known_variants, samples (sorted sample_type names), names (file entry names) and css
    :param css_files: css files inlined in the report
    :param output: path of the html file to write (optional)

    :return: the html text
    """
    with open(template) as fh:
        environment = Environment(autoescape=True, undefined=StrictUndefined)
        compiled = environment.from_string(fh.read())
    css = ""
    for css_file in css_files:
        with open(css_file) as fh:
            css += fh.read()
    samples = sorted(set("{}_{}".format(r["sample"], r["type"]) if r.get("sample") else "run" for r in summary["files"]))
    names = sorted(set(r.get("name") for r in summary["files"]), key=str)
    html = compiled.render(summary=summary, metadata=summary["metadata"], verdict=summary["verdict"],
                           totals=summary["totals"], files=summary["files"], known_variants=summary["known_variants"],
                           samples=samples, names=names, css=css)
    if output:
        with open(output, "w") as fh:
            fh.write(html)
    return html
