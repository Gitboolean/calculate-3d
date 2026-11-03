"""Pydantic building blocks shared by module schemas."""

from typing import Annotated

from pydantic import BeforeValidator, Field, StringConstraints

from calculate3d.core.text import normalize_name


def _normalise(value: object) -> object:
    # Non-str input passes through so type errors keep their usual shape.
    return normalize_name(value) if isinstance(value, str) else value


# Plastic and item names (cost-calculator ADR 0006): normalised first (NFC, trimmed of whitespace
# and invisible format characters), then measured 1 to 100 characters, so NFC expansion cannot
# push an accepted name past the limit. The `\S` pattern is schema-only: the normalisation +
# min_length already reject blank names with the established error, so a runtime regex would only
# add a second error to the same input. The bounds sit on an inner `Annotated` so they stay
# native string checks (`string_too_short` / `string_too_long`), not a generic post-validator.
Name = Annotated[
    Annotated[str, StringConstraints(min_length=1, max_length=100)],
    BeforeValidator(_normalise),
    Field(json_schema_extra={"pattern": r"\S"}),
]

# UUIDv7 ids (ADR 0003): the format is documented in the schema only; existence is checked
# against the DB, so a malformed id keeps its current 404 / "not found" behaviour.
Id = Annotated[str, Field(json_schema_extra={"format": "uuid"})]
