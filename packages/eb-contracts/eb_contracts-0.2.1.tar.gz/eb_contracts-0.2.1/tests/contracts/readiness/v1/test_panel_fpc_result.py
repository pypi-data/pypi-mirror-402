from __future__ import annotations

import pandas as pd
import pytest

from eb_contracts.contracts._internal.runtime import set_validation_mode
from eb_contracts.contracts.readiness.v1.panel_fpc_result import PanelFPCResultV1
from eb_contracts.definitions.conventions import ENTITY_ID
from eb_contracts.validation.errors import ContractViolationError

######################################
# Helpers
######################################


def _panel_fpc_minimal(
    *,
    invalid_class: bool = False,
    non_numeric: bool = False,
    null_required: bool = False,
) -> pd.DataFrame:
    fpc_class = "compatible"
    if invalid_class:
        fpc_class = "maybe"

    df = pd.DataFrame(
        {
            ENTITY_ID: ["A", "B"],
            "fpc_class": [fpc_class, fpc_class],
            "nsl_base": [0.10, 0.20],
            "nsl_ral": [0.30, 0.35],
            "delta_nsl": [0.20, 0.15],
            "hr_base_tau": [0.50, 0.55],
            "hr_ral_tau": [0.45, 0.50],
            "delta_hr_tau": [-0.05, -0.05],
            "ud": [5.0, 4.0],
        }
    )

    if non_numeric:
        # Avoid pandas FutureWarning by ensuring the column can hold strings first.
        df["ud"] = df["ud"].astype("object")
        df.loc[0, "ud"] = "not-a-number"

    if null_required:
        df.loc[0, "nsl_base"] = None

    return df


######################################
# PanelFPCResultV1
######################################


def test_panel_fpc_v1_valid_minimal_strict() -> None:
    df = _panel_fpc_minimal()
    with set_validation_mode("strict"):
        artifact = PanelFPCResultV1.from_frame(df)
    assert artifact.frame is df


def test_panel_fpc_v1_missing_columns_strict_raises() -> None:
    df = pd.DataFrame({ENTITY_ID: ["A"], "fpc_class": ["compatible"]})
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelFPCResultV1.from_frame(df)


def test_panel_fpc_v1_invalid_fpc_class_strict_raises() -> None:
    df = _panel_fpc_minimal(invalid_class=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelFPCResultV1.from_frame(df)


def test_panel_fpc_v1_non_numeric_strict_raises() -> None:
    df = _panel_fpc_minimal(non_numeric=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelFPCResultV1.from_frame(df)


def test_panel_fpc_v1_null_required_strict_raises() -> None:
    df = _panel_fpc_minimal(null_required=True)
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        PanelFPCResultV1.from_frame(df)


def test_panel_fpc_v1_warn_mode_does_not_raise() -> None:
    df = _panel_fpc_minimal(invalid_class=True)
    with set_validation_mode("warn"):
        PanelFPCResultV1.from_frame(df)


def test_panel_fpc_v1_off_mode_does_not_raise() -> None:
    df = _panel_fpc_minimal(invalid_class=True)
    with set_validation_mode("off"):
        PanelFPCResultV1.from_frame(df)
