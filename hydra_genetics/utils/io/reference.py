import hashlib
import logging
import os
import requests


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
            file_path = os.path.join(output_dir, validation_data[k]['path'])
            url = validation_data[k]['url']
            fetch_file = False
            if force and os.path.isfile(file_path):
                logging.debug(f"Overwriting {file_path}")
                fetch_file = True
            elif not os.path.isfile(file_path):
                fetch_file = True
                logging.debug(f"Fetching new file {file_path}")
            elif os.path.isfile(file_path):
                calculated_md5 = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                if not calculated_md5 == validation_data[k]['checksum']:
                    fetch_file = True

            if fetch_file:
                # Fetch and create parent directories
                parent_dir = os.path.dirname(file_path)
                if not os.path.exists(parent_dir):
                    os.mkdir(parent_dir)
                r = requests.get(url, allow_redirects=True)

                open(file_path, 'wb').write(r.content)

                # Make sure that the file was correctly downloaded
                calculated_md5 = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                if not calculated_md5 == validation_data[k]['checksum']:
                    failed.append(file_path)
                    files_failed += 1
                    logging.error(f"Failed to download file {url} to {file_path}, checksum didn't match, "
                                  f"got {calculated_md5}, expected {validation_data[k]['checksum']}")
                else:
                    logging.info(f"Retrieved: {url} to {file_path}")
                    fetched.append(file_path)
                    files_fetched += 1
            else:
                # Skip file if it exist, the checksum hasn't changed and force hasn't been used
                files_skipped += 1
                skipped.append(file_path)
                logging.debug(f"Skipping {file_path}, checksum matched")
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


def validate_reference_data(validation_data, path_to_ref_data,
                            file_list=[], not_found_in_config=[],
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
    for k in validation_data:
        # A validation entry
        if "path" in validation_data[k]:
            file_path = os.path.join(path_to_ref_data, validation_data[k]['path'])

            if not os.path.exists(file_path):
                counter_fail += 1
                logging.error(f"Could not locate: {file_path}")
            else:
                calculated_md5 = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                if not calculated_md5 == validation_data[k]['checksum']:

                    counter_fail += 1
                    logging.error(f"Incorrect checksum for {file_path}, expected"
                                  f" {validation_data[k]['checksum']}, got {calculated_md5}")
                else:
                    counter_pass += 1
                    logging.info(f"PASS: {file_path}")

                if validation_data[k]['path'] in file_list:
                    file_list.remove(validation_data[k]['path'])
                else:
                    not_found_in_config.append(validation_data[k]['path'])
        else:
            # Nested entry, recursively process content
            (file_list, not_found_in_config,
             counter_pass, counter_fail) = validate_reference_data(validation_data[k],
                                                                   path_to_ref_data,
                                                                   file_list, not_found_in_config,
                                                                   counter_pass, counter_fail)
    return file_list, not_found_in_config, counter_pass, counter_fail
