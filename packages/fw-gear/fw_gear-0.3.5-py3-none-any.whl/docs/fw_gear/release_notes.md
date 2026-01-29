# Release Notes

## 0.3.5

__Maintenance__:

* Moved `mike` documentation versioning tool from runtime to dev dependencies since
  it's only needed for documentation builds, not at runtime

## 0.3.4

__Maintenance__:

* Added comprehensive contributor documentation:
  * Created `CONTRIBUTING.md` with development setup, testing, documentation
    contribution guidelines, and mike versioning instructions
  * Created `getting_started.md` tutorial with practical GearContext examples
  * Enhanced `README.md` with features overview, quick start examples, and key
    concepts from getting_started guide
* Added API Reference links throughout `context.md` and `utils.md` for all
  classes, methods, and functions to enable easy navigation to detailed API
  documentation
* Fixed GitLab repository links in `index.md` for LICENSE and CONTRIBUTING.md
  files
* Added `__init__.py` files to `utils.archive`, `utils.licenses`, and
  `utils.wrapper` modules to enable proper API documentation generation via
  mkdocstrings
* Enabled one-click code copying in documentation by adding
  `content.code.copy` feature to mkdocs configuration
* Reformulated `context.md` documentation for clarity and consistency:
  * Rewrote introduction to align with actual `GearContext` implementation
  * Streamlined Structure section with clearer component descriptions
  * Improved Basic Usage section with explicit purpose statements
  * Added descriptive titles to all code snippets for better usability
* Expanded `utils.md` documentation to cover previously undocumented utilities:
  * Added comprehensive documentation for Context Utilities (SDK retry
    handlers, resource monitoring decorators)
  * Added Archive/ZIP Management utilities documentation
  * Added FreeSurfer License Utilities documentation
  * Added Nipype Integration documentation with workflow examples
  * Reformulated SDK Helpers and Command Execution sections for consistency
  * Grouped wrapper submodule documentation (Command Execution and Nipype
    Integration) under unified Command Wrapper section
* Expanded API Reference to include all modules and submodules:
  * Added File, Logging, and Invocation Schema to core modules
  * Added all utils submodules (SDK Helpers, Context Utilities, Archive/ZIP,
    FreeSurfer License, Command Wrapper, Nipype, HPC)
* Fixed broken internal documentation link in `context.md`
* Fixed Type argument rendering issue in `update_file_metadata` docstring
* Reorganized documentation navigation structure:
  * Renamed "Specification" to "Gear Specification"
  * Renamed "API" to "API Reference"
  * Renamed "Migration Guide" to "Migration from flywheel-gear-toolkit"
  * Moved "Overall Parity" under migration guide section
  * Moved "API Reference" to bottom of navigation

## 0.3.2

__Enhancement__:

* Updated manifest schema to require and validate config property types,
  ensuring all config properties specify a type from the allowed set: string,
  integer, number, boolean, or array.
* `fw_gear.utils.wrapper.command.exec_command`: added live streaming
  controls (`stream` + `stream_mode`)
  and optional `logfile` tee; improved env merging and safer shell handling.

__Breaking Changes__:

* Removed `stdout_msg` parameter from `fw_gear.utils.wrapper.command.exec_command`.
  This parameter previously allowed logging a custom message instead of command output
  and disabled streaming when provided.

__Maintainence__:

* Addressed potential OS command injection vulnerability when running
  external commands.

__Bug Fix__:

* Fixed issue where `GearContext` would raise a `FileNotFoundError` when
  initialized without a manifest.json file.
* Allow container type to be `Analysis` when updating metadata.
* Prevented pipe deadlocks in live streaming by merging `stderr` into `stdout`
  during streaming for `fw_gear.utils.wrapper.command.exec_command`

## 0.3.1

__Enhancement__:

* Updated `psutil` as optional dependency, allowing users to skip
  installation unless needed.
* Update gear manifest schema to include Flywheel gear classification.

## 0.3.0

__Enhancement__:

* Rollback on `update_file_metadata` to allow updating file metadata
  with file name and container_type inputs
* Added warning when `fw_path` and `local_path` is not available.
* Added missing methods from flywheel-gear-toolkit -
  `get_input_file_object` and `get_input_file_object_value`
* Improved error handling in `get_client()` — now raises `GearContextError`
  if the SDK is unavailable or the API key is invalid.
* Introduced `is_fw_context()` to explicitly check for Flywheel Gear runtime.
* Added `setup_gear_run()` to streamline gear setup and config handling.

__MAINTENANCE__:

* Major refactor: core modules migrated from `flywheel_gear_toolkit` to `fw_gear`.

* `GearToolkitContext` renamed and replaced by `GearContext`;
config handling is now managed via a new `Config` class.

* Refactored utility methods and decorators under `fw_gear/utils` structure.

* `Metadata` class now validates container types more strictly
and adds metadata size warnings (>16MB).

* New `add_qc_result_to_analysis()` method to attach QC results to analysis containers.

__DEPRECATIONS__:

* Removed `download_project_bids()` and `download_session_bids()`.

* Removed `tempdir` support from `GearContext`.

* Deprecated `datatypes`, `curator`, `reporters`, and `walker` — now moved to
`fw-curation`.
