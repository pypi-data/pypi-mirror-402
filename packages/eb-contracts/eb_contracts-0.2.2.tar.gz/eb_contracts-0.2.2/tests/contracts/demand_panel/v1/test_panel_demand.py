"""
Unit tests for the PanelDemandV1 contract (day-interval and timestamp modes).

These tests validate:
- happy-path validation passes
- missing required columns raise
- invalid interval index range raises
- negative target values raise
- timestamp parsing requirements are enforced
- gates must be nullable booleans with domain {True, False, NA}
- structural zeros are non-trainable (y must be null; must not be marked observable)
"""

from __future__ import annotations

import pandas as pd
import pytest

from eb_contracts.contracts.demand_panel.v1.panel_demand import (
    PanelDemandV1,
    validate_panel_demand_v1,
)


def _make_day_interval_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "STORE_ID": [101, 101, 101],
            "FORECAST_ENTITY_ID": [1, 1, 1],
            "BUSINESS_DAY": ["2025-05-01", "2025-05-01", "2025-05-01"],
            "INTERVAL_30_INDEX": [0, 1, 2],
            "y": [None, 4.0, 8.0],
            "is_observable": [True, True, True],
            "is_possible": [True, True, True],
            "is_structural_zero": [False, False, False],
        }
    )


def _make_timestamp_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "STORE_ID": [101, 101, 101],
            "FORECAST_ENTITY_ID": [1, 1, 1],
            "ts": ["2025-05-01 00:00:00", "2025-05-01 00:30:00", "2025-05-01 01:00:00"],
            "y": [None, 4.0, 8.0],
            "is_observable": [True, True, True],
            "is_possible": [True, True, True],
            "is_structural_zero": [False, False, False],
        }
    )


def test_validate_day_interval_happy_path() -> None:
    df = _make_day_interval_frame()

    panel = PanelDemandV1.from_frame(
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
        validate=True,
    )

    # explicit call should also pass
    validate_panel_demand_v1(panel)


def test_validate_raises_on_missing_required_columns() -> None:
    df = _make_day_interval_frame().drop(columns=["is_possible"])

    panel = PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="day_interval",
        day_col="BUSINESS_DAY",
        interval_index_col="INTERVAL_30_INDEX",
        interval_minutes=30,
        periods_per_day=48,
        validate=False,
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_panel_demand_v1(panel)


def test_validate_raises_on_invalid_interval_index_range() -> None:
    df = _make_day_interval_frame()
    df.loc[0, "INTERVAL_30_INDEX"] = 48  # out of range for periods_per_day=48

    panel = PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="day_interval",
        day_col="BUSINESS_DAY",
        interval_index_col="INTERVAL_30_INDEX",
        interval_minutes=30,
        periods_per_day=48,
        validate=False,
    )

    with pytest.raises(ValueError, match="must be in \\[0, 47\\]"):
        validate_panel_demand_v1(panel)


def test_validate_raises_on_negative_target_values() -> None:
    df = _make_day_interval_frame()
    df.loc[1, "y"] = -1.0

    panel = PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="day_interval",
        day_col="BUSINESS_DAY",
        interval_index_col="INTERVAL_30_INDEX",
        interval_minutes=30,
        periods_per_day=48,
        validate=False,
    )

    with pytest.raises(ValueError, match="contains negative values"):
        validate_panel_demand_v1(panel)


def test_validate_timestamp_happy_path() -> None:
    df = _make_timestamp_frame()

    panel = PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="timestamp",
        ts_col="ts",
        is_observable_col="is_observable",
        is_possible_col="is_possible",
        is_structural_zero_col="is_structural_zero",
        validate=True,
    )

    validate_panel_demand_v1(panel)


def test_validate_timestamp_raises_on_unparsable_ts() -> None:
    df = _make_timestamp_frame()
    df.loc[0, "ts"] = "not-a-timestamp"

    panel = PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="timestamp",
        ts_col="ts",
        validate=False,
    )

    with pytest.raises(ValueError, match="must be datetime-like"):
        validate_panel_demand_v1(panel)


def test_validate_raises_on_invalid_gate_domain() -> None:
    df = _make_day_interval_frame()
    df.loc[0, "is_observable"] = "yes"  # invalid: must be True/False/NA only

    panel = PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="day_interval",
        day_col="BUSINESS_DAY",
        interval_index_col="INTERVAL_30_INDEX",
        interval_minutes=30,
        periods_per_day=48,
        validate=False,
    )

    with pytest.raises(ValueError, match="must contain only True/False/NA"):
        validate_panel_demand_v1(panel)


def test_validate_raises_when_structural_zero_has_non_null_y() -> None:
    df = _make_day_interval_frame()
    df.loc[0, "is_structural_zero"] = True
    df.loc[0, "y"] = 0.0  # invalid: structural zeros must have null y

    panel = PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="day_interval",
        day_col="BUSINESS_DAY",
        interval_index_col="INTERVAL_30_INDEX",
        interval_minutes=30,
        periods_per_day=48,
        validate=False,
    )

    with pytest.raises(ValueError, match="Structural-zero intervals must have null targets"):
        validate_panel_demand_v1(panel)


def test_validate_raises_when_structural_zero_marked_observable() -> None:
    df = _make_day_interval_frame()
    df.loc[0, "is_structural_zero"] = True
    df.loc[0, "y"] = None
    df.loc[0, "is_observable"] = True  # invalid: structural zeros must not be observable

    panel = PanelDemandV1.from_frame(
        frame=df,
        keys=["STORE_ID", "FORECAST_ENTITY_ID"],
        y_col="y",
        time_mode="day_interval",
        day_col="BUSINESS_DAY",
        interval_index_col="INTERVAL_30_INDEX",
        interval_minutes=30,
        periods_per_day=48,
        validate=False,
    )

    with pytest.raises(ValueError, match="Structural-zero intervals must not be marked observable"):
        validate_panel_demand_v1(panel)
