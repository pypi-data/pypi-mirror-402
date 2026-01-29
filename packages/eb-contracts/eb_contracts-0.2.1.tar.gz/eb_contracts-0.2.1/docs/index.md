# eb-contracts

`eb-contracts` defines the canonical data contracts, schemas, and structural interfaces used across the Electric Barometer ecosystem.

This package establishes **shared meaning and shape**, ensuring that forecasts, evaluations, optimization outputs, and downstream systems interoperate consistently.

## Scope

This package is responsible for:

- Defining canonical data structures and schemas
- Formalizing inputs and outputs exchanged between EB components
- Encoding shared assumptions about forecast results, costs, and runtime context
- Providing validation and migration utilities for contract evolution

It intentionally avoids implementing metrics, models, optimization logic, or workflows.

## Contents

- **Core contracts**
  Canonical representations for forecasts, results, costs, and runtime context

- **Validation utilities**
  Tools for checking contract conformance and structural integrity

- **Migration support**
  Helpers for evolving contracts across versions

## API reference

- [Contract definitions](api/index.md)
