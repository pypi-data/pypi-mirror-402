from __future__ import annotations

import pandas as pd
import pytest

from eb_contracts.api import validate as validate_module
from eb_contracts.api.validate import (
    panel_demand_v1,
    panel_point_forecast_v1,
    panel_point_v1,
    panel_quantile_forecast_v1,
    panel_quantile_v1,
)
from eb_contracts.contracts._internal.runtime import set_validation_mode
from eb_contracts.contracts.demand_panel.v1.panel_demand import PanelDemandV1
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


def _panel_point_minimal(*, duplicate: bool = False) -> pd.DataFrame:
    ts = [
        pd.Timestamp("2025-01-01 00:00:00"),
        pd.Timestamp("2025-01-01 00:30:00"),
    ]
    if duplicate:
        ts = [ts[0], ts[0]]

    return pd.DataFrame(
        {
            ENTITY_ID: ["A", "A"],
            INTERVAL_START: ts,
            Y_TRUE: [10.0, 12.0],
            Y_PRED: [11.0, 13.0],
        }
    )


def _panel_quantile_minimal(*, q_out_of_range: bool = False) -> pd.DataFrame:
    q = [0.5, 0.9]
    if q_out_of_range:
        q = [0.5, 1.0]

    return pd.DataFrame(
        {
            ENTITY_ID: ["A", "A"],
            INTERVAL_START: [
                pd.Timestamp("2025-01-01 00:00:00"),
                pd.Timestamp("2025-01-01 00:00:00"),
            ],
            Y_TRUE: [10.0, 10.0],
            Q: q,
            Y_PRED_Q: [9.0, 12.0],
        }
    )


def _panel_demand_minimal(*, missing_required: bool = False) -> PanelDemandV1:
    df = pd.DataFrame(
        {
            "STORE_ID": [101, 101],
            "FORECAST_ENTITY_ID": [1, 1],
            "BUSINESS_DAY": ["2025-05-01", "2025-05-01"],
            "INTERVAL_30_INDEX": [0, 1],
            "y": [None, 4.0],
            "is_observable": [True, True],
            "is_possible": [True, True],
            "is_structural_zero": [False, False],
        }
    )

    if missing_required:
        df = df.drop(columns=["is_possible"])

    return PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="day_interval",
        day_col="BUSINESS_DAY",
        interval_index_col="INTERVAL_30_INDEX",
        interval_minutes=30,
        periods_per_day=48,
        business_day_start_local_minutes=240,
        is_observable_col="is_observable",
        is_possible_col="is_possible",
        is_structural_zero_col="is_structural_zero",
        validate=not missing_required,
    )


######################################
# Entry points: strict mode
######################################


def test_panel_point_v1_returns_point_artifact() -> None:
    df = _panel_point_minimal()
    with set_validation_mode("strict"):
        artifact = panel_point_v1(df)
    assert isinstance(artifact, PanelPointForecastV1)
    assert artifact.frame is df


def test_panel_point_forecast_v1_returns_point_artifact() -> None:
    df = _panel_point_minimal()
    with set_validation_mode("strict"):
        artifact = panel_point_forecast_v1(df)
    assert isinstance(artifact, PanelPointForecastV1)
    assert artifact.frame is df


def test_panel_quantile_v1_returns_quantile_artifact() -> None:
    df = _panel_quantile_minimal()
    with set_validation_mode("strict"):
        artifact = panel_quantile_v1(df)
    assert isinstance(artifact, PanelQuantileForecastV1)
    assert artifact.frame is df


def test_panel_quantile_forecast_v1_returns_quantile_artifact() -> None:
    df = _panel_quantile_minimal()
    with set_validation_mode("strict"):
        artifact = panel_quantile_forecast_v1(df)
    assert isinstance(artifact, PanelQuantileForecastV1)
    assert artifact.frame is df


def test_panel_point_v1_strict_raises_on_invalid_frame() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        panel_point_v1(df)


def test_panel_point_forecast_v1_strict_raises_on_invalid_frame() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        panel_point_forecast_v1(df)


def test_panel_quantile_v1_strict_raises_on_invalid_frame() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        panel_quantile_v1(df)


def test_panel_quantile_forecast_v1_strict_raises_on_invalid_frame() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        panel_quantile_forecast_v1(df)


def test_panel_demand_v1_strict_validates_panel() -> None:
    panel = _panel_demand_minimal()
    with set_validation_mode("strict"):
        result = panel_demand_v1(panel)
    assert result is None


def test_panel_demand_v1_strict_raises_on_invalid_panel() -> None:
    panel = _panel_demand_minimal(missing_required=True)
    with set_validation_mode("strict"), pytest.raises(ValueError):
        panel_demand_v1(panel)


######################################
# Entry points: public API aliases
######################################


def test_panel_point_v1_alias_delegates_to_panel_point_forecast_v1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Public API stability: panel_point_v1 should remain a backwards-compatible
    alias that delegates to the canonical panel_point_forecast_v1.
    """
    sentinel = object()

    def _fake(_: pd.DataFrame) -> object:
        return sentinel

    monkeypatch.setattr(validate_module, "panel_point_forecast_v1", _fake)

    out = validate_module.panel_point_v1(pd.DataFrame())
    assert out is sentinel


def test_panel_quantile_v1_alias_delegates_to_panel_quantile_forecast_v1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Public API stability: panel_quantile_v1 should remain a backwards-compatible
    alias that delegates to the canonical panel_quantile_forecast_v1.
    """
    sentinel = object()

    def _fake(_: pd.DataFrame) -> object:
        return sentinel

    monkeypatch.setattr(validate_module, "panel_quantile_forecast_v1", _fake)

    out = validate_module.panel_quantile_v1(pd.DataFrame())
    assert out is sentinel


######################################
# Entry points: warn / off modes
######################################


def test_panel_point_v1_warn_does_not_raise() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("warn"):
        panel_point_v1(df)


def test_panel_point_v1_off_does_not_raise() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("off"):
        panel_point_v1(df)


def test_panel_point_forecast_v1_warn_does_not_raise() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("warn"):
        panel_point_forecast_v1(df)


def test_panel_point_forecast_v1_off_does_not_raise() -> None:
    df = _panel_point_minimal(duplicate=True)
    with set_validation_mode("off"):
        panel_point_forecast_v1(df)


def test_panel_quantile_v1_warn_does_not_raise() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("warn"):
        panel_quantile_v1(df)


def test_panel_quantile_v1_off_does_not_raise() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("off"):
        panel_quantile_v1(df)


def test_panel_quantile_forecast_v1_warn_does_not_raise() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("warn"):
        panel_quantile_forecast_v1(df)


def test_panel_quantile_forecast_v1_off_does_not_raise() -> None:
    df = _panel_quantile_minimal(q_out_of_range=True)
    with set_validation_mode("off"):
        panel_quantile_forecast_v1(df)


def test_panel_demand_v1_warn_still_raises_on_invalid_panel() -> None:
    panel = _panel_demand_minimal(missing_required=True)
    with set_validation_mode("warn"), pytest.raises(ValueError):
        panel_demand_v1(panel)


def test_panel_demand_v1_off_still_raises_on_invalid_panel() -> None:
    panel = _panel_demand_minimal(missing_required=True)
    with set_validation_mode("off"), pytest.raises(ValueError):
        panel_demand_v1(panel)
