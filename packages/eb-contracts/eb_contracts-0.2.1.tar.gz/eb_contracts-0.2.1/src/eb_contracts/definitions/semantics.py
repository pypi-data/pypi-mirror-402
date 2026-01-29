"""
Semantic conventions for forecasting and panel-based evaluation.

This module defines interpretive semantics that apply across contract families.
It is intentionally declarative:

- It explains what fields mean and what assumptions consumers may rely on.
- It does not perform validation (validators live with contract implementations).
- It remains implementation- and industry-agnostic.

These semantics exist to reduce ambiguity and prevent subtle, silent misuse
(e.g., time misalignment or mixed-grain panels).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

# -------------------------------
# Temporal semantics
# -------------------------------

# Interval timestamp conventions:
# - interval_start identifies the beginning of the target interval.
# - interval_end, when present, identifies the end of the target interval.
# - A single observation corresponds to one entity and one target interval.

INTERVAL_BOUNDARY_CONVENTION: Final[str] = "left-closed_right-open"  # [start, end)

# Forecast issuance:
# - issued_at represents the time a forecast was generated.
# - In typical settings, issued_at <= interval_start for the target interval.
# - Some integrations may omit issued_at; in those cases, the dataset represents
#   target-time forecasts without explicit issuance context.

ISSUANCE_RELATION: Final[str] = "issued_at_precedes_or_equals_target_start"

# Horizon:
# - horizon represents lead time between issuance and target interval.
# - It may be stored explicitly (integer steps) or derived from issued_at and interval_start.
# - Not all contract variants require an explicit horizon field.

HORIZON_REPRESENTATION: Final[str] = "steps_ahead_or_derived"


# -------------------------------
# Identity and grain semantics
# -------------------------------

# Grain describes the non-temporal dimensions that uniquely define an entity.
# Grain excludes time; temporal resolution is represented by interval fields and frequency metadata.
# A single contract artifact should have a single, consistent grain.

MIXED_GRAIN_POLICY: Final[str] = (
    "disallowed_by_definition"  # mixed-grain panels are conceptually invalid
)

# Entity identity:
# - entity_id is a stable identifier at the dataset's declared grain.
# - entity_id may be a natural key or composite encoding.
# - The encoding strategy is an integration concern; consumers require only consistency.

ENTITY_ID_ENCODING_POLICY: Final[str] = "integration_defined_consumer_requires_consistency"


# -------------------------------
# Uniqueness semantics
# -------------------------------

# A panel dataset represents at most one observation per entity per target interval.
# Therefore, the canonical uniqueness constraints are:
# - point forecasts: (entity_id, interval_start)
# - quantile forecasts: (entity_id, interval_start, q)

UNIQUENESS_POLICY: Final[str] = "one_observation_per_key"


# -------------------------------
# Observed outcomes (actuals) semantics
# -------------------------------

# y_true represents the realized (observed) outcome for the target interval.
# Its semantic meaning (e.g., demand, utilization, volume) must be explicit in the integration.
# y_true should not be conflated with missingness; missing values should be represented explicitly.

ACTUALS_POLICY: Final[str] = "observed_outcome_semantics_must_be_explicit"


# -------------------------------
# Units and scaling semantics
# -------------------------------

# units indicates the measurement units for y_true and forecast values.
# scale is an optional uniform scaling factor applied to values.
# Units and scale are semantic information and should be consistent within a single artifact.

UNITS_POLICY: Final[str] = "units_consistent_within_artifact"
SCALE_POLICY: Final[str] = "scale_uniform_within_artifact"


# -------------------------------
# Missingness and availability semantics
# -------------------------------

# Missingness:
# - Missing values indicate absence of observation, not necessarily zero.
# - is_closed may indicate an entity is inactive/unavailable for an interval.
# - is_imputed may indicate values were imputed rather than directly observed.

MISSINGNESS_POLICY: Final[str] = "missing_is_not_zero_flags_capture_state"


# -------------------------------
# Optional: declared semantic profiles
# -------------------------------

ValidationStrictness = Literal["baseline", "strict"]


@dataclass(frozen=True, slots=True)
class SemanticProfile:
    """A named set of semantic expectations.

    Profiles are descriptive and may be used by validators to decide which checks
    to enforce. They do not perform validation themselves.
    """

    name: str
    strictness: ValidationStrictness = "baseline"


BASELINE_PROFILE: Final[SemanticProfile] = SemanticProfile(name="baseline", strictness="baseline")
STRICT_PROFILE: Final[SemanticProfile] = SemanticProfile(name="strict", strictness="strict")
