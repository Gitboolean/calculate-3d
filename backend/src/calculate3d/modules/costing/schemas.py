from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from calculate3d.core.problems import Problem

# Whole hours and minutes (AC-07): 3 год 30 хв → 12600.
PrintTime = Annotated[
    int, Field(ge=60, multiple_of=60, description="Час друку в секундах, кратний 60")
]


class PlasticUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    plastic_id: str
    usage_cg: int = Field(ge=1, description="Витрата в сотих грама; 120 г → 12000")


class QuoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    plastics: list[PlasticUsage] = Field(min_length=1)
    print_time_s: PrintTime

    @model_validator(mode="after")
    def _each_plastic_once(self) -> Self:
        ids = [usage.plastic_id for usage in self.plastics]
        if len(ids) != len(set(ids)):
            raise ValueError("plastic is listed twice")
        return self


class CostBreakdown(BaseModel):
    plastic_kop: int
    electricity_kop: int
    wear_kop: int
    scrap_kop: int


class Quote(BaseModel):
    min_donation_kop: int
    breakdown: CostBreakdown


class SettingsMissingProblem(Problem):
    missing: list[Literal["plastics", "price_settings"]]
