import gzip
import hashlib
import logging
import os
import requests
import shutil
import tarfile
import tempfile
from urllib.request import urlretrieve

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
                         fetched=[], links=[], failed=[], skipped=[],
                         force=False):
    '''
        Function used to validate entries found in validation files

        Parameters:
            validation_data (dict):
            output_dir (str): path to where data will be stored
            fetched (list): list with files that have been retrieved.
            links (list): list with links that have been retrieved.
            failed (list): list with files that couldn't correctly be retrieved
            skipped (list): list with files that weren't retrieved, checksum haven't changed

        Returns:
            (list, list, list, list): (fetched files, linked files, failed files, skipped files)
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
                logging.info(f"updating {content_path}")
                with tempfile.TemporaryDirectory() as tmpdirname:
                    temp_content_holder = os.path.join(tmpdirname, "tempfile")

                    # Fetch content and merge any split files
                    fetch_url_content(value['url'], temp_content_holder, tmpdirname)

                    checksum_value = value['compressed_checksum'] if 'compressed_checksum' in value else value['checksum']

                    if not checksum_validate_file(temp_content_holder, checksum_value, content_path):
                        failed.append(content_path)
                    else:
                        if 'folder' in content_type and os.path.isdir(content_path):
                            shutil.rmtree(content_path)
                        if 'compressed_checksum' in value:
                            if extract_compressed_data(value, content_type, content_path, temp_content_holder, force):
                                logging.info(f"folder {content_path} retrieved")
                                fetched.append(value['path'])
                            else:
                                failed.append(content_path)
                        else:
                            logging.info(f"file {content_path} retrieved")
                            fetched.append(value['path'])
                            move_content(temp_content_holder, content_path)
            else:
                logging.debug(f"skipped {content_path}")
                skipped.append(content_path)

            if 'link' in value:
                link_path = os.path.join(output_dir, value['link'])

                if not os.path.lexists(link_path):
                    logging.info(f"Creating link: {link_path}")
                    content_path = os.path.abspath(os.path.join(output_dir, value['path']))
                    links.append(link_path)
                    link_path = os.path.abspath(link_path)
                    if not os.path.isdir(os.path.dirname(link_path)):
                        os.mkdir(os.path.dirname(link_path))
                    relpath = os.path.relpath(os.path.dirname(content_path), os.path.dirname(link_path))
                    if relpath == ".":
                        content_path = os.path.basename(content_path)
                    elif relpath == "..":
                        content_path = os.path.join(relpath, os.path.basename(content_path))
                    else:
                        content_path = os.path.join(output_dir, value['path'])
                    os.symlink(content_path, link_path)
                else:
                    logging.info(f"link already exist: {link_path}")
        else:
            # Nested entry, recursively process content
            fetched, links, failed, skipped = fetch_reference_data(validation_data[k],
                                                                   output_dir,
                                                                   fetched,
                                                                   links,
                                                                   failed,
                                                                   skipped,
                                                                   force)
    return fetched, links, failed, skipped


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
            urlretrieve(part_url, temp_file)
            if not checksum_validate_file(temp_file, part_checksum):
                logging.info(f"Failed to retrieved part {counter}: {part_url}, expected {calculated_md5}, got {part_checksum}")
                return False
            else:
                logging.debug(f"Retrieved part {counter}: {part_url}")
            counter += 1
        with open(content_holder, 'wb') as writer:
            logging.debug(f"Merge {list_of_temp_files} into {content_holder}")
            for temp_content in list_of_temp_files:
                with open(temp_content, 'rb') as reader:
                    for line in reader:
                        writer.write(line)
    else:
        urlretrieve(url, content_holder)


def validate_reference_data(validation_data, path_to_ref_data,
                            file_list=[], not_found_in_config=[], found=[],
                            pass_list=[], link_list=[], failed_list=[]):
    '''
        Validate all entries in the validation dict

        Parameters:
            validation_data (dict): load json/yaml file in dict format
                                    ex {key: {key_s1: {path: value}, key_s2: {path: value}, k2: {path: value}}
            path_to_ref_data (str): path to where data is stored
            file_list (list): list with files in config file
            not_found_in_config (list): files in loaded validation that couldn't be found in the configuration file
            pass_list (list): files/folders passed validation
            linked_list (list): defined and existing links
            failed_list (list): files/folders failed validation

        Returns:
            (list, list, list, list, list,):
                list with files that haven't been validated,
                reference files not found in config,
                files found and defined in config,
                files passed validation,
                links defined and existing
                files failed validation
    '''
    def track_files(path, file_list=[], not_found_in_config=[], found=[]):
        if path in found:
            pass
        else:
            file_found = []
            for f in file_list:
                if f.endswith(path) or f == path:
                    file_found.append(f)
                    break
                elif path in f:
                    file_found.append(f)
            if file_found:
                for f in file_found:
                    file_list.remove(f)
                found.append(path)
            else:
                for f in found:
                    if f.endswith(f) or f in path:
                        return file_list, not_found_in_config, found
                if path not in found:
                    not_found_in_config.append(path)
        return file_list, not_found_in_config, found

    def valid_link(output_dir, item):
        if 'link' in item:
            link_path = os.path.join(path_to_ref_data, item['link'])
            if not os.path.lexists(link_path):
                logging.info(f"Missing link: {link_path}")
                return False
        return True

    for k, item in validation_data.items():
        # A validation entry
        if "path" in item:
            file_path = os.path.join(path_to_ref_data, item['path'])
            if not os.path.exists(file_path):
                logging.error(f"Could not locate: {file_path}")
                failed_list.append(item['path'])
                file_list, not_found_in_config, found = track_files(item['path'], file_list, not_found_in_config, found)
            else:
                if 'checksum' not in item and "content_checksum" not in item:
                    if not valid_link(path_to_ref_data, item):
                        failed_list.append(item['path'])
                    else:
                        if 'link' in item:
                            link_list.append(item['link'])
                        pass_list.append(item['path'])
                        logging.debug(f"{item['path']} found, no checksum validation!")
                elif "content_checksum" in item:
                    logging.debug(f"Folder found: {item['path']}")
                    _, failed, not_found = checksum_validate_content(item['content_checksum'], file_path)
                    if not failed and not not_found:
                        pass_list.append(item['path'])
                    else:
                        failed_list.append(item['path'])
                else:
                    if checksum_validate_file(file_path, validation_data[k]['checksum']) and valid_link(path_to_ref_data, item):
                        if 'link' in item:
                            link_list.append(item['link'])
                        pass_list.append(item['path'])
                    else:
                        failed_list.append(item['path'])
                file_list, not_found_in_config, found = track_files(item['path'], file_list, not_found_in_config, found)
        else:
            # Nested entry, recursively process content
            (file_list, not_found_in_config, found,
             pass_list, link_list, failed_list) = validate_reference_data(validation_data[k],
                                                                          path_to_ref_data,
                                                                          file_list, not_found_in_config,
                                                                          found, pass_list, link_list, failed_list)
    return file_list, not_found_in_config, found, pass_list, link_list, failed_list


def update_needed_for_entry(item, parent_dir="./"):
    """
        Checks if entry needs to be update, i.e checksum has change or the file/folder doesn't exist

        Patameters:
            item (dict): see top part of this page
            parent_dir (string): path to where content will be saved

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
            _, failed, not_found = checksum_validate_content(item['content_checksum'], content_path)
            if failed or not_found:
                return True
            else:
                return False
        else:
            logging.debug(f"{content_path} not validation done")


def checksum_validate_content(file_checksums, parent_dir=None, print_path_name=None, ) -> (int, int, int):
    """
        Used to validate content of a folders using a dict with path:md5sum values.

        Parameters:
            file_checksum (dict): dict with the following format {file_path: md5sum_value, }
            parent_dir (string): path to where the file is located
            print_path_name (string): when storing a file/folder using a temporary name this makes it possible to
                                      print a more human readable string.

        Returns:
            (int, int, int): file that passed checksum validation, files that failed checksum validation, files not found
    """
    passed = 0
    failed = 0
    not_found = 0
    failed_files = []
    files_not_found = []
    for file, checksum in file_checksums.items():
        full_file_path = os.path.join(parent_dir if parent_dir is not None else "./", file)
        if os.path.isfile(full_file_path):
            if checksum_validate_file(
                os.path.join(full_file_path),
                checksum,
                file
            ):
                passed += 1
            else:
                failed_files.append(file)
                failed += 1
        else:
            logging.debug(f"{full_file_path} not found")
            files_not_found.append(file)
            not_found += 1
    logging.debug(f"folder content validation, valid: {passed}, invalid {failed}, missing {not_found}")
    logging.debug(f"failed files: {failed_files}")
    logging.debug(f"failed files: {files_not_found}")
    return passed, failed, not_found


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
    m = hashlib.md5()
    with open(file, 'rb') as fp:
        for chunk in fp:
            m.update(chunk)
    calculated_md5 = m.hexdigest()
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
