"""
Runtime configuration for contract validation.

This module provides a minimal runtime surface used by contract validators to
determine validation behavior (e.g., strict, warn, off).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import contextvars
from dataclasses import dataclass
from typing import Literal

ValidationMode = Literal["strict", "warn", "off"]


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Runtime configuration controlling validation behavior."""

    validation: ValidationMode = "strict"


_runtime_var: contextvars.ContextVar[RuntimeConfig | None] = contextvars.ContextVar(
    "eb_contracts_runtime",
    default=None,
)


def get_runtime() -> RuntimeConfig:
    """Return the active runtime configuration."""
    cfg = _runtime_var.get()
    if cfg is None:
        cfg = RuntimeConfig()
        _runtime_var.set(cfg)
    return cfg


@contextmanager
def set_validation_mode(mode: ValidationMode) -> Iterator[None]:
    """Temporarily set validation behavior within a context."""
    token = _runtime_var.set(RuntimeConfig(validation=mode))
    try:
        yield
    finally:
        _runtime_var.reset(token)
