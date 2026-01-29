"""
Forecast contract models (V1).

This module defines V1 forecast contract artifacts and their validation routines.

V1 includes:
- PanelPointForecastV1: one point forecast per entity x interval
- PanelQuantileForecastV1: one quantile forecast per entity x interval x q
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
    Y_PRED_Q,
    Y_TRUE,
    Q,
)
from eb_contracts.validation.errors import ContractViolation, ContractViolationError

######################################
# Contract artifacts
######################################


@dataclass(frozen=True, slots=True)
class PanelPointForecastV1:
    """Validated panel point-forecast data (entity x interval)."""

    frame: pd.DataFrame

    CONTRACT_NAME: ClassVar[Final[str]] = "PanelPointForecastV1"

    ENTITY_COL: ClassVar[Final[str]] = ENTITY_ID
    INTERVAL_START_COL: ClassVar[Final[str]] = INTERVAL_START
    Y_TRUE_COL: ClassVar[Final[str]] = Y_TRUE
    Y_PRED_COL: ClassVar[Final[str]] = Y_PRED

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> PanelPointForecastV1:
        violations = validate_panel_point_forecast_v1(frame)
        _raise_or_warn(cls.CONTRACT_NAME, violations)
        return cls(frame=frame)


@dataclass(frozen=True, slots=True)
class PanelQuantileForecastV1:
    """Validated panel quantile-forecast data (entity x interval x q)."""

    frame: pd.DataFrame

    CONTRACT_NAME: ClassVar[Final[str]] = "PanelQuantileForecastV1"

    ENTITY_COL: ClassVar[Final[str]] = ENTITY_ID
    INTERVAL_START_COL: ClassVar[Final[str]] = INTERVAL_START
    Y_TRUE_COL: ClassVar[Final[str]] = Y_TRUE
    Q_COL: ClassVar[Final[str]] = Q
    Y_PRED_Q_COL: ClassVar[Final[str]] = Y_PRED_Q

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> PanelQuantileForecastV1:
        violations = validate_panel_quantile_forecast_v1(frame)
        _raise_or_warn(cls.CONTRACT_NAME, violations)
        return cls(frame=frame)


######################################
# Validators
######################################


def validate_panel_point_forecast_v1(frame: pd.DataFrame) -> list[ContractViolation]:
    """Validate a DataFrame against the PanelPointForecastV1 contract."""
    violations: list[ContractViolation] = []

    required = {
        PanelPointForecastV1.ENTITY_COL,
        PanelPointForecastV1.INTERVAL_START_COL,
        PanelPointForecastV1.Y_TRUE_COL,
        PanelPointForecastV1.Y_PRED_COL,
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

    if frame[PanelPointForecastV1.INTERVAL_START_COL].isna().to_numpy().any():
        violations.append(
            ContractViolation(
                code="null_interval_start",
                message="interval_start contains nulls.",
            )
        )

    dup = frame.duplicated(
        [PanelPointForecastV1.ENTITY_COL, PanelPointForecastV1.INTERVAL_START_COL]
    ).to_numpy()
    if dup.any():
        violations.append(
            ContractViolation(
                code="duplicate_entity_interval",
                message="(entity_id, interval_start) must be unique.",
            )
        )

    return violations


def validate_panel_quantile_forecast_v1(frame: pd.DataFrame) -> list[ContractViolation]:
    """Validate a DataFrame against the PanelQuantileForecastV1 contract."""
    violations: list[ContractViolation] = []

    required = {
        PanelQuantileForecastV1.ENTITY_COL,
        PanelQuantileForecastV1.INTERVAL_START_COL,
        PanelQuantileForecastV1.Y_TRUE_COL,
        PanelQuantileForecastV1.Q_COL,
        PanelQuantileForecastV1.Y_PRED_Q_COL,
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

    if frame[PanelQuantileForecastV1.INTERVAL_START_COL].isna().to_numpy().any():
        violations.append(
            ContractViolation(
                code="null_interval_start",
                message="interval_start contains nulls.",
            )
        )

    q = frame[PanelQuantileForecastV1.Q_COL]
    if q.isna().to_numpy().any():
        violations.append(ContractViolation(code="null_q", message="q contains nulls."))

    bad_q = (~q.between(0.0, 1.0, inclusive="neither")).fillna(False).to_numpy()
    if bad_q.any():
        violations.append(ContractViolation(code="q_out_of_range", message="q must be in (0, 1)."))

    dup = frame.duplicated(
        [
            PanelQuantileForecastV1.ENTITY_COL,
            PanelQuantileForecastV1.INTERVAL_START_COL,
            PanelQuantileForecastV1.Q_COL,
        ]
    ).to_numpy()
    if dup.any():
        violations.append(
            ContractViolation(
                code="duplicate_entity_interval_q",
                message="(entity_id, interval_start, q) must be unique.",
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
