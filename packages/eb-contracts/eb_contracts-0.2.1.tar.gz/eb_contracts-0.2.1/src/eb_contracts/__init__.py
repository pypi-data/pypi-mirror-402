"""
Public API for EB contracts.

This package provides contract artifacts and validation entrypoints for
forecasting and panel-based evaluation.
"""

from __future__ import annotations

from importlib.metadata import version as _pkg_version

from eb_contracts.api.validate import (
    panel_point_v1,
    panel_quantile_v1,
)

######################################
# Public API
######################################
from eb_contracts.contracts._internal.runtime import set_validation_mode

__version__ = _pkg_version("eb-contracts")

__all__ = [
    "__version__",
    "panel_point_v1",
    "panel_quantile_v1",
    "set_validation_mode",
]
