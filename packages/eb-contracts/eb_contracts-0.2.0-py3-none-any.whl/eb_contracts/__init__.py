"""
Public API for EB contracts.

This package provides contract artifacts and validation entrypoints for
forecasting and panel-based evaluation.
"""

from __future__ import annotations

from eb_contracts.api.validate import (
    panel_point_v1,
    panel_quantile_v1,
)

######################################
# Public API
######################################
from eb_contracts.contracts._internal.runtime import set_validation_mode

__all__ = [
    "panel_point_v1",
    "panel_quantile_v1",
    "set_validation_mode",
]
