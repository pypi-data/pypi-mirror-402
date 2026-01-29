<!-- Disable annoying code fencing rule which gets triggered on admonitions -->
<!-- markdownlint-disable MD046 MD007 MD013-->
# Gear Context

The [`GearContext`](./reference.md#gearcontext) class provides an interface for
interacting with gear runtime objects and performing common tasks in the
lifecycle of a gear:

* Provides access to gear runtime objects:
    * `config.json` (runtime configuration with inputs and config values)
    * `manifest.json` (gear metadata and available options)
    * `.metadata.json` (hierarchy metadata to be updated at end of gear run)
* Instantiates an SDK client when an API key input is provided
* Configures gear logging via
  [`init_logging()`](./reference.md#fw_gear.context.GearContext.init_logging)
* Manages output and work directories
* Opens output files for writing

## Structure

The `GearContext` class is composed of three main components:

* **[`Config`](./reference.md#config)**: Parses `config.json` to provide access
  to runtime configuration values and input files. See
  [Accessing Gear Runtime](#accessing-gear-runtime).

* **[`Manifest`](./reference.md#manifest)**: Parses `manifest.json` to provide
  access to gear metadata and available configuration options. See
  [Accessing Gear Metadata](#accessing-gear-metadata).

* **[`Metadata`](./reference.md#metadata)**: Manages `.metadata.json` for
  updating Flywheel hierarchy metadata without requiring SDK authentication. See
  [Writing Outputs](#writing-outputs).

## Basic Usage

Use [`GearContext`](./reference.md#gearcontext) as a context manager to ensure
proper initialization and cleanup of gear resources. A typical gear entrypoint
(`run.py`) follows this pattern:

```python title="run.py"
from fw_gear.context import GearContext
from my_awesome_module import do_something

def main(context):
    do_something(
        dicom=context.config.get_input_path('dicom'),
        output_dir=context.output_dir
    )

if __name__ == "__main__":
    with GearContext() as context:
        context.init_logging()
        main(context)
```

## Accessing Gear Runtime

Access runtime configuration via the `config` attribute, which provides access to
the [`Config`](./reference.md#config) object that parses `config.json`.

```python title="Accessing runtime configuration"
with GearContext() as context:
    # Get input object for named input
    input_obj = context.config.get_input('my-input')

    # Get path to input file
    input_path = context.config.get_input_path('my-input')

    # Get configuration option value
    cfg = context.config.opts['my-config']
```

### Configuration Options

Access configuration options from the `context.config.opts` dictionary:

```python title="Get configuration option"
my_speed = context.config.opts.get("speed")
```

### Inputs

Get the full path to a named input file or open it directly:

```python title="Working with input files"
# Get input file path
dicom_path = context.config.get_input_path("dicom")

# Get input filename
dicom_filename = context.config.get_input_filename("dicom")

# Open input file for reading
with context.config.open_input("dicom", "rb") as dicom_file:
    dicom_data = dicom_file.read()
```

### Destination Container

Access the destination container and its parent:

```python title="Get destination container"
destination = context.config.get_destination()
destination_parent = context.config.get_destination_parent()
```

!!! warning
    Requires at least read-only SDK access. See
    [API key input](./specs.md#api-keys).

### SDK Client

Access the Flywheel SDK Client when an API key input is provided:

```python title="Using SDK client"
project = context.client.lookup("my_group/Project 1")
```

## Accessing Gear Metadata

When `manifest.json` is available at `/flywheel/v0`, access it via the
`manifest` attribute:

```python title="Access manifest properties"
gear_name = context.manifest.name
gear_version = context.manifest.version
```

!!! note
    `manifest.json` is provided at build-time via the Dockerfile, whereas
    `config.json` is provided at run-time by the system. The
    [`GearContext`](./reference.md#gearcontext) looks for the manifest at
    `/flywheel/v0` by convention.

## Writing Outputs

### Output Files

The output directory is available as
[`output_dir`](./reference.md#fw_gear.context.GearContext.output_dir) (defaults
to `/flywheel/v0/output`). Use
[`open_output()`](./reference.md#fw_gear.context.GearContext.open_output) to
write files:

```python title="Writing output files"
# Access output directory path
print(f"Output path: {context.output_dir}")

# Open output file for writing
with context.open_output('out-file.dcm', 'wb') as f:
    f.write(dicom_data)
```

!!! note
    The output directory is cleaned when the context manager exits with an
    exception unless `clean_on_error=False` is set when initializing
    [`GearContext`](./reference.md#gearcontext).

### Metadata

#### Overview

Gears can write metadata to Flywheel containers without SDK authentication using
`.metadata.json`. If this file exists in the output directory, its contents are
uploaded as metadata upon job completion.

This allows updating the destination container and its parent containers without
SDK access. For metadata updates outside this hierarchy, use SDK-enabled methods.

!!! info
    See the [.metadata.json spec](./specs.md#output-metadata) for details.

#### Non-SDK Methods

##### Update Container Metadata

[`update_container()`](./reference.md#fw_gear.metadata.Metadata.update_container)
adds custom metadata to containers within the hierarchy:

**Arguments:**

* `container_type` (str): Container type
* `deep` (bool): If True, recursively update subdictionaries
* `**kwargs` (dict): Metadata fields to update

**Example:**

```python title="Update container metadata"
with fw_gear.GearContext() as context:
    # Update destination container
    info = {"my-metric": "my-value"}
    context.metadata.update_container(context.config.destination.type, info=info)

    # Update parent session
    info = {"my-metric": "my-other-value"}
    context.metadata.update_container("session", label="Session 1", info=info)
```

##### Update File Metadata

[`update_file_metadata()`](./reference.md#fw_gear.metadata.Metadata.update_file_metadata)
adds metadata to input, output, or sibling files:

**Arguments:**

* `file_` (Any): File name (str), SDK file object, or file dict from `config.json`
* `deep` (bool): If True, recursively update subdictionaries
* `container_type` (str, optional): Parent container type
* `**kwargs` (dict): Metadata fields to update

**Example:**

```python title="Update file metadata"
with fw_gear.GearContext() as context:
    context.metadata.update_file_metadata(
        file_="out-file.dcm",  # Must exist in output directory
        container_type="acquisition",
        modality="MR",
        classification={"Measurement": ["T1"]}
    )
```

##### Add QC Result to File

[`add_qc_result()`](./reference.md#fw_gear.metadata.Metadata.add_qc_result)
adds QC results to input, output, or sibling files:

**Arguments:**

* `file_` (Any): File name (str), SDK file object, or file dict from `config.json`
* `name` (str): QC result name
* `state` (str): QC state (`pass`, `fail`, or `na`)
* `**data` (dict): Additional QC data

**Example:**

```python title="Add QC result to file"
with fw_gear.GearContext() as context:
    file_obj = context.config.get_input("input-file")
    context.metadata.add_qc_result(
        file_obj,
        "qc",
        "pass",
        parameter1="value1",
        parameter2="value2"
    )
```

The resulting metadata structure for an acquisition destination:

```json title="Example QC metadata output"
{
    "acquisition": {
        "files": [
            {
                "name": "out_file.dcm",
                "info": {
                    "qc": {
                        "<gear-name>": {
                            "job_info": {
                                "version": "<gear-version>",
                                "job_id": "62bc8cbcd98b86a919d60ead",
                                "inputs": {},
                                "config": {}
                            },
                            "my_qc": {
                                "state": "PASS",
                                "parameter1": "value1",
                                "parameter2": "value2"
                            }
                        }
                    }
                }
            }
        ]
    }
}
```

!!! note
    *`.metadata.json` is cleaned, validated, and written on context exit
    * Long lists in logs are truncated
    *By default, invalid metadata fails the gear. Disable with
      `fail_on_validation=False`
    * `.metadata.json` only updates destination container hierarchy. Use SDK
      methods for other containers

##### Add QC Result to Analysis

[`add_qc_result_to_analysis()`](./reference.md#fw_gear.metadata.Metadata.add_qc_result_to_analysis)
adds QC results to the analysis container:

**Arguments:**

* `name` (str): QC result name
* `state` (str): QC state (`pass`, `fail`, or `na`)
* `**data` (dict): Additional QC data

**Example:**

```python title="Add QC result to analysis"
with fw_gear.GearContext() as context:
    context.metadata.add_qc_result_to_analysis(
        "analysis-qc",
        "pass",
        parameter1="value1",
        parameter2="value2"
    )
```

##### Add File Tags

[`add_file_tags()`](./reference.md#fw_gear.metadata.Metadata.add_file_tags)
adds tags to input, output, or sibling files:

**Arguments:**

* `file_` (Any): File name (str), SDK file object, or file dict from `config.json`
* `tags` (str or Iterable[str]): Tag or list of tags

**Example:**

```python title="Add file tags"
with fw_gear.GearContext() as context:
    file_obj = context.config.get_input("input-file")
    context.metadata.add_file_tags(file_obj, "tag-01")
```

#### SDK-Enabled Methods

##### Modify Container Info

[`modify_container_info()`](./reference.md#fw_gear.metadata.Metadata.modify_container_info)
wraps the `flywheel.modify_container_info()` SDK method. Updates container
metadata using the `set` operation:

**Arguments:**

* `cont_id` (str): Container ID
* `**data` (dict): Metadata fields to update

**Example:**

```python title="Modify container info via SDK"
with fw_gear.GearContext() as context:
    new_info = {
        "infoA": "value1",
        "infoB": "value2"
    }
    context.metadata.modify_container_info("<container-id>", new_info)
```

##### Add QC Result via SDK

[`add_qc_result_via_sdk()`](./reference.md#fw_gear.metadata.Metadata.add_qc_result_via_sdk)
adds QC results to files outside the destination container hierarchy:

**Arguments:**

* `cont_` (Any): Flywheel container object
* `name` (str): QC result name
* `state` (str): QC state (`pass`, `fail`, or `na`)
* `**data` (dict): Additional QC data

**Examples:**

Add QC result to input file that triggered the gear:

```python title="Add QC result to input file via SDK"
with fw_gear.GearContext() as context:
    context.metadata.add_qc_result_via_sdk(
        cont_='input_file.dcm',
        name="input_qc",
        state="PASS",
        data={'my-result': 'test'}
    )
```

Add QC result to specific container:

```python title="Add QC result to container via SDK"
acquisition_cont = client.get_acquisition("<acquisition-id>")

with fw_gear.GearContext() as context:
    context.metadata.add_qc_result_via_sdk(
        cont_=acquisition_cont,
        name="input_qc",
        state="PASS",
        data={'my-result': 'test'}
    )
```

#### Complete Example

Update multiple metadata elements:

```python title="Complete metadata update example"
with fw_gear.GearContext() as context:
    # Update destination container
    info = {"my-metric": "my-value"}
    context.metadata.update_container(context.config.destination.type, info=info)

    # Update output file metadata
    context.metadata.update_file_metadata(
        "out-file.dcm",
        modality="MR",
        classification={"Measurement": ["T1"]}
    )

    # Update parent session
    info = {"my-metric": "my-other-value"}
    context.metadata.update_container("session", label="Session 1", info=info)
```

This produces the following `.metadata.json` (for an analysis gear):

```json title=".metadata.json"
{
    "analysis": {
        "info": {"my-metric": "my-value"},
        "files": [
            {
                "name": "out-file.dcm",
                "modality": "MR",
                "classification": {"Measurement": ["T1"]}
            }
        ]
    },
    "session": {
        "info": {"my-metric": "my-other-value"},
        "label": "Session 1"
    }
}
```

## Logging

Configure logging via
[`init_logging()`](./reference.md#fw_gear.context.GearContext.init_logging).
Sets log level to INFO by default, or DEBUG when a `debug` configuration option
is True:

```python title="Initialize logging"
with GearContext() as context:
    context.init_logging()
```

## SDK Profiling

The [`GearContext`](./reference.md#gearcontext) automatically logs SDK API usage when
`debug` is enabled in `config.json`:

```python title="SDK profiling example"
import logging
log = logging.getLogger(__name__)
from fw_gear.context import GearContext

with GearContext() as context:
    context.init_logging()
    proj = context.client.lookup('<group>/<project.label>')
    log.info(f"Found project: {proj.id}")
```

Output:

```text title="SDK profiling output"
[ 20210701 12:52:06     INFO fw_gear.logging: 219 - configure_logging()  ] Log level is DEBUG
[ 20210701 12:52:07     INFO __main__: 4 - <module>()  ] Found project: 603413543321ab021ef0a0a7
[ 20210701 12:52:07    DEBUG fw_gear.context: 618 - __exit__()  ] SDK usage:
{'GET': {'https://ga.ce.flywheel.io:443/api/version': 1},
'POST': {'https://ga.ce.flywheel.io:443/api/lookup': 1}}
```
