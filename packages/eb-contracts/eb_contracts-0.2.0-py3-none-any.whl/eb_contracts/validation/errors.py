"""
Error types for contract validation.

This module defines structured validation violations and a single exception type
raised when validation fails in strict mode.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContractViolation:
    """A single contract violation discovered during validation."""

    code: str
    message: str


class ContractViolationError(ValueError):
    """Raised when one or more contract violations occur in strict mode."""

    def __init__(self, *, contract: str, violations: Sequence[ContractViolation]) -> None:
        self.contract = contract
        self.violations = list(violations)
        joined = "; ".join(v.message for v in self.violations)
        super().__init__(f"{contract}: {joined}")
