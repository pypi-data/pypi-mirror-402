# MAJIS operations toolbox history

All notable changes to MAJIS operations toolbox will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


[Unreleased][new]
-----------------
[new]: https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/compare/1.2.1...main


[Release 1.2.1 - 2026/01/19][1.2.1]
-----------------------------------
[1.2.1]: https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/releases/1.2.1

### Changed
- Update SOC ITL and OPL schema to v4 ([!14](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/14))


[Release 1.2.0 - 2026/01/12][1.2.0]
-----------------------------------
[1.2.0]: https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/releases/1.2.0

### Added
- New generic OPL CSV and JSON reader and exporter ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13))
- Add OPL CSV to JSON and JSON to CSV convertor ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13))
- New OPL JSON schema ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13))
- Add a new `depreciated` method in `misc` sub-module ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13)).

### Changed
- Strip trailing `.000Z` to `Z` in datetime formatter ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13)).
- Change `majis.itl.csv.export.save_csv` to `majis.itl.csv.export.save_itl_csv` ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13)).
- Change `majis.itl.csv.export.save_xlsm` to `majis.itl.csv.export.save_itl_xlsm` ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13)).
- Move JSON schemas into their own submodule ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13)).
- `MAJIS_ITL_SCHEMAS` is replaced by `MAJIS_SCHEMAS` as a dict to support OPL schemas ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13)).

### Fixed
- Read the docs jupyter-book configuration ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13)).

### Depreciated
- Legacy `save_csv` and `save_xlsm` are depreciated in favor of `save_itl` ([!13](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/13)).


[Release 1.1.2 - 2025/11/27][1.1.2]
-----------------------------------
[1.1.2]: https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/releases/1.1.2

### Fixed
- Enforce type formatter in JSON ITL extra keys during export ([!12](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/12)).
- Fix jupyter-book dependency in RTD config ([!12](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/12)).


[Release 1.1.1 - 2025/11/25][1.1.1]
-----------------------------------
[1.1.1]: https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/releases/1.1.1

### Added
- Add ITL JSON parser `parse_json` public method to format ITL observation as events dictionary ([!10](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/10)).

### Fixed
- Temporary fix the timeline missing key in SOC v2 schema ([!10](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/10)).
- Enforce Jupyter Book version < 2 ([!11](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/11)).


[Release 1.1.0 - 2025/10/28][1.1.0]
-----------------------------------
[1.1.0]: https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/releases/1.1.0

### Added
- Add generic ITL writer `save_itl` to export a ITL timeline to different formats ([!9](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/9)).
- Add ITL JSON reader and writer with validator on SOC and MAJIS schema ([!9](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/9)).
- SonarQube code quality job in Gitlab CI ([!7](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/7)).

### Changed
- Isolate ITL text reader in EPS format in its own sub-module ([!9](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/9)).
- Isolate export to ITL EPS, JSON, CSV, XLS in their own sub-modules ([!9](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/9)).
- ITL EPS comments are now reformatted rather than copy-pasted ([!9](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/9)).
- Project status is now considered `stable`.

### Fixed
- Fix invalid timeline template format ([!8](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/8)).
- Fix ITL reader with missing space and single comment.
- Fix missing sphinx config for RTD.
- Gitlab-CI unquoted hatch version.
- Gitlab-CI build project before PyPI publication.
- Gitlab-CI add user `__token__` value for PyPI publication.

### Removed
- `.comments` properties from parsed `EventWindow` objects ([!9](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/merge_requests/9)).


[Release 1.0.0 - 2024/06/19][1.0.0]
-----------------------------------
[1.0.0]: https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/releases/1.0.0

### Added

- Add `read_itl()`, `save_itl()`, `save_csv()` and `save_xlsm()` methods.
- Add `Timeline` object to manipulate MAJIS `.xlsm` timeline file.
- Add `majis-itl` command line interface.
- Project init
