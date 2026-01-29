MAJIS Operations Toolbox
========================

<img src="https://majis-ops.readthedocs.io/en/latest/_images/logo-square.svg" align="right" hspace="50" vspace="50" height="200" alt="Majis operations toolbox logo">

[![Pipeline Status](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/badges/main/pipeline.svg)](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/pipelines/main/latest)
[![Test coverage](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/badges/main/coverage.svg)](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/pipelines/main/latest)
[![Documentation Status](https://readthedocs.org/projects/majis-ops/badge/?version=latest)](https://app.readthedocs.org/projects/majis-ops/builds/?version=latest)
[![Latest release](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/badges/release.svg)](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/releases)


This toolbox aims to collect MAJIS Operations scripts in a common python package.

The full documentation of the package can be found in [majis-ops.readthedocs.io](https://majis-ops.readthedocs.io)

🚀 Installation
---------------
```bash
python -m pip install majis-ops
```

🛰️ Basic examples
-----------------
### 🐍 As python package
- Read a ITL file:
```python
from majis import read_itl

# Load absolute time ITL as EventsDict object
itl_abs = read_itl('absolute_time.itl')

# Load relative time ITL as EventsList object
itl_rel = read_itl('relative_time.itl', refs='events.evf', flat=True)
```
__Note:__ Relative datetime can be provided either with a EVF file or inline with one or multiple strings: `DATETIME  REF_NAME (COUNT = N)`

- Export one (or multiple) ITL blocks:
```python
from majis import save_itl

# Export as absolute ITL
save_itl('output.itl', itl_abs, itl_rel, …)

# Export as relative ITL
save_itl('output.itl', itl_abs, itl_rel, …, ref='DATETIME  REF_NAME (COUNT = N)')

# Export as CSV
save_itl('output.csv', itl_abs, itl_rel, …)

# Export as XLSM timeline w.r.t. C/A reference (based on default template)
save_itl('output.xlsm', itl_abs, ca_ref='DATETIME  REF_CA (COUNT = N)')

# Append to an existing XLSM timeline
save_itl(None, itl_abs, timeline='timeline.xlsm')
```
__Notes:__
- When multiple ITL are provided, they will be concatenate and ordered by date.
- Absolute and relative ITL are compatible.
- Export can be either absolute or relative to a reference.
- Observation block must not overlap.

- Manipulate MAJIS timeline (`.xlsm` file):
```python
>>> from majis import Timeline

>>> timeline = Timeline(timeline='timeline.xlsm')

# Get template version
>>> template.version
<Version('2.0')>

# Get template changelog
>>> template.log
'>>>    2.0 | 2024-06-04 | Vincent Carlier'
'Empty template with 500 lines pre-filled with formulas and data validation format'
'...'
'>>>    1.0 | 2022-11-08 | François Poulet'
'creation'

# Get science changelog
>>> template.science
''  # Empty by default

# Get the number of observations
>>> len(timeline)
10

# Get the list of observations
>>> timeline['OBS_NAME']
['OBS_001', ...]

# Get an observation details
>>> timeline[1]
{'OBS_NAME': 'OBS_001', 'start_angle': 1.5, ...}

# Get an observation property
>>> timeline['start_angle', 1]
1.5

# Append new observations from ITL file
>>> timeline.append('absolute_time.itl')

# Edit a single field
>>> timeline['start_angle', 1] = -1.5
>>> timeline['start_angle', 1]
-1.5

# Save to the same XLSM timeline
>>> timeline.save()

# Create a new timeline from the default template and a relative ITL file
>>> timeline = Timeline('relative_time.itl', refs='events.evf')

# Compute all relative time w.r.t. to a C/A reference
>>> timeline.ca_ref = '2032-09-24T21:33:36 PERIJOVE_12PJ (COUNT = 1)'
>>> timeline['First CU_frame start wrt C/A', 1]
'-001.18:35:25'

# Export the timeline to a new file
>>> timeline.save('new_timeline.xlsm')
```

### 👾 As command line interface
```bash
$ majis-itl --help

usage: majis-itl [-h] [-o output.[itl|csv|xlsm]] [-f]
                 [-t "YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)"]
                 [-r "YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)"]
                 [--timeline timeline.xlsm] [--header "# my-custom-header"]
                 [--overlap] [--csv] [--csv-sep separator]
                 [input.itl ...]

MAJIS ITL toolbox

positional arguments:
  input.itl             Input ITL filename(s). If multiple files are provided
                        they will be concatenated.

options:
  -h, --help            show this help message and exit
  -o output.[itl|csv|xlsm], --output output.[itl|csv|xlsm]
                        Output filename, it could be either ITL, CSV or XLSM.
                        If none provided, the results will be displayed (only
                        for ITL and CSV).
  -f, --force           Overwrite the output file if already exists.
  -t "YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)", --time-ref "YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)"
                        Input events time reference(s). If multiple values are
                        required use an `events.evf` file.
  -r "YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)", --relative-to "YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)"
                        Reference time to be used for relative time output.
  --timeline timeline.xlsm
                        Original timeline to append. If no explicit `--output`
                        is provided new observations will be append in this
                        file.
  --header "# my-custom-header"
                        ITL custom file header.
  --overlap             Allow blocks overlap.
  --csv                 Display the ITL as CSV.
  --csv-sep separator   CSV separator (default: ";")
```

_Examples:_
- Convert a single ITL with relative time as an absolute CSV ITL file:
```bash
majis-itl relative_time.itl --time-ref "2032-09-24T21:33:36 PERIJOVE_12PJ (COUNT = 1)" --output output.csv
```

- Concatenate two ITL with absolute and relative times as an relative ITL file:
```bash
majis-itl absolute_time.itl relative_time.itl --ref-time events.evf --relative-to "2032-09-24T21:33:36 PERIJOVE_12PJ (COUNT = 1)" --output output.itl
```

__Note:__ If no `--output` flag is present, the output is display in the console.

- Create a new MAJIS timeline (`.xlsm`) from a ITL the default template.
```bash
majis-itl absolute_time.itl --output output.xlsm
```

- Edit an existing MAJIS timeline to compute relative time w.r.t. C/A reference.
```bash
majis-itl --timeline timeline.xlsm --relative-to "2032-09-24T21:33:36 PERIJOVE_12PJ (COUNT = 1)"
```

__Note:__ If no `--output` flag is present, the output will be save in the original template.


👐 Contribution
---------------
If you want to contribute to this project, you need to install [`hatch`](https://hatch.pypa.io/latest/install/) on your system, then clone the depot and install de default env:
```bash
git clone https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox.git
cd majis-ops-toolbox

# Install dev dependencies
hatch env create

# Setup pre-commit hook
hatch -e linter run pre-commit install
```

To lint and format the source code:

```bash
hatch -e linter run check
hatch -e linter run format
```

To test the module:
```bash
hatch -e tests run tests
```

To build the docs:
```bash
hatch -e docs run build
```
