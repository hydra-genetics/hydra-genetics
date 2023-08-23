import gzip
import hashlib
import logging
import os
from pathlib import Path
import requests
import shutil
import tarfile
import tempfile


def fetch_reference_data(validation_data, output_dir,
                         fetched=[], failed=[], skipped=[],
                         files_fetched=0, files_failed=0, files_skipped=0,
                         force=False):
    '''
        Function used to validate entries found in validation files

        Parameters:
            validation_data (dict):
            output_dir (str): path to where data will be stored
            fetched (list): list with files that have been retrieved.
            failed (list): list with files that couldn't correctly be retrieved
            skipped (list): list with files that weren't retrieved, checksum haven't changed
            files_fetched (int): counter variable for files that have been retrieved.
            files_failed (int): counter variable for files that couldn't correctly be retrieved
            files_skipped (int): counter variable for files that weren't retrieved, checksum haven't changed

        Returns:
            (list, list, list, int, int, int): (fetched files, failed files, skipped files,
                                                counter fetched files, counter failed files , counter skipped files)
    '''
    for k in validation_data:
        # If validation entry
        if "path" in validation_data[k]:
            content_path = os.path.join(output_dir, validation_data[k]['path'])
            content_type = validation_data[k]['type']
            md5_validation = False
            if 'url' not in validation_data[k]:
                logging.debug(f"Content {content_path} contains no url entry, i.e will not be retrieved!")
                continue

            url = validation_data[k]['url']

            # Files and folders are handled differently
            # Folder will only be checked if they exist, files will have there checksum validated
            if content_type in ["file", "split_file"]:
                fetch_file = False

                if force and os.path.isfile(content_path):
                    logging.debug(f"Overwriting {content_path}")
                    fetch_file = True
                elif not os.path.isfile(content_path):
                    fetch_file = True
                    logging.debug(f"Fetching new file {content_path}")
                elif os.path.isfile(content_path):
                    md5_validation = hashlib.md5(open(content_path, 'rb').read()).hexdigest() == validation_data[k]['checksum']
                    if not md5_validation:
                        fetch_file = True
                        logging.debug(f"Checksum changed: {url}, {content_path}")
                    else:
                        logging.debug(f"Checksum not changed: {url}, {content_path}")
                else:
                    raise Exception("Unhandled case!!!")

                if md5_validation:
                    # Skip file if it exist, the checksum hasn't changed and force hasn't been used
                    files_skipped += 1
                    skipped.append(content_path)
                    logging.debug(f"Skipping {content_path}, checksum matched")
                elif fetch_file:
                    parent_dir = os.path.dirname(content_path)
                    if not os.path.exists(parent_dir):
                        logging.debug(f"Creating directory {parent_dir}")
                        Path(parent_dir).mkdir(parents=True)
                    with tempfile.TemporaryDirectory() as tmpdirname:
                        temp_content_holder = os.path.join(tmpdirname, "tempfile")

                        fetch_url_content(url, temp_content_holder, tmpdirname)

                        if "compressed_checksum" in validation_data[k]:
                            compressed_content_path = temp_content_holder
                            compressed_checksum = validation_data[k]['compressed_checksum']

                            calculated_md5 = hashlib.md5(open(temp_content_holder, 'rb').read()).hexdigest()
                            if not calculated_md5 == compressed_checksum:
                                files_failed += 1
                                failed.append(content_path)
                                logging.error(f"Failed to download compressed file {url} to {compressed_content_path}, "
                                              "checksum didn't match, "
                                              f"got {calculated_md5}, expected {compressed_checksum}")
                            else:
                                with gzip.open(compressed_content_path, 'rb') as file:
                                    with open(content_path, 'wb') as writer:
                                        for line in file:
                                            writer.write(line)
                        else:
                            shutil.move(temp_content_holder, content_path)

                        # Make sure that the final file was has't changed
                        calculated_md5 = hashlib.md5(open(content_path, 'rb').read()).hexdigest()
                        if not calculated_md5 == validation_data[k]['checksum']:
                            failed.append(content_path)
                            files_failed += 1
                            logging.error(f"Failed to download file {url} to {content_path}, checksum didn't match, "
                                          f"got {calculated_md5}, expected {validation_data[k]['checksum']}")
                        else:
                            logging.info(f"Retrieved: {url} to {content_path}")
                            fetched.append(content_path)
                            files_fetched += 1
            elif content_type in ["folder", "split_folder"]:
                fetch_dir = False
                validation_data[k]['compressed_name']
                compressed_checksum = validation_data[k]['compressed_checksum']
                if os.path.isdir(content_path):
                    if force:
                        logging.info(f"Removing folder: {content_path}")
                        fetch_dir = True
                    else:
                        logging.info(f"Folder found: {content_path}, no validation will be made")
                        fetched.append(content_path)
                        skipped += 1
                else:
                    fetch_dir = True

                if fetch_dir:
                    with tempfile.TemporaryDirectory() as tmpdirname:
                        temp_content_holder = os.path.join(tmpdirname, "tempfile")
                        compressed_content_path = temp_content_holder
                        fetch_url_content(url, temp_content_holder, tmpdirname)

                        calculated_md5 = hashlib.md5(open(compressed_content_path, 'rb').read()).hexdigest()
                        if not calculated_md5 == compressed_checksum:
                            files_failed += 1
                            failed.append(content_path)
                            logging.error(f"Failed to download compressed folder {url} to {compressed_content_path}, "
                                          "checksum didn't match, "
                                          f"got {calculated_md5}, expected {compressed_checksum}")
                        else:
                            with tarfile.open(compressed_content_path, mode="r|gz") as tar:
                                tar.extractall(content_path)
                            fetched.append(content_path)
                            files_fetched += 1
                            logging.info(f"Retrieved: {url} and decompressed it to {content_path}")
            else:
                raise Exception(f"Unhandled content_type: {content_type}")
        else:
            # Nested entry, recursively process content
            fetched, failed, skipped, files_fetched, files_failed, files_skipped = fetch_reference_data(validation_data[k],
                                                                                                        output_dir,
                                                                                                        fetched,
                                                                                                        failed,
                                                                                                        skipped,
                                                                                                        files_fetched,
                                                                                                        files_failed,
                                                                                                        files_skipped,
                                                                                                        force)
    return fetched, failed, skipped, files_fetched, files_failed, files_skipped


def fetch_url_content(url, temp_content_holder, tmpdirname):
    if isinstance(url, dict):
        counter = 1
        list_of_temp_files = []
        for part_url, part_checksum in url.items():
            temp_file = os.path.join(tmpdirname, f"file{counter}")
            list_of_temp_files.append(temp_file)
            r = requests.get(part_url, allow_redirects=True)
            open(temp_file, 'wb').write(r.content)
            calculated_md5 = hashlib.md5(open(temp_file, 'rb').read()).hexdigest()
            if not calculated_md5 == part_checksum:
                logging.info(f"Failed to retrieved part {counter}: {part_url}, expected {calculated_md5}, got {part_checksum}")
                return False
            else:
                logging.info(f"Retrieved part {counter}: {part_url}")
            counter += 1
        with open(temp_content_holder, 'wb') as writer:
            for temp_content in list_of_temp_files:
                with open(temp_content, 'rb') as reader:
                    for line in reader:
                        writer.write(line)
    else:
        r = requests.get(url, allow_redirects=True)
        open(temp_content_holder, 'wb').write(r.content)
    return True


def validate_reference_data(validation_data, path_to_ref_data,
                            file_list=[], not_found_in_config=[], found=[],
                            counter_pass=0, counter_fail=0):
    '''
        Validate all entries in the validation dict

        Parameters:
            validation_data (dict): load json/yaml file in dict format
                                    ex {key: {key_s1: {path: value}, key_s2: {path: value}, k2: {path: value}}
            path_to_ref_data (str): path to where data is stored
            file_list (list): list with files in config file
            not_found_in_config (list): files in loaded validation that couldn't be found in the configuration file
            counter_pass (int): counter variable for files that passed test
            counter_fail (int): counter variable for files that did not pass test

        Returns:
            (list, int, int): list with files that haven't been validated, pass counter, fail counter
    '''
    def track_files(path, file_list=[], not_found_in_config=[], found=[]):
        if path in found:
            pass
        else:
            file_found = ""
            for f in file_list:
                if f.endswith(path) or f == path:
                    file_found = f
                    break
            if file_found:
                file_list.remove(f)
                found.append(path)
            else:
                if path not in found:
                    not_found_in_config.append(path)
        return file_list, not_found_in_config, found

    for k, item in validation_data.items():
        # A validation entry
        if "path" in item:
            file_path = os.path.join(path_to_ref_data, item['path'])
            if not os.path.exists(file_path):
                counter_fail += 1
                logging.error(f"Could not locate: {file_path}")
                file_list, not_found_in_config, found = track_files(item['path'], file_list, not_found_in_config, found)
            else:
                if 'checksum' not in item:
                    counter_pass += 1
                    logging.debug(f"{item['path']} found, no checksum validation!")
                else:
                    calculated_md5 = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                    if not calculated_md5 == item['checksum']:
                        counter_fail += 1
                        logging.error(f"Incorrect checksum for {file_path}, expected"
                                      f" {validation_data[k]['checksum']}, got {calculated_md5}")
                    else:
                        counter_pass += 1
                        logging.info(f"PASS: {file_path}")
                file_list, not_found_in_config, found = track_files(item['path'], file_list, not_found_in_config, found)
        else:
            # Nested entry, recursively process content
            (file_list, not_found_in_config, found,
             counter_pass, counter_fail) = validate_reference_data(validation_data[k],
                                                                   path_to_ref_data,
                                                                   file_list, not_found_in_config, found,
                                                                   counter_pass, counter_fail)
    return file_list, not_found_in_config, found, counter_pass, counter_fail
