# Migration from flywheel-gear-toolkit

## Overview

This document provides a structured guide for migrating from
`flywheel-gear-toolkit` to `fw-gear`, outlining key architectural and
functional changes to ensure a smooth and efficient transition.

## Installation

To remove the deprecated package and install the new package, execute
the following commands:

```sh
pip uninstall `flywheel-gear-toolkit`
pip install `fw-gear`
```

Or, if using `Poetry`, update the dependencies
by removing the old package and adding the new one:

```sh
# Remove flywheel-gear-toolkit
poetry remove flywheel-gear-toolkit

# install a specific version
poetry add fw-gear==<version>

# or

#install the latest version
poetry add fw-gear
```
<!-- markdownlint-disable MD013 MD060 -->

## Feature Comparison

| **Feature**              | `flywheel-gear-toolkit`                                | `fw-gear`                                     |
| ------------------------ | ------------------------------------------------------ | --------------------------------------------- |
| **Module Import**        | `from flywheel_gear_toolkit import GearToolkitContext` | `from fw_gear import GearContext`             |
| **Context Management**   | `with GearToolkitContext() as gear_context:`           | `with GearContext() as gear_context:`         |
| **Accessing `config.json`** | `gear_context.config_json` previously returned the entire `config.json` file as a dictionary. | In the new implementation, `gear_context.config` returns an instance of the `fw_gear.Config` class, which provides structured access to the following properties: <br> - **`opts`**: Job run configuration options <br> - **`job`**: Job-related information (available when `show-job` is set to true) <br> - **`inputs`**: Input files provided during the job run <br> - **`destination`**: Job run destination |
| **Configuration, Input, File, & Destination Handling**       | `GearToolkitContext` directly handles `config.json`, input files, file paths, and destination metadata. This includes the utility functions such as `get_input()`, `get_input_path()`, `get_input_file_object()`, `get_container_from_ref()`, and `get_destination_container()`.| Uses the `fw_gear.Config` class to handle the content of the `config.json`, input and output file information, and container hierarchy, which separating these responsibilities from `GearContext`. Example: `gear_context.config.get_input("input-name")` |
| **Metadata Management**    | Implements a `Metadata` class with methods such as `update_container_metadata()` and `update_file_metadata()` to manage `.metadata.json` | Uses a `Metadata` class that is tightly integrated within `GearContext`, ensuring metadata updates are handled within the execution flow |
| **BIDS Data Handling**     | Provides `download_project_bids()` and `download_session_bids()` (deprecated) for retrieving structured dataset formats | BIDS-specific functionality is no longer supported |

## Examples

### Example 1: Updating Imports and Context Management

**Description:** In `fw-gear`, `GearContext` is used instead of `GearToolkitContext`.

**Previous Code:**

```python
from flywheel_gear_toolkit import GearToolkitContext

with GearToolkitContext() as gear_context:
    gear_context.init_logging()
    code = main(gear_context)
    sys.exit(code)
```

**Updated Code:**

```python
from fw_gear import GearContext

with GearContext() as gear_context:
    gear_context.init_logging()
    code = main(gear_context)
    sys.exit(code)
```

### Example 2: Retrieving input file object from `config.json`

**Description:** To retrieve any information from `config.json`, `.config` should be appended after `gear_context`. Below is a quick example of retrieving the input file information from `config.json`.

**Previous Code:**

```python
input_file_object = gear_context.get_input("input-file")
```

**Updated Code:**

```python
input_file_object = gear_context.config.get_input("input-file")
```

### Example 3: Access gear config.json

**Description:** In `fw-gear`, `gear_context.config` is used to access
the contents of `config.json`. To get the debug value, use
`gear_context.config.opts` instead of
`gear_context.config.get("debug")`.

**Previous Code:**

```python
gear_config_options = gear_context.config

debug = gear_context.config.get("debug")
```

**Updated Code:**

```python
gear_config_options = gear_context.config.opts

debug = gear_context.config.opts.get("debug")
```

### Example 4: Access gear destination

**Description:** To access the destination of the job, use `context.config.destination` instead of `context.destination`.

**Previous Code:**

```python
destination_id = context.destination.get("id", "")
```

**Updated Code:**

```python
destination_id = context.config.destination.get("id", "")
```

### Example 5: Updating File Metadata

**Description:** A new parameter `container_type` has been introduced. The updated implementation retrieves `destination.get("type", "")` from the configuration and passes it as `container_type` when updating file metadata. Additionally, `update_file_metadata()` is now accessed through `context.metadata` instead of `context` directly.

**Previous Code:**

```python
context.update_file_metadata(
    file_="text_abc.txt", deep=True, info={"key1":"value1"}
)
```

**Updated Code:**

Note the new parameter `container_type` and the updated access to `update_file_metadata()`:

```python
dest_type = context.config.destination.get("type", "")
context.metadata.update_file_metadata(
    file_="text_abc.txt",
    deep=True,
    info={"key1":"value1"},
    container_type=dest_type,
)
```
