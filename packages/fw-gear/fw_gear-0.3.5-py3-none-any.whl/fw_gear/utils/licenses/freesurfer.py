"""Utilities for installing the Freesurfer license file in the expected location for algorithm execution."""

import logging
import os
import re
import subprocess
import typing as t
from pathlib import Path

from fw_gear.context import GearContext

if t.TYPE_CHECKING:
    pass
log = logging.getLogger(__name__)


def install_freesurfer_license(
    context: GearContext,
    fs_license_path: t.Optional[os.PathLike] = None,
) -> None:
    """
    Installs the FreeSurfer license file in the expected location.

    The license text is obtained using one of the following methods, in order of priority:

    1) Provided as an input file (`freesurfer_license_file` in the manifest).
    2) Retrieved from the "freesurfer_license_key" config parameter.
    3) Extracted from a Flywheel project's `info` metadata (`FREESURFER_LICENSE`).

    Once retrieved, the license file is written to the FreeSurfer top-level directory,
    enabling FreeSurfer usage within the gear.

    See `How to include a Freesurfer license file...
    <https://docs.flywheel.io/user/compute/gears/freesurfer/user_including_a_freesurfer_license_file_to_run_a_freesurfer_or_fmriprep_gear/>`_

    Args:
        context (fw_gear.GearContext): The gear context with core
            functionality.
        fs_license_path (str): The path where the license should be installed,
            typically `$FREESURFER_HOME/license.txt`. Defaults to None.

    Raises:
        FileNotFoundError: If the license cannot be found.

    Examples:
        >>> from fw_gear.utils.licenses.freesurfer import install_freesurfer_license
        >>> install_freesurfer_license(context, '/opt/freesurfer/license.txt')
    """
    log.debug("Locating FreeSurfer installation")
    fs_license_path = get_fs_license_path(fs_license_path)

    log.debug("Searching for FreeSurfer license")
    license_info = find_license_info(context)

    if license_info:
        write_license_info(fs_license_path, license_info)
    else:
        raise FileNotFoundError(
            f"Could not find FreeSurfer license ({fs_license_path})."
        )


def get_fs_license_path(fs_license_path: t.Optional[os.PathLike] = None) -> Path:
    """
    Determines the path where the FreeSurfer license should be installed.

    If a path is provided, ensures it ends with 'license.txt'. Otherwise, it
    attempts to infer the path from the `$FREESURFER_HOME` environment variable
    or by locating the FreeSurfer installation.

    Args:
        fs_license_path (Optional[os.PathLike]): Custom path for the license file. Defaults to None.

    Returns:
        Path: The resolved path for the FreeSurfer license file.

    Raises:
        RuntimeError: If the FreeSurfer installation path cannot be determined.
    """
    if fs_license_path:
        if Path(fs_license_path).suffix != ".txt":
            fs_license_path = Path(fs_license_path) / "license.txt"
    elif os.getenv("FREESURFER_HOME"):
        fs_license_path = Path(os.getenv("FREESURFER_HOME"), "license.txt")
    else:
        try:
            log.debug(
                "FREESURFER_HOME is either not defined in the manifest"
                "or does not exist as defined. (${FREESURFER_HOME})\n"
                "Trying to locate freesurfer."
            )
            which_output = subprocess.check_output(["which", "recon-all"], text=True)
            pattern = ".*freesurfer.*?"
            match = re.search(pattern, which_output)
            if match:
                fs_license_path = Path(match.group(), "license.txt")
            else:
                log.error(f"Could not isolate FreeSurfer path from {which_output}")
                raise RuntimeError("Failed to determine FreeSurfer license path.")
        except subprocess.CalledProcessError as e:
            log.error(e.output)
            raise
    return fs_license_path


def find_license_info(context: GearContext) -> t.Optional[str]:
    """
    Retrieves the FreeSurfer license text from available sources.

    It checks for the license in the following order:
    1) Input file (`freesurfer_license_file`).
    2) Config parameter (`freesurfer_license_key`).
    3) Flywheel project metadata (`FREESURFER_LICENSE`).

    Args:
        context (fw_gear.GearContext): The gear context containing configuration and inputs.

    Returns:
        Optional[str]: The extracted license text, or None if not found.
    """
    license_info = ""
    config_key = isolate_key_name(context)
    if context.config.get_input_path("freesurfer_license_file"):
        license_info = read_input_license(context)
        log.info("Using input file for FreeSurfer license information.")
    elif config_key:
        fs_arg = context.config.opts[config_key]
        license_info = "\n".join(fs_arg.split())
        log.info("Using FreeSurfer license in gear configuration argument.")
    else:
        license_info = check_project_for_license(context)
    return license_info


def isolate_key_name(context: GearContext) -> t.Optional[str]:
    """
    Identifies the relevant FreeSurfer license key from the gear configuration.

    This function searches for a predefined set of FreeSurfer license key names
    within the gear's configuration and returns the first matching key.

    Args:
        context (fw_gear.GearContext): The gear context containing configuration.

    Returns:
        Optional[str]: The matched license key name if found, otherwise None.

    """
    keys = [
        "freesurfer_license_key",
        "FREESURFER_LICENSE",
        "FREESURFER-LICENSE",
        "gear-FREESURFER_LICENSE",
    ]

    for k in keys:
        if context.config.opts.get(k):
            return k
        if context.config.opts.get(k.lower()):
            return k.lower()

    log.info("No matching FreeSurfer license key found in config.")
    return None


def read_input_license(context: GearContext) -> t.Optional[str]:
    """
    Reads and returns the FreeSurfer license text from an input file.

    This function retrieves the license file specified as `freesurfer_license_file`
    in the gear's inputs and returns its contents as a formatted string.

    Args:
        context (fw_gear.GearContext): The gear context containing configuration and inputs.

    Returns:
        Optional[str]: The license text as a formatted string, or None if the file is not found.

    Example:
        >>> license_text = read_input_license(context)
        >>> if license_text:
        >>>     print("License successfully retrieved.")
    """
    input_license = context.config.get_input_path("freesurfer_license_file")
    if input_license:
        with open(input_license) as lic:
            license_info = lic.read()
            license_info = "\n".join(license_info.split())
        return license_info


def check_project_for_license(
    context: GearContext,
) -> t.Optional[str]:
    """
    Retrieves the FreeSurfer license text from a Flywheel project metadata.

    This function checks the project's `info` field for a license key under
    either `FREESURFER-LICENSE` or `FREESURFER_LICENSE`.

    Args:
        context (fw_gear.GearContext): The gear context containing configuration and inputs.

    Returns:
        Optional[str]: The extracted license text if found, otherwise None.

    """
    fly = context.client
    destination_id = context.config.destination.get("id")
    project_id = fly.get_analysis(destination_id)["parents"]["project"]
    project = fly.get_project(project_id)
    if any(
        lic in ("FREESURFER-LICENSE", "FREESURFER_LICENSE") for lic in project["info"]
    ):
        try:
            space_separated_text = project["info"]["FREESURFER-LICENSE"]
        except KeyError:
            space_separated_text = project["info"]["FREESURFER_LICENSE"]
        license_info = "\n".join(space_separated_text.split())
        log.info("Using FreeSurfer license in project info.")
        return license_info


def write_license_info(fs_license_path: Path, license_info: str) -> None:
    """
    Writes the FreeSurfer license text to the specified file.

    This function ensures that the target directory exists before writing the
    license text to the specified path.

    Args:
        fs_license_path (Path): Path to the FreeSurfer license file.
        license_info (str): The license text to be written.

    Raises:
        OSError: If unable to write the license file.
    """
    head = Path(fs_license_path).parents[0]
    if not Path(head).exists():
        Path(head).mkdir(parents=True)
        log.debug(f"Created directory {head}")
    with open(fs_license_path, "w") as flp:
        flp.write(license_info)
        log.debug(f"Wrote license {license_info}")
        log.debug(f" to license file {fs_license_path}")
