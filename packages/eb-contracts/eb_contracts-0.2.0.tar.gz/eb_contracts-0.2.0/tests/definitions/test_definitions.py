from __future__ import annotations

######################################
# Imports smoke test
######################################


def test_definitions_imports() -> None:
    import eb_contracts.definitions as defs


def test_definitions_modules_import() -> None:
    import eb_contracts.definitions.conventions as conventions
    import eb_contracts.definitions.glossary as glossary
    import eb_contracts.definitions.semantics as semantics
    import eb_contracts.definitions.units as units
