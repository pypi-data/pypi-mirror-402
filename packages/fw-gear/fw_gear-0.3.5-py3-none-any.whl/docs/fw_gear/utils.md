# Utils Module Documentation

The `fw_gear.utils` module provides utilities for gear execution, SDK operations,
command execution, resource monitoring, and data processing.

## SDK Helpers

The [`fw_gear.utils.sdk_helpers`](./reference.md#sdk-helpers) module provides
utilities for programmatically launching gears via the Flywheel SDK.

### Setup Gear Run

[`setup_gear_run()`](./reference.md#fw_gear.utils.sdk_helpers.setup_gear_run)
prepares gear execution by gathering the gear document and formatting input/config
dictionaries for SDK-based gear launches. Can be used within a gear or externally.

**Parameters:**

* `client` (flywheel.Client): Flywheel SDK client instance
* `gear_name` (str): Name of the gear to run
* `inputs_and_config` (dict): Combined dictionary of gear inputs and configuration

**Returns:**

* `Tuple[GearDocument, dict, dict]`: Gear document, inputs dictionary, config dictionary

**Example - External SDK Launch:**

```python title="Setup gear run via SDK"
import flywheel
import os
from fw_gear.utils.sdk_helpers import setup_gear_run

API_KEY = os.environ.get("FW_API_KEY")
client = flywheel.Client(API_KEY, root=True)

dcm_file = client.get_file("<file-id>")

geardoc, inputs, config = setup_gear_run(
    client,
    "dicom-fixer",
    {
        "dicom": dcm_file,
        "debug": True,
        "tag": "test-run"
    }
)

# Launch gear
parent_container = dcm_file.parent_ref.get("type")
geardoc.run(inputs=inputs, config=config, destination=parent_container)
```

**Example - Within Gear Context:**

```python title="Setup gear run within gear context"
from fw_gear.context import GearContext
from fw_gear.utils.sdk_helpers import setup_gear_run

with GearContext() as context:
    # Get input file from current gear runtime
    input_file_id = context.config.get_input("inputA")["hierarchy"]["id"]
    input_file = context.client.get_file(input_file_id)

    geardoc, inputs, config = setup_gear_run(
        context.client,
        "dicom-fixer",
        {
            "dicom": input_file,
            "debug": True,
            "tag": "test-run"
        }
    )

    # Launch gear
    parent_container = input_file.parent_ref.get("type")
    geardoc.run(inputs=inputs, config=config, destination=parent_container)
```

## Context Utilities

The [`fw_gear.utils.contextutils`](./reference.md#context-utilities) module
provides context managers and decorators for SDK operations, resource monitoring,
and system profiling.

### SDK Retry Handler

[`sdk_post_retry_handler()`](./reference.md#fw_gear.utils.contextutils.sdk_post_retry_handler)
is a context manager that patches the SDK session to retry on specific HTTP errors
(429, 500, 502, 503, 504).

**Safe to use on:**

* Updating container info
* Updating file classification
* Adding notes
* Adding tags

**Not safe to use on:**

* Creating containers
* Uploading files

**Parameters:**

* `client` (flywheel.Client): Flywheel SDK client instance

**Environment Variables:**

* `FLYWHEEL_SDK_BACKOFF_FACTOR`: Backoff factor for retries (default: 0.5)

**Example:**

```python title="SDK retry handler"
from fw_gear.utils.contextutils import sdk_post_retry_handler

with sdk_post_retry_handler(client):
    # Update operations will retry on 429/500/502/503/504 errors
    client.modify_container_info("acquisition_id", {"my-key": "my-value"})
```

### SDK Delete 404 Handler

[`sdk_delete_404_handler()`](./reference.md#fw_gear.utils.contextutils.sdk_delete_404_handler)
is a context manager that ignores 404 errors on delete operations, useful for
retries.

**Parameters:**

* `client` (flywheel.Client): Flywheel SDK client instance

**Example:**

```python title="SDK delete 404 handler"
from fw_gear.utils.contextutils import sdk_delete_404_handler

with sdk_delete_404_handler(client):
    # Delete operations will ignore 404 responses
    client.delete_container("container_id")
```

### Report Open File Descriptors

[`report_open_fds()`](./reference.md#fw_gear.utils.contextutils.report_open_fds)
is a decorator that reports the number of open file descriptors before and after a
function execution.

**Parameters:**

* `sockets_only` (bool): If True, report only sockets; otherwise report all FDs

**Example:**

```python title="Report open file descriptors"
from fw_gear.utils.contextutils import report_open_fds

@report_open_fds(sockets_only=True)
def process_files():
    # Function that opens many files or sockets
    pass
```

### Resource Usage Monitoring

[`report_usage_stats()`](./reference.md#fw_gear.utils.contextutils.report_usage_stats)
is a decorator that monitors and reports resource usage (CPU, memory, disk, network)
during function execution. Generates CSV data and optional plots.

**Parameters:**

* `interval` (float): Update interval in seconds (default: 1.0)
* `save_output` (bool): Save CSV output (default: False)
* `plot` (bool): Generate usage plots (default: True)
* `save_dir` (str): Output directory (default: "/flywheel/v0/output")
* `cpu_usage` (bool): Monitor CPU usage (default: True)
* `disk_usage` (bool): Monitor disk usage (default: True)
* `mem_usage` (bool): Monitor memory usage (default: True)
* `net_usage` (bool): Monitor network usage (default: True)
* `disk_monitor_dirs` (Optional[List[str]]): Directories to monitor (default: ["/"])
* `output_format` (Optional[str]): Plot format (e.g., "png", "pdf")

**Requirements:**

* `psutil` package for CPU/memory/network monitoring
* `pandas` and `matplotlib` for plotting

**Example:**

```python title="Monitor resource usage"
from fw_gear.utils.contextutils import report_usage_stats

@report_usage_stats(
    interval=2.0,
    save_output=True,
    plot=True,
    disk_monitor_dirs=["/", "/tmp"],
    output_format="png"
)
def run_analysis():
    # Long-running analysis function
    pass
```

**Output:**

* CSV file: `{function_name}.csv` with timestamped resource measurements
* Plot file: `{function_name}.png` with resource usage graphs

## Archive/ZIP Management

The [`fw_gear.utils.archive.zip_manager`](./reference.md#archivezip-management)
module provides utilities for working with ZIP archives.

### Unzip Archive

[`unzip_archive()`](./reference.md#fw_gear.utils.archive.zip_manager.unzip_archive)
extracts the contents of a ZIP archive to a specified directory.

**Parameters:**

* `zipfile_path` (str): Absolute path to the ZIP file
* `output_dir` (str): Absolute path to the extraction directory
* `dry_run` (bool): If True, skip extraction (default: False)

**Example:**

```python title="Extract ZIP archive"
from fw_gear.utils.archive.zip_manager import unzip_archive

unzip_archive(
    '/flywheel/v0/input/archive/data.zip',
    '/flywheel/v0/work/'
)
```

### Get Config from ZIP

[`get_config_from_zip()`](./reference.md#fw_gear.utils.archive.zip_manager.get_config_from_zip)
extracts and parses a configuration JSON file from within a ZIP archive.

**Parameters:**

* `zipfile_path` (str): Absolute path to the ZIP file
* `search_str` (str): Regex pattern for config file (default: `r"_config\.json"`)

**Returns:**

* `Optional[dict]`: Configuration dictionary or None if not found

**Example:**

```python title="Extract config from ZIP"
from fw_gear.utils.archive.zip_manager import get_config_from_zip

config = get_config_from_zip('/flywheel/v0/input/archive/data.zip')
if config:
    print(f"Config: {config['config']}")
```

### Zip Output

[`zip_output()`](./reference.md#fw_gear.utils.archive.zip_manager.zip_output)
compresses a directory into a ZIP archive with optional file exclusions.

**Parameters:**

* `root_dir` (str): Root directory to zip relative to
* `source_dir` (str): Subdirectory within root_dir to compress
* `output_zip_filename` (str): Full path of output ZIP archive
* `dry_run` (bool): If True, skip compression (default: False)
* `exclude_files` (Optional[List[str]]): List of file paths to exclude

**Example:**

```python title="Create ZIP archive"
from fw_gear.utils.archive.zip_manager import zip_output

zip_output(
    root_dir='/flywheel/v0/work',
    source_dir='results',
    output_zip_filename='/flywheel/v0/output/results.zip',
    exclude_files=['results/temp.txt', 'results/cache/']
)
```

### Zip Info

[`zip_info()`](./reference.md#fw_gear.utils.archive.zip_manager.zip_info)
retrieves a list of file paths contained in a ZIP archive.

**Parameters:**

* `zipfile_path` (str): Absolute path to the ZIP archive

**Returns:**

* `List[str]`: Sorted list of relative file paths in the archive

**Example:**

```python title="List ZIP contents"
from fw_gear.utils.archive.zip_manager import zip_info

files = zip_info('/flywheel/v0/input/archive/data.zip')
print(f"Archive contains {len(files)} files:")
for file in files:
    print(f"  - {file}")
```

## FreeSurfer License Utilities

The [`fw_gear.utils.licenses.freesurfer`](./reference.md#freesurfer-license)
module provides utilities for installing FreeSurfer license files from multiple
sources.

### Install FreeSurfer License

[`install_freesurfer_license()`](./reference.md#fw_gear.utils.licenses.freesurfer.install_freesurfer_license)
installs the FreeSurfer license file in the expected location. The license is
obtained from one of the following sources (in priority order):

1. Input file (`freesurfer_license_file` in manifest)
2. Config parameter (`freesurfer_license_key`)
3. Flywheel project metadata (`FREESURFER_LICENSE`)

**Parameters:**

* `context` ([`GearContext`](./reference.md#gearcontext)): Gear context with
  configuration and inputs
* `fs_license_path` (Optional[PathLike]): Custom license file path (default: None)

**Raises:**

* `FileNotFoundError`: If license cannot be found

**Example:**

```python title="Install FreeSurfer license"
from fw_gear.context import GearContext
from fw_gear.utils.licenses.freesurfer import install_freesurfer_license

with GearContext() as context:
    # Install license to default location ($FREESURFER_HOME/license.txt)
    install_freesurfer_license(context)

    # Or specify custom location
    install_freesurfer_license(context, '/opt/freesurfer/license.txt')
```

**Manifest Configuration:**

To use input file method, add to your `manifest.json`:

```json title="manifest.json"
{
  "inputs": {
    "freesurfer_license_file": {
      "base": "file",
      "optional": true,
      "description": "FreeSurfer license file"
    }
  },
  "config": {
    "freesurfer_license_key": {
      "type": "string",
      "optional": true,
      "description": "FreeSurfer license key text"
    }
  }
}
```

**Project Metadata Method:**

Add license to project info:

```python title="Add license to project metadata"
# Via SDK
project = client.get_project('project_id')
client.modify_project('project_id', {
    'info': {
        'FREESURFER_LICENSE': 'license text here with spaces'
    }
})
```

### License Source Methods

The module includes helper functions for specific license sources:

[`get_fs_license_path()`](./reference.md#fw_gear.utils.licenses.freesurfer.get_fs_license_path)

Determines the FreeSurfer license file path.

[`find_license_info()`](./reference.md#fw_gear.utils.licenses.freesurfer.find_license_info)

Retrieves license text from available sources.

[`read_input_license()`](./reference.md#fw_gear.utils.licenses.freesurfer.read_input_license)

Reads license from input file.

[`check_project_for_license()`](./reference.md#fw_gear.utils.licenses.freesurfer.check_project_for_license)

Retrieves license from project metadata.

## Command Wrapper

The [`fw_gear.utils.wrapper`](./reference.md#command-wrapper-module) module
provides utilities for executing external commands and integrating with Nipype
workflows.

### Execute Command

[`exec_command()`](./reference.md#fw_gear.utils.wrapper.command.exec_command) runs
external commands with optional live streaming, shell support, and output filtering.
Returns stdout, stderr, and return code.

**Parameters:**

* `command` (List[str]): Command and arguments
* `stream` (bool): Enable live output streaming (default: False)
* `stream_mode` (Optional[str]): Streaming mode - `"all"`, `"filter_only"`, or `"throttled"`
* `throttle_sec` (float): Throttle interval for non-important lines (default: 1.0)
* `logfile` (Optional[str|Path]): Append full output to file
* `shell` (bool): Enable shell parsing and redirects (default: False)
* `environ` (Optional[Dict[str,str]]): Environment variables to merge

**Returns:**

* `Tuple[str, str, int]`: (stdout, stderr, return_code)

**Raises:**

* `RuntimeError`: If command exits with non-zero code

**Key Behavior:**

* When `stream=True`, stderr is merged into stdout to avoid deadlocks
* Shell mode safely quotes arguments except redirection tokens (`>`, `>>`, `2>&1`)
* Stdin is set to DEVNULL to prevent interactive blocking
* Environment variables merge with current process environment

**Example - Basic Execution:**

```python title="Basic command execution"
from fw_gear.utils.wrapper import exec_command

stdout, stderr, rc = exec_command(["du", "-h", "/var/log"])
if rc == 0:
    print(f"Output:\n{stdout}")
```

**Example - Filtered Streaming:**

Stream only important lines while logging all output:

```python title="Stream filtered output"
from fw_gear.utils.wrapper import exec_command

stdout, stderr, rc = exec_command(
    ["my-long-task", "--verbose"],
    stream=True,
    stream_mode="filter_only",
    logfile="task.log"
)
```

**Example - Throttled Streaming:**

Rate-limit non-important output while showing all important lines:

```python title="Throttled streaming"
from fw_gear.utils.wrapper import exec_command

stdout, stderr, rc = exec_command(
    ["trainer", "--epochs", "50"],
    stream=True,
    stream_mode="throttled",
    throttle_sec=2.0
)
```

**Example - Shell Redirects:**

```python title="Shell with redirects"
from fw_gear.utils.wrapper import exec_command

cmd = ["du", "-h", "/var/log", ">>", "du.out.log", "2>&1"]
stdout, stderr, rc = exec_command(cmd, shell=True)
```

**Example - Custom Environment:**

```python title="Custom environment variables"
from fw_gear.utils.wrapper import exec_command

stdout, stderr, rc = exec_command(
    ["bash", "-lc", "echo $MY_FLAG && which python"],
    environ={"MY_FLAG": "1"},
    shell=True
)
```

#### Output Filtering

Customize which output lines are treated as important during streaming by setting
the `EXEC_ALWAYS_PRINT_RE` environment variable.

**Set Before Import:**

```python title="Override filter before import"
import os
os.environ["EXEC_ALWAYS_PRINT_RE"] = r"\b(error|failed|timeout|warn(?:ing)?)\b"

from fw_gear.utils.wrapper import exec_command
```

**Dockerfile:**

```dockerfile title="Dockerfile"
ENV EXEC_ALWAYS_PRINT_RE="\b(error|failed|timeout|warn(?:ing)?)\b"
```

**Override After Import:**

```python title="Override filter after import"
import re
from fw_gear.utils import wrapper

wrapper._ALWAYS_PRINT_RE = re.compile(
    r"\b(error|failed|timeout|warn(?:ing)?)\b",
    re.I
)
```

### Nipype Integration

The [`fw_gear.utils.wrapper.nipype`](./reference.md#nipype-integration) module
provides utilities for integrating Flywheel gears with Nipype workflows.

#### Overview

Generate Nipype interfaces dynamically from Flywheel gear manifests, allowing gears to
be used as Nipype workflow nodes. The interface automatically maps gear inputs and
configuration to Nipype traits.

**Requirements:**

* `nipype` package must be installed

#### GearContextInterface Factory

[`GearContextInterfaceBase.factory()`](./reference.md#fw_gear.utils.wrapper.nipype.GearContextInterfaceBase.factory)
creates a Nipype interface from a gear manifest.

**Parameters:**

* `manifest` (dict): Gear manifest.json as dictionary

**Returns:**

* `type`: Dynamically generated Nipype interface class

**Example:**

```python title="Create Nipype interface from manifest"
from fw_gear.utils.wrapper.nipype import GearContextInterfaceBase
from fw_gear.context import GearContext

with GearContext() as context:
    manifest = context.manifest.to_dict()

    # Create interface class from manifest
    MyGearInterface = GearContextInterfaceBase.factory(manifest)

    # Instantiate and use in Nipype workflow
    interface = MyGearInterface()
    interface.inputs.config_dict = {
        'config': context.config.opts,
        'inputs': context.config.inputs
    }

    # Run interface
    result = interface.run()

    # Access outputs
    print(f"Config value: {result.outputs.config_my_param}")
    print(f"Input file: {result.outputs.inputs_my_input}")
```

#### Complete Nipype Workflow Example

```python title="Nipype workflow with gear interfaces"
from nipype import Workflow, Node
from fw_gear.utils.wrapper.nipype import GearContextInterfaceBase
from fw_gear.context import GearContext

with GearContext() as context:
    # Create workflow
    wf = Workflow(name='my_workflow')

    # Create interface from manifest
    GearInterface = GearContextInterfaceBase.factory(context.manifest.to_dict())

    # Create node
    gear_node = Node(
        GearInterface(),
        name='gear_processing'
    )

    # Set inputs
    gear_node.inputs.config_dict = {
        'config': {
            'param1': 'value1',
            'param2': 42
        },
        'inputs': {
            'input_file': {
                'base': 'file',
                'location': {
                    'path': '/path/to/input.nii.gz'
                }
            }
        }
    }

    # Add to workflow and run
    wf.add_nodes([gear_node])
    wf.run()
```

#### Datatype Mapping

The module maps Flywheel datatypes to Nipype traits:

| Flywheel Type | Nipype Trait     |
|---------------|------------------|
| `boolean`     | `traits.Bool`    |
| `string`      | `traits.Str`     |
| `context`     | `traits.Str`     |
| `integer`     | `traits.Int`     |
| `number`      | `traits.Float`   |
| `array`       | `traits.List`    |
| `file`        | `File`           |

#### Get Traits Object

[`get_traits_object()`](./reference.md#fw_gear.utils.wrapper.nipype.get_traits_object)
maps Flywheel datatype to Nipype trait.

**Parameters:**

* `datatype` (str): Flywheel datatype
* `description` (Optional[str]): Trait description

**Returns:**

* `Union[None, traits.TraitType, File]`: Corresponding Nipype trait

**Example:**

```python title="Map datatype to Nipype trait"
from fw_gear.utils.wrapper.nipype import get_traits_object

# Get trait for boolean
bool_trait = get_traits_object('boolean', 'Enable debug mode')

# Get trait for file
file_trait = get_traits_object('file', 'Input DICOM file')
```

!!! note
    The generated Nipype interfaces are fully serializable and can be used in
    distributed computing environments. The factory automatically handles
    pickling/unpickling of dynamically generated classes.
