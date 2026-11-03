from pydantic import BaseModel, ConfigDict, Field

from calculate3d.core.problems import Problem
from calculate3d.core.schemas import Id, Name

# Upper bounds (T24, S2-1): see the worst-case arithmetic in modules/costing/schemas.py.
MAX_PRICE_PER_KG_KOP = 1_000_000_000
MAX_TARIFF_PER_KWH_KOP = 1_000_000
MAX_PRINTER_POWER_W = 1_000_000
MAX_PRINTER_PRICE_KOP = 10_000_000_000
MAX_PRINTER_LIFETIME_H = 1_000_000
MAX_PARTS_PER_HOUR_KOP = 100_000_000


class PlasticInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: Name
    price_per_kg_kop: int = Field(
        ge=1,
        le=MAX_PRICE_PER_KG_KOP,
        description="Ціна за кілограм у копійках; 650 ₴ → 65000; до 1 000 000 000",
    )


class Plastic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Id
    name: Name
    price_per_kg_kop: int = Field(ge=1)


class PlasticList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Plastic]


class PriceSettingsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tariff_per_kwh_kop: int = Field(
        ge=0, le=MAX_TARIFF_PER_KWH_KOP, description="Тариф, копійок за кВт·год; 4,32 ₴ → 432"
    )
    printer_power_w: int = Field(
        ge=0, le=MAX_PRINTER_POWER_W, description="Середня потужність принтера, цілі вати"
    )
    printer_price_kop: int = Field(
        ge=0, le=MAX_PRINTER_PRICE_KOP, description="Ціна принтера, копійки"
    )
    printer_lifetime_h: int = Field(
        ge=1, le=MAX_PRINTER_LIFETIME_H, description="Термін служби, цілі години друку"
    )
    parts_per_hour_kop: int = Field(
        ge=0, le=MAX_PARTS_PER_HOUR_KOP, description="Деталі, копійок за годину друку"
    )
    scrap_rate_permille: int = Field(
        ge=0, le=1000, description="Брак у десятих відсотка; 10 % → 100"
    )


class PriceSettings(PriceSettingsInput):
    model_config = ConfigDict(extra="forbid")

    wear_per_hour_kop: int = Field(
        ge=0, description="Знос за годину друку, ROUND_HALF_UP до копійки лише для показу"
    )


class PlasticInUseProblem(Problem):
    items: list[str] = Field(
        min_length=1, description="Назви виробів, що використовують пластик (AC-03)"
    )
