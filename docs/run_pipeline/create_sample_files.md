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
| --help | Show help message and exit. |
