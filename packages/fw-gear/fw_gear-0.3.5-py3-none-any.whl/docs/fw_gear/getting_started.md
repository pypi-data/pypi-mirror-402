# Getting Started

This guide walks you how to use the [`GearContext`](./reference.md#gearcontext) class.

## Installation

Install fw-gear via pip:

```bash title="Install fw-gear"
pip install fw-gear
```

For SDK-enabled gears that interact with the Flywheel platform:

```bash title="Install with SDK support"
pip install fw-gear[sdk]
```

## Your First Gear

A minimal gear consists of a Python script that uses
[`GearContext`](./reference.md#gearcontext) to access inputs, configuration, and
outputs.

### Basic Example

Create a `run.py` file:

```python title="run.py"
from fw_gear.context import GearContext

def main(context):
    # Get configuration value
    greeting = context.config.opts.get("greeting", "Hello")

    # Get input file path
    input_file = context.config.get_input_path("input_file")

    # Process and write output
    with context.open_output("output.txt", "w") as f:
        f.write(f"{greeting} from {input_file}\n")

if __name__ == "__main__":
    with GearContext() as context:
        context.init_logging()
        context.log_config()
        main(context)
```

### Understanding the Code

#### Initialize GearContext

```python title="Context manager pattern"
with GearContext() as context:
    # Automatically handles initialization and cleanup
    pass
```

#### Configure Logging

```python title="Setup logging"
context.init_logging()  # Sets up logging (INFO or DEBUG based on config)
```

#### Access Configuration

```python title="Read config values"
debug_mode = context.config.opts.get("debug", False)
speed = context.config.opts.get("speed", 1.0)
```

#### Access Input Files

```python title="Read input files"
# Get file path
dicom_path = context.config.get_input_path("dicom")

# Get filename only
filename = context.config.get_input_filename("dicom")

# Open file directly
with context.config.open_input("dicom", "rb") as f:
    data = f.read()
```

#### Write Output Files

```python title="Write outputs"
# Write to output directory
with context.open_output("results.txt", "w") as f:
    f.write("Analysis complete\n")

# Access output directory path
print(f"Outputs saved to: {context.output_dir}")
```

## Common Patterns

### Adding Metadata

```python title="Update metadata"
from fw_gear.context import GearContext

def main(context):
    # Process data...

    # Add QC result to output file
    context.metadata.add_qc_result(
        "output.nii.gz",
        "quality_check",
        "pass",
        snr=42.5,
        motion_mm=0.2
    )

    # Update container metadata
    context.metadata.update_container(
        context.config.destination["type"],
        info={"processing_complete": True}
    )

if __name__ == "__main__":
    with GearContext() as context:
        context.init_logging()
        main(context)
```

### Using the SDK Client

For gears that need to interact with the Flywheel platform:

```python title="SDK-enabled gear"
from fw_gear.context import GearContext

def main(context):
    # Access SDK client (requires api-key input)
    if context.client:
        # Look up a project
        project = context.client.lookup("group/project")

        # Get destination container
        dest = context.config.get_destination()
        print(f"Running on {dest.container_type}: {dest.label}")
    else:
        print("No SDK client available")

if __name__ == "__main__":
    with GearContext() as context:
        context.init_logging()
        main(context)
```

## Next Steps

- **[GearContext Documentation](./context.md)** - Detailed guide to all
  GearContext features
- **[Utils Documentation](./utils.md)** - Helper utilities for common tasks
- **[Specifications](./specs.md)** - Gear manifest and configuration specs
- **[API Reference](./reference.md)** - Complete API documentation
- **[Migration Guide](./migrate-guide/how_to_migrate.md)** - Migrating from
  flywheel-gear-toolkit

## Getting Help

- [fw-gear Documentation](https://flywheel-io.gitlab.io/scientific-solutions/lib/fw-gear/)
- [Open an issue](https://gitlab.com/flywheel-io/scientific-solutions/lib/fw-gear/-/issues)
- [Flywheel Documentation](https://docs.flywheel.io/)
