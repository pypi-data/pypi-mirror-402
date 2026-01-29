How to contribution 👐
======================

If you want to contribute to this project, you need to install [`hatch`](https://hatch.pypa.io/latest/install/) on your system, then clone the depot and install de default env:

```bash
git clone https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox.git
cd majis-ops-toolbox

# Install dev dependencies
hatch env create

# Setup pre-commit hook
hatch run pre-commit install
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
