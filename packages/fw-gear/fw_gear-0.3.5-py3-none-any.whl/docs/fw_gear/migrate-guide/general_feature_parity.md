<!-- markdownlint-disable MD013 -->
# Feature Parity Matrix: `flywheel-gear-toolkit` vs. `fw-gear`

## 1. Overview

This document compares key features across five major components between
**flywheel-gear-toolkit** and **fw-gear**. The goal is to assess **feature parity**,
highlight any changes, and identify any known limitations.

---

## 2. Feature Parity Table

| **Feature Category** | **flywheel-gear-toolkit (Legacy)** | **fw-gear (Current)** | **Status** | **Notes / Limitations** |
| ---------------------- | ---------------------------------- | ---------------------- | ----------- | ---------------------- |
| **Context Management** | `GearToolkitContext` provides an all-in-one class for managing config, manifest, and metadata | `GearContext` is used, but configuration handling is offloaded to `Config` | ⚠️ Updated | Context management exists, but now follows a modular approach |
| **Configuration Handling** | `GearToolkitContext` directly manages `config.json` | `Config` class now encapsulates configuration parsing, input management, and destination handling | ✅ Same, but modularized | Configuration handling is now in a dedicated class (`Config`) |
| **Logging Setup** | `init_logging()` method applies `_recursive_update()` to configure logs dynamically | Uses `configure_logging()`, directly referencing manifest values | ✅ Same | No major differences |
| **Flywheel SDK Client Handling** | Managed within `GearToolkitContext` | Now handled within `Config` | ✅ Same, but refactored | SDK initialization logic moved inside `Config` |
| **Metadata Management** | `Metadata` class is used for `.metadata.json` handling | `Metadata` class remains, but methods are now accessed within `GearContext` | ✅ Same | No major differences |
| **Input & File Handling** | Methods like `get_input()`, `get_input_path()`, `open_input()` exist within `GearToolkitContext` | Moved to `Config` for better modularity | ✅ Same, but modularized | Input file handling is now part of `Config` |
| **File Object Representation** | `File` class used for representing Flywheel files | `File` class remains, but `fw_type` replaces `type` | ⚠️ Modified | `fw_type` replaces `type`, which may require minor updates in some cases |
| **Manifest Management** | `manifest.json` is read directly in `GearToolkitContext` | Dedicated `Manifest` class now handles parsing and validation | ✅ Same, but modularized | Manifest parsing is now separate from the context |
| **Destination Container & Hierarchy** | `get_container_from_ref()`, `get_destination_container()`, `get_parent()` | Now handled within `Config` | ✅ Same, but modularized | Destination management is now part of `Config` |
| **BIDS Data Handling** | `download_project_bids()`, `download_session_bids()` (deprecated) | No BIDS-specific methods | ❌ Removed | BIDS download functions now supported in a separate, BIDS suite |
| **Logging Configuration** | Reads `log_config` from `manifest.json` | Retrieves log settings from `manifest.get_value("custom")` | ✅ Same | No major differences |
| **Deprecation Warnings** | `deprecated()` decorator warns about deprecated functions | No explicit deprecation warnings; removed in favor of restructuring | ⚠️ Modified | Deprecated functions removed; restructuring replaces them |
| **Error Handling** | Uses `try/except` with broad exception handling | Introduces `GearContextError` for structured error handling | ✅ Same, but improved | Better error management with `GearContextError` |
| **Output Directory Management** | `_clean_output()` cleans directories on errors | `_clean_output()` still exists, with improved logging | ✅ Same | Minor improvements in logging |

---

## 3. Key Changes

## ⚠️ Breaking Changes

- **Renamed Context Class:**
  `GearToolkitContext` has been renamed to `GearContext` in `fw_gear`, requiring updates to imports and usage.

- **New `Config` Class for Managing `config.json`:**
  Previously, configuration data was handled as a dictionary in `flywheel_gear_toolkit`. Now, the `fw_gear` package includes a dedicated `Config` class, providing a structured approach to managing `config.json`.

- **Methods Moved from `GearToolkitContext` to `Config`:**
  The following methods have been moved from `GearToolkitContext` to the `Config` class in `fw_gear`. They should now be accessed as `gear_context.config.<method>` instead of `gear_toolkit_context.<method>`:

  - `get_input()`
  - `get_input_path()`
  - `get_input_filename()`
  - `get_input_file_object()`
  - `get_input_file_object_value()`
  - `get_destination_container()`
  - `get_destination_parent()`
  - `open_input()`

- **Changes in the `Metadata` Class:**
  - **Modified Methods:**
    - `update_container()` and `update_file_metadata()` now enforce validation to ensure only valid Flywheel container types are provided.
    - `clean()` now includes a metadata size check and issues a warning if the size exceeds **16MB**.

  - **New Method:**
    - `add_qc_result_to_analysis()` allows users to add QC results directly to the **analysis** container via `.metadata.json`.

- **Module Reorganizations and Renames:**
  - `flywheel_gear_toolkit.utils.zip_tools` has been **renamed** and **reorganized** into `fw_gear.utils.archive.zip_manager`.
  - Methods previously found in `flywheel_gear_toolkit.utils.decorators` are now located in `fw_gear.utils.contextutils`.
  - `sdk_post_retry_handler()` and `sdk_delete_404_handler()`, originally in `flywheel_gear_toolkit.utils`, have been moved to `fw_gear.utils.contextutils`.
  - `flywheel_gear_toolkit.licenses.freesurfer` has been moved to `fw_gear.utils.licenses.freesurfer`.
  - `get_parent()` and `get_container_from_ref()`, which were originally in `flywheel_gear_toolkit.GearContext`, are now located in `fw_gear.utils.sdk_helpers`.
  - The `flywheel_gear_toolkit.interfaces` package, which contained `flywheel_gear_toolkit.interfaces.command_line` and `flywheel_gear_toolkit.interfaces.nipype`, has been moved to:
    - `fw_gear.utils.wrapper.command` (previously `command_line`).
    - `fw_gear.utils.wrapper.nipype` (previously `nipype`).

---

## ✅ Enhancements

- **Improved Flywheel SDK Handling:**
  - `get_client()` now raises `GearContextError` if the Flywheel SDK is
    missing or the API key is invalid.
- **New Method:**
  - Added `is_fw_context()` method in the `GearContext` class to check
    if it is running in a Flywheel Gear environment.
  - Added `setup_gear_run()` under `fw_gear.utils.sdk_helpers`, which
    gathers necessary information for running the specified gear with
    the provided gear inputs and configuration.

---

## ❌ Removals

- **BIDS-related Methods:**
  - `download_project_bids()` and `download_session_bids()` have been
    removed from `GearToolkitContext`.
  - BIDS-related utilities will be available in a newly restructure bids-client library (repo TBD).

- **Temporary Directory (`tempdir`):**
  - The `tempdir` feature has been removed from `GearContext`.
  - It was originally meant for testing purposes. However, its usage has
    been deprecated and no longer serves its intended purposes.

- **Removed `datatypes` Submodule:**
  - The `datatypes` submodule under `flywheel_gear_toolkit.utils` has been removed.

- **Curator and Reporters Migration:**
  - The `curator`, `reporters`, and `walker` submodules from `flywheel_gear_toolkit.utils` have been moved to a separate Python package named `fw-curation`.

---

## 4. Known Limitations

| **Limitation** | **Impact** |
| --------------- | ------------ |
| No BIDS Support | Refer to the BIDS App Toolkit or Template for updated handling of BIDS dataset workflows. |
| File Object Changes | The change from `type` to `fw_type` in the `File` class may require minor updates in existing codebases. |
| More Explicit Error Handling | While beneficial, developers may need to update their error handling logic to accommodate `GearContextError`. |

---

## 5. Summary

The `fw-gear` package introduces **better modularization, improved error handling, and structured configuration management**. While most functionalities remain **unchanged or improved**, some legacy features such as **BIDS support** and **deprecated functions** have been removed.

This feature parity matrix provides a reference for tracking changes between the two packages.

---
