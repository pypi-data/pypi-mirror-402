# Electric Barometer · Contracts (`eb-contracts`)

![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)

Data contract and validation layer for the Electric Barometer ecosystem, defining canonical schemas, semantics, and enforcement for forecasts, costs, results, and run context.

---

## Overview

This repository contains the data contract and validation layer of the Electric Barometer ecosystem. It defines the canonical schemas, semantics, and invariants that govern how forecasts, costs, results, and contextual metadata are represented, validated, and exchanged across systems.

Rather than producing forecasts, computing metrics, or applying optimization logic, this repository focuses on structural correctness and shared meaning: how data artifacts are shaped, what guarantees they provide, and how violations are detected and handled. By formalizing these contracts as versioned, validated artifacts, eb-contracts ensures that all downstream components operate on consistent, explicit, and auditable data interfaces—reducing ambiguity, preventing silent errors, and enabling long-term evolution without breaking consumers.

---

## Role in the Electric Barometer Ecosystem

`eb-contracts` defines the canonical data contracts and validation boundaries used throughout the Electric Barometer ecosystem. It is responsible for specifying how core data artifacts—such as forecasts, cost specifications, evaluation results, and run context—are structured, interpreted, and validated before they are consumed by downstream systems.

This repository focuses exclusively on data shape, semantic consistency, and enforcement. It does not generate forecasts, compute metrics, select parameters, perform optimization, or orchestrate evaluation workflows. Those responsibilities are handled by adjacent layers in the ecosystem that produce predictions, compute metric values, calibrate parameters, or apply decision logic in operational settings.

By separating data contracts and validation from computation and policy concerns, eb-contracts provides a stable, versioned interface layer that enables interoperability, reduces ambiguity, and ensures that all components of the Electric Barometer ecosystem operate on shared, explicit assumptions—supporting long-term evolution without breaking consumers.

---

## Installation

`eb-optimization` is distributed as a standard Python package.

```bash
pip install eb-contracts
```

---

## Core Concepts

- **Canonical data contracts** — Core data artifacts (forecasts, cost specifications, results, and context) are represented using explicit, versioned schemas rather than implicit conventions or ad-hoc DataFrame shapes.

- **Semantic consistency** — Column names, units, grain, and meaning are standardized and enforced so that downstream systems can rely on shared interpretation rather than contextual knowledge or undocumented assumptions.

- **Validation as a boundary** — Contract validation establishes a clear boundary between “valid” and “invalid” data, preventing silent failures and making structural issues visible at ingestion time rather than during downstream computation.

- **Versioned evolution** — Contracts are versioned to allow schemas and semantics to evolve over time without breaking existing consumers, enabling forward progress while preserving backward compatibility.

- **Explicit migration** — Adaptation from external or legacy data formats into contract-compliant artifacts is performed through explicit migration utilities, avoiding implicit coercion or guesswork.

- **Separation of structure from logic** — Data shape and meaning are defined independently of metric computation, optimization, or execution logic, ensuring that structural correctness is not entangled with algorithmic behavior.

---

## Minimal Example

The example below illustrates a typical contract workflow using `eb-contracts`: adapting an external forecast frame into a canonical contract artifact and validating it at the system boundary.

```python
import pandas as pd

from eb_contracts.migrate import (
    PanelPointColumns,
    to_panel_point_v1,
)
from eb_contracts.validate import panel_point_v1
from eb_contracts._runtime import set_validation_mode

# External (non-canonical) forecast data
raw = pd.DataFrame(
    {
        "store": ["A", "A"],
        "timestamp": [
            pd.Timestamp("2025-01-01 00:00:00"),
            pd.Timestamp("2025-01-01 00:30:00"),
        ],
        "actual": [10.0, 12.0],
        "forecast": [11.0, 13.0],
    }
)

# Explicitly map external columns to the EB contract
columns = PanelPointColumns(
    entity_id="store",
    interval_start="timestamp",
    y_true="actual",
    y_pred="forecast",
)

# Enable strict validation at the contract boundary
with set_validation_mode("strict"):
    forecast = to_panel_point_v1(raw, columns=columns)

# `forecast` is now a validated PanelPointForecastV1 artifact
print(type(forecast))
```

---

## License

BSD 3-Clause License.
© 2025 Kyle Corrie.
