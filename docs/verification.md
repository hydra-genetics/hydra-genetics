# Verification utilities

`hydra_genetics.utils.verification` compares result files from two versions of a pipeline (a *reference* and a
*candidate*), checks known (true positive) variants and summarises everything in a report that can be reviewed
and signed. It is used by the [verification module](https://github.com/hydra-genetics/verification), but the
functions can also be called directly.

`hydra_genetics.utils.vcf_filter` holds the VCF filter expression engine of the
[filtering module](https://github.com/hydra-genetics/filtering), so that other modules can reuse it.

## Comparators

Every comparator takes `(reference, candidate, settings=None, max_differences=100)` (`compare_bam` also takes
`threads`) and returns a dict that can be written as JSON:

| Key | Content |
|---|---|
| `kind` | `comparison` |
| `comparator` | `vcf`, `bam`, `table` or `text` |
| `status` | `identical`, `within_tolerance`, `different`, `missing` (a file does not exist) or `error` (the data could not be compared, see `messages`) |
| `counts` | numbers of records, matched, identical, within tolerance, different and only in one file |
| `differences` | the first `max_differences` differences: `key`, `type`, `column`, `reference`, `candidate`, `status` |
| `differences_total`, `truncated` | total number of differences and whether the list was cut |
| `messages` | notes such as fields missing from a header |
| `settings` | the settings used |

`compare_file` chooses the comparator from the setting `type` (`vcf`, `bam`, `cram`, `table`, `json`, `html`,
`text`) or from the file extension.

### Tolerances

Columns are given as a list of single key dicts, `[{chrom: =}, {AF: 0.01}]`:

| Tolerance | Meaning |
|---|---|
| `=`, empty, `exact` | the text must be identical |
| a number | absolute numeric tolerance, e.g. `0.01` |
| `N%` | relative numeric tolerance |
| `unordered` | lists separated by `,`, `&`, `|` or `;` may be in any order |
| `ignore` | not compared |

A bare `=` is not valid YAML for `yaml.safe_load`; load spec files with `load_yaml` (or `SpecLoader`), or quote it.

### VCF (`compare_vcf`)

Records are matched on chrom, pos, ref and alt. Settings:

- `columns`: fixed columns (`chrom`, `pos`, `id`, `ref`, `alt`, `qual`, `filter`) and lists under `FORMAT:`,
  `INFO:` and `VEP:` (first transcript of CSQ); default every field, exact.
- `filter`: a hydra filter expression; variants for which it is true are removed from both files. Fields with
  several values need an index, e.g. `FORMAT:AF:0 < 0.011`.
- `sample` (index or name) or `sample_name_regex`: the sample used for FORMAT fields.
- `header`: also compare `##` header lines; dates, command lines, paths and versions are ignored, plus
  `header_ignore` regexes.

### BAM (`compare_bam`)

Records are compared as SAM text, streamed with pysam. Settings: `sort` (order independent comparison, e.g.
for STAR output), `tags` (compare optional tags, default true), `header` (compare header lines except `@PG`
and `@CO`), `reference_fasta` (for CRAM).

### Tables (`compare_table`)

Reading: `source` (`delimited`, `json`, `html`; default from the extension), `sep` (default tab, or
`whitespace`), `header` (default true; without header columns are `0`, `1`, ...), `comment`, `skip_until`,
`stop_at`, `ignore_lines`, `replace`, `rows`.
JSON: `records`, a path such as `[*].callers[*].segments` (scalar fields of the objects on the way are added as
`<list name>.<field>`, `root.<field>` for a top level list), otherwise the document is flattened to `path`/`value`
rows; base64 encoded gzip data is decoded automatically. HTML: `table` (index or id) or
`embedded_json: {pattern: <regex with one group>}` plus `records`.
Comparing: `key` (columns identifying a row, otherwise rows are compared in order), `columns` (only these
columns are compared, with tolerances), `ignore_columns`.

### Text (`compare_text`)

Line by line comparison after `skip_until`, `stop_at`, `ignore_lines`, `replace` (`[regex, replacement]` pairs)
and optionally `sort`.

## Known variants (`check_known_variants`)

`check_known_variants(expectations, files)` takes a list of expectations and a dict of files
(`{name: {path, comparator, settings}}`). An expectation names a `file` and either

- `variant: {chrom, pos, ref, alt}` plus an optional `expression` that must be true for that record (VCF), or
- `match: {column: value or {regex: ...}}` plus `expect: {column: {min, max, equals, regex}}` (tables).

The status is `found`, `not_found`, `failed_expectation`, `not_checked` (file missing) or `error`.

## Report

`summarise_results(results, metadata)` combines result dicts or JSON files; the verdict is `passed` when every
comparison is identical or within tolerance and every known variant is found, otherwise `review_required`.
`write_summary_tsv` writes one row per check and `render_report(summary, template, css_files, output)` renders
a jinja2 template with autoescaping.
