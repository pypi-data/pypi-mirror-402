"""Module for class represent Flywheel file object."""

import logging
import os
import shutil
import tempfile
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

HAVE_FLYWHEEL = False

if t.TYPE_CHECKING:
    import flywheel  # Imported only for type checking

try:
    import flywheel

    HAVE_FLYWHEEL = True
except (ModuleNotFoundError, ImportError):
    HAVE_FLYWHEEL = False


log = logging.getLogger(__name__)

FLYWHEEL_HIERARCHY = [
    "group",
    "project",
    "subject",
    "session",
    "acquisition",
    "analysis",
]


@dataclass
class File:
    """Class representing a context agnostic Flywheel file.

    The SDK and config.json represent files differently. This object
    holds all the metadata associated with a file in a predictable manner
    and allows for converting from SDK or config.json file representations.

    Attributes:
        name (str): File name.
        parent_type (str): Container type of file's parent.
        modality (str): File modality.
        type (str): Flywheel file type.
        mimetype (str): File mimetype.
        classification (Dict[str, List[str]]): Classification dictionary.
        tags (List[str]): List of tags.
        info (dict): Custom information dict.
        _local_path (Optional[Path]): Local path to file
        parents (Dict[str, str]): File parents.
        zip_member_count (Optional[int]): File zip member count.
        version (Optional[int]): File version.
        file_id (Optional[str]): File id.
        size (Optional[int]): File size in bytes.
        fw_path(str): Path to file in Flywheel.
    """

    name: str
    parent_type: str
    modality: str = ""
    type: str = ""
    mimetype: str = ""
    classification: t.Dict[str, t.List[str]] = field(default_factory=dict)
    tags: t.List[str] = field(default_factory=list)
    info: dict = field(default_factory=dict)
    _local_path: t.Optional[Path] = None
    parents: t.Dict[str, str] = field(default_factory=dict)
    zip_member_count: t.Optional[int] = None
    version: t.Optional[int] = None
    file_id: t.Optional[str] = None
    size: t.Optional[int] = None
    parent_id: t.Optional[str] = None
    source: str = ""
    _client: t.Any = None
    _fw_path: t.Optional[str] = field(init=False, default=None)

    @classmethod
    def from_config(cls, file_: dict, context: t.Any) -> "File":
        """Returns a File object from a GearContext.

        Args:
            file_ (dict): Config.json dictionary representing the file.
        """
        # file_ passed in from config.json
        obj = file_.get("object", {})
        origin_file_id = obj.get("file_id", None)
        if not origin_file_id:
            raise ValueError("File ID not found in file object")

        parents_ = context.client.get_file(origin_file_id).get("parents", {})

        return cls(
            name=file_.get("location", {}).get("name", ""),
            parent_type=file_.get("hierarchy", {}).get("type", ""),
            parent_id=file_.get("hierarchy", {}).get("id", None),
            modality=obj.get("modality", ""),
            type=obj.get("type", ""),
            mimetype=obj.get("mimetype", ""),
            classification=obj.get("classification", {}),
            tags=obj.get("tags", []),
            info=obj.get("info", {}),
            _local_path=file_.get("location", {}).get("path", None),
            zip_member_count=obj.get("zip_member_count", None),
            version=obj.get("version", None),
            file_id=origin_file_id,
            size=obj.get("size", None),
            parents=parents_,
            source="gear_config",
            _client=context.client,
        )

    @classmethod
    def from_sdk(
        cls, file_: "flywheel.models.file_output.FileOutput", context: t.Any
    ) -> "File":
        """Returns a File from an SDK "file".

        Args:
            file_ (flywheel.models.file_output.FileOutput): SDK "file" object
        """
        parent_type = file_.get("parent_ref", {}).get("type", "")

        parents_ = file_.get("parents", {})

        return cls(
            name=file_.get("name", ""),
            parent_type=parent_type,
            modality=file_.get("modality", ""),
            type=file_.get("type", ""),
            mimetype=file_.get("mimetype", ""),
            classification=file_.get("classification", {}),
            tags=file_.get("tags", []),
            info=file_.get("info", {}),
            parents=parents_,
            zip_member_count=file_.get("zip_member_count", None),
            version=file_.get("version", None),
            file_id=file_.get("file_id", None),
            size=file_.get("size", None),
            parent_id=file_.get("parents", {}).get(parent_type, ""),
            source="sdk",
            _client=context.client,
        )

    @property
    def fw_path(self) -> str:
        """Lazy-load the Flywheel path to the file."""
        if self._fw_path is None:
            # Assuming you can construct the Flywheel path from existing attributes
            self._fw_path = self._construct_fw_path()
        return self._fw_path

    def _construct_fw_path(self) -> str:
        """Construct the Flywheel path to the file."""
        if not self.parents:
            log.warning("Parents information is missing, using default parents.")
            self.parents = {key: "unknown" for key in FLYWHEEL_HIERARCHY}
        if not all(key in self.parents for key in FLYWHEEL_HIERARCHY):
            log.warning(
                "Some hierarchy information is missing, using defaults where necessary."
            )
            for key in FLYWHEEL_HIERARCHY:
                self.parents.setdefault(key, "unknown")

        path_components = []

        for key in FLYWHEEL_HIERARCHY:
            cont_id = self.parents.get(key)

            if cont_id is not None:
                try:
                    cont_label = self._client.get(cont_id).label
                    if key == "analysis":
                        path_components.append("analyses")
                    path_components.append(cont_label)
                except Exception as e:
                    raise ValueError(f"Failed to get container label for {key}: {e}")
        path_components.extend(["files", self.name])
        # return path as list of strings
        return path_components

    @property
    def local_path(self) -> t.Optional[Path]:
        """Lazy-load the local path by downloading the file on first access."""
        if self._local_path is None:
            if self._client:
                file_cont = self._client.get_file(self.file_id)
                self._local_path = self.download_file_to_temp(file_cont)
            else:
                log.warning("Client not set, cannot download file.")
                self._local_path = None
        return self._local_path

    @staticmethod
    def download_file_to_temp(file_: "flywheel.models.file_output.FileOutput") -> Path:
        """Downloads a file to a temporary directory and returns the path.

        Args:
            file_ (flywheel.models.file_output.FileOutput): FW file object.

        Returns:
            Path: Local path to the downloaded file.
        """

        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()

            # Download the file to the temporary directory
            local_file_path = os.path.join(temp_dir, file_.name)
            file_.download(local_file_path)

            return Path(local_file_path)
        except Exception as e:
            log.error(f"Failed to download file: {e}")
            raise

    def __del__(self):
        """Clean up the temporary file if the source is 'sdk'."""
        if self.source == "sdk" and self._local_path:
            try:
                if self._local_path.exists():
                    shutil.rmtree(self._local_path.parent)
            except Exception as e:
                log.error(f"Failed to delete temporary file: {e}")
