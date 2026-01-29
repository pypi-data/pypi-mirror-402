"""
Cost asymmetry contract models (V1).

This module defines V1 cost-asymmetry specifications used by downstream
evaluation and optimization.

V1 includes:
- CostAsymmetrySpecV1: one cost ratio specification per entity, optionally time-scoped
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final

import pandas as pd

from eb_contracts.contracts._internal.runtime import get_runtime
from eb_contracts.definitions.conventions import (
    ENTITY_ID,
    INTERVAL_START,
)
from eb_contracts.validation.errors import ContractViolation, ContractViolationError

######################################
# Contract artifacts
######################################


@dataclass(frozen=True, slots=True)
class CostAsymmetrySpecV1:
    """Validated cost-asymmetry specifications."""

    frame: pd.DataFrame

    CONTRACT_NAME: ClassVar[Final[str]] = "CostAsymmetrySpecV1"

    ENTITY_COL: ClassVar[Final[str]] = ENTITY_ID
    EFFECTIVE_AT_COL: ClassVar[Final[str]] = INTERVAL_START

    COST_RATIO_COL: ClassVar[Final[str]] = "cost_ratio_r"

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> CostAsymmetrySpecV1:
        violations = validate_cost_asymmetry_spec_v1(frame)
        _raise_or_warn(cls.CONTRACT_NAME, violations)
        return cls(frame=frame)


######################################
# Validators
######################################


def validate_cost_asymmetry_spec_v1(frame: pd.DataFrame) -> list[ContractViolation]:
    """Validate a DataFrame against the CostAsymmetrySpecV1 contract."""
    violations: list[ContractViolation] = []

    required = {
        CostAsymmetrySpecV1.ENTITY_COL,
        CostAsymmetrySpecV1.COST_RATIO_COL,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        violations.append(
            ContractViolation(
                code="missing_columns",
                message=f"Missing required columns: {missing}",
            )
        )
        return violations

    r = frame[CostAsymmetrySpecV1.COST_RATIO_COL]

    if r.isna().to_numpy().any():
        violations.append(
            ContractViolation(
                code="null_cost_ratio",
                message="cost_ratio_r contains nulls.",
            )
        )
    else:
        bad = r.le(0).to_numpy()
        if bad.any():
            violations.append(
                ContractViolation(
                    code="nonpositive_cost_ratio",
                    message="cost_ratio_r must be > 0.",
                )
            )

    if CostAsymmetrySpecV1.EFFECTIVE_AT_COL in frame.columns:
        eff = frame[CostAsymmetrySpecV1.EFFECTIVE_AT_COL]
        if eff.isna().to_numpy().any():
            violations.append(
                ContractViolation(
                    code="null_effective_at",
                    message="effective time column contains nulls.",
                )
            )

        dup = frame.duplicated(
            [CostAsymmetrySpecV1.ENTITY_COL, CostAsymmetrySpecV1.EFFECTIVE_AT_COL]
        ).to_numpy()
        if dup.any():
            violations.append(
                ContractViolation(
                    code="duplicate_entity_effective_at",
                    message="(entity_id, interval_start) must be unique when interval_start is present.",
                )
            )
    else:
        dup = frame.duplicated([CostAsymmetrySpecV1.ENTITY_COL]).to_numpy()
        if dup.any():
            violations.append(
                ContractViolation(
                    code="duplicate_entity",
                    message="entity_id must be unique when no effective time column is present.",
                )
            )

    return violations


######################################
# Internal helpers
######################################


def _raise_or_warn(contract: str, violations: list[ContractViolation]) -> None:
    """Apply runtime validation behavior."""
    if not violations:
        return

    mode = get_runtime().validation
    if mode == "off":
        return

    if mode == "warn":
        print(f"[eb-contracts] WARN: {contract}: " + "; ".join(v.message for v in violations))
        return

    raise ContractViolationError(contract=contract, violations=violations)
