from __future__ import annotations

import pandas as pd
import pytest

from eb_contracts.contracts._internal.runtime import set_validation_mode
from eb_contracts.contracts.forecast_panel.v1.forecast_panel import (
    PanelPointForecastV1,
    PanelQuantileForecastV1,
)
from eb_contracts.definitions.conventions import (
    ENTITY_ID,
    INTERVAL_START,
    Y_PRED,
    Y_PRED_Q,
    Y_TRUE,
    Q,
)
from eb_contracts.validation.errors import ContractViolationError

######################################
# Helpers
######################################


def _panel_point_minimal(*, duplicate: bool = False, null_interval: bool = False) -> pd.DataFrame:
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


def _panel_quantile_minimal(
    *,
    duplicate: bool = False,
    null_interval: bool = False,
    null_q: bool = False,
    q_out_of_range: bool = False,
) -> pd.DataFrame:
    ts = [pd.Timestamp("2025-01-01 00:00:00"), pd.Timestamp("2025-01-01 00:00:00")]
    qs = [0.5, 0.9]

    if duplicate:
        ts = [ts[0], ts[0]]
        qs = [0.5, 0.5]

    if null_interval:
        ts = [ts[0], pd.NaT]

    if null_q:
        qs = [0.5, None]

    if q_out_of_range:
        qs = [0.5, 1.0]

    return pd.DataFrame(
        {
            ENTITY_ID: ["A", "A"],
            INTERVAL_START: ts,
            Y_TRUE: [10.0, 10.0],
            Q: qs,
            Y_PRED_Q: [9.0, 12.0],
        }
    )


######################################
# PanelPointForecastV1
######################################


def test_panel_point_v1_valid_minimal_strict() -> None:
    df = _panel_point_minimal()
    with set_validation_mode("strict"):
        artifact = PanelPointForecastV1.from_frame(df)
    assert artifact.frame is df


def test_panel_point_v1_missing_columns_strict_raises() -> None:
    df = pd.DataFrame({ENTITY_ID: ["A"], INTERVAL_START: [pd.Timestamp("2025-01-01")]})
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelPointForecastV1.from_frame(df)


def test_panel_point_v1_duplicate_key_strict_raises() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelPointForecastV1.from_frame(df)


def test_panel_point_v1_null_interval_start_strict_raises() -> None:
    df = _panel_point_minimal(null_interval=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelPointForecastV1.from_frame(df)


def test_panel_point_v1_warn_mode_does_not_raise() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("warn"):
        PanelPointForecastV1.from_frame(df)


def test_panel_point_v1_off_mode_does_not_raise() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("off"):
        PanelPointForecastV1.from_frame(df)


######################################
# PanelQuantileForecastV1
######################################


def test_panel_quantile_v1_valid_minimal_strict() -> None:
    df = _panel_quantile_minimal()
    with set_validation_mode("strict"):
        artifact = PanelQuantileForecastV1.from_frame(df)
    assert artifact.frame is df


def test_panel_quantile_v1_missing_columns_strict_raises() -> None:
    df = pd.DataFrame({ENTITY_ID: ["A"], INTERVAL_START: [pd.Timestamp("2025-01-01")]})
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelQuantileForecastV1.from_frame(df)


def test_panel_quantile_v1_duplicate_key_strict_raises() -> None:
    df = _panel_quantile_minimal(duplicate=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelQuantileForecastV1.from_frame(df)


def test_panel_quantile_v1_null_interval_start_strict_raises() -> None:
    df = _panel_quantile_minimal(null_interval=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelQuantileForecastV1.from_frame(df)


def test_panel_quantile_v1_null_q_strict_raises() -> None:
    df = _panel_quantile_minimal(null_q=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelQuantileForecastV1.from_frame(df)


def test_panel_quantile_v1_q_out_of_range_strict_raises() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelQuantileForecastV1.from_frame(df)


def test_panel_quantile_v1_warn_mode_does_not_raise() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("warn"):
        PanelQuantileForecastV1.from_frame(df)


def test_panel_quantile_v1_off_mode_does_not_raise() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("off"):
        PanelQuantileForecastV1.from_frame(df)
