# coding: utf-8

import click
import hashlib
import json
import logging
import os
import pathlib
import re
import requests
import yaml

from hydra_genetics.utils.misc import merge
from hydra_genetics.utils.io.reference import fetch_reference_data, validate_reference_data


@click.group("references", short_help="setup/validate reference files")
def references():
    pass


@references.command(short_help="make sure that all reference file exist and are valid")
@click.option(
    "-c",
    "--config-file",
    prompt="path",
    required=True,
    multiple=True,
    type=str,
    help="config file used by pipeline",
)
@click.option(
    "-v",
    "--validation-file",
    prompt="path",
    required=True,
    multiple=True,
    type=str,
    help="json/yaml file defining required reference files",
)
@click.option(
    "-p",
    "--path-to-ref-data",
    required=False,
    type=str,
    default="",
    help="path to where reference files are stored",
)
@click.option(
    "-s",
    "--skip-regex",
    required=False,
    multiple=True,
    default=[r"config\/\S+\.(json|yaml|yml|tsv|html|hg19)"],
    type=str,
    help="regex for warning skip",
)
def validate(config_file, validation_file, path_to_ref_data, skip_regex):
    def is_file_or_folder(possible_file):
        '''
            Function used to make sure that the provided argument is a file.

            Parameters:
                possible_file (string): path for file

            Returns:
                bool: if file has been found
        '''
        if not isinstance(possible_file, str):
            return False

        if re.match("^[0-9.]+$", possible_file):
            return False

        extension = pathlib.Path(possible_file)
        # docker container aren't files
        if ":" in possible_file or possible_file.endswith(".sif"):
            return False
        # Skip files that are configured per analysis/site
        if possible_file.endswith("samples.tsv") \
           or possible_file.endswith("resources.yaml") \
           or possible_file.endswith("units.tsv") \
           or possible_file.endswith("output_list.yaml") \
           or possible_file.endswith("output_list.json") \
           or possible_file.endswith("snakemake-wrappers"):
            logging.debug(f"Ignore: {possible_file}")
            return False
        # If a extension can be found we consider it as a file
        if extension.suffix:
            # File
            return True
        else:
            if re.search(r"\/([A-Za-z0-9_.-]*)", possible_file):
                # Folder
                return True
            return False

    def locate_possible_files_in_config(config_data, files=[], skip_regex=[]):
        '''
            function used to extract files from provided config

            Parameters:
                config_data (dict): loaded configuration
                file_list (list): list used to store found files

            Returns:
                files (list): all files found in the config dict
        '''
        for config in config_data:
            possible_file = config_data[config]
            if isinstance(possible_file, dict):
                files = locate_possible_files_in_config(possible_file, files, skip_regex)
            else:
                if not isinstance(possible_file, str):
                    continue
                result = re.search(r"(\S+)", possible_file)
                if result:
                    for f in re.findall(r"(\S+)", possible_file):
                        skip_file = False
                        for skip in skip_regex:
                            if re.match(skip, f):
                                skip_file = True
                                break

                        if not skip_file and is_file_or_folder(f):
                            files.append(f)
        return files

    # Load and merge multiple config
    config_data = {}
    for config in config_file:
        # Note that duplicate entries will be replaced with latest data load
        config_data = merge(config_data, yaml.safe_load(open(config)))

    validation_data = {}
    # Load and merge multiple validation files
    for validation in validation_file:
        # Note that duplicate entries will be replaced with latest data load
        if validation.endswith(".json"):
            validation_data = merge(validation_data, json.load(open(validation)))
        elif validation.endswith(".yaml") or validation.endswith(".yml"):
            validation_data = merge(validation_data, yaml.safe_load(open(validation)))
        else:
            raise IOError(f"Unknown file format passed as validation data: {validation}")

    # All files that we should validate, note that all may not be specified in the validation files
    possible_files = [*set(locate_possible_files_in_config(config_data, skip_regex=skip_regex))]

    # List of files that haven't been validated and counters for success and failures
    (possible_files, files_not_in_config, found,
     pass_list, link_list, failed_list) = validate_reference_data(validation_data,
                                                                  path_to_ref_data,
                                                                  possible_files)

    logging.info(f"Files/Folders pass: {len(pass_list)}, links; {len(link_list)}, fail: {len(failed_list)}")
    logging.debug(f"Files/Folders pass: {pass_list}")
    logging.debug(f"links; {link_list}")
    logging.debug(f"fail: {failed_list}")

    if len(possible_files) > 0:
        logging.warning(f"Found more possible files in config ({', '.join(possible_files)}) that haven't been validated!")

    if len(files_not_in_config) > 0:
        logging.warning("The following files in provided validation files couldn't"
                        f" be located in the provided config: ({', '.join(files_not_in_config)})")

    if len(failed_list) > 0:
        print(f"PASS: {len(pass_list)}, FAILED: {len(failed_list)}")
        exit(1)
    else:
        print(f"PASS: {len(pass_list)}")
        print(f"Links PASS: {len(link_list)}")


@references.command(short_help="download reference data, if needed")
@click.option(
    "-v",
    "--validation-file",
    prompt="path",
    required=True,
    multiple=True,
    type=str,
    help="json/yaml file defining required reference files",
)
@click.option(
    "-o",
    "--output-dir",
    required=False,
    type=str,
    default="",
    help="path to where reference files will be stored",
)
@click.option(
    "-f",
    "--force",
    required=False,
    type=bool,
    is_flag=True,
    default=False,
    help="replace files even though they exist (skip checksum validation)",
)
def download(validation_file, output_dir, force):
    validation_data = {}
    # Load and merge multiple validation files
    for validation in validation_file:
        # Note that duplicate entries will be replaced with latest data load
        if validation.endswith(".json"):
            validation_data = merge(validation_data, json.load(open(validation)))
        elif validation.endswith(".yaml") or validation.endswith(".yml"):
            validation_data = merge(validation_data, yaml.safe_load(open(validation)))
        else:
            raise IOError(f"Unknown file format passed as validation data: {validation}")

    # Make sure that output directory exists
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    fetched_list, links_list, failed_list, skipped_list = fetch_reference_data(validation_data,
                                                                               output_dir,
                                                                               force=force)

    if len(failed_list) > 0:
        logging.error(f"Failed to retrieve {len(failed_list)}")
        logging.error(f"Failed: {', '.join(failed_list)}")

    if len(skipped_list) > 0:
        logging.info(f"Skipped {len(skipped_list)} since checksum didn't change")
        logging.debug(f"Skipped: {', '.join(skipped_list)}")

    if len(fetched_list) > 0:
        logging.info(f"Retrieved {len(fetched_list)} files")
        logging.debug(f"Retrieved: {', '.join(fetched_list)}")

    if len(links_list) > 0:
        logging.info(f"Links created: {len(links_list)}")
        logging.debug(f"Links: {', '.join(links_list)}")

    print(f"UPDATED: {len(fetched_list)}")
    print(f"NOT UPDATED: {len(skipped_list)}")

    return 0
