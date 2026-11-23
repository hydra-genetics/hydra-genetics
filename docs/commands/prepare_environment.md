# prepare-environment

`hydra-genetics prepare-environment` gets a pipeline ready to run where containers and reference files have to be local, for example on a cluster without internet access. See [How-to run on a restricted cluster](../packaging_pipeline/prepare_pipeline.md) for the whole procedure.

| Subcommand | What it does |
|---|---|
| [`create-singularity-files`](#create-singularity-files) | Builds a Singularity/Apptainer image for every container in a config |
| [`container-path-update`](#container-path-update) | Points the containers in a config at those local images |
| [`reference-path-update`](#reference-path-update) | Replaces a path prefix everywhere in a config |

## Which config values are containers

`create-singularity-files` and `container-path-update` treat every key named `container` or `default_container` as a container, at any depth in the config:

```yaml
default_container: "docker://hydragenetics/common:1.0.1"   # found

fastp_pe:
  container: "docker://hydragenetics/fastp:0.20.1"         # found

my_module:
  my_rule:
    container: "docker://hydragenetics/bwa:0.7.17"         # found
```

Values that are already local paths (anything without `://`, such as `/data/images/common.sif`) are left alone.

Each image is named after its container, with `/` replaced by `__` and `:` by `_`:

| Container | Image file |
|---|---|
| `docker://hydragenetics/common:1.0.1` | `hydragenetics__common_1.0.1.sif` |
| `docker://hydragenetics/fastp:0.20.1` | `hydragenetics__fastp_0.20.1.sif` |

Two different containers can end up with the same file name, for example `docker://example/tool:1_2` and `docker://example/tool_1:2` both become `example__tool_1_2.sif`. `create-singularity-files` and `container-path-update` check for this and exit with code 1 without building images or writing a config. The check only covers the containers in the config being processed: if several configs share one image folder, a clash between them is not detected.

## create-singularity-files

```bash
hydra-genetics prepare-environment create-singularity-files -c config/config.yaml -o apptainer_cache
```

| Option | Description |
|---|---|
| `-c`, `--configfile` | Pipeline config to read containers from. **Required.** |
| `-o`, `--output-folder` | Folder to store the images in. Created if it doesn't exist. **Required.** |
| `--force` | Rebuild images that already exist in the output folder. |

Runs `singularity build` once for each container in the config. When at least one image has to be built, it needs `singularity` (or Apptainer's `singularity` command) on `PATH` and network access to the container registry; if every image already exists or is local, neither is needed.

* Images that already exist in the output folder are skipped, so the command can be re-run after a failure to build only what is missing. Use `--force` to rebuild them; if a forced rebuild fails, the existing image is kept.
* Each image is built to `<image>.sif.tmp` and only renamed to `<image>.sif` when the build succeeds, so a failed or interrupted build never leaves an image that a later run would skip. A leftover `.tmp` file is removed before the next build.
* If a build fails, the remaining images are still built. The failed containers are listed at the end and the command exits with code 1.

## container-path-update

```bash
hydra-genetics prepare-environment container-path-update -c config/config.yaml -n config/config.local.yaml -p /path/to/apptainer_cache
```

| Option | Description |
|---|---|
| `-c`, `--configfile` | Pipeline config to read. **Required.** |
| `-n`, `--new-configfile` | Where to write the updated config. **Required.** |
| `-p`, `--singularity-cache-path` | Folder holding the images built by `create-singularity-files`. **Required.** |

Writes a copy of the config where each container is replaced by the path to its image in the cache, using the naming shown [above](#which-config-values-are-containers):

```yaml
# before
default_container: "docker://hydragenetics/common:1.0.1"
# after, with -p /path/to/apptainer_cache
default_container: /path/to/apptainer_cache/hydragenetics__common_1.0.1.sif
```

The input config is not changed. The new config is written by a YAML library, so comments and the original formatting are not kept.

## reference-path-update

```bash
hydra-genetics prepare-environment reference-path-update -c config/config.yaml -n config/config.local.yaml \
    --reference-path /data/ref_data:/proj/my_project/design_and_ref_files
```

| Option | Description |
|---|---|
| `-c`, `--configfile` | Pipeline config to read. **Required.** |
| `-n`, `--new-configfile` | Where to write the updated config. **Required.** |
| `--reference-path` | `old_path:new_path`. Every occurrence of `old_path` in a string value of the config is replaced with `new_path`. Can be given several times. **Required.** |

Use it when the reference files have been moved to another folder, for example after unpacking them on a cluster. The value is split on `:`, so neither path can contain a `:`. Strings inside lists are not updated. As with `container-path-update`, the input config is not changed and comments are not kept.

!!! tip
    An alternative to rewriting paths is to put the folder in a variable at the top of the config, such as `REFERENCE_DATA` or `APPTAINER_CACHE`, and refer to it as `{{REFERENCE_DATA}}`. Then only one line has to change. See [Preparing your pipeline](../packaging_pipeline/prepare_pipeline.md).

## Typical order

```bash
# where you have internet access
hydra-genetics references download -v config/references/references.hg19.yaml -o design_and_ref_files
hydra-genetics prepare-environment create-singularity-files -c config/config.yaml -o apptainer_cache

# on the restricted cluster, after copying the files over
hydra-genetics prepare-environment container-path-update -c config/config.yaml -n config/config.local.yaml -p /path/to/apptainer_cache
# only if the config uses absolute reference paths instead of a variable such as {{REFERENCE_DATA}}
hydra-genetics prepare-environment reference-path-update -c config/config.local.yaml -n config/config.local.yaml \
    --reference-path /old/path/to/design_and_ref_files:/path/to/design_and_ref_files
hydra-genetics references validate -c config/config.local.yaml -v config/references/references.hg19.yaml -p /path/to/design_and_ref_files
```
