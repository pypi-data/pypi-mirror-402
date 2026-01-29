"""
Canonical definitions for forecasting and panel-based evaluation.

This package provides shared vocabulary, conventions, and semantic declarations
used across contract schemas and evaluation workflows.

It is intentionally lightweight and declarative:
- No validation logic
- No business rules
- No framework- or industry-specific assumptions
"""

from __future__ import annotations

######################################
# Public API
######################################
# -------------------------------
# Naming conventions (canonical field names)
# -------------------------------
from eb_contracts.definitions.conventions import (
    ENTITY_ID,
    GRAIN,
    HORIZON,
    INTERVAL_END,
    INTERVAL_START,
    ISSUED_AT,
    PANEL_POINT_KEYS,
    PANEL_QUANTILE_KEYS,
    SCALE,
    UNITS,
    Y_PRED,
    Y_PRED_Q,
    Y_TRUE,
    Q,
    required_columns_point,
    required_columns_quantile,
)

# -------------------------------
# Glossary (semantic vocabulary)
# -------------------------------
from eb_contracts.definitions.glossary import (
    ACTUAL,
    COST_RATIO_R,
    ENTITY,
    ENTITY_ID as ENTITY_ID_TERM,
    FORECAST,
    FREQUENCY,
    GRAIN as GRAIN_TERM,
    HORIZON as HORIZON_TERM,
    INTERVAL,
    ISSUED_AT as ISSUED_AT_TERM,
    POINT_FORECAST,
    QUANTILE_FORECAST,
    READINESS,
    TAU,
    UNITS as UNITS_TERM,
)

# -------------------------------
# Semantics (interpretive declarations)
# -------------------------------
from eb_contracts.definitions.semantics import (
    BASELINE_PROFILE,
    STRICT_PROFILE,
    SemanticProfile,
)

# -------------------------------
# Units and scaling
# -------------------------------
from eb_contracts.definitions.units import (
    Scale,
    UnitPolicy,
    UnitSpec,
    UnitString,
)

######################################
# Export control
######################################

__all__ = [
    "ACTUAL",
    "BASELINE_PROFILE",
    "COST_RATIO_R",
    "ENTITY",
    "ENTITY_ID",
    "ENTITY_ID_TERM",
    "FORECAST",
    "FREQUENCY",
    "GRAIN",
    "GRAIN_TERM",
    "HORIZON",
    "HORIZON_TERM",
    "INTERVAL",
    "INTERVAL_END",
    "INTERVAL_START",
    "ISSUED_AT",
    "ISSUED_AT_TERM",
    "PANEL_POINT_KEYS",
    "PANEL_QUANTILE_KEYS",
    "POINT_FORECAST",
    "QUANTILE_FORECAST",
    "READINESS",
    "SCALE",
    "STRICT_PROFILE",
    "TAU",
    "UNITS",
    "UNITS_TERM",
    "Y_PRED",
    "Y_PRED_Q",
    "Y_TRUE",
    "Q",
    "Scale",
    "SemanticProfile",
    "UnitPolicy",
    "UnitSpec",
    "UnitString",
    "required_columns_point",
    "required_columns_quantile",
]
