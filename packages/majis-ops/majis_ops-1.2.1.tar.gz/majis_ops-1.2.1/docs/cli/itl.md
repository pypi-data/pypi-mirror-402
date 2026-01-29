MAJIS Command Line Interfaces
=============================

You can use the MAJIS operations toolbox directly in the terminal with a few command line interfaces:
- [`majis-itl`](majis-itl)

:::{Note}
More interface will be added in the future
:::

(majis-itl)=
ITL interface
-------------

```bash
majis-itl --help
```
```text
usage: majis-itl [-h] [-o output.[itl|json|csv|xlsm]] [-f]
                 [-t "YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)"]
                 [-r "YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)"]
                 [--timeline timeline.xlsm] [--header "# my-custom-header"]
                 [--overlap] [--json] [--csv] [--csv-sep separator]
                 [input.[itl|json] ...]

MAJIS ITL toolbox

positional arguments:
  input.[itl|json]      Input ITL filename(s). If multiple files are provided
                        they will be concatenated.

options:
  -h, --help            show this help message and exit
  -o output.[itl|json|csv|xlsm], --output output.[itl|json|csv|xlsm]
                        Output filename, it could be either ITL, JSON, CSV or
                        XLSM. If none provided, the results will be displayed
                        (only for ITL, JSON and CSV).
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
  --json                Display the ITL as JSON.
  --csv                 Display the ITL as CSV.
  --csv-sep separator   CSV separator (default: ";")
```

Examples
--------
Convert a single ITL with relative time as an absolute CSV ITL file:
```bash
majis-itl relative_time.itl --time-ref "2032-09-24T21:33:36 PERIJOVE_12PJ (COUNT = 1)" --output output.csv
```

Concatenate two ITL with absolute and relative times as an relative ITL file:
```bash
majis-itl absolute_time.itl relative_time.itl --ref-time events.evf --relative-to "2032-09-24T21:33:36 PERIJOVE_12PJ (COUNT = 1)" --output output.itl
```

If no `--output` flag is present, the output is display in the console:
```bash
majis-itl ITL_absolute_time.json
```
```text
# MAJIS - OBS_KEY=MAJ_JUP_DISK_SCAN OBS_NAME=MAJ_JUP_DISK_SCAN_001 TYPE=OBSERVATION
# MAJIS - OBSERVATION_TYPE=PRIME TARGET=JUPITER SCENARIO=S007_01 CU_TREP=500 CU_FRAME=300
# MAJIS - BINNING=1 PPE=400 START_ROW_VIS=100 MIRROR_FLAG=ENABLE START_ANGLE=-1.31051
# MAJIS - STOP_ANGLE=0.10202 SYNCHRONOUS=0 START_SCAN_SPEED=0.0022421078
# MAJIS - STOP_SCAN_SPEED=0.0022421078
# MAJIS - COMMENT: This comment will be included in the exported ITL file.
2032-09-23T05:15:45.000Z  MAJIS  OBS_START  MAJ_JUP_DISK_SCAN (PRIME=TRUE)
2032-09-23T05:26:15.000Z  MAJIS  OBS_END    MAJ_JUP_DISK_SCAN

# MAJIS - OBS_KEY=MAJ_JUP_DISK_SCAN OBS_NAME=MAJ_JUP_DISK_SCAN_002 TYPE=OBSERVATION
# MAJIS - OBSERVATION_TYPE=PRIME TARGET=JUPITER SCENARIO=S007_01 CU_TREP=2100 CU_FRAME=300
# MAJIS - BINNING=2 PPE=400 START_ROW_VIS=372 MIRROR_FLAG=ENABLE START_ANGLE=1.32935
# MAJIS - STOP_ANGLE=-0.08318 SYNCHRONOUS=3 START_SCAN_SPEED=-0.0022421078
# MAJIS - STOP_SCAN_SPEED=-0.0022421078
2032-09-23T06:09:45.000Z  MAJIS  OBS_START  MAJ_JUP_DISK_SCAN (PRIME=TRUE)
2032-09-23T06:20:15.000Z  MAJIS  OBS_END    MAJ_JUP_DISK_SCAN
```

The output format can be selected with different flags:
```bash
majis-itl absolute_time.itl --json
```
```json
{
  "header": {
    "filename": "ITL_.json",
    "creation_date": "2025-10-28T18:46:00.122Z",
    "author": "username"
  },
  "timeline": [
    {
      "name": "MAJ_JUP_DISK_SCAN",
      "unique_id": "MAJ_JUP_DISK_SCAN_001",
      "instrument": "MAJIS",
      "type": "OBSERVATION",
      "observation_type": "PRIME",
      "target": "JUPITER",
      "start_time": "2032-09-23T05:15:45.000Z",
      "end_time": "2032-09-23T05:26:15.000Z",
      "parameters": {
        "scenario_id": "S007_01",
        "cu_trep_ms": 500,
        "nb_cu_frames_tot": 300,
        "spatial_binning": 1,
        "ppe": 400,
        "start_row_vi": 100,
        "mirror_flag": "ENABLE",
        "start_angle": -1.31051,
        "stop_angle": 0.10202,
        "scanner_step_per_frame": 0,
        "start_scan_speed": 0.0022421078,
        "stop_scan_speed": 0.0022421078
      },
      "comment": "This comment will be included in the exported ITL file."
    },
    {
      "name": "MAJ_JUP_DISK_SCAN",
      "unique_id": "MAJ_JUP_DISK_SCAN_002",
      "instrument": "MAJIS",
      "type": "OBSERVATION",
      "observation_type": "PRIME",
      "target": "JUPITER",
      "start_time": "2032-09-23T06:09:45.000Z",
      "end_time": "2032-09-23T06:20:15.000Z",
      "parameters": {
        "scenario_id": "S007_01",
        "cu_trep_ms": 2100,
        "nb_cu_frames_tot": 300,
        "spatial_binning": 2,
        "ppe": 400,
        "start_row_vi": 372,
        "mirror_flag": "ENABLE",
        "start_angle": 1.32935,
        "stop_angle": -0.08318,
        "scanner_step_per_frame": 3,
        "start_scan_speed": -0.0022421078,
        "stop_scan_speed": -0.0022421078
      },
      "comment": ""
    }
  ]
}
```

```bash
majis-itl absolute_time.itl --csv
```
```text
#OBS_NAME;OBS_START;OBS_END;INSTRUMENT;SCENARIO;TARGET;CU_TREP;CU_FRAME;BINNING;PPE;START_ROW_VIS;START_ANGLE;STOP_ANGLE;SYNCHRONOUS;START_SCAN_SPEED;STOP_SCAN_SPEED;PRIME;ITL;COMMENTS
MAJ_JUP_DISK_SCAN_001;2032-09-23T05:15:45.000Z;2032-09-23T05:26:15.000Z;MAJIS;S007_01;JUPITER;500ms;300;1;400;100;-1.31051;+0.10202;0;+0.0022421078;+0.0022421078;True;absolute_time.itl;"MULTI WORDS COMMENT with , and ; / MULTI LINES COMMENT"
MAJ_JUP_DISK_SCAN_002;2032-09-23T06:09:45.000Z;2032-09-23T06:20:15.000Z;MAJIS;S007_01;JUPITER;2100ms;300;2;400;372;+1.32935;-0.08318;+3;-0.0022421078;-0.0022421078;True;absolute_time.itl;"None"
```

Create a new MAJIS timeline (`.xlsm`) from a ITL the default template:
```bash
majis-itl absolute_time.itl --output output.xlsm
```

Edit an existing MAJIS timeline to compute relative time w.r.t. C/A reference:
```bash
majis-itl --timeline timeline.xlsm --relative-to "2032-09-24T21:33:36 PERIJOVE_12PJ (COUNT = 1)"
```

```{Warning}
If no `--output` flag is present, the output will be save in the original template.
```
