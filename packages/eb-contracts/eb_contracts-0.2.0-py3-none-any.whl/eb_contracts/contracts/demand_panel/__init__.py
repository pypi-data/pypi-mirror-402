"""
Public demand contract API.

This module provides access to all demand panel contract versions
(e.g., PanelDemandV1).

These contracts define the expected structure of demand / usage
dataframes and support governance-aware validation via versioned
dataclass wrappers.

Demand contracts are intentionally domain-agnostic and are designed
to interoperate with DQC, FPC/RAL, and cost-aware evaluation layers.
"""

from __future__ import annotations

######################################
# Public API
######################################
from eb_contracts.contracts.demand_panel.v1.panel_demand import PanelDemandV1

__all__ = [
    "PanelDemandV1",
]
