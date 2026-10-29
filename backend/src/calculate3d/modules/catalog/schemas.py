from pydantic import BaseModel, ConfigDict, Field

from calculate3d.core.schemas import Id, Name
from calculate3d.modules.costing.service import PlasticUsage, PrintTime, Quote, QuoteInput


class ItemInput(QuoteInput):
    """A quote's parameters plus a name — the catalog stores parameters, never a price."""

    name: Name


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Id
    name: Name
    plastics: list[PlasticUsage] = Field(min_length=1)
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
