"""
Shared typing definitions for EB contracts.

This module centralizes type aliases and lightweight protocol definitions
used across contract artifacts, validators, and public entrypoints.

It contains no runtime logic.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

import pandas as pd

######################################
# Core data structures
######################################

# Canonical DataFrame type used throughout contract artifacts.
Frame: TypeAlias = pd.DataFrame


######################################
# Validation behavior
######################################

ValidationMode: TypeAlias = Literal["strict", "warn", "off"]


######################################
# Contract markers
######################################

# Marker alias for validated contract artifacts.
# Contract classes typically expose a `.frame` attribute of type Frame.
ContractArtifact: TypeAlias = object
