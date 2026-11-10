from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from calculate3d.core.schemas import Id

MAX_FILAMENT_NAME = 200

# Keys arrive already normalized by the parser (SAD §8), so the input checks the canonical form
# instead of normalizing again: a trimmed 1–200 code-point name and an upper-case #RRGGBB.
FilamentName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=MAX_FILAMENT_NAME, pattern=r"^\S(.*\S)?$"),
]
FilamentColor = Annotated[str, StringConstraints(pattern=r"^#[0-9A-F]{6}$")]


class FilamentMappingInput(BaseModel):
    """The author's choice «slicer filament → plastic»; upserted by (name, color) (AC-07, AC-08)."""

    model_config = ConfigDict(extra="forbid")

    filament_name: FilamentName
    filament_color: FilamentColor
    plastic_id: Annotated[Id, Field(description="filament_mappings.plastic_id → plastics.id")]
