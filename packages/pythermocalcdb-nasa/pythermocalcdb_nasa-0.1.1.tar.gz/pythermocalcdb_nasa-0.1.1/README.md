# 🚀 PyThermoCalcDB-NASA

[![PyPI Downloads](https://static.pepy.tech/badge/pythermocalcdb-nasa/month)](https://pepy.tech/projects/pythermocalcdb-nasa)
![PyPI](https://img.shields.io/pypi/v/pythermocalcdb-nasa)
![Python Version](https://img.shields.io/pypi/pyversions/pythermocalcdb-nasa.svg)
![License](https://img.shields.io/pypi/l/pythermocalcdb-nasa)

NASA-polynomial thermochemistry for species, reactions, and equilibrium calculations.

---

## 🧭 Overview

PyThermoCalcDB-NASA is a scientific Python library for evaluating NASA-7 and NASA-9 polynomial thermochemistry for ideal-gas species and reactions. It focuses on reference-state consistency while staying decoupled from how data is stored or sourced.

---

## ✨ Key Features

- NASA-7 and NASA-9 support with automatic temperature-break selection
- Species properties: `Cp(T)`, `H^0(T)`, `S^0(T)`, `G^0(T)` on molar or mass basis
- Reaction properties: `Delta H^0(T)`, `Delta S^0(T)`, `Delta G^0(T)` plus equilibrium constants `K(T)`
- Van't Hoff shortcut helper (`Keq_vh_shortcut`) using `Delta H^0(298 K)`
- Clean separation of data (PyThermoDB/LinkDB) from the calculation engine
- Returns `CustomProp` objects with units and metadata; optional timing logs via `mode`

---

## 📦 Installation

```bash
pip install pythermocalcdb-nasa
```

Examples rely on helper packages and the ThermoDB pickles shipped under `examples/thermodb`:

```bash
pip install pythermodb-settings pythermodb pythermolinkdb pyreactlab-core rich
```

---

## ⚡ Quick start

Build a `ModelSource` from the packaged NASA pickles and evaluate properties:

```python
from pythermodb_settings.models import Component, ComponentThermoDBSource, Temperature
from pyThermoLinkDB import load_and_build_model_source
from pyreactlab_core.models.reaction import Reaction
from pythermocalcdb_nasa import Cp_T, Keq

CO2 = Component(name="carbon dioxide", formula="CO2", state="g")
CO = Component(name="carbon monoxide", formula="CO", state="g")
H2O = Component(name="dihydrogen monoxide", formula="H2O", state="g")
H2 = Component(name="dihydrogen", formula="H2", state="g")
CH4 = Component(name="methane", formula="CH4", state="g")

thermodb_sources = [
    ComponentThermoDBSource(component=CO2, source="examples/thermodb/carbon dioxide-CO2-g-nasa-1.pkl"),
    ComponentThermoDBSource(component=CO, source="examples/thermodb/carbon monoxide-CO-g-nasa-1.pkl"),
    ComponentThermoDBSource(component=H2O, source="examples/thermodb/dihydrogen monoxide-H2O-g-nasa-1.pkl"),
    ComponentThermoDBSource(component=H2, source="examples/thermodb/dihydrogen-H2-g-nasa-1.pkl"),
    ComponentThermoDBSource(component=CH4, source="examples/thermodb/methane-CH4-g-nasa-1.pkl"),
]

model_source = load_and_build_model_source(
    thermodb_sources=thermodb_sources,
    original_equation_label=False,  # normalize NASA labels
)

# Species property
Cp = Cp_T(
    component=CH4,
    temperature=Temperature(value=600.0, unit="K"),
    model_source=model_source,
    mode="log",  # optional timing log
)
print(Cp)

# Reaction equilibrium
reaction = Reaction(
    name="Water-Gas Shift",
    reaction="CO(g) + H2O(g) => CO2(g) + H2(g)",
    components=[CO, H2O, CO2, H2],
)

Keq_T = Keq(
    reaction=reaction,
    temperature=Temperature(value=1000.0, unit="K"),
    model_source=model_source,
)
print(Keq_T)
```

---

## 🧰 Helper functions

Available helpers (all return `CustomProp` or `None`):

- `H_T`, `S_T`, `G_T`, `Cp_T` - species properties on molar or mass basis
- `dH_rxn_STD`, `dS_rxn_STD`, `dG_rxn_STD` - reaction properties from stoichiometry
- `Keq`, `Keq_vh_shortcut` - equilibrium constants from `Delta G^0(T)` or Van't Hoff

---

## 📚 Examples

Run from the project root, e.g. `python examples/exp-2.py`:

- `examples/exp-1.py` - build `ModelSource` objects and inspect NASA segments
- `examples/exp-2.py` - evaluate `H_T`, `S_T`, `G_T`, and `Cp_T` for CO2/CH4
- `examples/exp-3.py` - water-gas shift reaction properties and `Keq(T)`
- `examples/build-thermodb.py` - generate ThermoDB pickles from reference data
- `examples/filter_reference-thermodb.py` - subset the reference dataset for examples/tests

---

## 📖 Documentation

Documentation is available at [https://pythermocalcdb-nasa.readthedocs.io/en/latest/](https://pythermocalcdb-nasa.readthedocs.io/en/latest/).

---

## 🤝 Contributing

Contributions are welcome: bug fixes, new calculation routines, expanded examples, unit tests, or documentation improvements.

---

## ⚖️ License

This project is distributed under the Apache License, Version 2.0. If you incorporate this work into your own software, please acknowledge Sina Gilassi as the original author (a repository or documentation reference is appreciated).

---

## ❓ FAQ

Questions? Contact me on [LinkedIn](https://www.linkedin.com/in/sina-gilassi/).

---

## 👤 Authors

- [@sinagilassi](https://www.github.com/sinagilassi)
