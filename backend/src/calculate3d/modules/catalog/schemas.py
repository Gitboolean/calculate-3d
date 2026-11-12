from pydantic import BaseModel, ConfigDict, Field, field_validator

from calculate3d.core.schemas import Id, Name
from calculate3d.modules.costing.service import (
    MAX_PLASTICS,
    PlasticUsage,
    PrintTime,
    Quote,
    QuoteInput,
)
from calculate3d.modules.importing.service import FilamentMappingInput, each_filament_once


class ItemInput(QuoteInput):
    """A quote's parameters plus a name — the catalog stores parameters, never a price."""

    name: Name
    filament_mappings: list[FilamentMappingInput] = Field(
        default_factory=list,
        min_length=0,
        max_length=MAX_PLASTICS,
        description=(
            "Необов'язково (ADR 0003): зіставлення з імпорту, що запам'ятовуються разом із виробом;"
            " у відповіді виробу не повертаються"
        ),
    )

    _each_filament_once = field_validator("filament_mappings")(each_filament_once)


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Id
    name: Name
    plastics: list[PlasticUsage] = Field(min_length=1, max_length=MAX_PLASTICS)
    print_time_s: PrintTime


class ItemDetail(Item):
    quote: Quote


class ItemSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Id
    name: Name
    min_donation_kop: int = Field(
        ge=0, description="Перераховано з поточних налаштувань цін (ADR 0003)"
    )


class ItemList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ItemSummary]
