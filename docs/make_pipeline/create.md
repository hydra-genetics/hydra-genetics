# Create a new pipeline
Using the **hydra-genetics tool** it is very easy to create a new pipeline skeleton following the hydra-genetics standard.
Note, hydra-genetics modules are created in the exact same way.
## Installation
Install hydra-genetics as described in [Installation](../installation.md).
## Make a pipeline skeleton
The hydra-genetics tools will set up a folder structure following the hydra-genetics standard
as well as ready made code testing for github.
```
hydra-genetics create-pipeline -n new_pipeline_name -d "solid cancer" -a "Your Name" -e name@email.com -g git_username [OPTIONS]
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

After creation, push the new pipeline skeleton to git:

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
The `workflow` folder contains the actual pipeline with all the rules, scripts, schemas and so on.
```
├── .git
├── .github
│   ├── CODEOWNERS
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── linters
│   │   ├── .snakefmt.toml
│   │   └── report
│   └── workflows
│       ├── conventional-prs.yml
│       ├── integration.yaml
│       ├── lint.yaml
│       ├── pycodestyle.yaml
│       ├── pytest.yaml
│       ├── release-please.yaml
│       ├── snakefmt.yaml
│       ├── snakemake-dry-run.yaml
│       └── test-build-mkdocs
├── .gitignore
├── .readthedocs.yaml
├── .tests
│   └── integration
│       ├── config
│       │   ├── config.yaml
│       │   └── resources.yaml
│       ├── samples.tsv
│       └── units.tsv
├── LICENSE.md
├── README.md
├── config
│   ├── config.yaml
│   ├── output_files.yaml
│   ├── resources.yaml
│   ├── samples.tsv
│   └── units.tsv
├── docs
│   ├── extra.css
│   ├── includes
│   │   └── abbreviations.md
│   ├── index.md
│   ├── intro.md
│   ├── requirements.txt
│   └── softwares.md
├── images
│   └── hydragenetics.png
├── mkdocs.yaml
├── requirements.test.txt
├── requirements.txt
└── workflow
    ├── Snakefile
    ├── notebooks
    │   └── describe_jupyter_notebook.txt
    ├── rules
    │   └── common.smk
    ├── schemas
    │   ├── config.schema.yaml
    │   ├── output_files.schema.yaml
    │   ├── resources.schema.yaml
    │   ├── rules.schema.yaml
    │   ├── samples.schema.yaml
    │   └── units.schema.yaml
    └── scripts
        ├── dummy.py
        └── test_dummy.py
```
Rule files (`workflow/rules/<tool>.smk`) and environment files (`workflow/envs/`) are added with the `create-rule` command.
