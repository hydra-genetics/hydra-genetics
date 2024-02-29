# Create a new pipeline
Using the **hydra-genetics tool** it is very easy to create a new pipeline skeleton following the hydra-genetics standard.
Note, hydra-genetics modules are created in the exact same way.
## Installation
Activate a python virtual environment. Then install the hydra-genetics tools using pip
```
source venv/bin/activate
pip install hydra_genetics
```
## Make a pipeline skeleton
The hydra-genetics tools will set up a folder structure following the hydra-genetics standard
as well as ready made code testing for github.
```
hydra-genetics create-module -n new_pipeline_name -d "solid cancer" -a "Your Name" -e name@email.com -g git_username [OPTIONS]
```
| Option | Explanation |
|--------|-------------|
| -n, --name TEXT | The name of your new pipeline  [required] |
| -d, --description TEXT | A short description of your pipeline [required] |
| -a, --author TEXT | Name of the main author(s) [required] |
| -e, --email TEXT | E-mail(s) of the main author(s) [required] |
| --version TEXT | The initial version number to use |
| --min-snakemake-version TEXT | Min snakemake version |
| -g, --git-user TEXT | User name of main git user(s) [required] |
| --no-git | Do not create git repo |
| -f, --force | Overwrite output directory if it already exists |
| -o, --outdir TEXT | Output directory for new pipeline (default: pipeline name) |
| --help | Show help text |

After creation, add the push the new pipeline skeleton to git:

```bash
cd new_pipeline_name
git remote add origin git@github.com:git_username/new_pipeline.git
git push --all origin
```
## Folder structure
The folder structure is listed below.
Code testing using github actions is set up in `.github`.
In `.tests` small datasets are run through the pipeline.
The `config` folder holds all configuration files.
In the `workflow` folder contains the actual pipeline with all the rules, scripts, schemas and so on.
```
├── .git
├── .github
│   ├── CODEOWNERS
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── linters
│   │   └── report
│   └── workflows
│       ├── integration.yaml
│       ├── lint.yaml
│       ├── pycodestyle.yaml
│       ├── pytest.yaml
│       ├── snakefmt.yaml
│       └── snakemake-dry-run.yaml
├── .gitignore
├── README.md
├── LICENSE.md
├── requirements.test.txt
├── requirements.txt
├── .tests
│   └── integration
│       ├── config.yaml
│       ├── resources.tsv
│       ├── samples.tsv
│       └── units.tsv
├── config
│   ├── config.yaml
│   ├── resources.tsv
│   ├── samples.tsv
│   └── units.tsv
├── images
│   └── rulegraph.svg
└── workflow
    ├── envs
    │   ├── tool1.yaml
    │   └── tool2.yaml
    ├── notebooks
    │   ├── notebook1.py.ipynb
    │   └── notebook2.r.ipynb
    ├── rules
    │   ├── common.smk
    │   ├── tool1.smk
    │   └── tool2.smk
    ├── schemas
    │   ├── config.schema.yaml
    │   ├── resources.schema.yaml
    │   ├── samples.schema.yaml
    │   └── units.schema.yaml
    ├── scripts
    │   ├── script1.py
    │   ├── script1_test.py
    │   ├── script2.R
    │   └── script2_test.R
    └── Snakefile
```
