import gzip
import hashlib
import logging
import os
import shutil
import tarfile
import tempfile
import requests
import time
import zlib
from requests import HTTPError
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from urllib.parse import urlparse

# Retries of failed requests, done by urllib3: connection errors, timeouts, and the status codes below
RETRY_TOTAL = 5
RETRY_BACKOFF_FACTOR = 2
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
# Attempts to download a file whose connection drops after the response started, which urllib3 does not retry
DOWNLOAD_ATTEMPTS = 3
# tarfile's extraction filters, Python 3.12+ and the 2023 security releases of 3.8-3.11
HAS_DATA_FILTER = hasattr(tarfile, "data_filter")

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
                    try:
                        if not fetch_url_content(value['url'], temp_content_holder, tmpdirname):
                            failed.append(content_path)
                            continue
                    except requests.RequestException as e:
                        logging.error(f"failed to fetch resource at {value['url']}: {e}")
                        failed.append(content_path)
                        continue

                    checksum_value = value['compressed_checksum'] if 'compressed_checksum' in value else value['checksum']

                    if not checksum_validate_file(temp_content_holder, checksum_value, content_path):
                        failed.append(content_path)
                    else:
                        compressed_folder = None
                        if 'folder' in content_type:
                            if 'compressed_checksum' in value and 'content_checksum' in value:
                                parts = list(value['content_checksum'].keys())[0].split(os.sep)
                                if len(parts) > 1:
                                    compressed_folder = parts[0]

                        if 'compressed_checksum' in value:
                            if extract_compressed_data(value, content_type, content_path, temp_content_holder, compressed_folder, force):
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


class InterruptedDownload(Exception):
    """The connection failed while the response body was being downloaded"""


def retrying_session():
    """A requests session that retries connection errors, timeouts and RETRY_STATUS_CODES with exponential backoff"""
    retry = Retry(total=RETRY_TOTAL, backoff_factor=RETRY_BACKOFF_FACTOR, status_forcelist=RETRY_STATUS_CODES,
                  allowed_methods=["GET"], raise_on_status=False)
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_url_content(url, content_holder, tmpdir):
    """
    Fetch content from the provided url and make sure that the downloaded file
    has the correct md5 value.
    """
    def download_with_retry(target_url, target_path):
        with retrying_session() as s:
            for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
                try:
                    return download_once(s, target_url, target_path)
                except InterruptedDownload as e:
                    if attempt == DOWNLOAD_ATTEMPTS:
                        raise e.__cause__
                    wait = RETRY_BACKOFF_FACTOR * 2 ** (attempt - 1)
                    logging.warning(f"download of {target_url} was interrupted ({e.__cause__}), retrying in {wait}s "
                                    f"(attempt {attempt + 1} of {DOWNLOAD_ATTEMPTS})")
                    time.sleep(wait)

    def download_once(s, target_url, target_path):
        for i in range(10):
            r = s.get(target_url, stream=True, allow_redirects=True, timeout=60)
            # A bot challenge (e.g. figshare) can't be passed by a script, retrying won't help
            if "x-amzn-waf-action" in r.headers:
                r.close()
                logging.error(f"{target_url} is blocked by a bot challenge ({r.status_code}), "
                              "download it with a browser and place it at the entry's path")
                return False
            if r.status_code == 202:
                logging.info(f"Server is preparing file (202). Waiting 10s... (Attempt {i+1})")
                r.close()
                time.sleep(10)
                continue
            try:
                r.raise_for_status()
            except HTTPError as e:
                e.status = e.response.status_code
                raise e
            try:
                with open(target_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
            except (requests.exceptions.ChunkedEncodingError, requests.ConnectionError, requests.Timeout) as e:
                # urllib3 only retries until the response starts, a connection dropped while the body
                # streams is retried by download_with_retry
                raise InterruptedDownload() from e
            finally:
                r.close()
            return True
        return False

    def copy_local_file(source_url, target_path):
        local_path = urlparse(source_url).path
        try:
            shutil.copy2(local_path, target_path)
        except OSError as e:
            logging.error(f"failed to copy local file {local_path}: {e}")
            return False
        return True

    if isinstance(url, dict):
        counter = 1
        list_of_temp_files = []
        for part_url, part_checksum in url.items():
            temp_file = os.path.join(tmpdir, f"file{counter}")
            list_of_temp_files.append(temp_file)
            if urlparse(part_url).scheme == "file":
                if not copy_local_file(part_url, temp_file):
                    return False
            elif not download_with_retry(part_url, temp_file):
                return False
            if not checksum_validate_file(temp_file, part_checksum):
                logging.info(f"Failed to retrieved part {counter}: {part_url}, expected {part_checksum}")
                return False
            counter += 1
        with open(content_holder, 'wb') as writer:
            for temp_content in list_of_temp_files:
                with open(temp_content, 'rb') as reader:
                    shutil.copyfileobj(reader, writer)
        return True
    else:
        if urlparse(url).scheme == "file":
            return copy_local_file(url, content_holder)
        return download_with_retry(url, content_holder)


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

        Parameters:
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
            logging.warning(f"{file}: listed in content_checksum but not found in {print_path_name or parent_dir or './'}")
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


def extract_compressed_data(item, content_type, content_path, temp_content_holder, compressed_folder=None, force=False) -> bool:
    """
        Function used to extract compressed content, both files and folders.

        Parameters:
            item (dict): a dict with checksum or content_checksum (a dict with path:md5sum values)
            content_path (string): path to where the file or folder will be saved
            temp_content_folder (string): path to where content can be temporary stored
            compress_folder (string): name of folder that should be moved.

        Returns:
            bool: if extraction was successful
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
        try:
            extract_tar(temp_content_holder, extracted_content_path)
        except (tarfile.TarError, EOFError, OSError, zlib.error) as e:
            # EOFError for a truncated archive, OSError and zlib.error for other broken gzip data
            logging.error(f"failed to extract {content_path}: {e}")
            return False
        if 'content_checksum' in item:
            _, n_failed, n_not_found = checksum_validate_content(item['content_checksum'], extracted_content_path,
                                                                 content_path)
            if not n_failed and not n_not_found:
                if compressed_folder is not None:
                    extracted_content_path = os.path.join(extracted_content_path, compressed_folder)
                    content_path = os.path.join(content_path, compressed_folder)
                move_content(extracted_content_path, content_path)
                return True
            else:
                return False
        else:
            move_content(extracted_content_path, content_path)
            return True


class UnsafeArchiveError(tarfile.TarError):
    """An archive member would be written outside the destination folder, or is a link or a special file"""


def extract_tar(archive, destination):
    """
    Extract a tar.gz archive into destination without writing anything outside of it.

    Only regular files and folders are accepted: links and special files are rejected, also links inside
    destination, since copying the folder into place would follow them. Paths are checked by tarfile's data filter
    when available, otherwise every member is checked first and absolute paths and paths that leave destination are
    rejected. Raises a tarfile.TarError if the archive is unsafe, EOFError or OSError if it can't be read.
    """
    with tarfile.open(archive, mode="r:gz") as tar:
        root = os.path.realpath(destination)
        for member in tar.getmembers():
            if not (member.isfile() or member.isdir()):
                raise UnsafeArchiveError(f"{member.name} is a link or a special file")
            if not HAS_DATA_FILTER:
                path = os.path.realpath(os.path.join(root, member.name))
                if os.path.isabs(member.name) or os.path.commonpath([root, path]) != root:
                    raise UnsafeArchiveError(f"{member.name} would be extracted outside {destination}")
        if HAS_DATA_FILTER:
            tar.extractall(destination, filter="data")
        else:
            tar.extractall(destination)


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
    if os.path.isdir(old_path):
        shutil.copytree(old_path, new_path, dirs_exist_ok=True)
    else:
        shutil.move(old_path, new_path)
