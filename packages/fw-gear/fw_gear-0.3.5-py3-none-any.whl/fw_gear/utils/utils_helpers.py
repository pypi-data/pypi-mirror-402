"""Modules for general utilities."""

import logging
import math
import subprocess
import sys
import typing as t
from pathlib import Path

# Import sanitize_label from fw_meta
from fw_meta.imports import sanitize_label

__all__ = ["sanitize_label"]
if t.TYPE_CHECKING:
    pass


log = logging.getLogger(__name__)


def _convert_nan(
    data: t.Optional[t.Union[dict, str, list, float, int]],
) -> t.Optional[t.Union[dict, str, list, float, int]]:
    # Note: _convert_nan is borrowed from core-api
    """Return converted values."""
    if data is None:
        return None
    if isinstance(data, (str, int)):
        return data
    if isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    if isinstance(data, dict):
        return {key: _convert_nan(value) for key, value in data.items()}
    if isinstance(data, list):
        return [_convert_nan(item) for item in data]
    return data


def convert_nan_in_dict(data: dict) -> dict:  # noqa: D103
    """Convert NaN values in a dictionary to None."""
    # Note: convert_nan_in_dict is borrowed from core-api
    return {key: _convert_nan(value) for key, value in data.items()}


def deep_merge(base, **update):
    """Recursive merging of `update` dict on `base` dict.

    Instead of updating only top-level keys, `deep_merge` recurse down to
    perform a "nested" update.
    """
    for k, v in update.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            deep_merge(base[k], **v)
        else:
            base[k] = v


def trim(obj: dict):
    """Trim object for printing."""
    return {key: trim_lists(val) for key, val in obj.items()}


def trim_lists(obj: t.Any):
    """Replace a long list with a representation.

    List/Arrays greater than 5 in length will be replaced with the first two
    items followed by `...` then the last two items
    """
    if isinstance(obj, (list, tuple)):
        # Trim list
        if len(obj) > 5:
            return [*obj[:1], f"...{len(obj) - 2} more items...", *obj[-1:]]
        # Recurse into lists
        return [trim_lists(v) for v in obj]
    # Recurse into dictionaries
    if isinstance(obj, dict):
        return {key: trim_lists(val) for key, val in obj.items()}
    return obj


def validate_requirements_file(req_file):
    req_path = Path(req_file).resolve()
    if not req_path.is_file():
        raise ValueError(f"File does not exist: {req_path}")
    if req_path.suffix not in {".txt", ".in"}:
        raise ValueError(f"Invalid file type: {req_path.suffix}")
    return str(req_path)


def _run_pip_install(req_path: str):
    cmd = [sys.executable, "-m", "pip", "install", "-r", req_path]
    subprocess.run(cmd, check=True)


def install_requirements(req_file):
    """Install requirements from a file programmatically

    Args:
        req_file (str): Path to requirements file

    Raises:
        SystemExit: If there was an error from pip
    """
    try:
        req_path = validate_requirements_file(req_file)
        _run_pip_install(req_path)
    except (ValueError, subprocess.CalledProcessError) as e:
        log.error(f"Requirement installation failed: {e}")
        sys.exit(1)
