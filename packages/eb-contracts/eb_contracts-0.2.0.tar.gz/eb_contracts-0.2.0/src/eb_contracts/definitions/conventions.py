"""
Canonical naming conventions for Electric Barometer contract artifacts.

This module defines **canonical field names** used across EB contract schemas.

Why this exists:
- Prevents "column name drift" across repos (adapters, evaluation, optimization, features).
- Allows validators to reference a single source of truth for required column names.
- Encodes a consistent vocabulary for temporal alignment and forecast representation.

Notes:
- These are conventions, not business-specific requirements. Adapters are responsible for
  mapping source-system fields into these canonical names.
- Contract schemas (e.g., PanelPointForecastV1) decide which of these are required vs optional.
"""

from __future__ import annotations

from typing import Final

# -------------------------------
# Core identity and time keys
# -------------------------------

# Entity identifier (store, store x channel, store x sku, etc.). See definitions/glossary.py for semantics.
ENTITY_ID: Final[str] = "entity_id"

# Start timestamp of the target interval the forecast/actual refers to.
INTERVAL_START: Final[str] = "interval_start"

# Optional end timestamp of the target interval.
INTERVAL_END: Final[str] = "interval_end"

# Optional timestamp representing when the forecast was issued (creation time).
ISSUED_AT: Final[str] = "issued_at"


# -------------------------------
# Core observed and forecast values
# -------------------------------

# Realized outcome for the target interval. Semantics depend on the contract (e.g., demand vs sales).
Y_TRUE: Final[str] = "y_true"

# Point forecast for the same target interval.
Y_PRED: Final[str] = "y_pred"

# Quantile level (0, 1) for quantile forecasts.
Q: Final[str] = "q"

# Forecasted quantile value at level q for the target interval.
Y_PRED_Q: Final[str] = "y_pred_q"


# -------------------------------
# Forecast horizon / lead-time vocabulary (optional)
# -------------------------------

# Optional: horizon index or number of steps ahead (e.g., 1 = next interval).
HORIZON: Final[str] = "horizon"

# Optional: explicit target timestamp keys used in some systems (aliases to interval_start/end).
TARGET_START: Final[str] = "target_start"
TARGET_END: Final[str] = "target_end"


# -------------------------------
# Grain and segmentation (optional but strongly recommended)
# -------------------------------

# Optional string describing the grain of the panel (e.g., "store", "store_channel", "store_sku").
GRAIN: Final[str] = "grain"

# Optional segmentation or grouping key(s) when an entity_id alone is not sufficient.
SEGMENT_ID: Final[str] = "segment_id"


# -------------------------------
# Missingness / availability flags (optional)
# -------------------------------

# Optional boolean indicating the entity is closed/unavailable for the interval (store closed, etc.).
IS_CLOSED: Final[str] = "is_closed"

# Optional boolean indicating values were imputed rather than observed.
IS_IMPUTED: Final[str] = "is_imputed"


# -------------------------------
# Cost / asymmetry vocabulary (optional; cost specs are their own contract family)
# -------------------------------

# Cost ratio / asymmetry parameter (often denoted R in EB).
COST_RATIO: Final[str] = "cost_ratio"

# Optional: identifier for the estimation method/source of the cost ratio.
COST_RATIO_SOURCE: Final[str] = "cost_ratio_source"


# -------------------------------
# Units / scaling (optional, but helps prevent silent nonsense)
# -------------------------------

# Optional string describing units of y_true/y_pred (e.g., "units", "dollars", "minutes").
UNITS: Final[str] = "units"

# Optional numeric scaling factor applied to values (e.g., 1.0 for raw, 0.001 for thousands).
SCALE: Final[str] = "scale"


# -------------------------------
# Common key sets (helpers)
# -------------------------------

# Canonical key columns for point forecast panels.
PANEL_POINT_KEYS: Final[tuple[str, ...]] = (ENTITY_ID, INTERVAL_START)

# Canonical key columns for quantile forecast panels.
PANEL_QUANTILE_KEYS: Final[tuple[str, ...]] = (ENTITY_ID, INTERVAL_START, Q)


def required_columns_point() -> set[str]:
    """Required columns for the canonical panel point forecast representation."""
    return {ENTITY_ID, INTERVAL_START, Y_TRUE, Y_PRED}


def required_columns_quantile() -> set[str]:
    """Required columns for the canonical panel quantile forecast representation."""
    return {ENTITY_ID, INTERVAL_START, Y_TRUE, Q, Y_PRED_Q}
