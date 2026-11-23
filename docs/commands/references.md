# references

`hydra-genetics references` fetches and checks the design and reference files a pipeline needs. Both subcommands are driven by **validation files**: YAML or JSON files, usually stored under `config/references/`, that list every file with its path, checksum and where to get it. The format is described in [Make reference file configs](../packaging_pipeline/prepare_pipeline.md#make-reference-file-configs).

| Subcommand | What it does |
|---|---|
| [`download`](#download) | Fetches the files listed in validation files and checks their checksums |
| [`validate`](#validate) | Checks that the files a pipeline config points to exist and have the expected checksums |

## Validation file entries

Entries can be nested to any depth, so they can mirror the structure of the pipeline config. An entry is recognised by its `type` key.

| Key | Required | Meaning |
|---|---|---|
| `type` | yes | `file` or `folder` |
| `path` | yes | Where the file or folder is stored, relative to the output/reference folder. This should match the end of the path written in the pipeline config. |
| `url` | no | Where to get it: `https://...`, or `file:/path/on/disk` for a local copy. Entries without `url` are skipped by `download` but still checked by `validate`. |
| `checksum` | for files | md5sum of the file |
| `compressed_checksum` | for archives | md5sum of the downloaded archive; the archive is extracted into `path` |
| `content_checksum` | no | For folders: a mapping of `file: md5sum` for the files inside the extracted folder. Without it, only the existence of the folder is checked. |
| `link` | no | Also create a symlink with this name (relative to the output folder) that points to `path` |

## download

```bash
hydra-genetics references download -v config/references/references.hg19.yaml -v config/references/design_files.hg19.yaml -o design_and_ref_files
```

| Option | Description |
|---|---|
| `-v`, `--validation-file` | Validation file (`.yaml`, `.yml` or `.json`). Can be given several times; later files override earlier ones when entries overlap. **Required.** |
| `-o`, `--output-dir` | Folder to store the files in. Created if it doesn't exist. Defaults to the current folder. |
| `-f`, `--force` | Download again even if a file already exists with a valid checksum. Downloaded files are still checked. |

For each entry the command:

1. skips it if the file or folder already exists with the expected checksum (unless `--force` is given),
2. downloads it from `url` (or copies it, for `file:` URLs), retrying on network errors,
3. checks the checksum and, for archives, extracts them and checks `content_checksum`,
4. creates the `link` symlink if one is defined.

If every entry succeeds, it prints how many files were `UPDATED` and `NOT UPDATED`. If any file could not be fetched or failed its checksum, the failed files are logged and the command exits with code 1 without printing the counts.

## validate

```bash
hydra-genetics references validate \
    -c config/config.yaml -c config/config.data.hg19.yaml \
    -v config/references/references.hg19.yaml -v config/references/design_files.hg19.yaml \
    -p /path/to/design_and_ref_files
```

| Option | Description |
|---|---|
| `-c`, `--config-file` | Pipeline config file. Can be given several times; they are merged, later files overriding earlier ones. **Required.** |
| `-v`, `--validation-file` | Validation file, as for `download`. Can be given several times. **Required.** |
| `-p`, `--path-to-ref-data` | Folder the reference files were downloaded or extracted to (the `-o` folder of `download`). Defaults to the current folder. |
| `-s`, `--skip-regex` | Regex for config values that should not be treated as reference files. Can be given several times. Has a default, shown below; giving `-s` replaces it. |

The default `--skip-regex` skips files under `config/` such as other config, schema and sample files:

```
config\/\S+\.(json|yaml|yml|tsv|html|hg19)
```

The command:

1. collects every value in the config that looks like a file or folder path. Values containing a `:` (such as containers, `docker://...`) or ending in `.sif`, numbers, and per-run files such as `samples.tsv`, `units.tsv`, `resources.yaml` and `output_list.yaml` are ignored, as are values matching `--skip-regex`,
2. matches those paths against the `path` of each validation entry. A config value matches when it ends with the entry's `path`, so values such as `{{REFERENCE_DATA}}/hastings/regions.bed` match an entry with `path: hastings/regions.bed`,
3. checks that each entry exists under `--path-to-ref-data` with the expected checksum, `content_checksum`, and `link`.

Because any value containing a `:` is skipped, a reference path with a `:` in it is never validated.

It prints `PASS` and `FAILED` counts, and exits with code 1 if any entry fails.

Two kinds of warning do **not** make the command fail:

* `Found more possible files in config (...) that haven't been validated!` – a config value looked like a path but no validation entry matched it. This is expected for paths that aren't reference data, for example scripts or output paths. Add an entry to a validation file if the path really is a reference file, or a `--skip-regex` to silence it.
* `The following files in provided validation files couldn't be located in the provided config` – a validation entry isn't used by any of the given config files. Usually the entry belongs to a config file that wasn't passed with `-c`.

Run with `hydra-genetics --debug references validate ...` to list every file that passed, failed or was linked.
