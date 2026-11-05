# How to create sample files
The files `samples.tsv` and `units.tsv` store all sample meta data needed to run pipelines that uses hydra-genetics.
These can be automatically generated from fastq files (Illumina) or unaligned BAM files (PacBio/ONT) with the `create-input-files` command.
## Installation
Install hydra-genetics as described in [Installation](../installation.md).
## Usage
Create `samples.tsv` and `units.tsv` for all fastq files in a specified folder:
```
hydra-genetics create-input-files -d path/to/fastq-files/ -p Illumina
```
## Note
<span style="color:red">**OBS! Sample names cannot include "_" (underscore)!**</span>
## Options
| Option | Explanation |
|--------|-------------|
| -d, --directory TEXT | Path to dir where fastq files should be looked for (Illumina) or to unaligned BAM files (PACBIO/ONT). Several folders can be specified by adding extra -d. [required] |
| -o, --outdir TEXT | Output directory for the generated files (default: current dir) |
| -p, --platform TEXT | Sequence platform that the data originate from, e.g. nextseq, miseq, Illumina. For long read data it needs to be PACBIO or ONT. [required] |
| -t, --sample-type TEXT | Sample type, N\|T\|R, default T |
| -s, --sample-regex TEXT | Regex used to find fastq files and to extract sample from filename. Default '([A-Za-z0-9-]+)_.+\.fastq.gz' |
| -n, --read-number-regex TEXT | Regex used to extract read number from filename (note only number value). Default '_R([12]{1})_' |
| -a, --adapters TEXT | Adapter sequence, comma separated. Default: the Illumina adapters for short read data, none for PACBIO/ONT |
| --post-file-modifier TEXT | Add string to output files |
| -f, --force | Overwrite existing files |
| -b, --default-barcode TEXT | Default barcode value that should be used when the fastq files are missing barcode information in their header, <br/> if not set the tool will fail if barcode can not be extracted |
| --tc FLOAT | Tumor content for all samples. If not provided, no `tumor_content` column will be added to `samples.tsv`. |
| --data-json TEXT | Json file with data that should be added to the samples/units tsv files, see [Adding columns from a JSON file](#adding-columns-from-a-json-file) |
| --data-columns TEXT | Json file specifying which data should be added as columns to the samples/units tsv files, see [Adding columns from a JSON file](#adding-columns-from-a-json-file) |
| --validate | See if fastq contain multiple runs/lanes by comparing first and last read. <br/> Note, will take time since whole file need to be parsed. |
| --ask | Ask user input when inconsistent machine id or flow cell id are found, only asked when --validate is set. |
| --th FLOAT | If occurrences of a consensus base in barcode is below this value a warning will be printed |
| --nreads INTEGER | Number of reads that will be used to generate consensus barcode. |
| --every INTEGER | Select every N reads for validation. |
| --min-file-size INTEGER | Minimum total input file size on disk, in bytes, summed per sample (compressed fastq.gz files for Illumina, BAM files for `--platform PACBIO`/`ONT`) for a sample to be included. Samples below this are left out of `samples.tsv`/`units.tsv` and instead reported in `excluded_samples_mqc.tsv` (see below). Default: disabled. |
| --help | Show help message and exit. |

## Adding columns from a JSON file
`--data-json` and `--data-columns` add per-sample information, for example from a LIMS export, as columns in
`samples.tsv` and `units.tsv`. Both options must be given together.

`--data-json` holds the data. Only its `samples` object is used; it has one entry per sample name:
```json
{
  "samples": {
    "HG002": {"settings": {"sex": "male", "type": "T", "kit": "SPRQ"}},
    "HG003": {"settings": {"sex": "male"}},
    "HG004": {"settings": {"sex": "female", "kit": "SPRQ"}}
  }
}
```

`--data-columns` lists the values to add. Entries under `samples` become columns in `samples.tsv`, entries under
`units` become columns in `units.tsv`:
```json
{
  "samples": ["samples.{SAMPLE}.settings.sex:NA"],
  "units": ["samples.{SAMPLE}.settings.type:N", "samples.{SAMPLE}.settings.kit:NA"]
}
```

Each entry is a path, a `:` and a default value:

- The path starts with `samples.{SAMPLE}.`. These two parts are skipped (`{SAMPLE}` is not replaced), and the rest
  of the path is looked up in the sample's entry in `--data-json`. For example, `samples.{SAMPLE}.settings.kit`
  reads `kit` inside `settings`.
- The last part of the path is the column name, here `kit`.
- The default is used when the sample has no value at that path. The `:` is required, but the default can be
  empty, e.g. `samples.{SAMPLE}.settings.mother:`.

Rules:

- Every sample found in the input files must have an entry under `samples` in `--data-json`.
- `type`, `platform` and `adapter` in the `units` list don't add columns. They replace the values of `-t`, `-p`
  and `-a`. A sample with no value in the JSON gets the default from `--data-columns`, not the command line value.
  Pipelines only accept `N`, `T` or `R` as `type`.
- When `--data-columns` has a `samples` list, `--tc` is ignored. Add `tumor_content` as a column instead.
- Other `units` entries are added after the standard columns.

For long read data (PACBIO/ONT):

- Values are looked up for each BAM file. A sample with several BAM files gets one row per BAM file, each with the
  sample's values.
- `platform` must be the same as `-p`, because every BAM file is checked against `-p`. A different value, from
  the JSON or from the default, stops the command with an error.
- An extra `units` column can't have the name of a column that is read from the BAM files, such as `barcode`,
  `machine` or `bam`.

Running the example above on the PacBio test data in this repository:
```
hydra-genetics create-input-files -d .tests/integration/pacbio_bams -p PACBIO --data-json data.json --data-columns columns.json
```
gives this `samples.tsv`:
```
sample  sex
HG002   male
HG003   male
HG004   female
```
and this `units.tsv` (some columns left out):
```
sample  type  platform  ...  bam                                       kit
HG002   T     PACBIO    ...  .../m84011_220902_175841_s1.hifi_reads.bam  SPRQ
HG003   N     PACBIO    ...  .../m84010_220919_235306_s2.hifi_reads.bam  NA
HG004   N     PACBIO    ...  .../m84010_220919_232145_s1.hifi_reads.bam  SPRQ
```

## Flagging excluded samples in MultiQC
When `--min-file-size` is set, any sample whose input files (fastq.gz for Illumina, BAM for PACBIO/ONT) are
too small to be worth running through the pipeline is left out of `samples.tsv`/`units.tsv` entirely — it
never enters the Snakemake DAG, so there's no risk of some downstream rule crashing on a near-empty BAM/VCF
further down the line.

That sample isn't just silently missing, though: it's written to `excluded_samples_mqc.tsv`
(or `excluded_samples_<post_file_modifier>_mqc.tsv` if `--post-file-modifier` is used), in the file in the
current directory (or wherever your pipeline run looks for input files alongside `samples.tsv`/`units.tsv`).
This file is always written once `--min-file-size` is set, even when nothing was excluded (header only) — so
its presence/absence isn't itself a signal, but its *content* is.

It's formatted as a [MultiQC custom-content](https://docs.seqera.io/multiqc/custom_content) file, detected by
its `_mqc.tsv` suffix — but whether that happens *automatically* depends on how your pipeline invokes MultiQC:

- **Plain `multiqc <directory>` invocations** (or MultiQC's Snakemake wrapper with
  `use_input_files_only: false`, the wrapper's own default): MultiQC recursively scans the given directory and
  will pick up `excluded_samples_mqc.tsv` on its own, no configuration needed, as long as that directory is in
  its search path (typically the same directory you ran `create-input-files` from):
  ```
  multiqc .
  ```

- **hydra-genetics pipelines using the `qc` module's `multiqc`/`multiqc_longread` rules — the common case**:
  these explicitly set `use_input_files_only: true`. With that set, MultiQC is only ever given the literal set
  of files listed in `snakemake.input` (built from `config["multiqc"]["reports"][<report>]["qc_files"]`), not
  a directory to scan — so nothing is auto-detected, no matter the filename suffix. For this file to show up,
  add its path to the relevant report's `qc_files` entry in your pipeline's config *and* make sure it's wired
  as a real Snakemake `input:` to that `multiqc` rule instance (config alone doesn't make Snakemake treat it as
  a dependency) — check your specific pipeline for how that report's rule is defined.

Once it does reach MultiQC, it shows up as its own "Excluded samples" section in the report, listing each
excluded sample, why it was excluded, its observed total size, and the threshold that was in effect — visible
to anyone reviewing the report, without ever causing the pipeline run itself to fail.
