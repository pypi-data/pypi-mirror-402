"""
Units and scaling conventions for forecasting and panel-based evaluation.

This module is intentionally lightweight and declarative:

- It defines vocabulary and expectations for measurement units and scaling.
- It does not attempt to infer units or validate data (validators live with contracts).
- It remains implementation- and industry-agnostic.

Goal: prevent "numerically valid but semantically wrong" evaluation caused by unit
mismatches (e.g., mixing dollars with counts, mixing minutes with hours, mixing raw
values with values scaled to thousands).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

# -------------------------------
# Core concepts
# -------------------------------

# Units are represented as free-form strings by default. This keeps integrations flexible
# (e.g., "units", "transactions", "dollars", "minutes", "events").
#
# If you later want stricter enforcement, you can introduce a controlled vocabulary
# or map common unit strings into a canonical form at the adapter layer.

UnitString = str

# Scaling is a multiplicative factor applied uniformly to values.
# Example:
# - raw values: scale = 1.0
# - values reported in thousands: scale = 0.001 (or equivalently report units as "thousands")
Scale = float

# Desired policy for unit compatibility within an artifact.
UnitPolicy = Literal["declared", "unknown"]


@dataclass(frozen=True, slots=True)
class UnitSpec:
    """Declarative unit specification for a set of values.

    Attributes:
        units:
            A string describing the measurement units (e.g., "units", "dollars", "minutes").
        scale:
            A multiplicative scale factor applied uniformly to values. Defaults to 1.0.
        policy:
            Whether units are expected to be declared ("declared") or may be unknown ("unknown").
            This is descriptive; enforcement belongs in contract validators or higher layers.
    """

    units: UnitString | None = None
    scale: Scale = 1.0
    policy: UnitPolicy = "declared"


# -------------------------------
# Recommended conventions
# -------------------------------

# Baseline recommendations (descriptive, not enforced here).
RECOMMENDED_DECLARED_POLICY: Final[UnitPolicy] = "declared"
RECOMMENDED_SCALE_DEFAULT: Final[Scale] = 1.0

# A small set of commonly used unit labels (non-exhaustive).
COMMON_UNIT_LABELS: Final[tuple[str, ...]] = (
    "units",
    "count",
    "events",
    "transactions",
    "dollars",
    "minutes",
    "hours",
    "requests",
)


# -------------------------------
# Compatibility semantics (no validation)
# -------------------------------

Compatibility = Literal["compatible", "incompatible", "unknown"]


def describe_compatibility(a: UnitSpec, b: UnitSpec) -> Compatibility:
    """Describe unit compatibility between two specs.

    This is a *semantic* helper, not a validator. It returns:
    - "compatible" if both units and scale match exactly,
    - "incompatible" if both units are declared and differ, or scales differ,
    - "unknown" if either spec has unknown/None units under an "unknown" policy.

    Integrations may choose to treat "unknown" as an error in strict settings.
    """
    if (a.policy == "unknown" or b.policy == "unknown") and (a.units is None or b.units is None):
        return "unknown"

    if a.units is None or b.units is None:
        return "unknown"

    if a.units != b.units:
        return "incompatible"

    if a.scale != b.scale:
        return "incompatible"

    return "compatible"


# -------------------------------
# Display helpers
# -------------------------------


def format_unit_spec(spec: UnitSpec) -> str:
    """Format a unit spec for logging, messages, or error details."""
    units = spec.units if spec.units is not None else "unknown"
    return f"units={units}, scale={spec.scale}, policy={spec.policy}"


def choose_unit_label(preferred: Sequence[str], available: Sequence[str]) -> str | None:
    """Choose a unit label from available labels, given a preference order.

    This is a convenience helper for integrations and adapters. It does not
    modify data and does not validate semantics.
    """
    available_set = set(available)
    for label in preferred:
        if label in available_set:
            return label
    return None
