"""
Public validation entrypoints for contract artifacts.

This module defines stable, versioned entrypoints for validating and constructing
contract-wrapped data artifacts. Consumers should prefer these functions over
importing versioned contract modules directly.
"""

from __future__ import annotations

import pandas as pd

from eb_contracts.contracts.costs.v1.cost_asymmetry_spec import CostAsymmetrySpecV1
from eb_contracts.contracts.demand_panel.v1.panel_demand import (
    PanelDemandV1,
    validate_panel_demand_v1,
)
from eb_contracts.contracts.forecast_panel.v1.forecast_panel import (
    PanelPointForecastV1,
    PanelQuantileForecastV1,
)
from eb_contracts.contracts.results.v1.panel_point_result import PanelPointResultV1

######################################
# Public API
######################################


def panel_demand_v1(panel: PanelDemandV1) -> None:
    """Validate a V1 demand panel artifact."""
    validate_panel_demand_v1(panel)


def panel_point_forecast_v1(frame: pd.DataFrame) -> PanelPointForecastV1:
    """
    Validate and construct a V1 panel point forecast artifact.

    This is the canonical, explicit entrypoint for point forecast panels.
    """
    return PanelPointForecastV1.from_frame(frame)


def panel_quantile_forecast_v1(frame: pd.DataFrame) -> PanelQuantileForecastV1:
    """
    Validate and construct a V1 panel quantile forecast artifact.

    This is the canonical, explicit entrypoint for quantile forecast panels.
    """
    return PanelQuantileForecastV1.from_frame(frame)


# Backwards-compatible aliases (keep these stable for downstream users).
def panel_point_v1(frame: pd.DataFrame) -> PanelPointForecastV1:
    """Alias for `panel_point_forecast_v1` (kept for backwards compatibility)."""
    return panel_point_forecast_v1(frame)


def panel_quantile_v1(frame: pd.DataFrame) -> PanelQuantileForecastV1:
    """Alias for `panel_quantile_forecast_v1` (kept for backwards compatibility)."""
    return panel_quantile_forecast_v1(frame)


def cost_asymmetry_v1(frame: pd.DataFrame) -> CostAsymmetrySpecV1:
    """Validate and construct a V1 cost-asymmetry specification artifact."""
    return CostAsymmetrySpecV1.from_frame(frame)


def panel_point_result_v1(frame: pd.DataFrame) -> PanelPointResultV1:
    """Validate and construct a V1 panel point result artifact."""
    return PanelPointResultV1.from_frame(frame)


__all__ = [
    "cost_asymmetry_v1",
    "panel_demand_v1",
    "panel_point_forecast_v1",
    "panel_point_result_v1",
    "panel_point_v1",
    "panel_quantile_forecast_v1",
    "panel_quantile_v1",
]
