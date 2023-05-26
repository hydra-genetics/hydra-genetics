# coding: utf-8

import click
import hashlib
import json
import logging
import os
import pathlib
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
def validate(config_file, validation_file, path_to_ref_data):
    def is_file(possible_file):
        '''
            Function used to make sure that the provided argument is a file.

            Parameters:
                possible_file (string): path for file

            Returns:
                bool: if file has been found
        '''
        if not isinstance(possible_file, str):
            return False
        
        extension = pathlib.Path(possible_file)
        # docker container aren't files
        if ":" in possible_file:
            return False
        # Skip files that are configured per analysis/site
        if possible_file.endswith("samples.tsv") \
           or possible_file.endswith("resources.tsv") \
           or possible_file.endswith("units.tsv"):
            logging.debug(f"Ignore: {possible_file}")
            return False
        # If a extension can be found we consider it as a file
        if extension.suffix:
            return True
        else:
            return False

    def locate_possible_files_in_config(config_data, files=[]):
        '''
            function used to extract files from provided config

            Parameters:
                config_data (dict): loaded configuration
                file_list (list): list used to store found files

            Returns:
                files (list): all files found in the config dict
        '''
        for config in config_data:
            if isinstance(config_data[config], dict):
                files = locate_possible_files_in_config(config_data[config], files)
            else:
                possible_file = config_data[config]
                if is_file(possible_file):
                    files.append(possible_file)
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
    possible_files = locate_possible_files_in_config(config_data)

    # List of files that haven't been validated and counters for success and failures
    possible_files, files_not_in_config, counter_pass, counter_fail = validate_reference_data(validation_data,
                                                                                              path_to_ref_data,
                                                                                              possible_files)

    logging.info(f"Files pass: {counter_pass}, fail: {counter_fail}")
    if len(possible_files) > 0:
        logging.warning(f"Found more possible files in config ({', '.join(possible_files)}) that haven't been validated!")

    if len(files_not_in_config) > 0:
        logging.warning("The following files in provided validation files couldn't"
                        f" be located in the provided config: ({', '.join(files_not_in_config)})")

    if counter_fail > 0:
        exit(1)


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
        os.mkdir(output_dir)

    fetched_list, failed_list, skipped_list, files_fetched, files_failed, files_skipped = fetch_reference_data(validation_data,
                                                                                                               output_dir,
                                                                                                               force=force)

    if files_failed > 0:
        logging.error(f"Failed to retrieve {files_failed}")
        logging.error(f"Failed: {', '.join(failed_list)}")

    if files_skipped > 0:
        logging.info(f"Skipped {files_skipped} since checksum didn't change")
        logging.debug(f"Skipped: {', '.join(skipped_list)}")

    if files_fetched > 0:
        logging.info(f"Fetched {files_fetched} files")
        logging.debug(f"Retrieved: {', '.join(fetched_list)}")
