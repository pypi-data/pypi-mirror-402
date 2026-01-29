---
title: Majis Operations Toolbox
---

# Majis Operations Toolbox

::::{grid} 2
:reverse:

:::{grid-item}
:columns: 4
:class: sd-m-auto

![Logo](images/logo-square.svg)

:::

:::{grid-item}
:columns: 8
:class: sd-fs-3

This toolbox contrains python modules and command line interfaces
to manipulate and visualize the Majis data.


:::

::::

::::{grid} 1 2 1 2
:class-container: text-center
:gutter: 3

:::{grid-item-card}
:link:  notebooks/opl
:link-type: doc
:class-header: bg-light

OPL 🔭
^^^

Load and manipulate Majis observation plan `.opl` files.
:::

:::{grid-item-card}
:link:  notebooks/itl
:link-type: doc
:class-header: bg-light

ITL 🎺
^^^

Load and manipulate Majis instrument timeline `.itl` files.
:::

:::{grid-item-card}
:link:  notebooks/timeline
:link-type: doc
:class-header: bg-light

Timeline ⏳
^^^

Load and fill Majis Timeline `.xlsm` files.

:::

:::{grid-item-card}
:link: cli/itl
:link-type: doc
:class-header: bg-light

CLI 👾
^^^

Perform `itl` and `timeline` operations from the command line.

:::

::::

---

How to install it 🚀
--------------------

````{margin}
```{note}
_Deployement on `conda-forge` should be available in the future._
```
````

The Majis Operations toolbox is available on [PyPI](https://pypi.org/project/majis-ops/) (Python Package Index).
You can install it with `pip`:


```bash
pip install majis-ops
```

About this project 💬
---------------------
This project is under active developement by the Juice-Majis Operations Team
mainly located at [IAS](https://www.ias.universite-paris-saclay.fr/fr/content/juicemajis)
and [Osuna](https://osuna.univ-nantes.fr/osuna-services-dobservation).
The source code is available in [IAS Gitlab](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox)
and distributed under a [BSD-3 Clause](https://git.ias.u-psud.fr/majis_sgs/operations/majis-ops-toolbox/-/blob/main/LICENSE.md) public license.
