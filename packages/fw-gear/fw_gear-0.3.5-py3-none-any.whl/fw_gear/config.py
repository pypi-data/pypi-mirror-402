"""Config module."""

import json
import typing as t
from pathlib import Path

from .logging import unauthenticated
from .manifest import Manifest, ManifestValidationError
from .utils.sdk_helpers import get_container_from_ref, get_parent

if t.TYPE_CHECKING:
    import flywheel


class Config:
    """Basic Config class akin to Manifest class.

    This class is mainly used as a helper for the
    `gear config create` function of the python-cli,
    however it may have unforeseen programmatic usages.

    There is some confusing nomenclature here.  The gear
    configuration is stored in a file named `config.json`,
    within the config.json file, there are at three keys:
        * config:  configuration options for the gear,
            often booleans, integers, floats, or short
            strings.
        * inputs: Gear inputs, usually in the form of files,
            longer text.
        * destination: Information on where the gear is
            being run within the flywheel hierarchy.

    This class represents the `config.json` file, meaning
    that is has attributes which store the configuration
    options, inputs, and destination. That means that the
    class `Config` has a `config` attribute (configuration
    options) and the constructor accepts a `config`
    dictionary that contains a `config` (configuration
    options) key.
    """

    def __init__(
        self,
        client: t.Optional["flywheel.Client"],
        config: t.Optional[dict],
        path: Path = Path.cwd(),
    ):
        """Load or generate config.

        Args:
            client: Optional flywheel SDK client.
            config: Config dictionary with any of
                the following keys: 'config','inputs','destination'.
                Defaults to None.
            path: Path to existing
                configuration or path to directory in which to create
                config. Defaults to Path.cwd().

        Raises:
            ConfigValidationError:
                1. When a config kwarg has been passed but is
                    not of type dict.
                2. When a config.json exists at the passed path,
                    but it is not valid JSON
                3. When a file is passed in for path, but it does
                    not exist.
        """
        self._opts = dict()
        self._inputs = dict()
        self._destination = dict()
        self._path = Path(path)
        self._job = dict()
        self._client = client
        if config is not None:
            self._load_config_from_dict(config)
        else:
            self._load_config_from_file()

    def _load_config_from_dict(self, config: dict):
        """Load config values from a provided dictionary."""
        if not isinstance(config, dict):
            raise ConfigValidationError("Passed in", ["Cannot read config"])

        self.opts = config.get("config", {})
        self.inputs = config.get("inputs", {})
        self.destination = config.get("destination", {})
        self.job = config.get("job", {})

    def _load_config_from_file(self):
        """Load config values from a JSON file."""
        if self._path.is_dir():
            self._path = self._path / "config.json"
        if not self._path.exists() or not self._path.is_file():
            raise ConfigValidationError(self._path, ["File doesn't exist"])

        try:
            with open(self._path, "r") as fp:
                cfg = json.load(fp)
            self.opts = cfg.get("config", {})
            self.inputs = cfg.get("inputs", {})
            self.destination = cfg.get("destination", {})
            self.job = cfg.get("job", {})
        except json.JSONDecodeError:
            raise ConfigValidationError(self._path, ["Cannot read config file"])

    @property
    def opts(self):
        """Get provided configuration values."""
        return self._opts

    @property
    def job(self):
        """Get provided job info when show-job set to true."""
        return self._job

    @property
    def inputs(self):
        """Get provided inputs."""
        return self._inputs

    @property
    def destination(self):
        """Get gear run destination."""
        return self._destination

    @opts.setter
    def opts(self, config: dict):
        """Set gear config (for use in building gear local runs)."""
        self._opts = config

    @job.setter
    def job(self, job: dict):
        """Set gear config (for use in building gear local runs)."""
        self._job = job

    @inputs.setter
    def inputs(self, inputs: dict):
        """Set gear inputs (for use in building gear local runs)."""
        self._inputs = inputs

    @destination.setter
    def destination(self, dest: dict):
        """Set gear destination (for use in building gear local runs)."""
        self._destination = dest

    def update_opts(self, vals: dict):
        """Perform dictionary update on configuration values."""
        self._opts.update(vals)

    def update_destination(self, dest: dict):
        """Perform dictionary on destination dictionary."""
        self._destination.update(dest)

    def add_input(
        self, name: str, val: str, type_: str = "file", file_: t.Optional[t.Any] = None
    ):
        """Add an input to the config.

        Args:
            name: name of input
            val (str): input value, file path, api-key, context
            type_: file, api-key, or context. Defaults to "file".
            file_: File object to set

        Raises:
            ValueError: When file doesn't exist.
            NotImplementedError: When type is not file or api-key
        """
        if type_ == "file":
            path = Path(val)
            try:
                stat_result = path.resolve().stat()
            except FileNotFoundError:
                raise ValueError(
                    f"Cannot resolve file input at {path}, is the path correct?"
                )

            if file_:
                obj = {
                    "size": file_.size,
                    "type": file_.type,
                    "mimetype": file_.mimetype,
                    "modality": file_.modality,
                    "classification": file_.classification,
                    "tags": file_.tags,
                    "info": file_.info,
                    "zip_member_count": file_.zip_member_count,
                    "version": file_.version,
                    "file_id": file_.file_id,
                    "origin": {"type": "user", "id": ""},
                }
            else:
                obj = {
                    "size": stat_result.st_size,
                    "type": None,
                    "mimetype": "application/octet-stream",
                    "modality": None,
                    "classification": {},
                    "tags": [],
                    "info": {},
                    "zip_member_count": None,
                    "version": 1,
                    "file_id": "",
                    "origin": {"type": "user", "id": ""},
                }
            file = {
                "base": "file",
                "location": {
                    "name": path.name,
                    "path": f"/flywheel/v0/input/{name}/{path.name}",
                },
                "object": obj,
            }
            self.inputs.update({name: file})
        elif type_ == "api-key":
            self.inputs.update({name: {"base": "api-key", "key": val}})
        else:
            raise NotImplementedError(f"Unknown input type {type_}")

    @classmethod
    def default_config_from_manifest(
        cls, manifest: t.Union[Path, Manifest]
    ) -> "Config":
        """Create a default config.json from a manifest file.

        Args:
            manifest: Path to manifest or instantiated Manifest object.

        Raises:
            ValueError: When there is a problem parsing the manifest.

        Returns:
            Config: new config class with a default configuration.
        """
        if not isinstance(manifest, Manifest):
            try:
                manifest = Manifest(manifest)
            except ManifestValidationError:
                raise ValueError("Could not load manifest to generate config")

        config = {}

        for k, v in manifest.config.items():
            if "default" in v:
                config[k] = v["default"]

        return cls(None, config={"config": config})

    def get_input(self, name: str) -> t.Optional[dict]:
        """Get raw input object by name.

        Args:
            name: Name of input.
        """
        return self._inputs.get(name)

    def get_input_path(self, name: str) -> t.Optional[Path]:
        """Get input filepath by name.

        Args:
            name: Input name

        Raises:
            ValueError: If found input is not a file.

        Returns:
            t.Optional[Path]: Input filepath if found
        """
        input_ = self.get_input(name)
        if input_ is None:
            return None
        if input_.get("base") != "file":
            raise ValueError(f"The specified input {name} is not a file")
        return input_.get("location", {}).get("path")

    def get_input_filename(self, name) -> t.Optional[str]:
        """Get the the filename of given input file.
        Sourced from the 'inputs' field in the manifest.json

        Args:
            name (str): The name of the input.

        Raises:
            ValueError: if the input exists, but is not a file.

        Returns:
            str: The filename to the input file if it exists, otherwise None.
        """
        input_ = self.get_input(name)
        if input_ is None:
            return None
        if input_.get("base") != "file":
            raise ValueError(f"The specified input {name} is not a file")
        return input_.get("location", {}).get("name")

    def get_input_file_object(self, name: str) -> t.Optional[dict]:
        """Get the specified input file object from config.json

        Args:
            name (str): The name of the input.

        Returns:
            dict: The input dictionary, or None if not found.
        """
        input_ = self.get_input(name)
        if input_ is None:
            return None
        if input_.get("base") != "file":
            raise ValueError(f"The specified input {name} is not a file")
        return input_.get("object")

    def get_input_file_object_value(self, name: str, key: str) -> t.Any:
        """Get the value of the input file metadata from config.json.

        Args:
            name (str): The name of the input.
            key (str): The name of the file container metadata.

        Raises:
            ValueError: if the input exists, but is not a file.

        Returns:
            Union[str, list, dict]: The value of the specified file metadata, or None if not found.

        """
        inp_obj = self.get_input_file_object(name)
        return inp_obj.get(key, None) if key in inp_obj.keys() else None

    def open_input(self, name: str, mode: str = "r", **kwargs) -> t.IO:
        """Open the named input file, derived from the 'inputs' field in the manifest.

        Args:
            name: The name of the input.
            mode: The open mode (Default value = 'r').
            **kwargs (dict): Keyword arguments for `open`.

        Raises:
            ValueError: If input `name` is not defined in config.json.
            FileNotFoundError: If the path in the config.json for input `name` is
                not a file/

        Returns:
            The file object.
        """
        path = self.get_input_path(name)
        if path is None:
            raise ValueError(f"Input {name} is not defined in the config.json")
        if not Path(path).is_file():
            raise FileNotFoundError(f"Input {name} does not exist at {path}")
        return open(path, mode, **kwargs)

    def get_destination_container(self):
        """Returns the destination container."""
        if not self._client:
            # Error that we need API key.
            unauthenticated("Config.get_destination_container")
        return get_container_from_ref(self._client, self.destination)

    def get_destination_parent(self):
        """Returns the parent container of the destination container."""
        if not self._client:
            # Error that we need API key.
            unauthenticated("Config.get_destination_container")
        dest = self.get_destination_container()
        return get_parent(self._client, dest)

    ############### Utilities
    def to_json(self, path: t.Optional[Path] = None):
        """Dump config to a file in config.json format."""
        to_write = {
            "config": self.opts,
            "inputs": self.inputs,
            "destination": self.destination,
        }
        with open(path if path is not None else str(self._path), "w") as fp:
            json.dump(to_write, fp, indent=4)

    def __str__(self):  # pragma: no cover
        """Return string representation."""
        to_write = {
            "config": self.opts,
            "inputs": self.inputs,
            "destination": self.destination,
        }
        return json.dumps(to_write, indent=4)


class ConfigValidationError(Exception):
    """Indicates that the file at path is invalid.

    Attributes:
        path (str): The path to the file
        errors (list(str)): The list of error messages
    """

    def __init__(self, path, errors):
        """Init error."""
        super(ConfigValidationError, self).__init__()
        self.path = path
        self.errors = errors

    def __str__(self):
        """Return string representation."""
        result = "The config at {} is invalid:".format(self.path)
        for error in self.errors:
            result += "\n  {}".format(error)
        return result
