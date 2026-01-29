"""Modules for zip manager utilities."""

import json
import logging
import os
import os.path as op
import re
import typing as t
from zipfile import ZIP_DEFLATED, ZipFile

log = logging.getLogger(__name__)


def unzip_archive(zipfile_path: str, output_dir: str, dry_run: bool = False) -> None:
    """Extracts the contents of a ZIP archive to a specified directory.

    This function extracts the contents of `zipfile_path` into `output_dir`.
    Extraction is performed only if `dry_run` is set to False.

    Args:
        zipfile_path (str): Absolute path to the ZIP file.
        output_dir (str): Absolute path to the directory where the extracted
            files will be placed.
        dry_run (bool, optional): If True, the extraction is skipped, allowing
            for debugging without modifying files.

    Examples:
        >>> unzip_archive('/flywheel/v0/inputs/ZIP/file.zip', '/flywheel/v0/work/')
        >>> unzip_archive('/flywheel/v0/inputs/ZIP/file.zip', '/flywheel/v0/work/', dry_run=True)

    """
    input_zip = ZipFile(zipfile_path, "r")
    log.info(f"Unzipping file, {zipfile_path}")

    if not dry_run:
        input_zip.extractall(output_dir)


def get_config_from_zip(
    zipfile_path: str, search_str: str = r"_config\.json"
) -> t.Optional[t.Dict]:
    """Extracts and returns configuration data from a JSON file within a ZIP archive.

    This function searches for a file within `zipfile_path` whose name matches
    the `search_str` pattern and returns its contents as a Python dictionary.

    Args:
        zipfile_path (str): Absolute path to the ZIP file to be searched.
        search_str (str, optional): Regular expression pattern for identifying
            the target JSON file. Defaults to '_config.json'.

    Returns:
        dict or None: A dictionary containing the extracted JSON data if found,
        otherwise None.

    Example:
        >>> config = get_config_from_zip('/flywheel/v0/inputs/ZIP/file.zip')
    """

    config = {}
    zf = ZipFile(zipfile_path)
    for fl in zf.filelist:
        if fl.filename[-1] != os.path.sep:  # not (fl.is_dir()):
            # if search_str in filename
            if re.search(search_str, fl.filename):
                json_str = zf.read(fl.filename).decode()
                config = json.loads(json_str)

                # This corrects for leaving the initial "config" key out
                # of previous gear versions without error
                if "config" not in config.keys():
                    config = {"config": config}

    if not config:
        log.warning("Configuration file is empty or not found.")
        return None

    return config


def zip_output(
    root_dir: str,
    source_dir: str,
    output_zip_filename: str,
    dry_run: bool = False,
    exclude_files: t.Optional[t.List[str]] = None,
) -> None:
    """
    Compresses a directory into a ZIP archive.

    This function creates a ZIP file containing the contents of `source_dir`
    relative to `root_dir`. The resulting ZIP archive is saved at `output_zip_filename`.

    Args:
        root_dir (str): The root directory to zip relative to.
        source_dir (str): Subdirectory within `root_dir` to be compressed.
        output_zip_filename (str): Full path of the output ZIP archive.
        dry_run (bool, optional): If True, skips actual compression for debugging.
        exclude_files (Optional[List[str]], optional): List of file paths to exclude
            from the ZIP archive. Defaults to None.

    Raises:
        FileNotFoundError: If `root_dir` does not exist.

    Examples:
        >>> zip_output('/flywheel/v0/work', 'gear_output', 'output.zip')
        >>> zip_output('/flywheel/v0/work', 'gear_output', 'output.zip', dry_run=True)

        .. code-block:: python

            zip_output(
                '/flywheel/v0/work', 'gear_output', 'output.zip',
                exclude_files=['sub_dir1/file1.txt', 'sub_dir2/file2.txt']
            )
    """
    exclude_from_output = exclude_files if exclude_files else []

    if not op.exists(root_dir):
        raise FileNotFoundError(f"The directory '{root_dir}' does not exist.")

    log.info(f"Zipping output file: {output_zip_filename}")

    if not dry_run:
        current_directory = os.getcwd()
        os.chdir(root_dir)
        try:
            os.remove(output_zip_filename)
        except FileNotFoundError:
            pass

        with ZipFile(output_zip_filename, "w", ZIP_DEFLATED) as outzip:
            for root, subdirs, files in os.walk(source_dir):
                for fl in files + subdirs:
                    fl_path = op.join(root, fl)
                    if fl_path not in exclude_from_output:
                        outzip.write(fl_path)

        os.chdir(current_directory)


def zip_info(zipfile_path: str) -> t.List[str]:
    """
    Retrieves a list of relative file paths stored in a ZIP archive.

    Args:
        zipfile_path (str): Absolute path to the ZIP archive.

    Returns:
        List[str]: A sorted list of relative file paths contained in the ZIP archive.

    Example:
        >>> file_info = zip_info('/path/to/zipfile.zip')
    """
    return sorted(
        filter(
            lambda x: len(x) > 0,
            [
                x.filename if x.filename[-1] != os.path.sep else ""
                for x in ZipFile(zipfile_path).filelist
            ],
        )
    )
