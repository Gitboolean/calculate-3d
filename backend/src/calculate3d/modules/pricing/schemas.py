from pydantic import BaseModel, ConfigDict, Field

from calculate3d.core.problems import Problem
from calculate3d.core.schemas import Name


class PlasticInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: Name
    price_per_kg_kop: int = Field(ge=1, description="Ціна за кілограм у копійках; 650 ₴ → 65000")


class Plastic(BaseModel):
    id: str
    name: str
    price_per_kg_kop: int


class PlasticList(BaseModel):
    items: list[Plastic]


class PriceSettingsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tariff_per_kwh_kop: int = Field(ge=0, description="Тариф, копійок за кВт·год; 4,32 ₴ → 432")
    printer_power_w: int = Field(ge=0, description="Середня потужність принтера, цілі вати")
    printer_price_kop: int = Field(ge=0, description="Ціна принтера, копійки")
    printer_lifetime_h: int = Field(ge=1, description="Термін служби, цілі години друку")
    parts_per_hour_kop: int = Field(ge=0, description="Деталі, копійок за годину друку")
    scrap_rate_permille: int = Field(
        ge=0, le=1000, description="Брак у десятих відсотка; 10 % → 100"
    )


class PriceSettings(PriceSettingsInput):
    model_config = ConfigDict(extra="forbid")

    wear_per_hour_kop: int = Field(
        ge=0, description="Знос за годину друку, ROUND_HALF_UP до копійки лише для показу"
    )


class PlasticInUseProblem(Problem):
    items: list[str] = Field(description="Назви виробів, що використовують пластик (AC-03)")
