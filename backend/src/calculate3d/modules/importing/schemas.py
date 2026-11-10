from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

from calculate3d.core.problems import Problem
from calculate3d.core.schemas import Id
from calculate3d.modules.costing.service import MAX_PLASTICS, PrintTime
from calculate3d.modules.importing.normalize import MAX_SAFE_INTEGER

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


def each_filament_once(mappings: list[FilamentMappingInput]) -> list[FilamentMappingInput]:
    """One mapping per (name, color) — the UNIQUE key of filament_mappings (contract)."""
    seen: set[tuple[str, str]] = set()
    for index, m in enumerate(mappings):
        key = (m.filament_name, m.filament_color)
        if key in seen:
            detail = InitErrorDetails(
                type=PydanticCustomError("value_error", "filament is mapped twice"),
                loc=(index, "filament_color"),
                input=m.filament_color,
            )
            raise ValidationError.from_exception_data("FilamentMappingList", [detail])
        seen.add(key)
    return mappings


class SlicedPlate(BaseModel):
    """Which plate was imported (AC-02) — the only one with slicing results."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=1, description="Номер пластини в проєкті (`slice_info.config` index)")
    name: str = Field(description="`plater_name` як у слайсері; може бути порожньою")


class SlicerFilament(BaseModel):
    """A slicer filament as the slicer wrote it, plus the remembered plastic (AC-07)."""

    model_config = ConfigDict(extra="forbid")

    filament_name: FilamentName
    filament_type: str = Field(description="Тип філамента з результатів нарізки; лише для показу")
    filament_color: FilamentColor
    usage_mg: int = Field(
        ge=1,
        le=MAX_SAFE_INTEGER,
        description="Точна витрата в мг разом із промивкою (ADR 0004); usage_cg складає веб",
    )
    plastic_id: Id | None = Field(
        description="Пластик із запам'ятаного зіставлення або null (AC-07, AC-09)"
    )


class SlicerFile(BaseModel):
    """The parsed file; it lives only in the response and the web form state (ADR 0001)."""

    model_config = ConfigDict(extra="forbid")

    plate: SlicedPlate
    print_time_s: PrintTime
    filaments: list[SlicerFilament] = Field(min_length=1, max_length=MAX_PLASTICS)


class ImportSettingsMissingProblem(Problem):
    code: Literal["importing.settings_missing"]
    missing: list[Literal["plastics", "price_settings"]] = Field(
        min_length=1, json_schema_extra={"uniqueItems": True}
    )


class ImportRejectedProblem(Problem):
    """A rejection of the SAD §8 check chain — one reason per code (AC-12, AC-13, AC-14)."""

    code: Literal[
        "importing.not_slicer_project",
        "importing.not_sliced",
        "importing.multiple_sliced_plates",
        "importing.corrupted_file",
        "importing.print_time_out_of_range",
        "importing.no_filament_usage",
    ]
