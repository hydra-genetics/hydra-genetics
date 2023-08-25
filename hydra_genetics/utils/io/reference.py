import gzip
import hashlib
import logging
import os
import requests
import shutil
import tarfile
import tempfile

# Expected input file format
# --------------------------
# rule_name1:
#     variable1:
#        entry
#
# rule_name2:
#     variable2:
#        entry
#
#
# --------------------------
#
# Expected formats for an entry
# A file
# {checksum: md5sum_value, type: file, path: path_to_file, url: url_path}
# Compressed file that will be extracted
# {checksum: md5sum_value, compressed_checksum: md5sum_value, type: file, path: path_storage_location, url: url_path}
# Folder (it must be compressed)
# {type: folder, compressed_checksum: md5sum_value, path: folder_storage_location,
#   content_checksum: { file1:md5sum_value, file2:md5sum_value}, url: url_path}
# content_checksum is optional, when it's not set the only validation made is the existence of the folder


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
    for k, value in validation_data.items():
        # If validation entry
        if "path" in value:
            content_path = os.path.join(output_dir, value['path'])
            content_type = value['type']

            # Some entries may not be fetchable and only added for validation
            if 'url' not in value:
                logging.debug(f"Content {content_path} contains no url entry, i.e will not be retrieved!")
                continue

            # Check if content needs to be updated
            update_needed = update_needed_for_entry(value, output_dir)

            if update_needed or force:
                with tempfile.TemporaryDirectory() as tmpdirname:
                    temp_content_holder = os.path.join(tmpdirname, "tempfile")

                    # Fetch content and merge any split files
                    fetch_url_content(value['url'], temp_content_holder, tmpdirname)

                    checksum_value = value['compressed_checksum'] if 'compressed_checksum' in value else value['checksum']

                    if not checksum_validate_file(temp_content_holder, checksum_value, content_path):
                        files_failed += 1
                        failed.append(content_path)
                    else:
                        if 'folder' in content_type and os.path.isdir(content_path):
                            shutil.rmtree(content_path)
                        if 'compressed_checksum' in value:
                            if extract_compressed_data(value, content_type, content_path, temp_content_holder, force):
                                files_fetched += 1
                            else:
                                failed.append(content_path)
                                files_failed += 1
                        else:
                            files_fetched += 1
                            move_content(temp_content_holder, content_path)
            else:
                skipped += content_path
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


def fetch_url_content(url, content_holder, tmpdir) -> None:
    """
        Fetch content from the provided url and make sure that the downloaded file
        has the correct md5 value.

        Parameters:
            url (string): url to file
            content_holder (string): path where the data will be saved
            tmpdir: folder where we can save data temporary


    """
    if isinstance(url, dict):
        counter = 1
        list_of_temp_files = []
        for part_url, part_checksum in url.items():
            temp_file = os.path.join(tmpdir, f"file{counter}")
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
        with open(content_holder, 'wb') as writer:
            for temp_content in list_of_temp_files:
                with open(temp_content, 'rb') as reader:
                    for line in reader:
                        writer.write(line)
    else:
        r = requests.get(url, allow_redirects=True)
        open(content_holder, 'wb').write(r.content)


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
                if 'checksum' not in item and "content_checksum" not in item:
                    counter_pass += 1
                    logging.debug(f"{item['path']} found, no checksum validation!")
                elif "content_checksum" in item:
                    logging.debug(f"Folder found: {item['path']}")
                    _, failed = checksum_validate_content(item['content_checksum'], file_path)
                    if not failed:
                        counter_pass += 1
                    else:
                        counter_fail += 1
                else:
                    if checksum_validate_file(file_path, validation_data[k]['checksum']):
                        counter_pass += 1
                    else:
                        counter_fail += 1
                file_list, not_found_in_config, found = track_files(item['path'], file_list, not_found_in_config, found)
        else:
            # Nested entry, recursively process content
            (file_list, not_found_in_config, found,
             counter_pass, counter_fail) = validate_reference_data(validation_data[k],
                                                                   path_to_ref_data,
                                                                   file_list, not_found_in_config, found,
                                                                   counter_pass, counter_fail)
    return file_list, not_found_in_config, found, counter_pass, counter_fail


def update_needed_for_entry(item):
    """
        Checks if entry needs to be update, i.e checksum has change or the file/folder doesn't exist

        Patameters:
            item (dict): see top part of this page

        Returns:
            bool: if the entry needs to be updated
    """
    if item['path'].startswith("/"):
        content_path = item['path']
    else:
        content_path = os.path.join(parent_dir, item['path'])

    if 'file' in item['type'] and not os.path.isfile(content_path) or \
       'folder' in item['type'] and not os.path.isdir(content_path):
        logging.debug(f"{content_path} not found")
        return True
    else:
        if "checksum" in item:
            return not checksum_validate_file(content_path, item['checksum'])
        elif "content_checksum" in item:
            _, failed = checksum_validate_content(item['content_checksum'], content_path)
            if failed:
                return True
            else:
                return False
        else:
            logging.debug(f"{content_path} not validation done")


def checksum_validate_content(file_checksums, parent_dir=None, print_path_name=None) -> (int, int):
    """
        Used to validate content of a folders using a dict with path:md5sum values.

        Parameters:
            file_checksum (dict): dict with the following format {file_path: md5sum_value, }
            parent_dir (string): path to where the file is located
            print_path_name (string): when storing a file/folder using a temporary name this makes it possible to
                                      print a more human readable string.

        Returns:
            (int, int): file that passed checksum validation followed by files that failed checksum validation
    """
    passed = 0
    failed = 0
    for file, checksum in file_checksums.items():
        if checksum_validate_file(
            os.path.join(parent_dir if parent_dir is not None else "./", file),
            checksum,
            print_path_name
        ):
            passed += 1
        else:
            failed += 1
    logging.debug(f"folder content validation, valid: {passed}, invalid {failed}")
    return passed, failed


def checksum_validate_file(file, expected_checksum, print_path_name=None) -> bool:
    """
        function used to validate checksum.

        Parameters:
            file (str): path to file
            expected_checksum (str): md5sum value
            print_path_name (str): when storing a file/folder using a temporary name this makes it possible to
                                   print a more human readable string.

        Returns
            bool: true passed validation
    """
    calculated_md5 = hashlib.md5(open(file, 'rb').read()).hexdigest()
    print_name = print_path_name if print_path_name is not None else file
    if calculated_md5 == expected_checksum:
        logging.debug(f"{print_name}: valid checksum")
        return True
    else:
        logging.error(f"{print_name}: invalid checksum, got {calculated_md5}, expected {expected_checksum}")
        return False


def extract_compressed_data(item, content_type, content_path, temp_content_holder, force=False) -> bool:
    """
        Function used to extract compressed content, both files and folders.

        Parameters:
            item (dict): a dict with checksum or content_checksum (a dict with path:md5sum values)
            content_path (string): path to where the file or folder will be saved
            temp_content_folder (string): path to where content can be temporary stored

        Returns:
            bool: if extraction was succefull
    """
    extracted_content_path = f"{temp_content_holder}_extracted"
    print(extracted_content_path)
    if "file" in content_type:
        with gzip.open(temp_content_holder, 'rb') as file:
            with open(extracted_content_path, 'wb') as writer:
                for line in file:
                    writer.write(line)
        if checksum_validate_file(extracted_content_path, item['checksum']):
            move_content(extracted_content_path, content_path)
            return True
        else:
            return False
    else:
        with tarfile.open(temp_content_holder, mode="r|gz") as tar:
            tar.extractall(extracted_content_path)
        if 'content_checksum' in item:
            if checksum_validate_content(item['content_checksum'], extracted_content_path, content_path):
                if force and os.path.isdir(content_path):
                    shutil.rmtree(content_path)
                move_content(extracted_content_path, content_path)
                return True
            else:
                return False
        else:
            move_content(extracted_content_path, content_path)
            return True


def move_content(old_path, new_path):
    """
        Helper function that will make sure that all
        parent folders for new path exists.

        Parameters:
            old_path (string): location of data that will be moved
            new_path (string): where the data will be saved
    """
    parent_dir = os.path.dirname(new_path)
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    shutil.move(old_path, new_path)
