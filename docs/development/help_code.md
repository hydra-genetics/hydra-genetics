In addition to the command line tools used to create new pipelines and rules, there is also a collection of functions that can be used in a pipeline. These functions include version checking of Hydra-Genetics, helper functions for module importation, and more

# Version handling
## version checking
To make sure that a hydra-genetics library of a suitable version is installed one can use min_version and
max_version.

**Code**
```python
from hydra_genetics import min_version as hydra_min_version
# Make sure that hydra-genetics 1.10.0 or newer is installed
hydra_min_version("1.10.0")

from hydra_genetics import max_version as hydra_max_version
# Make sure that installed version of hydra-genetics is 1.10.0 or older
hydra_max_version("1.12.0")
```
## version logging

### Pipeline version
To log the used version of the pipeline, one can utilize `get_pipeline_version` which will 
locate the path of the Snakefile and uses git to fetch the checkout tag/branch and commit ID.
`export_pipeline_version_as_file` can later be used to print the information as a file.

**Code**
```python
from hydra_genetics.utils.software_versions import export_pipeline_version_as_file
from hydra_genetics.utils.software_versions import get_pipeline_version

# default value for pipeline_name is 'pipeline'
pipeline_version = get_pipeline_version(workflow, pipeline_name="Twist_Solid")

# pipeline_version
{
    "Twist_Solid": {
        'version': 'v1.0.0',
        'commit': 'ac739ca938c'
    }
}

# Additional variables that can be set
# - directory, defualt value software_versions
# - file_name_ending, default value mqv_versions.yaml
# date_string, a string that will be added to the folder name to make it unique (preferably a timestamp)
export_pipeline_version_as_file(pipeline_version, date_string=date_string)
```

**Folder/file structure**

Example:

```bash
software_versions__20210403--14-00-21/
|--Twist_Solid_mqv_versions.yaml

```


### Tool version
To log the versions of the software used during the analysis of the samples, multiple functions exist to help with this task.

**Code**
```python
from hydra_genetics.utils.misc import export_config_as_file
from hydra_genetics.utils.software_versions import export_pipeline_version_as_file
from hydra_genetics.utils.software_versions import get_pipeline_version
from hydra_genetics.utils.software_versions import add_software_version_to_config
from hydra_genetics.utils.software_versions import export_software_version_as_files

# Use onstart to make sure that containers have been downloaded
# before extracting versions
onstart:
    # Make sure that the user have requested containers to be used
    if use_container(workflow):
        date_string = datetime.now().strftime('%Y%m%d--%H-%M-%S')
        # From the config retrieve all dockers used and parse labels for software versions. Add
        # this information to config dict.
        update_config, software_info = add_software_version_to_config(config, workflow, False)
        # Print all softwares used as files. Additional parameters that can be set
        # - directory, defualt value software_versions
        # - file_name_ending, default value mqv_versions.yaml
        # date_string, a string that will be added to the folder name to make it unique (preferably a timestamp)
        export_software_version_as_files(software_info, date_string=date_string)
        
        # print config dict as a file. Additional parameters that can be set
        # output_file, default config
        # output_directory, default =None, i.e no folder
        # date_string, a string that will be added to the folder name to make it unique (preferably a timestamp)
        export_config_as_file(update_config, date_string=date_string)
```


**Folder and file structure**

Example output

```bash
# Config file
config__20210403--14-00-21.yaml
# Softwares
software_versions__20210403--14-00-21
|--bwa_mem__0.7.17_mqv_versions.yaml
|--CONTAINERNAME__VERSION_mqv_versions.yaml
```

# Variable usage in config
Modifying paths for all reference and design files in the configuration can be time-consuming and may result in long strings, making it challenging to read the configuration file. To simplify this process, one can use the `replace_dict_variable` function. This function allows the definition of variables in the YAML file, providing a more streamlined approach. 

**Code**
```python
from hydra_genetics.utils.misc import replace_dict_variables

config = replace_dict_variables(config)
```

**Config**
```yaml
# Variable
PROJECT_DESIGN_DATA: "/PATH_TO_DESIGN_DATA"
PROJECT_REF_DATA: "/PATH_TO_REFERENCE_FILES"

# Usage of variable
reference:
  fasta: "{{PROJECT_REF_DATA}}/ref_data/hg19.with.mt.fasta"
  design_bed: "{{PROJECT_DESIGN_DATA}}/design/panel_design.bed"
```

**Example**
The function will look for `{{VARIABLE_NAME}}` and modify the config dict, example:
```python
{
    'PROJECT_REF_DATA': '/data/cluster',
    'reference': {
        'fasta': '{{PROJECT_REF_DATA}}/ref_data//hg19.with.mt.fasta',
    },
}
```
to 
```python
{
    'PROJECT_REF_DATA': '/data/cluster',
    'reference': {
        'fasta': '/data/cluster/ref_data//hg19.with.mt.fasta',
    },
}
```

# Load resources
For Hydra-Genetics modules and pipelines, resource definitions are stored in a YAML file (`resource.yaml`). These settings need to be added to the config dictionary, and this can be achieved using the `load_resources` function.
**Code**
```python
from hydra_genetics.utils.resources import load_resources

# config["resources"] points to the location of resources.yaml
config = load_resources(config, config["resources"])
```

# Import modules
Snakemake supports the import of modules stored both locally and remotely. The existence of `get_module_snakefile` simplifies this process, making it easy to switch between locally and remotely stored modules. By default, the behavior is set to fetch modules from https://github.com. This default behavior can be changed by setting the variable `hydra_local_path` in the configuration file or adding it as a key to the configuration dictionary.

**Folder structure**
```bash
LOCAL_PATH_WHERE_MODULES_HAVE_BEEN_STORED
|--prealignment
|  |--workflow
|  |  |--Snakefile
|--alignment
|  |--workflow
|  |  |--Snakefile
|--snv_indels
|  |--workflow
|  |  |--Snakefile

```

**Config**
```yaml
hydra_local_path: "/LOCAL_PATH_WHERE_MODULES_HAVE_BEEN_STORED"
```

**Code**
```python
from hydra_genetics.utils.misc import get_module_snakefile

module prealignment:
    snakefile:
        get_module_snakefile(config, "hydra-genetics/prealignment", path="workflow/Snakefile", tag="v1.0.0")
    config:
        config
```

