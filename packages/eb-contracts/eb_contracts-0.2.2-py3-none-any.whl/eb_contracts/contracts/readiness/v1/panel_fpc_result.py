"""
Readiness contract models (V1).

This module defines V1 readiness artifacts produced by governance-oriented
evaluation.

V1 includes:
- PanelFPCResultV1: Forecast Primitive Compatibility (FPC) result artifact at an
  entity grain (optionally keyed by run_id / as_of if the producer includes them).

Design notes
------------
- Contracts are schema + validation only. No business rules, no thresholds logic.
- This artifact is intended for cross-repo persistence (parquet/json) so that
  multiple systems can consume the same stable output surface.
- FPC here refers to the *diagnostic result + signals* (not the computation).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final

import pandas as pd

from eb_contracts.contracts._internal.runtime import get_runtime
from eb_contracts.definitions.conventions import ENTITY_ID
from eb_contracts.validation.errors import ContractViolation, ContractViolationError

######################################
# Contract artifacts
######################################


@dataclass(frozen=True, slots=True)
class PanelFPCResultV1:
    """
    Validated Forecast Primitive Compatibility (FPC) artifact at entity grain.

    Required columns (minimum stable surface)
    ----------------------------------------
    - entity_id
    - fpc_class: {"compatible", "marginal", "incompatible"}
    - nsl_base, nsl_ral, delta_nsl
    - hr_base_tau, hr_ral_tau, delta_hr_tau
    - ud

    Optional columns (recommended when available)
    --------------------------------------------
    - cwsl_base, cwsl_ral, delta_cwsl
    - intervals, shortfall_intervals
    - tau (the tau used for HR@tau signals)
    - run_id, as_of (provenance keys)
    - preset, thresholds_ref (threshold provenance)
    - reasons (string or JSON-encoded string)
    """

    frame: pd.DataFrame

    CONTRACT_NAME: ClassVar[Final[str]] = "PanelFPCResultV1"

    # Canonical keys
    ENTITY_COL: ClassVar[Final[str]] = ENTITY_ID

    # Contract-specific columns
    FPC_CLASS_COL: ClassVar[Final[str]] = "fpc_class"

    NSL_BASE_COL: ClassVar[Final[str]] = "nsl_base"
    NSL_RAL_COL: ClassVar[Final[str]] = "nsl_ral"
    DELTA_NSL_COL: ClassVar[Final[str]] = "delta_nsl"

    HR_BASE_TAU_COL: ClassVar[Final[str]] = "hr_base_tau"
    HR_RAL_TAU_COL: ClassVar[Final[str]] = "hr_ral_tau"
    DELTA_HR_TAU_COL: ClassVar[Final[str]] = "delta_hr_tau"

    UD_COL: ClassVar[Final[str]] = "ud"

    # Optional but common
    CWSL_BASE_COL: ClassVar[Final[str]] = "cwsl_base"
    CWSL_RAL_COL: ClassVar[Final[str]] = "cwsl_ral"
    DELTA_CWSL_COL: ClassVar[Final[str]] = "delta_cwsl"

    INTERVALS_COL: ClassVar[Final[str]] = "intervals"
    SHORTFALL_INTERVALS_COL: ClassVar[Final[str]] = "shortfall_intervals"

    TAU_COL: ClassVar[Final[str]] = "tau"

    RUN_ID_COL: ClassVar[Final[str]] = "run_id"
    AS_OF_COL: ClassVar[Final[str]] = "as_of"

    PRESET_COL: ClassVar[Final[str]] = "preset"
    THRESHOLDS_REF_COL: ClassVar[Final[str]] = "thresholds_ref"
    REASONS_COL: ClassVar[Final[str]] = "reasons"

    ALLOWED_FPC_CLASSES: ClassVar[Final[set[str]]] = {
        "compatible",
        "marginal",
        "incompatible",
    }

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> PanelFPCResultV1:
        violations = validate_panel_fpc_result_v1(frame)
        _raise_or_warn(cls.CONTRACT_NAME, violations)
        return cls(frame=frame)


######################################
# Validators
######################################


def validate_panel_fpc_result_v1(frame: pd.DataFrame) -> list[ContractViolation]:
    """Validate a DataFrame against the PanelFPCResultV1 contract."""
    violations: list[ContractViolation] = []

    required = {
        PanelFPCResultV1.ENTITY_COL,
        PanelFPCResultV1.FPC_CLASS_COL,
        PanelFPCResultV1.NSL_BASE_COL,
        PanelFPCResultV1.NSL_RAL_COL,
        PanelFPCResultV1.DELTA_NSL_COL,
        PanelFPCResultV1.HR_BASE_TAU_COL,
        PanelFPCResultV1.HR_RAL_TAU_COL,
        PanelFPCResultV1.DELTA_HR_TAU_COL,
        PanelFPCResultV1.UD_COL,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        violations.append(
            ContractViolation(
                code="missing_columns",
                message=f"Missing required columns: {missing}",
            )
        )
        return violations

    # Required null checks
    for col, code in (
        (PanelFPCResultV1.ENTITY_COL, "null_entity_id"),
        (PanelFPCResultV1.FPC_CLASS_COL, "null_fpc_class"),
        (PanelFPCResultV1.NSL_BASE_COL, "null_nsl_base"),
        (PanelFPCResultV1.NSL_RAL_COL, "null_nsl_ral"),
        (PanelFPCResultV1.DELTA_NSL_COL, "null_delta_nsl"),
        (PanelFPCResultV1.HR_BASE_TAU_COL, "null_hr_base_tau"),
        (PanelFPCResultV1.HR_RAL_TAU_COL, "null_hr_ral_tau"),
        (PanelFPCResultV1.DELTA_HR_TAU_COL, "null_delta_hr_tau"),
        (PanelFPCResultV1.UD_COL, "null_ud"),
    ):
        s = frame.loc[:, col]
        if bool(pd.isna(s).any()):
            violations.append(
                ContractViolation(
                    code=code,
                    message=f"{col} contains nulls",
                )
            )

    # fpc_class domain check (only validate non-null)
    if PanelFPCResultV1.FPC_CLASS_COL in frame.columns:
        s = frame.loc[:, PanelFPCResultV1.FPC_CLASS_COL]
        bad = s.dropna().astype(str).map(lambda x: x not in PanelFPCResultV1.ALLOWED_FPC_CLASSES)
        if bool(bad.any()):
            violations.append(
                ContractViolation(
                    code="invalid_fpc_class",
                    message=(
                        f"{PanelFPCResultV1.FPC_CLASS_COL} must be one of "
                        f"{sorted(PanelFPCResultV1.ALLOWED_FPC_CLASSES)}"
                    ),
                )
            )

    # Numeric columns: require coercible to numeric and finite where non-null
    numeric_cols = [
        PanelFPCResultV1.NSL_BASE_COL,
        PanelFPCResultV1.NSL_RAL_COL,
        PanelFPCResultV1.DELTA_NSL_COL,
        PanelFPCResultV1.HR_BASE_TAU_COL,
        PanelFPCResultV1.HR_RAL_TAU_COL,
        PanelFPCResultV1.DELTA_HR_TAU_COL,
        PanelFPCResultV1.UD_COL,
        # optional
        PanelFPCResultV1.CWSL_BASE_COL,
        PanelFPCResultV1.CWSL_RAL_COL,
        PanelFPCResultV1.DELTA_CWSL_COL,
        PanelFPCResultV1.TAU_COL,
    ]
    for col in numeric_cols:
        if col not in frame.columns:
            continue
        s = frame.loc[:, col]

        # Coerce; then immediately re-wrap as Series to keep Pyright on the rails.
        coerced_raw = pd.to_numeric(s, errors="coerce")
        coerced = pd.Series(coerced_raw, index=s.index)

        # If original non-null values became NaN after coercion => not numeric.
        if bool(s.notna().any()) and bool((pd.isna(coerced) & s.notna()).any()):
            violations.append(
                ContractViolation(
                    code="non_numeric",
                    message=f"{col} must be numeric where present",
                )
            )
            continue

        # Disallow inf/-inf (only check non-null coerced entries)
        non_null = pd.Series(pd.notna(coerced), index=coerced.index)
        coerced_nn = pd.Series(coerced.loc[non_null], index=coerced.index[non_null])
        if bool(coerced_nn.isin([float("inf"), float("-inf")]).any()):
            violations.append(
                ContractViolation(
                    code="non_finite",
                    message=f"{col} contains inf/-inf",
                )
            )

    # intervals / shortfall_intervals (optional) should be integer-like and non-negative
    for col, code in (
        (PanelFPCResultV1.INTERVALS_COL, "invalid_intervals"),
        (PanelFPCResultV1.SHORTFALL_INTERVALS_COL, "invalid_shortfall_intervals"),
    ):
        if col not in frame.columns:
            continue
        s = frame.loc[:, col]
        if s.dropna().empty:
            continue

        coerced_raw = pd.to_numeric(s, errors="coerce")
        coerced = pd.Series(coerced_raw, index=s.index)

        if bool((pd.isna(coerced) & s.notna()).any()):
            violations.append(
                ContractViolation(
                    code=code,
                    message=f"{col} must be numeric/integer-like where present",
                )
            )
            continue

        nn = pd.Series(pd.notna(coerced), index=coerced.index)
        if bool((coerced.loc[nn] < 0).any()):
            violations.append(
                ContractViolation(
                    code=code,
                    message=f"{col} must be >= 0 where present",
                )
            )

    # shortfall_intervals <= intervals when both present
    if (
        PanelFPCResultV1.INTERVALS_COL in frame.columns
        and PanelFPCResultV1.SHORTFALL_INTERVALS_COL in frame.columns
    ):
        a_raw = pd.to_numeric(frame.loc[:, PanelFPCResultV1.INTERVALS_COL], errors="coerce")
        b_raw = pd.to_numeric(
            frame.loc[:, PanelFPCResultV1.SHORTFALL_INTERVALS_COL], errors="coerce"
        )

        a = pd.Series(a_raw, index=frame.index)
        b = pd.Series(b_raw, index=frame.index)

        mask = pd.Series(pd.notna(a) & pd.notna(b), index=frame.index)
        if bool(mask.any()) and bool((b.loc[mask] > a.loc[mask]).any()):
            violations.append(
                ContractViolation(
                    code="shortfall_gt_intervals",
                    message="shortfall_intervals must be <= intervals where both are present",
                )
            )

    # Simple optional string columns validation (non-null values must be str)
    for col in (
        PanelFPCResultV1.RUN_ID_COL,
        PanelFPCResultV1.AS_OF_COL,
        PanelFPCResultV1.PRESET_COL,
        PanelFPCResultV1.THRESHOLDS_REF_COL,
        PanelFPCResultV1.REASONS_COL,
    ):
        if col not in frame.columns:
            continue
        s = frame.loc[:, col].dropna()
        if s.empty:
            continue
        # Use pandas string conversion check to avoid object weirdness
        if not bool(s.map(lambda v: isinstance(v, str)).all()):
            violations.append(
                ContractViolation(
                    code="invalid_string_field",
                    message=f"{col} must be a string where present",
                )
            )

    return violations


######################################
# Runtime behavior
######################################


def _raise_or_warn(contract: str, violations: list[ContractViolation]) -> None:
    """Apply runtime validation behavior."""
    if not violations:
        return

    mode = get_runtime().validation
    if mode == "off":
        return

    if mode == "warn":
        print(f"[eb-contracts] WARN: {contract}: " + "; ".join(v.message for v in violations))
        return

    raise ContractViolationError(contract=contract, violations=violations)
