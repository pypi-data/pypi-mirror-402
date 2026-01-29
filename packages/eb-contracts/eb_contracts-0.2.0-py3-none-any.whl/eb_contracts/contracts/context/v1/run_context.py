"""
Context contract models (V1).

This module defines V1 context artifacts for attaching non-tabular metadata to
forecasts, costs, and results.

V1 includes:
- RunContextV1: run-level metadata describing provenance and semantics
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Final

from eb_contracts.contracts._internal.runtime import get_runtime
from eb_contracts.validation.errors import ContractViolation, ContractViolationError

######################################
# Contract artifacts
######################################


@dataclass(frozen=True, slots=True)
class RunContextV1:
    """Validated run-level context metadata."""

    run_id: str
    issued_at: datetime

    model_id: str | None = None
    dataset_id: str | None = None

    horizon: int | None = None
    interval_minutes: int | None = None
    tz: str | None = None

    tags: dict[str, str] | None = None

    CONTRACT_NAME: ClassVar[Final[str]] = "RunContextV1"

    @classmethod
    def from_values(
        cls,
        *,
        run_id: str,
        issued_at: datetime,
        model_id: str | None = None,
        dataset_id: str | None = None,
        horizon: int | None = None,
        interval_minutes: int | None = None,
        tz: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> RunContextV1:
        violations = validate_run_context_v1(
            run_id=run_id,
            issued_at=issued_at,
            model_id=model_id,
            dataset_id=dataset_id,
            horizon=horizon,
            interval_minutes=interval_minutes,
            tz=tz,
            tags=tags,
        )
        _raise_or_warn(cls.CONTRACT_NAME, violations)
        return cls(
            run_id=run_id,
            issued_at=issued_at,
            model_id=model_id,
            dataset_id=dataset_id,
            horizon=horizon,
            interval_minutes=interval_minutes,
            tz=tz,
            tags=tags,
        )


######################################
# Validators
######################################


def validate_run_context_v1(
    *,
    run_id: str,
    issued_at: datetime,
    model_id: str | None,
    dataset_id: str | None,
    horizon: int | None,
    interval_minutes: int | None,
    tz: str | None,
    tags: dict[str, str] | None,
) -> list[ContractViolation]:
    """Validate values against the RunContextV1 contract."""
    violations: list[ContractViolation] = []

    if not run_id or not isinstance(run_id, str):
        violations.append(
            ContractViolation(
                code="invalid_run_id",
                message="run_id must be a non-empty string.",
            )
        )

    if not isinstance(issued_at, datetime):
        violations.append(
            ContractViolation(
                code="invalid_issued_at",
                message="issued_at must be a datetime.",
            )
        )

    if horizon is not None and horizon <= 0:
        violations.append(
            ContractViolation(
                code="invalid_horizon",
                message="horizon must be a positive integer when provided.",
            )
        )

    if interval_minutes is not None and interval_minutes <= 0:
        violations.append(
            ContractViolation(
                code="invalid_interval_minutes",
                message="interval_minutes must be a positive integer when provided.",
            )
        )

    if tags is not None:
        if not isinstance(tags, dict):
            violations.append(
                ContractViolation(
                    code="invalid_tags",
                    message="tags must be a dict[str, str] when provided.",
                )
            )
        else:
            for k, v in tags.items():
                if not isinstance(k, str) or not k:
                    violations.append(
                        ContractViolation(
                            code="invalid_tag_key",
                            message="All tag keys must be non-empty strings.",
                        )
                    )
                    break
                if not isinstance(v, str):
                    violations.append(
                        ContractViolation(
                            code="invalid_tag_value",
                            message="All tag values must be strings.",
                        )
                    )
                    break

    if model_id is not None and not isinstance(model_id, str):
        violations.append(
            ContractViolation(
                code="invalid_model_id",
                message="model_id must be a string when provided.",
            )
        )

    if dataset_id is not None and not isinstance(dataset_id, str):
        violations.append(
            ContractViolation(
                code="invalid_dataset_id",
                message="dataset_id must be a string when provided.",
            )
        )

    if tz is not None and (not isinstance(tz, str) or not tz):
        violations.append(
            ContractViolation(
                code="invalid_tz",
                message="tz must be a non-empty string when provided.",
            )
        )

    return violations


######################################
# Internal helpers
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
