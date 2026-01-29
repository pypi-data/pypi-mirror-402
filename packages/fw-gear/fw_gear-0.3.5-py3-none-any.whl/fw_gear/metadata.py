"""Metadata module."""

import copy
import json
import logging
import sys
import typing as t
import warnings
import zipfile
from pathlib import Path

import jsonschema

if t.TYPE_CHECKING:
    # Gear toolkit import is only used for type checking.
    from fw_gear.context import GearContext  # pylint: disable=unused-import


from .file import File
from .utils import convert_nan_in_dict, deep_merge, trim

try:
    # Make numpy optional
    import numpy as np

    NUMPY = True
except ImportError:
    NUMPY = False

PARENT_DIR = Path(__file__).parents[0]
CONT_ORDER = ["project", "subject", "session", "acquisition", "analysis"]

log = logging.getLogger(__name__)


def create_qc_result_dict(name: str, state: str, **data) -> dict:
    """Create a pass/fail/na QC result dict for a file.

    Args:
        name (str): QC result name
        state (str): pass, fail, or na
        data: custom data
    """
    if state.lower() not in ["pass", "fail", "na"]:
        raise ValueError(f"Expected state to be PASS|FAIL|NA, found {state.upper()}")
    result = {name: {"state": state.upper(), **data}}
    return result


def sanitize_periods(
    d: t.Optional[t.Union[dict, str, list, float, int]],
) -> t.Optional[t.Union[dict, str, list, float, int]]:
    """Sanitize keys in dict. Recursive in case of nested dicts."""
    if d is None:
        return None
    if isinstance(d, (str, int, float, list)):
        return d
    if isinstance(d, dict):
        return {
            (key.replace(".", "_") if isinstance(key, str) else key): sanitize_periods(
                value
            )
            for key, value in d.items()
        }
    return d


class Metadata:
    """Class to store and interact with Flywheel metadata via .metadata.json or SDK call."""

    def __init__(
        self,
        context: t.Optional["GearContext"] = None,
        name_override: str = "",
        version_override: str = "",
    ):
        """Initialize metadata class.

        Args:
            context (Optional[GearContext]): GearContext from
                which to populate gear info (inputs, config, destination, ...)
            name_override (str, optional): Optional gear name to use, overrides
                manifest value from GearContext. Defaults to "".
            version_override (str, optional): Optional gear version to use,
                overrides manifest value from GearContext.
                Defaults to "".
        """
        self._metadata: dict = {}
        # Read-only gear context for configuration options
        self._context = context
        self._has_job_info = False
        self.name_override = name_override
        self.version_override = version_override

    ###################
    # HELPER FUNCTION #
    ###################
    def _validate_container_type(self, container_type: str) -> bool:
        """Validate container type is part of the destination hierarchy.

        Args:
            container_type (str): Container type to validate.
        """
        if container_type not in CONT_ORDER:
            raise ValueError(
                f"Container type {container_type} is not part of the hierarchy."
            )

        if self._context.config.destination.get("type") == "analysis":
            parent_container = self._context.config.get_destination_parent()
        else:
            parent_container = self._context.config.get_destination_container()
        # validate if container type is part of the hierarchy
        if parent_container.container_type not in CONT_ORDER:
            raise ValueError(
                f"Parent container type {parent_container.container_type} is not part of the hierarchy."
            )
        parent_container_index = CONT_ORDER.index(parent_container.container_type)

        container_index = CONT_ORDER.index(container_type)
        if container_index > parent_container_index:
            return False  # not allowed to update children
        return True  # ok to update same level or parent

    ##################
    # UPDATE METHODS #
    ##################
    # update methods with .metadata.json
    def update_container(
        self, container_type: str, deep: bool = True, **kwargs
    ) -> None:
        """Update metadata for the given container type in the hierarchy.

        Args:
            container_type (str): The container type (e.g. session or
                acquisition).
            deep (bool): Perform a deep (recursive) update on subdictionaries.
                Default: True
            **kwargs (dict): Update arguments
        """
        if not self._validate_container_type(container_type):
            raise ValueError(
                f"Container type {container_type} is outside the hierarchy that can be updated via .metadata.json."
            )
        dest = self._metadata.setdefault(container_type, {})
        if deep:
            deep_merge(dest, **kwargs)
        else:
            dest.update(**kwargs)

    def update_file_metadata(
        self,
        file_: t.Any,
        container_type: str,
        deep: bool = True,
        **kwargs,
    ) -> None:
        """Update file metadata by name.

        Update a file by name in the hierarchy at the given container type.

        Args:
            file_: File name (str), SDK file (flywheel.FileEntry) or
                dictionary from config.json
            container_type (str): Type of parent container.
            deep (bool): Perform a deep (recursive) update on subdictionaries.
                Default: True
            **kwargs (dict): Update arguments
        """
        if container_type != "analysis" and not self._validate_container_type(
            container_type
        ):
            raise ValueError(
                f"Container type {container_type} is outside the hierarchy that can be updated via .metadata.json."
            )

        # Find file by name in the given container
        file_obj = get_file(file_, self._context, container_type)
        parent = self._metadata.setdefault(file_obj.parent_type, {})
        files = parent.setdefault("files", [])
        file_entry = None
        for fe in files:
            if fe.get("name") == file_obj.name:
                file_entry = fe
                break
        # No metadata entry for given file exists yet.
        if file_entry is None:
            # Initialize with file name and any existing info if present
            file_entry = {"name": file_obj.name, "info": file_obj.info}
            # Add this file entry to the parent container's 'file' key
            files.append(file_entry)
        # Placeholder reference to location in the full dictionary we want
        # to update, i.e. the file entry
        target = file_entry
        # Update metadata with kwargs
        if deep:
            deep_merge(target, **kwargs)
        else:
            target.update(kwargs)

    def update_zip_member_count(
        self,
        path: Path,
        container_type: t.Optional[str] = None,
    ) -> None:
        """Update metadata with zip-member count.

        Add the zip member count for files in a given directory the metadata

        Args:
            path (Path): directory or file.
            container_type (Optional[str]): Container type found files should
                be associated with.
        """
        if not path.exists():
            log.warning("Provided path does not exist: %s", path)
            return
        if path.is_file():
            files = iter([path])
        else:
            files = path.rglob("*")
        for file in files:
            if file.suffix != ".zip":
                continue
            try:
                with zipfile.ZipFile(file) as archive:
                    count = len(archive.infolist())
                    self.update_file_metadata(
                        file.name,
                        container_type=container_type,
                        zip_member_count=count,
                    )
            except zipfile.BadZipFile:
                log.warning("Invalid zip file %s. Skipping update", file)

    # update methods with HTTP requests
    def modify_container_file_info(
        self,
        file_: File,
        **info,
    ) -> None:
        """Modify file info with HTTP requests.

        Wrapper for modify_container_file_info SDK method call.
        Using set method (add on) to update.

        Args:
            file_ (File): File Object
            info (e.Dict[t.Any]): Info dictionary that will be used to update file info.
        """
        if self._context.client is None:
            raise AttributeError("FW Client was not initialized or set.")

        self._context.client.modify_container_file_info(
            file_.parent_id, file_.name, {"set": info}
        )

    def modify_container_info(self, cont_id: str, **info) -> None:
        """Update metadata for the given container type in the hierarchy.

        Wrapper for modify_container_info SDK method call.
        Using set method (add on) to update.

        Args:
            cont_id (str): Container ID that will be used to update container info
            info (e.Dict[t.Any]): Info dictionary that will be used to update the container info.
        """
        if self._context.client is None:
            raise AttributeError("FW Client was not initialized or set.")

        self._context.client.modify_container_info(cont_id, {"set": info})

    ###################
    # WRITING METHODS #
    ###################
    # methods that will be used with .metadata.json
    def clean(self):
        """Clean metadata before writing."""
        self._metadata = convert_nan_in_dict(self._metadata)
        self._metadata = sanitize_periods(self._metadata)

        # Serialize to JSON string
        json_string = json.dumps(self._metadata, cls=MetadataEncoder)

        # Check size
        size = len(json_string.encode("utf-8"))
        if size > 16 * 1024 * 1024:  # 16MB limit
            warnings.warn(
                f"Metadata size exceeds 16MB: {size} bytes. Consider breaking metadata into smaller chunks.",
                UserWarning,
            )

        # Deserialize to prepare for writing (if needed)
        self._metadata = json.loads(json_string)

    def log(self):
        """Log representation of metadata."""
        rep = copy.deepcopy(self._metadata)
        log.info(
            ".metadata.json:\n%s",
            json.dumps(trim(rep), indent=2, cls=MetadataEncoder),
        )

    def write(
        self, directory: Path, fail_on_validation: bool = False, log_meta: bool = True
    ) -> None:
        """Write metadata to .metadata.json in the given directory.

        Args:
            directory (Path): Directory in which to write .metadata.json
            fail_on_validation (bool): Fail if engine metadata schema
                validation has errors. Default: False
            log_meta (bool): Also log cleaned metadata. Default: True
        """
        if not self._metadata:
            return
        self.clean()
        log.debug("Validating generated metadata")
        with open(PARENT_DIR / "engine_metadata_schema.json") as fp:
            engine_metadata_schema = json.load(fp)
        validator = jsonschema.Draft7Validator(engine_metadata_schema)
        errors = []
        for err in validator.iter_errors(self._metadata):
            errors.append(err)
        if errors:
            log.error("Error(s) validating produced metadata.")
            for err in errors:
                log.error(err)
            if fail_on_validation:
                self.log()
                sys.exit(1)
        if log_meta:
            self.log()

        with open(directory / ".metadata.json", "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2, cls=MetadataEncoder)

    ##############
    # QC METHODS #
    ##############
    # adding qc result to .metadata.json
    def add_qc_result(self, file_: t.Any, name: str, state: str, **data) -> None:
        """Add a pass/fail/na QC results to a file and update .metadata.json.

        Args:
            file_ (t.Any): File object
            name (str): QC result name
            state (str): pass, fail, or na
            data: custom data
        """
        qc_result = create_qc_result_dict(name, state, **data)
        file_obj = get_file(file_, self._context)
        updated_file_info = self.add_gear_info("qc", file_, **qc_result)  # type: ignore
        self.update_file_metadata(
            file_, container_type=file_obj.parent_type, info=updated_file_info
        )

    # add qc methods for analysis container via .metadata.json
    def add_qc_result_to_analysis(self, name: str, state: str, **data) -> None:
        """Add a pass/fail/na QC results to the destination analysis container via update .metadata.json.

        Args:
            name (str): QC result name
            state (str): pass, fail, or na
            data: custom data
        """
        qc_result = create_qc_result_dict(name, state, **data)
        if self._context.config.destination.get("type") != "analysis":
            raise TypeError("Destination container is not an analysis container.")
        analysis_container = self._context.config.get_destination_container()
        updated_file_info = self.add_gear_info("qc", analysis_container, **qc_result)  # type: ignore
        self.update_container("analysis", info=updated_file_info)

    # add qc methods via API call
    def add_qc_result_via_sdk(self, cont_: t.Any, name: str, state: str, **data):
        """Add a pass/fail/na QC results to a container/file and update the container/file info via HTTP methods.

        Args:
            cont_ (t.Any): Flywheel Container object
            name (str): QC result name
            state (str): pass, fail, or na
            data: custom data

        """
        # generate qc result with provided information
        qc_result = create_qc_result_dict(name, state, **data)

        if isinstance(cont_, (dict, str)) or not hasattr(cont_, "files"):
            file_obj = get_file(cont_, self._context)
            updated_file_info = self.add_gear_info("qc", file_obj, **qc_result)
            self.modify_container_file_info(file_obj, **updated_file_info)
        else:
            updated_cont_info = self.add_gear_info("qc", cont_, **qc_result)
            self.modify_container_info(cont_.id, **updated_cont_info)

    # adding file tag to .metadata.json
    def add_file_tags(self, file_: t.Any, tags: t.Union[str, t.Iterable[str]]) -> None:
        """Add tag(s) to a file.

        Args:
            file_ (t.Any): File Object
            tags (str or Iterable[str]): Tags to add.
        """
        file_obj = get_file(file_, self._context)
        to_add = tags
        if not tags:
            to_add = []
        if isinstance(tags, str):
            to_add = [tags]
        exist_tags = file_obj.tags
        new_tags = list(set([*exist_tags, *to_add]))  # Ensure unique tags
        self.update_file_metadata(
            file_, tags=new_tags, container_type=file_obj.parent_type
        )

    ####################
    # JOB/GEAR METHODS #
    ####################
    def pull_job_info(self):
        """Pull job info from GearContext if present.

        Get job input files, configuration, and job id.

        Args:
            name (str): Gear name override.
            version (str): Gear version override.
        """
        name = self.name_override
        version = self.version_override
        # Don't attempt to set gear info if context not passed in.
        self.job = ""
        if not self._context:
            log.info("Context not provided, adding gear info from name and version")
            info = {name: {"job_info": version}}
            self.job_info = info
            self.name = name
            self.version = version
            self._has_job_info = True
            return
        # Add gear information, configuration, inputs, etc.
        gear_inputs = {}
        for i_name, fe in self._context.config.inputs.items():
            if fe["base"] != "file":
                continue
            obj = fe.get("object", {})
            gear_inputs[i_name] = {
                "parent": fe.get("hierarchy"),
                "file_id": obj.get("file_id", ""),
                "version": obj.get("version", ""),
                "file_name": fe.get("location", {}).get("name", ""),
            }
        # First check for job provided in config
        if self._context.config.job:
            self.job = self._context.config.job.get("id", "")
        elif self._context.config.destination.get("type", "") == "analysis":  # noqa: PLR5501
            try:
                dest = self._context.config.get_destination_container()
                self.job = dest.get("job", {}).get("id", "")
            except AttributeError:
                # When client = None
                log.warning("Could not use SDK to look up job id for analysis")
        if not self.job:
            log.warning("Could not determine job id.")

        m = self._context.manifest
        # Handle the case when manifest is None
        if m is None:
            if not name or not version:
                log.debug(
                    "Manifest is None and no name/version override provided. Using defaults."
                )
                name = name or "unknown-gear"
                version = version or "0.0.0"
        else:
            name = name if name else m.name
            version = version if version else m.version
        info = {
            name: {
                "job_info": {
                    "version": version,
                    "job_id": self.job,
                    "inputs": gear_inputs,
                    "config": self._context.config.opts,
                },
            }
        }
        self.job_info = info
        self.name = name
        self.version = version
        self._has_job_info = True

    def add_or_update_gear_info(
        self, top_level_keys: t.List[str], cont_info: t.Any, **kwargs: t.Any
    ) -> dict:
        """Modify container info section with current job run info
        including info about the gear."""

        if not self._has_job_info:
            self.pull_job_info()

        top = cont_info
        for key in top_level_keys:
            # Check if the current value is not a dictionary
            if key in top and not isinstance(top[key], dict):
                raise TypeError(
                    f"Expected a dictionary at key '{key}', but got {type(top[key]).__name__}."
                )

            # Set default to an empty dictionary if the key doesn't exist
            top = top.setdefault(key, {})

        # Check if gear info has already been added
        if self.name in top:
            # Same (present) job id --> don't update job_info
            existing_info = top[self.name].get("job_info", {})
            if not (id := existing_info.get("job_id", "")) or id != self.job:
                top.update(self.job_info)
        else:
            top.update(self.job_info)

        top = top[self.name]
        top.update(**kwargs)

        return cont_info

    def add_gear_info(
        self,
        top_level: str,
        cont_: t.Any,
        **kwargs: t.Any,
    ) -> dict:
        """Add arbitrary gear info to a particular file/container.

        Add predefined info on gear configuration, as well as custom free-form
        information to a given file/container.

        Args:
            top_level (str): Top level info key under "info" in which to store
                the data, i.e. "qc.result" stores info under "info.qc.result".
            cont_ (t.Any]): File/container to store information on
            kwargs: Custom information to add under gear info.
        """
        if not self._has_job_info:
            self.pull_job_info()

        if isinstance(cont_, (dict, str)) or not hasattr(cont_, "files"):
            if isinstance(cont_, File):
                cont_obj = cont_
            else:
                # Get existing info on file
                cont_obj = get_file(cont_, self._context)
        else:
            cont_obj = cont_

        # Insert or get top level key(s)
        keys = top_level.split(".")

        # updated file/container info object
        return self.add_or_update_gear_info(keys, cont_obj.info, **kwargs)


def get_file(
    file_: t.Any,
    context: t.Optional["GearContext"],
    container_type: t.Optional[str] = None,
) -> File:
    """Get the file object parent container type for the given file definition.

    Args:
        file_ (t.Any): File definition, either a file name (str),
            an SDK file (flywheel.FileEntry) or an entry from the
            config.json (dict).
        context (t.Optional[GearContext]): Read-only gear
            toolkit context to lookup files by name.
        container_type (Optional[str]): Optional parent container
            type to use when str is passed in for file.

    Raises:
        ValueError: When file given by name (str) and no
            GearContext provided.
        RuntimeError: If file by name can't be found.

    Returns:
        File: File object.
    """
    file_name = ""
    if "object" in file_:
        # file_ passed in from config.json
        return File.from_config(file_, context)
    if "info" in file_:
        # file_ passing in from SDK.
        return File.from_sdk(file_, context)
    if not context:
        raise ValueError("Cannot find parent from file name only without GearContext")
    file_name = t.cast(str, file_)

    # should only be applied for output file
    if container_type:
        return File(
            file_name,
            container_type,
        )
    # Search inputs:
    for v in context.config.inputs.values():
        if file_name == v.get("location", {}).get("name"):
            return File.from_config(v, context)
    # Search outputs
    for file_path in context.output_dir.glob("*"):
        if file_path.name == file_name:
            return File(
                file_name,
                context.config.get_destination_container().container_type,
            )
    raise RuntimeError(f"Could not determine parent container of input file {file_}.")


class MetadataEncoder(json.JSONEncoder):
    """Encode metadata to JSON format in order to upload back to Flywheel."""

    # Overwrite default handler for bytes objects
    def default(self, obj: t.Any) -> t.Any:
        """Default json encoder when not handled.

        Handle bytes objects and pass everything else to the default JSONEncoder.

        For bytes, convert to hex and return the first 10 characters, or truncate.

        Args:
            obj (Any): Object to be encoded, can be anything, this only handles bytes.

        Returns:
            str: encoded obj.
        """
        if isinstance(obj, bytes):
            return (
                obj.hex()
                if len(obj) < 10
                else f"{obj.hex()[:10]} ... truncated byte value."
            )

        if NUMPY:  # only if numpy is available
            if type(obj).__module__ == np.__name__:
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return obj.item()

        return json.JSONEncoder.default(self, obj)
