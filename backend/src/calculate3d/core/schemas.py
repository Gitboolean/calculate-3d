"""Pydantic building blocks shared by module schemas."""

from typing import Annotated

from pydantic import StringConstraints

# Plastic and item names (cost-calculator ADR 0006): trimmed first, then 1 to 100 characters.
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
