from __future__ import annotations

import pandas as pd
import pytest

from eb_contracts.contracts._internal.runtime import set_validation_mode
from eb_contracts.contracts.costs.v1.cost_asymmetry_spec import CostAsymmetrySpecV1
from eb_contracts.definitions.conventions import (
    ENTITY_ID,
    INTERVAL_START,
)
from eb_contracts.validation.errors import ContractViolationError

######################################
# Helpers
######################################


def _cost_spec_minimal(*, with_effective_at: bool = False) -> pd.DataFrame:
    data: dict[str, object] = {
        ENTITY_ID: ["A", "B"],
        CostAsymmetrySpecV1.COST_RATIO_COL: [2.0, 3.0],
    }
    if with_effective_at:
        data[INTERVAL_START] = [
            pd.Timestamp("2025-01-01 00:00:00"),
            pd.Timestamp("2025-01-01 00:00:00"),
        ]
    return pd.DataFrame(data)


######################################
# CostAsymmetrySpecV1
######################################


def test_cost_asymmetry_v1_valid_minimal_strict() -> None:
    df = _cost_spec_minimal()
    with set_validation_mode("strict"):
        artifact = CostAsymmetrySpecV1.from_frame(df)
    assert artifact.frame is df


def test_cost_asymmetry_v1_valid_with_effective_at_strict() -> None:
    df = _cost_spec_minimal(with_effective_at=True)
    with set_validation_mode("strict"):
        artifact = CostAsymmetrySpecV1.from_frame(df)
    assert artifact.frame is df


def test_cost_asymmetry_v1_missing_columns_strict_raises() -> None:
    df = pd.DataFrame({ENTITY_ID: ["A"]})
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        CostAsymmetrySpecV1.from_frame(df)


def test_cost_asymmetry_v1_null_cost_ratio_strict_raises() -> None:
    df = pd.DataFrame(
        {
            ENTITY_ID: ["A"],
            CostAsymmetrySpecV1.COST_RATIO_COL: [None],
        }
    )
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        CostAsymmetrySpecV1.from_frame(df)


def test_cost_asymmetry_v1_nonpositive_cost_ratio_strict_raises() -> None:
    df = pd.DataFrame(
        {
            ENTITY_ID: ["A", "B"],
            CostAsymmetrySpecV1.COST_RATIO_COL: [0.0, -1.0],
        }
    )
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        CostAsymmetrySpecV1.from_frame(df)


def test_cost_asymmetry_v1_duplicate_entity_without_effective_at_strict_raises() -> None:
    df = pd.DataFrame(
        {
            ENTITY_ID: ["A", "A"],
            CostAsymmetrySpecV1.COST_RATIO_COL: [2.0, 3.0],
        }
    )
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        CostAsymmetrySpecV1.from_frame(df)


def test_cost_asymmetry_v1_duplicate_entity_effective_at_strict_raises() -> None:
    df = pd.DataFrame(
        {
            ENTITY_ID: ["A", "A"],
            INTERVAL_START: [
                pd.Timestamp("2025-01-01 00:00:00"),
                pd.Timestamp("2025-01-01 00:00:00"),
            ],
            CostAsymmetrySpecV1.COST_RATIO_COL: [2.0, 3.0],
        }
    )
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        CostAsymmetrySpecV1.from_frame(df)


def test_cost_asymmetry_v1_null_effective_at_strict_raises() -> None:
    df = pd.DataFrame(
        {
            ENTITY_ID: ["A", "B"],
            INTERVAL_START: [pd.Timestamp("2025-01-01 00:00:00"), pd.NaT],
            CostAsymmetrySpecV1.COST_RATIO_COL: [2.0, 3.0],
        }
    )
    with set_validation_mode("strict"), pytest.raises(ContractViolationError):
        CostAsymmetrySpecV1.from_frame(df)


def test_cost_asymmetry_v1_warn_mode_does_not_raise() -> None:
    df = pd.DataFrame(
        {
            ENTITY_ID: ["A", "A"],
            CostAsymmetrySpecV1.COST_RATIO_COL: [2.0, 3.0],
        }
    )
    with set_validation_mode("warn"):
        CostAsymmetrySpecV1.from_frame(df)


def test_cost_asymmetry_v1_off_mode_does_not_raise() -> None:
    df = pd.DataFrame(
        {
            ENTITY_ID: ["A", "A"],
            CostAsymmetrySpecV1.COST_RATIO_COL: [2.0, 3.0],
        }
    )
    with set_validation_mode("off"):
        CostAsymmetrySpecV1.from_frame(df)
