from pydantic import BaseModel, Field

from calculate3d.core.schemas import Name
from calculate3d.modules.costing.service import PlasticUsage, Quote, QuoteInput


class ItemInput(QuoteInput):
    """A quote's parameters plus a name — the catalog stores parameters, never a price."""

    name: Name


class Item(BaseModel):
    id: str
    name: str
    plastics: list[PlasticUsage]
    print_time_s: int


class ItemDetail(Item):
    quote: Quote


class ItemSummary(BaseModel):
    id: str
    name: str
    min_donation_kop: int = Field(description="Перераховано з поточних налаштувань цін (ADR 0003)")


class ItemList(BaseModel):
    items: list[ItemSummary]
