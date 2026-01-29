"""
Public API for EB contracts.

This package provides contract artifacts and validation entrypoints for
forecasting and panel-based evaluation.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from eb_contracts.api.validate import (
    panel_point_v1,
    panel_quantile_v1,
)
from eb_contracts.contracts._internal.runtime import set_validation_mode

try:
    __version__ = version("eb-contracts")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "panel_point_v1",
    "panel_quantile_v1",
    "set_validation_mode",
]
