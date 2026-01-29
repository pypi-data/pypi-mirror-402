from __future__ import annotations

import pandas as pd
import pytest

from eb_contracts.contracts._internal.runtime import set_validation_mode
from eb_contracts.contracts.results.v1.panel_point_result import PanelPointResultV1
from eb_contracts.definitions.conventions import (
    ENTITY_ID,
    INTERVAL_START,
    Y_PRED,
    Y_TRUE,
)
from eb_contracts.validation.errors import ContractViolationError

######################################
# Helpers
######################################


def _panel_point_result_minimal(
    *, duplicate: bool = False, null_interval: bool = False
) -> pd.DataFrame:
    ts = [pd.Timestamp("2025-01-01 00:00:00"), pd.Timestamp("2025-01-01 00:30:00")]
    if duplicate:
        ts = [ts[0], ts[0]]
    if null_interval:
        ts = [ts[0], pd.NaT]

    return pd.DataFrame(
        {
            ENTITY_ID: ["A", "A"],
            INTERVAL_START: ts,
            Y_TRUE: [10.0, 12.0],
            Y_PRED: [11.0, 13.0],
        }
    )


######################################
# PanelPointResultV1
######################################


def test_panel_point_result_v1_valid_minimal_strict() -> None:
    df = _panel_point_result_minimal()
    with set_validation_mode("strict"):
        artifact = PanelPointResultV1.from_frame(df)
    assert artifact.frame is df


def test_panel_point_result_v1_missing_columns_strict_raises() -> None:
    df = pd.DataFrame({ENTITY_ID: ["A"], INTERVAL_START: [pd.Timestamp("2025-01-01")]})
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelPointResultV1.from_frame(df)


def test_panel_point_result_v1_duplicate_key_strict_raises() -> None:
    df = _panel_point_result_minimal(duplicate=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelPointResultV1.from_frame(df)


def test_panel_point_result_v1_null_interval_start_strict_raises() -> None:
    df = _panel_point_result_minimal(null_interval=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelPointResultV1.from_frame(df)


def test_panel_point_result_v1_warn_mode_does_not_raise() -> None:
    df = _panel_point_result_minimal(duplicate=True)
    with set_validation_mode("warn"):
        PanelPointResultV1.from_frame(df)


def test_panel_point_result_v1_off_mode_does_not_raise() -> None:
    df = _panel_point_result_minimal(duplicate=True)
    with set_validation_mode("off"):
        PanelPointResultV1.from_frame(df)
