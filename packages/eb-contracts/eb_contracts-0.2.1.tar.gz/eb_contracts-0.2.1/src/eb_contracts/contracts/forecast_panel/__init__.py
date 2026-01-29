"""
Public forecast contract API.

This module provides access to all forecast contract versions
(e.g., PanelPointForecastV1, PanelQuantileForecastV1).

These contracts define the expected structure of forecast dataframes
and support validation via versioned dataclass wrappers.
"""

from __future__ import annotations

######################################
# Public API
######################################
from eb_contracts.contracts.forecast_panel.v1.forecast_panel import (
    PanelPointForecastV1,
    PanelQuantileForecastV1,
)

__all__ = [
    "PanelPointForecastV1",
    "PanelQuantileForecastV1",
]
