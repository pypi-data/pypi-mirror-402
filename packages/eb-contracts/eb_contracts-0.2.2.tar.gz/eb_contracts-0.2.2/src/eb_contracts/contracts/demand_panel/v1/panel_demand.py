"""
PanelDemandV1 contract.

A domain-agnostic, governance-aware demand panel contract intended to support forecasting,
DQC, FPC/RAL diagnostics, and cost-aware evaluation.

Core principles
---------------
- Identity (keys) and time indexing must be present and well-formed.
- Governance gates are **nullable booleans** with domain {True, False, NA}.
- Targets are numeric when present and nonnegative.
- Structural impossibility implies non-trainability (minimal universal semantic):
  - structural_zero == True => y must be NA
  - structural_zero == True => is_observable must not be True

This contract intentionally avoids domain-specific policy (e.g., "observable implies y is present").
Such rules can be enforced upstream or via domain-specific adapters.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import pandas as pd

TimeMode = Literal["timestamp", "day_interval"]


@dataclass(frozen=True, slots=True)
class PanelDemandV1:
    """A normalized, validated demand panel."""

    frame: pd.DataFrame
    keys: tuple[str, ...]
    y_col: str

    time_mode: TimeMode
    ts_col: str | None = None
    day_col: str | None = None
    interval_index_col: str | None = None

    interval_minutes: int | None = None
    periods_per_day: int | None = None
    business_day_start_local_minutes: int | None = None

    is_observable_col: str = "is_observable"
    is_possible_col: str = "is_possible"
    is_structural_zero_col: str = "is_structural_zero"

    @classmethod
    def from_frame(
        cls,
        frame: pd.DataFrame,
        *,
        keys: Sequence[str],
        y_col: str,
        time_mode: TimeMode,
        ts_col: str | None = None,
        day_col: str | None = None,
        interval_index_col: str | None = None,
        interval_minutes: int | None = None,
        periods_per_day: int | None = None,
        business_day_start_local_minutes: int | None = None,
        is_observable_col: str = "is_observable",
        is_possible_col: str = "is_possible",
        is_structural_zero_col: str = "is_structural_zero",
        validate: bool = True,
    ) -> PanelDemandV1:
        obj = cls(
            frame=frame,
            keys=tuple(keys),
            y_col=y_col,
            time_mode=time_mode,
            ts_col=ts_col,
            day_col=day_col,
            interval_index_col=interval_index_col,
            interval_minutes=interval_minutes,
            periods_per_day=periods_per_day,
            business_day_start_local_minutes=business_day_start_local_minutes,
            is_observable_col=is_observable_col,
            is_possible_col=is_possible_col,
            is_structural_zero_col=is_structural_zero_col,
        )
        if validate:
            validate_panel_demand_v1(obj)
        return obj


def _assert_nullable_bool_series(s: pd.Series, *, name: str) -> None:
    """
    Require that values are in {True, False, NA}.

    Accepts:
    - bool dtype
    - pandas nullable boolean dtype ("boolean")
    - object dtype containing only bools + nulls

    This is stricter than "castable-to-bool" and preserves governance semantics
    for tri-state gates (unknown vs false).
    """
    if s.dtype == bool or str(s.dtype) == "boolean":
        return

    nn = s.dropna()
    if nn.empty:
        return

    bad = ~nn.map(lambda v: isinstance(v, bool))
    if bool(bad.any()):
        raise ValueError(f"Gate column {name!r} must contain only True/False/NA values.")


def validate_panel_demand_v1(panel: PanelDemandV1) -> None:
    """Validate a PanelDemandV1 instance.

    Validation is semantic (governance-aware) and designed to prevent misuse:
    - Keys and time index must exist
    - Gates must exist and be nullable booleans with domain {True, False, NA}
    - y must be numeric when present and nonnegative
    - time must be well-formed per mode
    - structural impossibility implies non-trainability (minimal universal semantic)

    Notes:
    - We intentionally keep this validator minimal and deterministic.
    - Monotonicity and uniqueness checks may be added later (or made configurable)
      to avoid over-constraining datasets that rely on scaffolds or sparse windows.
    """
    df = panel.frame

    # --- required columns
    required: list[str] = [
        *panel.keys,
        panel.y_col,
        panel.is_observable_col,
        panel.is_possible_col,
        panel.is_structural_zero_col,
    ]

    if panel.time_mode == "timestamp":
        if not panel.ts_col:
            raise ValueError("time_mode='timestamp' requires ts_col.")
        required.append(panel.ts_col)

    elif panel.time_mode == "day_interval":
        if not panel.day_col or not panel.interval_index_col:
            raise ValueError("time_mode='day_interval' requires day_col and interval_index_col.")
        required.extend([panel.day_col, panel.interval_index_col])

        if panel.interval_minutes is None or panel.periods_per_day is None:
            raise ValueError(
                "time_mode='day_interval' requires interval_minutes and periods_per_day."
            )

        # Optional timestamp column is allowed for debugging/joins even in day_interval mode.
        if panel.ts_col:
            required.append(panel.ts_col)

    else:
        raise ValueError(f"Unrecognized time_mode: {panel.time_mode!r}")

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # --- gates: nullable boolean domain (True/False/NA)
    #
    # NOTE: We explicitly coerce to Series for Pyright. Pandas typing can infer df[col]
    # as Series | DataFrame | Unknown depending on key typing, even when "col" is str.
    _assert_nullable_bool_series(
        pd.Series(df.loc[:, panel.is_observable_col]),
        name=panel.is_observable_col,
    )
    _assert_nullable_bool_series(
        pd.Series(df.loc[:, panel.is_possible_col]),
        name=panel.is_possible_col,
    )
    _assert_nullable_bool_series(
        pd.Series(df.loc[:, panel.is_structural_zero_col]),
        name=panel.is_structural_zero_col,
    )

    # --- target: numeric when present, nonnegative
    y_raw = df[panel.y_col]
    y = pd.to_numeric(y_raw, errors="coerce")
    y_series = pd.Series(y, index=y_raw.index)

    # If non-null originals became NaN after coercion => non-numeric values present.
    if bool(y_raw.notna().any()) and bool((y_series.isna() & y_raw.notna()).any()):
        raise ValueError(f"Target column {panel.y_col!r} must be numeric where present.")

    if bool((y_series.dropna() < 0).any()):
        raise ValueError(f"Target column {panel.y_col!r} contains negative values.")

    # --- day/interval mode checks
    if panel.time_mode == "day_interval":
        if panel.periods_per_day is None:
            raise ValueError("periods_per_day must be provided for time_mode='day_interval'.")

        idx_raw = df[panel.interval_index_col]
        idx = pd.to_numeric(idx_raw, errors="coerce")
        idx_series = pd.Series(idx, index=idx_raw.index)

        # Disallow non-numeric junk where provided
        if bool((idx_series.isna() & idx_raw.notna()).any()):
            raise ValueError(
                f"interval_index_col {panel.interval_index_col!r} must be integer-like."
            )

        nn = idx_series.dropna()
        if bool(((nn < 0) | (nn >= panel.periods_per_day)).any()):
            raise ValueError(
                f"interval_index_col {panel.interval_index_col!r} must be in "
                f"[0, {panel.periods_per_day - 1}]."
            )

        day = pd.to_datetime(df[panel.day_col], errors="coerce").dt.date
        if bool(pd.Series(day, index=df.index).isna().any()):
            raise ValueError(f"day_col {panel.day_col!r} must be date-like (parsable).")

    # --- timestamp mode checks (or optional timestamp column)
    if panel.ts_col:
        ts = pd.to_datetime(df[panel.ts_col], errors="coerce")
        if bool(pd.Series(ts, index=df.index).isna().any()):
            raise ValueError(f"ts_col {panel.ts_col!r} must be datetime-like (parsable).")

    # --- minimal governance semantics (agnostic)
    structural = df[panel.is_structural_zero_col]
    observable = df[panel.is_observable_col]

    # Structural impossibility => non-trainable: y must be null
    mask = structural == True  # noqa: E712 (explicit tri-state check)
    if bool(mask.any()) and bool(y_series.loc[mask].notna().any()):
        raise ValueError("Structural-zero intervals must have null targets (y).")

    # Structural zero should not be marked observable
    if bool(mask.any()) and bool((observable.loc[mask] == True).any()):  # noqa: E712
        raise ValueError("Structural-zero intervals must not be marked observable.")
