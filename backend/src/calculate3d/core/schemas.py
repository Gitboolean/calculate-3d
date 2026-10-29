"""Pydantic building blocks shared by module schemas."""

from typing import Annotated

from pydantic import Field, StringConstraints

# Plastic and item names (cost-calculator ADR 0006): trimmed first, then 1 to 100 characters.
# The `\S` pattern is schema-only: the strip + min_length already reject blank names with the
# established error, so a runtime regex would only add a second error to the same input.
Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
    Field(json_schema_extra={"pattern": r"\S"}),
]

# UUIDv7 ids (ADR 0003): the format is documented in the schema only; existence is checked
# against the DB, so a malformed id keeps its current 404 / "not found" behaviour.
Id = Annotated[str, Field(json_schema_extra={"format": "uuid"})]
