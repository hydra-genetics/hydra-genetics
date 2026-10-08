# How to create sample files
The files `samples.tsv` and `units.tsv` store all sample meta data needed to run pipelines that uses hydra-genetics.
These can be automatically generated from the `.fastq`-files by the hydra-genetics help tool.
## Installation
Activate a python virtual environment. Then install the hydra-genetics tools using pip
```
source venv/bin/activate
pip install hydra_genetics
```
## Usage
Create `samples.tsv` and `units.tsv` for all fastq files in a specified folder:
```
hydra-genetics create-input-files -d path/to/fastq-files/
```
## Note
<span style="color:red">**OBS! Sample names cannot include "_" (underscore)!**</span>
## Options
| Option | Explanation |
|--------|-------------|
| -d, --directory TEXT | path to dir where fastq-files should be looked for. Several folders can be specified by adding extra -d. [required] |
| -o, --outdir TEXT | Output directory for where rule will be added (default: current dir) |
| -p, --platform TEXT | Sequence platform that the data originate from, ex nextseq, miseq. Default Illumina |
| -t, --sample-type TEXT | Sample type, N|T|R, default T |
| -s, --sample-regex TEXT | Regex used find fastq files and to extract sample from filename. Default '([A-Za-z0-9-]+)_.+.gz$' |
| -n, --read-number-regex TEXT | Regex used to extract read number from filename (note only number value). Default '_R([1-2]{1})_001' |
| -a, --adapters TEXT | Adapter sequence, comma separated |
| --post-file-modifier TEXT | Add string to output files |
| -f, --force | Overwrite existing files |
| -b, --default-barcode TEXT | Default barcode value that should be used when the fastq files are missing barcode information in their header, <br/> if not set the tool will fail if barcode can not be extracted |
| --tc FLOAT | Tumor content for all samples (default: 1.0) |
| --validate | See if fastq contain multiple runs/lanes by comparing first and last read. <br/> Note, will take time since whole file need to be parsed. |
| --ask | Ask user input when inconsistent machine id or flow cell id are found, only asked when --validate is set. |
| --th FLOAT | If occurences of a concesuns base in barcode is below this value a warning will be printed |
| --nreads INTEGER | Number of reads that will be used to generate consensus barcode. |
| --every INTEGER | Select every N reads for validation. |
| --min-file-size INTEGER | Minimum total compressed fastq.gz size (bytes, summed across all of a sample's fastq files) for a sample to be included. Samples below this are left out of `samples.tsv`/`units.tsv` and instead reported in `excluded_samples_mqc.tsv` (see below). Illumina input only, not supported for `--platform PACBIO`/`ONT`. Default: disabled. |
| --help | Show help message and exit. |

## Flagging excluded samples in MultiQC
When `--min-file-size` is set, any sample whose fastq files are too small to be worth running through the
pipeline is left out of `samples.tsv`/`units.tsv` entirely — it never enters the Snakemake DAG, so there's no
risk of some downstream rule crashing on a near-empty BAM/VCF further down the line.

That sample isn't just silently missing, though: it's written to `excluded_samples_mqc.tsv`
(or `excluded_samples_<post_file_modifier>_mqc.tsv` if `--post-file-modifier` is used), in the file in the
current directory (or wherever your pipeline run looks for input files alongside `samples.tsv`/`units.tsv`).
This file is always written once `--min-file-size` is set, even when nothing was excluded (header only) — so
its presence/absence isn't itself a signal, but its *content* is.

It's formatted as a [MultiQC custom-content](https://docs.seqera.io/multiqc/custom_content) file,
auto-detected by its `_mqc.tsv` suffix — no extra MultiQC configuration is required. Just make sure
MultiQC's search path includes the directory this file was written to (typically the same directory you ran
`create-input-files` from), for example:
```
multiqc . 
```
or, if your pipeline's own MultiQC rule only searches specific result directories, copy/symlink
`excluded_samples_mqc.tsv` into one of them before running MultiQC. It will then show up as its own
"Excluded samples" section in the report, listing each excluded sample, why it was excluded, its observed
total fastq size, and the threshold that was in effect — visible to anyone reviewing the report, without
ever causing the pipeline run itself to fail.
