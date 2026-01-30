# Actual Causes Identification — actualcauses

## Description

**actualcauses** is a Python package to identify *actual causes* (Halpern–Pearl style) in deterministic or stochastic systems.  
It implements approximate algorithms with adjustable precision introduced in the paper:

> *Searching for actual causes: approximate algorithms with adjustable precision* (Reyd, Diaconescu, Dessalles).  
> Preprint: arXiv:2507.07857

The package is designed for explainability and causal analysis of autonomous / AI-based systems: given a system model, a context, and a target consequence, it searches for exact or approximate actual causes.

---

## Installation

```bash
pip install actualcauses
```

For local development:
```bash
git clone https://github.com/SamuelReyd/ActualCausesIdentification
cd ActualCausesIdentification
python -m pip install -e ".[dev]"
```

---

## Core concepts (v1.0.0)
### `SCM`

An SCM object represents a Structural Causal Model:

- V: endogenous variables (names)
- U: exogenous variables (names)
- D: variable domains
- u: a context (values for exogenous variables)
- dag: optional causal graph (for algorithms that exploit structure)
- model: a system model (see [`SystemModel`](src/system_model.py) class) used to evaluate interventions

Once created, you call:

```python
scm.find_causes(...)
scm.show_identification_result()
```

### System models (`SystemModel`, `BaseNumpyModel`, …)

A system model defines how the system responds to interventions.

For simple Python models, subclass `SystemModel` and implement __call__(u, e).

For accelerated / vectorized evaluation, subclass `BaseNumpyModel` (and optionally its stochastic variants).

---
## Quickstart (Suzzy rock-throwing example)
The package provides a ready-to-run example SCM:
```python
from actualcauses import suzzy_example_scm

# Identify causes with two algorithms (Beam Search / ISI)
suzzy_example_scm.find_causes(ISI=False, max_steps=5, beam_size=20, epsilon=0.05, early_stop=False, verbose=2)
suzzy_example_scm.show_identification_result()

suzzy_example_scm.find_causes(ISI=True,  max_steps=5, beam_size=20, epsilon=0.05, early_stop=False, verbose=2)
suzzy_example_scm.show_identification_result()
```

A complete runnable version is in [examples/quickstart.py](examples/quickstart.py).

See the [examples/](examples/) folder for additional scenarios and advanced usage.

---
## Minimal custom SCM example (deterministic)

This mirrors [examples/custom_scm.py](examples/custom_scm.py) (forest fire scenario). The important part is implementing a `SystemModel` and passing it to `SCM`.

```python
from actualcauses import SCM, SystemModel

class ForestFireModel(SystemModel):
    def __init__(self, disjunctive=True):
        super().__init__(
            phi=lambda s: s[-1],  # consequence predicate (example: last variable)
            psi=lambda s: sum(s), # heuristic used by search
        )
        self.disjunctive = disjunctive

    def __call__(self, u, e):
        md, l = u
        e = dict(e)
        MD = e.get("MD", md)
        L  = e.get("L",  l)
        if self.disjunctive:
            FF = e.get("FF", int(L or MD))
        else:
            FF = e.get("FF", int(L and MD))
        self.n_calls += 1
        return [MD, L, FF]

scm = SCM(
    V=("MD", "L", "FF"),
    U=("md", "l"),
    D=(0, 1),
    u=(1, 1),
    model=ForestFireModel(disjunctive=True),
    dag={"MD": [], "L": [], "FF": ["MD", "L"]},
)

scm.find_causes()
scm.show_identification_result()
```

---
## Algorithms (high level)

The package provides:

- Beam-search style identification for (approximate) actual causes.

- ISI (Iterative Subinstance Identification) that can exploit a DAG to restrict search to relevant ancestors.

- LUCB-based estimation for stochastic models, to allocate samples adaptively.

Exact knobs/parameters are exposed via SCM.find_causes(...). Notable usefull parameters include `beam_size` (integer), `ISI` (boolean), `max_steps`(integer), and `early_stop` (boolean). Algorithm have 3 level of verbosity (accessible via `verbose=...`).

--- 

## Examples

The [examples/](examples/) folder contains scripts intended to be read and modified:

- [quickstart.py](examples/quickstart.py) — Minimal end-to-end run using suzzy_example_scm.
- [custom_scm.py](examples/custom_scm.py) — Implement a custom basic SCM and identify actual causes.
- [custom_heuristic.py](examples/custom_heuristic.py) — Use different heuristics (psi) with a fixed system model and SCM.
- [vectorized_system_model.py](examples/vectorized_system_model.py) — Use BaseNumpyModel to accelerate identification by vectorizing intervention evaluation.
- [stochastic_system_model.py](examples/stochastic_system_model.py) — Stochastic evaluation with a naive average estimator and the LUCB estimator.

Run any example from the repository root, e.g.:
```bash
python examples/quickstart.py
```

--- 
## License

MIT License. See [LICENSE](LICENSE).

---
## Citation

If you use this software in academic work, please cite:

> Reyd, S., Diaconescu, A., & Dessalles, J. (2025). Searching for actual causes: Approximate algorithms with adjustable precision. arXiv:2507.07857.

```bibtex
@misc{reyd2025searchingactualcausesapproximate,
  title        = {Searching for actual causes: Approximate algorithms with adjustable precision},
  author       = {Samuel Reyd and Ada Diaconescu and Jean-Louis Dessalles},
  year         = {2025},
  eprint       = {2507.07857},
  archivePrefix= {arXiv},
  primaryClass = {cs.AI},
  url          = {https://arxiv.org/abs/2507.07857}
}
```