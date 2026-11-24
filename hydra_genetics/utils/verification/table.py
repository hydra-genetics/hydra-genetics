"""
Comparison of tables read from delimited text, JSON or HTML files.
"""

import base64
import binascii
import csv
import json
import re
import zlib
from collections import OrderedDict
from html.parser import HTMLParser

from hydra_genetics.utils.verification.common import (
    Result, VerificationError, check_files, column_id, open_text, parse_columns, read_lines, run_comparison,
)
from hydra_genetics.utils.verification.records import compare_records
from hydra_genetics.utils.verification.text import select_lines

SOURCES = ("delimited", "json", "html")


def table_source(path, settings):
    """The source format of a table: settings 'source'/'type', otherwise the file extension."""
    source = settings.get("source") or settings.get("type")
    if source in ("json", "html"):
        return source
    if source in (None, "table", "delimited"):
        lower = path.lower()
        if lower.endswith(".json") or lower.endswith(".json.gz"):
            return "json"
        if lower.endswith(".html") or lower.endswith(".htm"):
            return "html"
        return "delimited"
    raise VerificationError("unknown table source '{}', use one of {}".format(source, ", ".join(SOURCES)))


# Delimited text

def read_delimited(path, settings):
    sep = settings.get("sep", "\t")
    lines = select_lines(read_lines(path), settings)
    comment = settings.get("comment")
    lines = [line for line in lines if line.strip() and not (comment and line.startswith(comment))]
    if sep == "whitespace":
        parsed = [line.split() for line in lines]
    else:
        parsed = list(csv.reader(lines, delimiter=sep))
    header = settings.get("header", True)
    columns = None
    if header and parsed:
        columns = [c.strip() for c in parsed[0]]
        parsed = parsed[1:]
    rows = []
    for fields in parsed:
        if columns is None:
            rows.append(OrderedDict((str(i), v) for i, v in enumerate(fields)))
        else:
            row = OrderedDict((name, fields[i]) for i, name in enumerate(columns) if i < len(fields))
            for i in range(len(columns), len(fields)):
                row[str(i)] = fields[i]
            rows.append(row)
    if columns is None:
        columns = [str(i) for i in range(max([len(r) for r in rows] or [0]))]
    return columns, rows


# JSON

def decode_json_text(text, compressed="auto"):
    """
    Parse JSON text, optionally stored as base64 encoded gzip/zlib data (as the hydra-genetics CNV report does).

    :param compressed: 'auto', 'none' or 'gzip+base64'
    """
    text = text.strip()
    if compressed not in ("auto", "none", "gzip+base64"):
        raise VerificationError("unknown compression '{}', use auto, none or gzip+base64".format(compressed))
    if compressed == "gzip+base64" or (compressed == "auto" and text[:1] not in ("{", "[", '"')):
        try:
            text = zlib.decompress(base64.b64decode(text, validate=True), 47).decode()
        except (binascii.Error, zlib.error, ValueError) as e:
            raise VerificationError("could not decode base64 compressed JSON: {}".format(e))
    try:
        return json.loads(text)
    except ValueError as e:
        raise VerificationError("invalid JSON: {}".format(e))


def _flatten(value, prefix, row):
    if isinstance(value, dict):
        for key, item in value.items():
            _flatten(item, "{}.{}".format(prefix, key) if prefix else str(key), row)
    elif isinstance(value, list) and all(not isinstance(v, (dict, list)) for v in value):
        row[prefix] = ",".join("" if v is None else str(v) for v in value)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _flatten(item, "{}[{}]".format(prefix, index), row)
    else:
        row[prefix] = "" if value is None else str(value)


def _scalars(node):
    return OrderedDict((k, v) for k, v in node.items() if not isinstance(v, (dict, list)))


def _path_steps(path):
    steps = []
    for part in [p for p in path.strip().split(".") if p]:
        match = re.match(r"^([^\[\]]*)((\[(\*|\d+)\])*)$", part)
        if match is None:
            raise VerificationError("invalid records path element '{}'".format(part))
        if match.group(1):
            steps.append(("key", match.group(1)))
        for index in re.findall(r"\[(\*|\d+)\]", match.group(2)):
            steps.append(("all", None) if index == "*" else ("index", int(index)))
    return steps


def json_records(data, path):
    """
    Extract records from parsed JSON with a path such as '[*].callers[*].segments'.

    Steps are separated by '.', '[*]' iterates over a list and '[N]' selects one element. Scalar fields of the
    objects passed on the way are added to each record as '<key>.<field>', where key is the name of the list
    the object came from ('root' for a top level list). A path that ends on a list of objects gives one record
    per object, a path that ends on an object gives one record.
    """
    nodes = [(data, OrderedDict(), "root")]
    for kind, value in _path_steps(path):
        next_nodes = []
        for node, context, name in nodes:
            if kind == "key":
                if isinstance(node, dict) and value in node:
                    context = OrderedDict(context)
                    context.update(("{}.{}".format(name, k), v) for k, v in _scalars(node).items())
                    next_nodes.append((node[value], context, value))
            elif isinstance(node, list):
                items = enumerate(node) if kind == "all" else [(value, node[value])] if -len(node) <= value < len(node) else []
                for _, item in items:
                    next_nodes.append((item, context, name))
        nodes = next_nodes
    records = []
    for node, context, name in nodes:
        items = node if isinstance(node, list) else [node]
        for item in items:
            row = OrderedDict((k, "" if v is None else str(v)) for k, v in context.items())
            if isinstance(item, dict):
                _flatten(item, "", row)
            else:
                _flatten(item, "value", row)
            records.append(row)
    return records


def read_json(path, settings, text=None):
    if text is None:
        with open_text(path) as fh:
            text = fh.read()
    data = decode_json_text(text, settings.get("compressed", "auto"))
    if settings.get("records"):
        rows = json_records(data, settings["records"])
    else:
        flat = OrderedDict()
        _flatten(data, "", flat)
        rows = [OrderedDict([("path", k), ("value", v)]) for k, v in flat.items()]
        if "key" not in settings:
            settings["key"] = ["path"]
    columns = []
    for row in rows:
        columns.extend(c for c in row if c not in columns)
    return columns, rows


# HTML

class _TableParser(HTMLParser):
    """Collects all <table> elements: their id and their rows of (cell text, is header cell)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.stack, self.cell = [], [], None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            table = {"id": dict(attrs).get("id"), "rows": []}
            self.tables.append(table)
            self.stack.append(table)
        elif not self.stack:
            return
        elif tag == "tr":
            self._close_cell()
            self.stack[-1]["rows"].append([])
        elif tag in ("td", "th"):
            self._close_cell()
            if not self.stack[-1]["rows"]:
                self.stack[-1]["rows"].append([])
            self.cell = {"text": [], "header": tag == "th"}
        elif tag == "br" and self.cell is not None:
            self.cell["text"].append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th", "tr"):
            self._close_cell()
        elif tag == "table" and self.stack:
            self._close_cell()
            self.stack.pop()

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"].append(data)

    def _close_cell(self):
        if self.cell is not None and self.stack:
            text = " ".join("".join(self.cell["text"]).split())
            self.stack[-1]["rows"][-1].append((text, self.cell["header"]))
        self.cell = None


def read_html(path, settings):
    with open_text(path) as fh:
        text = fh.read()
    embedded = settings.get("embedded_json")
    if embedded:
        pattern = embedded.get("pattern") if isinstance(embedded, dict) else embedded
        match = re.search(pattern, text, re.DOTALL)
        if match is None:
            raise VerificationError("embedded_json pattern '{}' not found".format(pattern))
        json_settings = dict(settings)
        json_settings["compressed"] = embedded.get("compressed", "auto") if isinstance(embedded, dict) else "auto"
        columns, rows = read_json(path, json_settings, text=match.group(1) if match.groups() else match.group(0))
        if "key" in json_settings and "key" not in settings:
            settings["key"] = json_settings["key"]
        return columns, rows
    parser = _TableParser()
    parser.feed(text)
    parser.close()
    selector = settings.get("table", 0)
    if isinstance(selector, int) and not isinstance(selector, bool):
        if selector >= len(parser.tables):
            raise VerificationError("table index {} not found, the file has {} tables".format(selector, len(parser.tables)))
        table = parser.tables[selector]
    else:
        tables = [t for t in parser.tables if t["id"] == selector]
        if not tables:
            raise VerificationError("table with id '{}' not found, ids: {}".format(
                selector, ", ".join(str(t["id"]) for t in parser.tables)))
        table = tables[0]
    rows = [r for r in table["rows"] if r]
    header = settings.get("header", "auto")
    columns = None
    if rows and (header is True or (header == "auto" and all(is_header for _, is_header in rows[0]))):
        columns = [text for text, _ in rows[0]]
        rows = rows[1:]
    if columns is None:
        columns = [str(i) for i in range(max([len(r) for r in rows] or [0]))]
    records = [OrderedDict((columns[i] if i < len(columns) else str(i), text) for i, (text, _) in enumerate(r)) for r in rows]
    return columns, records


def read_table(path, settings):
    """
    Read a table as (columns, rows) where rows are dicts column -> text. Column ids are strings; files without
    header get the ids '0', '1', ...
    """
    source = table_source(path, settings)
    if source == "json":
        return read_json(path, settings)
    if source == "html":
        return read_html(path, settings)
    return read_delimited(path, settings)


def _key_function(key_columns):
    if not key_columns:
        return None
    key_columns = [column_id(k) for k in (key_columns if isinstance(key_columns, list) else [key_columns])]

    def key(row):
        return tuple(row.get(k, "") for k in key_columns)
    return key, key_columns


def compare_table(reference, candidate, settings=None, max_differences=100):
    """
    Compare two tables.

    Settings for reading: source (delimited, json or html; default from the extension), sep (default tab, or
    'whitespace'), header (default true), comment, skip_until, stop_at, ignore_lines, replace, rows (number of
    data rows to read), records and compressed (json), table, embedded_json (html).

    Settings for comparing:
      - key: list of columns identifying a row; without key rows are compared by position
      - columns: columns to compare with tolerances; default: all columns, exact
      - ignore_columns: columns that are not compared

    :return: result dict, see the verification documentation
    """
    settings = dict(settings or {})
    result = Result("table", reference, candidate, settings, max_differences)

    def run():
        if not check_files(result, reference, candidate):
            return
        tables = []
        for path in (reference, candidate):
            read_settings = dict(settings)
            columns, rows = read_table(path, read_settings)
            if settings.get("rows") is not None:
                rows = rows[:int(settings["rows"])]
            tables.append((columns, rows, read_settings))
        key_setting = settings.get("key", tables[0][2].get("key"))
        ref_columns, cand_columns = tables[0][0], tables[1][0]
        if [c for c in ref_columns if c not in cand_columns] or [c for c in cand_columns if c not in ref_columns]:
            result.message("columns differ: only in reference: [{}], only in candidate: [{}]".format(
                ", ".join(c for c in ref_columns if c not in cand_columns),
                ", ".join(c for c in cand_columns if c not in ref_columns)))
        key_function = _key_function(key_setting)
        if key_function is not None:
            for column in key_function[1]:
                for label, columns in (("reference", ref_columns), ("candidate", cand_columns)):
                    if column not in columns:
                        raise VerificationError("key column '{}' not found in the {} table".format(column, label))
        compared = parse_columns(settings.get("columns")) if settings.get("columns") is not None else None
        ignore = set(column_id(c) for c in settings.get("ignore_columns") or [])
        if key_function is not None:
            ignore.update(key_function[1])
        if compared is None:
            all_columns = ref_columns + [c for c in cand_columns if c not in ref_columns]
            compared = OrderedDict((c, parse_columns([c])[c]) for c in all_columns)
        compared = OrderedDict((c, t) for c, t in compared.items() if c not in ignore)
        records = []
        for columns, rows, _ in tables:
            if key_function is None:
                records.append([(("row {}".format(i + 1),), row) for i, row in enumerate(rows)])
            else:
                records.append([(key_function[0](row), row) for row in rows])
        compare_records(result, records[0], records[1], compared, format_key=lambda key: " | ".join(key))

    return run_comparison(result, run)
