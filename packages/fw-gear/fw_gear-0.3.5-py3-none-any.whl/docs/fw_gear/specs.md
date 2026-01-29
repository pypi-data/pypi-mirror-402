<!-- Disable annoying code fencing rule which gets triggered on admonitions -->
<!-- markdownlint-disable MD046 -->
# Flywheel Gear Spec (v0.3.0)

This document defines the required structure and behavior for Flywheel Gears.

## Structure & behavior of a gear

A Flywheel gear is a tar file (.tar) of a container; the container must include a
specific directory that contains two special files.

This tar file can be created from most common container tools (e.g., Docker).

## Minimum container requirements

The only requirement for the underlying container is that it must be a \*nix system that
provides a bash shell on the path.

## The base folder

To be a Flywheel gear, the container in the tar file must include a folder named:
`/flywheel/v0`.

All following references to folders are relative to this folder.

The `/flywheel/v0` folder contains two specific files:

* `manifest.json`   - Describes critical properties of how the gear computes.
* `run` - (Optional) Describes how to execute the algorithm in the gear. Alternately,
  use the manifest `command` key.

The contents of these files are described here.

## The manifest

Here's an example manifest.json that specifies a Flywheel gear which reads one dicom
file as input and specifies one configuration parameter. The keys listed in this example
are all required, unless marked otherwise.

For other restrictions and required fields, you can view our [manifest
schema](manifest.schema.json).

!!! important "Manifest keys have restrictions on length, format, content, etc."

    **Read a human-friendly description of the requirements of the manifest in our
    [property requirements](#manifest-property-requirements) section.**

This document is a [JSON schema](http://json-schema.org), which allows for automatic
validation of structured documents.

Note, the `// comments` shown below are not JSON syntax and cannot be included in a real
manifest file.

```javascript
{
 // Computer-friendly name; unique for your organization
 "name": "example-gear",

 // Human-friendly name; displayed in user interface
 "label": "Example Gear",

 // A brief description of the gear's purpose; ideally 1-4 sentences
 "description": "A gear that performs a task.",

 // Human-friendly version identifier
 "version": "1.0",

 // The author of this gear or algorithm.
 "author":  "Flywheel",

 // (Optional) the maintainer, which may be distinct from the algorithm author.
 // Can be the same as the author field if both roles were filled by the same individual.
 "maintainer":  "Nathaniel Kofalt",

 // (Optional) Any citations you wish to add.
 "cite":  "",

 // Must be an OSI-approved SPDX license string or 'Other'. Ref: https://spdx.org/licenses
 "license": "Apache-2.0",

 // The URL where to go to learn more about the gear. You can leave this blank.
 "url": "http://example.example",

 // Where to go for the source algorithm that the gear is wrapping, if applicable.
 // Just point to the URL value if not applicable.
 "source":  "http://example.example/code",

 // (Optional) Environment variables to set for the gear.
 "environment": {},

 // (Optional) A place for gear authors to put arbitrary information.
 "custom": {},

 // (Optional) Command to execute. Ran inside a bash shell.
 "command": "python script.py"

 // Options that the gear can use
 "config": {

  // A name for this option to show in the user interface
  "speed": {
   "type": "integer",

   // (Optional) json-schema syntax to provide further guidance
   "minimum": 0,
   "maximum": 3,

   "description": "How fast do you want the gear to run? Choose 0-3."
  },

  "coordinates": {
   "type": "array",

    // (Optional) json-schema syntax to provide further guidance on the number of items
    //  in the array
    "minItems": 1,
    "maxItems": 3,

    "items": {
      "type": "number",
    }
   },

   "description": "A set of 3D coordinates."
  },
 },

 // Inputs that the gear consumes
 "inputs": {

  // A label - describes one of the inputs. Used by the user interface and by the run script.
  "dicom": {

   // Specifies that the input is a single file. For now, it's the only type.
   "base": "file",

   // (Optional) json-schema syntax to provide further guidance
   "type": { "enum": [ "dicom" ] },

   "description": "Any dicom file."
  },

  // A contextual key-value, provided by the environment. Used for values that are
  // generally the same for an entire project. Not guaranteed to be found - the gear
  // should decide if it can continue to run, or exit with an error.
  "matlab_license_code": {
   "base": "context",
  },

  // An API key, specific to this job, with the same access as the user that launched
  // the gear. Useful for aggregations, integrating with an external system, data
  // analysis, or other automated tasks.
  "key": {
   "base": "api-key",

   // (Optional) request that the API key only be allowed read access.
   "read-only": true
  }
 },
 // A configuration for outputs
  "output_configuration": {
   // (Optional) Force fileversion match when engine is modifying a file
   // If a newer version of file is uploaded while job is running and this is set to true,
   // job can't modify that file
   "enforce_file_version_match": true
 },

 // Capabilities the gear requires. Not necessary unless you need a specific feature.
 "capabilities": [
  "networking"
 ],
}
```

### Manifest inputs

Each key of `inputs` specifies an input to the gear.

At this point, the inputs are always files and the `"base": "file"` is part of the
specification.

Further constraints are an advanced feature, so feel free to leave this off until you
want to pursue it. When present, they will be used to guide the user to give them hints
as to which files are probably the right choice. In the example above, we add a
constraint describing the `type` of file. File types will be matched against our [file
data
model](https://docs.flywheel.io/user/upload/user_file_types_in_flywheel/#file-types).

The example has named one input, called "dicom", and requests that the file's type be
dicom.

!!! warning "Input key naming"

    The property names under "inputs" should be simple identifiers without dots (.),
    spaces, or slashes (/). Dots can interfere with dot‑notation used in the UI and
    examples (e.g., inputs.dicom.path) and may lead to rendering or binding issues.
    Recommended pattern: ^[A-Za-z0-9_-]+$

### Manifest configuration

Each key of `config` specifies a configuration option.

Like the inputs, you can add JSON schema constraints as desired. Please specify a `type`
on each key. Please only use non-object types: `string`, `integer`, `number`, `boolean`,
`array`.

The example has named one config option, called `speed`, which must be an integer
between zero and three, and another called "coordinates", which must be a set of three
floats.

In some cases, a configuration option may not have a safe default, and it only makes
sense to sometimes omit it entirely. If that is the case, specify `"optional": true` on
that config key.

Here are some examples of valid configuration options:

```json
"config": {
    "an_optional_bool": {
      "description": "Bool value",
      "type": "boolean",
      "optional": true
    },
    "an_optional_string": {
      "description": "String value",
      "type": "string",
      "optional": true
    },
    "an_optional_number": {
      "description": "Number value",
      "type": "number",
      "optional": true
    },
    "a_required_string_array": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["val1", "val2", "val3"]
      },
      "description": "An array",
      "default": ["val1", "val2"],
      "minItems": 1,
      "maxItems": 3,
      "optional": false
    },
    "a_required_number_array": {
      "type": "array",
      "items": {
        "type": "number"
      },
      "description": "An array",
      "optional": false
    }
  }
```

### Contextual values

Context inputs are values that are generally provided by the environment, rather than
the human or process running the gear. These are generally values that are incidentally
required rather than directly a part of the algorithm - for example, a license key.

It is up to the gear executor to decide how (and if) context is provided. In the
Flywheel system, the values can be provided by setting a `context.key-name` value on a
container's metadata. For example, you could set `context.matlab_license_code: "AEX"` on
the project, and then any gear running in that project with a context input called
`matlab_license_code` would receive the value.

Unlike a gear's config values, contexts are not guaranteed to exist _or_ have a specific
type or format. It is up to the gear to decide if it can continue, or exit with an
error, when a context value does not match what the gear expects. In the example config
file below, note that the `found` key can be checked to determine if a value was
provided by the environment.

Because context values are not namespaced, it is suggested that you use a specific and
descriptive name. The `matlab_license_code` example is a good, self-explanatory key that
many gears could likely reuse.

### API keys

It is possible for gear code to interact with the Flywheel data hierarchy using an API
key and the [Flywheel
SDK](https://flywheel-io.gitlab.io/product/backend/sdk/branches/master/python/index.html).

Generally, you will want to figure out a script that you like, using your normal user
API key, before turning it into a gear. To do this, specify an `api-key` type input as
show in the example above, and use that value in your gear script.

The key provided will be a special key that has the same access as the running user (not
necessarily the gear author), and only work while the job is running. After the job
completes, the key is retired. This has write access by default, but you can make it
read only by adding `"read-only": true` to the manifest as shown above.

### The input folder

When a gear is executed, an `input` folder will be created relative to the base folder.
If a gear has anything previously existing in the `input` folder it will be removed at
launch time.

In this example, the input is called "dicom", and so will be in a folder inside `input`
called `dicom`. The full path would be, for example:
`/flywheel/v0/input/dicom/my-data.dcm`.

### The input configuration

Inside the `/flywheel/v0` folder a `config.json` file will be provided with any settings
the user has provided, and information about provided files. For example, if your gear
uses the example manifest above, you'd get a file like the following:

```javascript
{
 "config": {
  "speed": 2,
  "coordinates": [1, 2, 3]
 },
 "inputs" : {
  "dicom" : {
   "base" : "file",
   "hierarchy" : {
    "type" : "acquisition",
    "id" : "5988d38b3b49ee001bde0853"
   },
   "location" : {
    "path" : "/flywheel/v0/input/dicom/example.dcm",
    "name" : "example.dcm"
   },
   "object" : {
    "info" : {},
    "mimetype" : "application/octet-stream",
    "tags" : [],
    "measurements" : [],
    "type" : "dicom",
    "modality" : null,
    "size" : 2913379
   }
  },

  "matlab_license_code": {
   "base": "context",
   "found": true,
   "value": "ABC"
  }
 }
}
```

Each configuration key will have been checked server-side against any constraints you
specified, so you can be assured that your gear will be provided valid values.

The `inputs` key will hold useful information about the files. For example, you can use
`inputs.dicom.path` to get the full path to the provided file. Also provided will be the
location of the input in the hierarchy (if applicable) and any scientific information
and metadata known at the time of the job creation. This `inputs` key will currently
only be present when running on the Flywheel system.

### The output folder

When a gear is executed, an `output` folder will be created relative to the base folder.
If a gear has anything previously existing in the `output` folder it will be removed at
launch time.

The gear should place any files that it wants saved into the `output` folder - and only
those files. Anything in the `output` folder when the gear is complete will be saved as
a result.

**Note** There is a maximum limit of 100 files saved, and if the gear produces more than
100, users will receive a warning message to the log that output number was truncated to
100 and that this job will fail in a future version (19.0).

If you don’t want results saved, it’s okay to leave this folder empty.

Do not remove the `output` folder.

### Output metadata

Optionally, a gear can provide metadata about the files it produces. This is
communicated via creating a `.metadata.json` file in the output folder.

```javascript
{
 "acquisition": {
  "files": [
   {
    "name": "example.nii.gz",
    "type": "nifti",
    "instrument": "mri",
    "info": {
     "value1": "foo",
     "value2": "bar"
    }
   }
  ]
 }
}
```

If you are familiar with [JSON schema](http://json-schema.org) you can look at our
[metadata
schema](https://github.com/scitran/core/blob/master/swagger/schemas/input/enginemetadata.json)
and our related [file
schema](https://github.com/scitran/core/blob/master/swagger/schemas/input/file.json). In
this example, the file `example.nii.gz` (which must exist in the output folder) is
specified as being a nifti file from an MRI machine, with a few custom key/value pairs.

If you are curious about the typical file types, [this is a list of
them](https://github.com/scitran/core/blob/d4da9eb299db9a7c6c27bdee1032d36db7cef919/api/files.py#L245-L269)
. You can also set metadata on the acquisition itself or its parent containers, though
these features are less-used; see the metadata schema for more details.

As you might expect, gears cannot produce "normal" files called `.metadata.json`, and
might cause the gear to fail if the file is improperly formed.

### Manifest property requirements

* `author` - A string up to 100 characters identifying the gear's author. Can contain
  any characters.

* `capabilities` - An array of strings. No restrictions on string values. Example:
  ["networking"]

* `cite` - (Optional) A string up to 5000 characters containing relevant citations. Can
  contain any characters.

* `command` - A string specifying the starting command for the gear. Can contain any
  characters, no length restriction.

* `config` - An object that defines the type and limits of the gear's configuration
parameters. Each property must have a "type" field with one of these values: "string",
"integer", "number", "boolean", "array". Cannot include both "default" and "optional"
fields on the same property. For example, to define a config option named "speed" that
can be a number between 0 and 3, inclusive:

  ```json
  {
    "config": {
      "speed": {
        "type": "integer",
        "minimum": 0,
        "maximum": 3
      }
    }
  }
  ```

* `custom` - An arbitrary object for gear authors to store additional information. No
  restrictions on structure or content.

* `description` - A string up to 5000 characters describing the gear's purpose (ideally
  1-4 sentences). Can contain any characters.

* `environment` - Optional environment variables to set when the gear runs. An object
where keys and values must be strings. Values can contain any characters. Example:

  ```json
  {
    "environment": {
      "PATH": "/usr/local/bin:/usr/bin:/bin",
      "LD_LIBRARY_PATH": "/usr/local/lib"
    }
  }
  ```

* `inputs` - An object describing inputs. Each input must have a `base` property with
  one of these values:

  * `file` - For file inputs. Additional properties allowed via schema directives
  * `api-key` - For API key access. Additional property allowed: "read-only" (boolean)
  * `context` - For contextual values. No additional properties allowed. "context" is
      provided to the gear automatically at gear launch and should not be used by gear
      authors.

* `label` - A human-friendly string name up to 100 characters. Can contain any
  characters.

* `license` - Must be an OSI-approved SPDX license string from the enumerated list in
  [schema](https://gitlab.com/flywheel-io/public/gears/-/blob/master/spec/manifest.schema.json#L179)
  or 'Other'.  See <https://spdx.org/licenses/> for more info.  Valid values are the
  name given in the "Identifier" column. Examples: "Apache-2.0", "MIT", "GPL-3.0",
  "Other"

* `maintainer` - (Optional) A string up to 100 characters identifying the gear's
  maintainer. Can contain any characters.

* `name` - A computer-friendly name; unique for your organization, that must be a string
  with these requirements:

  * Maximum length: 100 characters
  * Must match regex pattern: ^[a-z0-9\-]+$
  * Can only contain lowercase letters, numbers, and hyphens

* `output_configuration` - A configuration object for outputs consisting of a single
  option with a boolean value:

  * `enforce_file_version_match` - Boolean value (default: false)

* `source` - Must be either:

  * A valid URI up to 1000 characters
  * An empty string

* `url` - Must be either:

  * A valid URI up to 1000 characters
  * An empty string

* `version` - A string up to 100 characters. Can contain any characters.

## The run target and environment

By default, the gear is invoked by running is `/flywheel/v0/run`. The file must be
executable (`chmod +x run`). It can be a bash or a Python script, or any other
executable. If it is a script, please make sure to include appropriate shebang (`#!`)
leading line.

You can change this by setting the `command` key of the manifest.

Your run script is the only entry point used for the gear and must accomplish everything
the gear sets out to do. On success, exit zero. If the algorithm encounters a failure,
exit non-zero. Ideally, print something out before exiting non-zero, so that your users
can check the logs to see why things did not work.

### The environment for the run script

An important consideration is the environment where the `run` command is executed. The
command will be executed in the folder containing it (`/flywheel/v0`), and with no
environment variables save the `PATH`:

```bash
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

Any required environment and path variables should be specified within the script. This
can be important if, for example, you're producing a gear from a Dockerfile, as the
variables there will not transfer over. We typically specify the path and environment
variables in a `.bashrc` file, and source that file at the beginning of the `run`
script.

The file is also executed with no arguments. You must specify the inputs to the
executables in the `run` script, such as the input file names or flags.

### Capabilities

Capabilities allow for a gear to require certain environmental feature support.

Currently, the only capability available is `networking`, which requires basic outbound
networking as described below. In the future, there will likely be more added: `cuda`,
`hpc`, etc.

Do not add speculative capabilities to your manifest. Executors that do not recognize or
cannot provide a specified capability are forbidden from launching the job.

### Networking

Some gears may require outbound networking (to contact the Flywheel API, or for some
other purpose). If your gear needs this, please add the `networking` capability to your
manifest as shown in the example above.

For now, all gears are provided some networking, but this is not guaranteed, and may
vary depending on your installation's setup. Adding the capability will future-proof
your gear as it is likely this will be changed in the future.

Be sure to get in touch with us regarding your networking needs - Matlab license checks,
for example.

There are no plans to allow inbound networking.

### Custom information

There is a final manifest key, `custom`, that is entirely freeform. If you have
additional information you'd like to record about your gear - possibly as a result of
some toolchain or wrapper - this is a great place to put it.

An example:

```javascript
{
    "name": "gear-with-custom-info",

    // ...

    "custom": {
      "generator": {
        "generated-via": "antlr",
        "credit": "Terence Parr",
        "version": 4
      }
    }
```

In general, try to place your information under a single, top-level key, as in the
example above.

#### Reserved custom keys

We use some custom keys for notekeeping, or to enable features that might change in the
future. In this way, we can offer functionality without the more onerous process of
standardizing it & supporting in perpetuity.

The 2 reserved namespaces are `flywheel` and `gear-builder`. Here's a full list:

* `custom`
  * `flywheel`
    * `module`: Requests a specific module to execute this gear. Currently only `runc`
      is respected; all other values are ignored.
    * `suite`: This identifies a gear as part of a larger suite of tools.
    * `classification`: This is used to classify the gear for the purpose of grouping
      gears in the gear-exchange portal.
    * `show-job`: If set to `true`, the job ID is exposed in the config.json under
      job.id.
    * `private`: If set to `true`, the gear docker image is not pushed to the Flywheel
      public registry and can only be installed by a Flywheel employee that has access
      to the docker image in the private registry.
  * `gear-builder`
    * `image`: The docker image to use as a base for the gear builder, if applicable.
    * `container`: The docker container to use as a base for the gear builder, if
      applicable.

Example:

```javascript
{
 "name": "gear-with-custom-info",

 // ...

 "custom": {

  // flyhweel namespace where additional key/value can be stored
  "flywheel": {

   // If set to true, the job ID is defined in the config.json under job.id
   "show-job": true,

   // The suite the gear belong to (used in the gear selection UI and gear-exchange portal)
   "suite": "Utility",

   // The classification of the gear (used in the gear-exchange portal)
   "classification": {

    // Categories for the gear (see below for possible values)
        "species": [
          "Human",
        ],
        "organ": [
          "Brain"
        ],
        "therapeutic_area": [
          "Neurology"
        ],
        "function": [
          "Image Processing - Structural"
        ],
        // Based on the DICOM Modality (0008,0060) tag
        "modality": [
          "MR"
        ],
      }
   },
   "gear-builder": {
     "image": "flywheel/mygear:0.1.0"
   }
  }
 }
```

#### Flywheel gear classification

To categorize gear in the UI and on the [gear
exchange](https://flywheel.io/gear-exchange/#library), gears get classified from their
`suite` and `classification` keys. The `suite` key can take any arbitrary value, but the
`classification` key is restricted to a set of predefined categories as defined in the
[manifest schema](manifest.schema.json).

For standardization purposes, gears develop by Flywheel will use one of the following
value for `suite`:

* Conversion
* Curation
* Quality Assurance
* Utility
* Export
* Report
* Image Processing
* Other

The `classification` key is an object that must match the schema defined in the
[manifest schema](manifest.schema.json). In a human-friendly format, it looks like this:

* `species`:

  * Animal
  * Human
  * Phantom
  * Other
  * Any

* `organ`:

  * Adrenal
  * Anus
  * Appendix
  * Biliary Tree
  * Bladder
  * Bone Marrow
  * Brain
  * Breast
  * Esophagus
  * Eyes
  * Gallbladder
  * Heart
  * Kidney
  * Large Bowel
  * Liver
  * Lung
  * Ovary
  * Pancreas
  * Prostate
  * Rectum
  * Salivary Glands
  * Skin
  * Small Bowel
  * Spleen
  * Stomach
  * Thyroid
  * Uterus
  * Multiple
  * Other
  * Any

* `function`:

  * Conversion
  * Curation
  * Quality Assurance
  * Utility
  * Export
  * Report
  * Image Processing - Cardiac
  * Image Processing - Diffusion
  * Image Processing - Digital Pathology
  * Image Processing - Functional
  * Image Processing - Musculoskeletal
  * Image Processing - Other
  * Image Processing - Perfusion
  * Image Processing - Segmentation
  * Image Processing - Spectroscopy
  * Image Processing - Structural
  * Other

* `modality`:

  * AR
  * AS
  * ASMT
  * AU
  * BDUS
  * BI
  * BMD
  * CD
  * CF
  * CP
  * CR
  * CS
  * CT
  * DD
  * DF
  * DG
  * DM
  * DOC
  * DS
  * DX
  * EC
  * ECG
  * EEG
  * EPS
  * ES
  * FID
  * FP
  * FS
  * GM
  * HD
  * KO
  * LEN
  * LP
  * LS
  * MA
  * MEG
  * MG
  * MR
  * MS
  * NIRS
  * NM
  * OAM
  * OCT
  * OT
  * PT
  * PR
  * PX
  * REG
  * RESP
  * RF
  * RG
  * RTDOSE
  * RTIMAGE
  * RTPLAN
  * RTRECORD
  * RTSTRUCT
  * RWV
  * SC
  * SEG
  * SM
  * SMR
  * SR
  * SRF
  * ST
  * STAIN
  * TG
  * US
  * VA
  * VF
  * XA
  * XC
  * Any
  * Other

* `therapeutic_area`:

  * Cardiology/Vascular Disease
  * Dental and Oral Health
  * Dermatology
  * Devices
  * Endocrinology
  * Family Medicine
  * Gastroenterology
  * Gene Therapy
  * Genetic Disease
  * Hematology
  * Hepatology
  * Immunology
  * Infectious Disease
  * Internal Medicine
  * Musculoskeletal
  * Nephrology
  * Neurology
  * Nutrition and Weight Loss
  * Obstetrics & Gynecology
  * Oncology
  * Ophthalmology
  * Orthopedics
  * Otolaryngology
  * Pediatrics & Neonatology
  * Pharmacology & Toxicology
  * Plastic Surgery
  * Podiatry
  * Psychiatry/Psychology
  * Pulmonary/Respiratory Disease
  * Rheumatology
  * Sleep Medicine
  * Trauma
  * Urology
  * Multiple
  * Other
  * Any
