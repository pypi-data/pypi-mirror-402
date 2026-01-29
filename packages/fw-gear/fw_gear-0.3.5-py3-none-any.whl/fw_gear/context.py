"""Flywheel gear context."""

import json
import logging
import os
import typing as t
import warnings
from pathlib import Path
from pprint import pformat
from shutil import rmtree

from .config import Config
from .logging import configure_logging
from .manifest import Manifest
from .metadata import Metadata

HAVE_FLYWHEEL = False

if t.TYPE_CHECKING:
    import flywheel  # Imported only for type checking

try:
    import flywheel

    HAVE_FLYWHEEL = True
except (ModuleNotFoundError, ImportError):
    HAVE_FLYWHEEL = False

log = logging.getLogger(__name__)


class GearContextError(Exception):
    """Custom exception for errors related to GearContext."""

    def __init__(self, message: str = "An error occurred in GearContext"):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class GearContext:
    """Context for gear runtime.

    * Provides methods for interacting with gear runtime objects such as:
        * `config.json` (Runtime configuration)
        * `manifest.json` (Defined configuration and gear metadata)
        * `.metadata.json` (Hierarchy metadata to be updated at end of gear run)
    * Configures gear logging


    Args:
        gear_path: Path to gear directory, default behavior will use `/flywheel/v0`.
        manifest_path: Path to the gear's manifest.json file,
            defaults to ``self.path/'manifest.json'``.
        config_path: Path to the gear's config.json file, defaults to
            ``self._path/'config.json'``.
        log_metadata: Whether to log .metadata.json to log upon write,
            defaults to True.
        clean_on_error: Whether to clean output directory upon exit
            with error, defaults to False.
    """

    def __init__(
        self,
        gear_path: t.Optional[str] = "/flywheel/v0",
        manifest_path: t.Optional[str] = "/flywheel/v0/manifest.json",
        config_path: t.Optional[str] = "/flywheel/v0/config.json",
        log_metadata: bool = True,
        fail_on_validation: bool = True,
        clean_on_error: bool = False,
    ):  # noqa: D107
        self._path = Path(gear_path or Path.cwd()).resolve()
        self.config = Config(None, self._load_json(config_path))
        self._client: t.Optional["flywheel.Client"] = self.get_client()
        self.config._client = self.config._client or self._client
        self._out_dir = None
        self._work_dir = None
        self._log_metadata = log_metadata
        self.fail_on_validation = fail_on_validation
        self._clean_on_error = clean_on_error
        self.manifest = None

        # Having a manifest.json is not required per gear specifications
        try:
            self.manifest = Manifest(manifest_path)
        except FileNotFoundError:
            log.debug(
                f"Manifest file not found at {manifest_path}. Continuing without manifest."
            )

        # Needs to be last
        self.metadata = Metadata(self)

    def init_logging(self, default_config_name=None, update_config=None):
        """Configures logging via `fw_gear.logging.configure_logging`.

        If no `default_config_name` is provided, will get `debug` from the
        configuration options. If `debug` is False or not defined in the gear
        configuration options, `default_config_name` will be set to info.

        If `update_config` is not provided, manifest['custom']['log_config'] will be
        used (if defined in the manifest).

        Args:
            default_config_name (str, optional): A string, 'info' or 'debug', indicating
                the default template to use. (Defaults to 'info').
            update_config (dict, optional): A dictionary containing the keys, sub-keys,
                and values of the templates to update. (Defaults to
                None).
        """
        if not default_config_name:
            if self.config.opts.get("debug"):
                default_config_name = "debug"
            else:
                default_config_name = "info"
        if not update_config:
            # Only try to get log_config from manifest if manifest exists
            if self.manifest is not None:
                if isinstance(self.manifest.get_value("custom"), dict):
                    update_config = self.manifest.get_value("custom").get(
                        "log_config", None
                    )

        configure_logging(
            default_config_name=default_config_name,
            update_config=update_config,
        )
        return default_config_name, update_config

    @property
    def work_dir(self) -> Path:
        """Get the absolute path to a work directory.

        Returns:
            pathlib.Path: The absolute path to work.
        """
        if self._work_dir is None:
            self._work_dir = self._path / "work"
            if not self._work_dir.exists():
                self._work_dir.mkdir(parents=True)
        return self._work_dir

    @property
    def output_dir(self) -> Path:
        """Get the absolute path to the output directory.

        Returns:
            pathlib.Path: The absolute path to outputs.
        """
        if self._out_dir is None:
            self._out_dir = self._path / "output"
            if not self._out_dir.exists():
                self._out_dir.mkdir(parents=True)
        return self._out_dir

    @property
    def client(self) -> t.Optional["flywheel.Client"]:  # noqa: D402
        """Wrapper around self.get_client()."""
        if not self._client:
            self._client = self.get_client()
        return self._client

    def is_fw_context(self) -> bool:
        """Return True if the gear is running in a Flywheel gear context, False otherwise."""

        gear_path = Path("/flywheel/v0")

        return gear_path.exists() and Path(gear_path / "config.json").exists()

    def get_client(self) -> t.Optional["flywheel.Client"]:
        """Get the SDK client, if an api key input exists or CLI client exists.

        Returns:
          flywheel.Client: The Flywheel SDK client.


        Raises:
            GearContextError: If the Flywheel SDK is not installed, no API key is found in `config.json`, or initializing the Flywheel Client fails.
        """
        if not HAVE_FLYWHEEL:
            warnings.warn(
                "Please install the `sdk` extra or install `flywheel-sdk` within"
                " your gear in order to use the SDK client."
            )
            return None
        api_key = None
        client = None

        for inp in self.config.inputs.values():
            if inp["base"] == "api-key" and inp["key"]:
                api_key = inp["key"]
                break
        if api_key:
            try:
                client = flywheel.Client(api_key)

            except Exception as exc:  # pylint: disable=broad-except
                log.exception(
                    "An exception was raised when initializing the Flywheel Client with the provided API key."
                )
                raise GearContextError(
                    "Failed to initialize the Flywheel Client with the provided API key."
                ) from exc
        return client

    def log_config(self):
        """Print the configuration and input files to the logger."""
        # Log destination
        log.info(
            "Destination is %s=%s",
            self.config.destination.get("type"),
            self.config.destination.get("id"),
        )

        # Log file inputs
        for inp_name, inp in self.config.inputs.items():
            if inp["base"] != "file":
                continue

            container_type = inp.get("hierarchy", {}).get("type")
            container_id = inp.get("hierarchy", {}).get("id")
            file_name = inp.get("location", {}).get("name")

            log.info(
                'Input file "%s" is %s from %s=%s',
                inp_name,
                file_name,
                container_type,
                container_id,
            )

        # Log configuration values
        for key, value in self.config.opts.items():
            log.info('Config "%s=%s"', key, value)

    def open_output(self, name: str, mode: str = "w", **kwargs) -> t.IO:
        """Open the named output file.

        Args:
            name: The name of the output.
            mode: The open mode (Default value = 'w').
            **kwargs (dict): Keyword arguments for `open`.

        Returns:
            File: The file object.
        """
        path = self.output_dir / name
        return path.open(mode, **kwargs)

    def get_context_value(self, name: str) -> t.Optional[dict]:
        """Get the context input for name.

        Args:
            name: The name of the input.

        Returns:
            dict: The input context value, or None if not found.
        """
        inp = self.config.get_input(name)
        if not inp:
            return None
        if inp["base"] != "context":
            raise ValueError(f"The specified input {name} is not a context input")
        return inp.get("value")

    def __enter__(self):  # noqa: D105
        return self

    def __exit__(self, exc_type, exc_value, _traceback):
        if exc_type is None or (
            issubclass(exc_type, SystemExit) and exc_value.code == 0
        ):
            self.metadata.update_zip_member_count(
                self.output_dir,
                container_type=self.config.destination["type"],
            )
            self.metadata.write(
                self.output_dir, self.fail_on_validation, self._log_metadata
            )
        elif self._clean_on_error:  # noqa: PLR5501
            log.info("Cleaning output folder.")
            self._clean_output()
        else:
            log.debug(f"Skipping cleanup of {self.output_dir}")

        if self._client:
            sdk_usage = getattr(
                self._client.api_client.rest_client, "request_counts", None
            )
            if not sdk_usage:
                log.debug("SDK profiling not available in this version of flywheel-sdk")
            else:
                log.debug(f"SDK usage:\n{pformat(sdk_usage, indent=2)}")

    def _clean_output(self):
        for path in Path(self.output_dir).glob("**/*"):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                rmtree(path)

    @staticmethod
    def _load_json(filepath):
        """Return dictionary for input json file.

        Args:
          filepath (str): Path to a JSON file.

        Raises:
            RuntimeError: If filepath cannot be parsed as JSON.

        Returns:
            (dict): The dictionary representation of the JSON file at filepath.
        """
        json_dict = dict()
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r") as f:
                    json_dict = json.load(f)
            except json.JSONDecodeError:
                raise RuntimeError(f"Cannot parse {filepath} as JSON.")

        return json_dict
