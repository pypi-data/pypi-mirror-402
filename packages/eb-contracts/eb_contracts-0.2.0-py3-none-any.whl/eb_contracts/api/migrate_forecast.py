"""
Forecast migration helpers.

This module contains explicit utilities for adapting "in the wild" forecast frames
into EB contract artifacts.

Migration is intentionally explicit:
- You provide column mappings.
- The output is a validated contract artifact (unless validation mode is off).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import pandas as pd

from eb_contracts.contracts.forecast_panel.v1.forecast_panel import (
    PanelPointForecastV1,
    PanelQuantileForecastV1,
)
from eb_contracts.contracts.results.v1.panel_point_result import PanelPointResultV1

######################################
# Mapping specs
######################################


@dataclass(frozen=True, slots=True)
class PanelPointColumns:
    """Column mapping for point forecasts."""

    entity_id: str
    interval_start: str
    y_true: str
    y_pred: str


@dataclass(frozen=True, slots=True)
class PanelQuantileColumns:
    """Column mapping for quantile forecasts."""

    entity_id: str
    interval_start: str
    y_true: str
    q: str
    y_pred_q: str


######################################
# Public API
######################################


_RESULT_COLUMNS: Final[set[str]] = {
    PanelPointResultV1.Y_TRUE_COL,
    PanelPointResultV1.Y_PRED_COL,
}


def to_panel_point_v1(frame: pd.DataFrame, *, columns: PanelPointColumns) -> PanelPointForecastV1:
    """Adapt a frame into the PanelPointForecastV1 contract."""
    out = frame.rename(
        columns={
            columns.entity_id: PanelPointForecastV1.ENTITY_COL,
            columns.interval_start: PanelPointForecastV1.INTERVAL_START_COL,
            columns.y_true: PanelPointForecastV1.Y_TRUE_COL,
            columns.y_pred: PanelPointForecastV1.Y_PRED_COL,
        }
    )
    keep = [
        PanelPointForecastV1.ENTITY_COL,
        PanelPointForecastV1.INTERVAL_START_COL,
        PanelPointForecastV1.Y_TRUE_COL,
        PanelPointForecastV1.Y_PRED_COL,
    ]
    return PanelPointForecastV1.from_frame(out.loc[:, keep])


def to_panel_quantile_v1(
    frame: pd.DataFrame, *, columns: PanelQuantileColumns
) -> PanelQuantileForecastV1:
    """Adapt a frame into the PanelQuantileForecastV1 contract."""
    out = frame.rename(
        columns={
            columns.entity_id: PanelQuantileForecastV1.ENTITY_COL,
            columns.interval_start: PanelQuantileForecastV1.INTERVAL_START_COL,
            columns.y_true: PanelQuantileForecastV1.Y_TRUE_COL,
            columns.q: PanelQuantileForecastV1.Q_COL,
            columns.y_pred_q: PanelQuantileForecastV1.Y_PRED_Q_COL,
        }
    )
    keep = [
        PanelQuantileForecastV1.ENTITY_COL,
        PanelQuantileForecastV1.INTERVAL_START_COL,
        PanelQuantileForecastV1.Y_TRUE_COL,
        PanelQuantileForecastV1.Q_COL,
        PanelQuantileForecastV1.Y_PRED_Q_COL,
    ]
    return PanelQuantileForecastV1.from_frame(out.loc[:, keep])


def to_panel_point_result_v1(
    frame: pd.DataFrame, *, columns: PanelPointColumns
) -> PanelPointResultV1:
    """Adapt a frame into the PanelPointResultV1 contract."""
    out = frame.rename(
        columns={
            columns.entity_id: PanelPointResultV1.ENTITY_COL,
            columns.interval_start: PanelPointResultV1.INTERVAL_START_COL,
            columns.y_true: PanelPointResultV1.Y_TRUE_COL,
            columns.y_pred: PanelPointResultV1.Y_PRED_COL,
        }
    )
    keep = [
        PanelPointResultV1.ENTITY_COL,
        PanelPointResultV1.INTERVAL_START_COL,
        PanelPointResultV1.Y_TRUE_COL,
        PanelPointResultV1.Y_PRED_COL,
    ]
    return PanelPointResultV1.from_frame(out.loc[:, keep])
