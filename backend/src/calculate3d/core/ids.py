"""Application-generated identifiers (ADR 0003): UUIDv7 stored as canonical TEXT."""

import uuid


def new_id() -> str:
    return str(uuid.uuid7())
