"""
Results contract models (V1).

This module defines V1 result artifacts produced by evaluation and optimization
pipelines.

V1 includes:
- PanelPointResultV1: point-forecast results at entity x interval grain
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final

import pandas as pd

from eb_contracts.contracts._internal.runtime import get_runtime
from eb_contracts.definitions.conventions import (
    ENTITY_ID,
    INTERVAL_START,
    Y_PRED,
    Y_TRUE,
)
from eb_contracts.validation.errors import ContractViolation, ContractViolationError

######################################
# Contract artifacts
######################################


@dataclass(frozen=True, slots=True)
class PanelPointResultV1:
    """Validated point-forecast results (entity x interval)."""

    frame: pd.DataFrame

    CONTRACT_NAME: ClassVar[Final[str]] = "PanelPointResultV1"

    ENTITY_COL: ClassVar[Final[str]] = ENTITY_ID
    INTERVAL_START_COL: ClassVar[Final[str]] = INTERVAL_START
    Y_TRUE_COL: ClassVar[Final[str]] = Y_TRUE
    Y_PRED_COL: ClassVar[Final[str]] = Y_PRED

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> PanelPointResultV1:
        violations = validate_panel_point_result_v1(frame)
        _raise_or_warn(cls.CONTRACT_NAME, violations)
        return cls(frame=frame)


######################################
# Validators
######################################


def validate_panel_point_result_v1(frame: pd.DataFrame) -> list[ContractViolation]:
    """Validate a DataFrame against the PanelPointResultV1 contract."""
    violations: list[ContractViolation] = []

    required = {
        PanelPointResultV1.ENTITY_COL,
        PanelPointResultV1.INTERVAL_START_COL,
        PanelPointResultV1.Y_TRUE_COL,
        PanelPointResultV1.Y_PRED_COL,
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

    if frame[PanelPointResultV1.INTERVAL_START_COL].isna().to_numpy().any():
        violations.append(
            ContractViolation(
                code="null_interval_start",
                message="interval_start contains nulls.",
            )
        )

    dup = frame.duplicated(
        [PanelPointResultV1.ENTITY_COL, PanelPointResultV1.INTERVAL_START_COL]
    ).to_numpy()
    if dup.any():
        violations.append(
            ContractViolation(
                code="duplicate_entity_interval",
                message="(entity_id, interval_start) must be unique.",
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
