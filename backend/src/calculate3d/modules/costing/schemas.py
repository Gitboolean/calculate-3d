from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError

from calculate3d.core.problems import Problem
from calculate3d.core.schemas import Id

# Whole hours and minutes (AC-07): 3 год 30 хв → 12600.
PrintTime = Annotated[
    int, Field(ge=60, multiple_of=60, description="Час друку в секундах, кратний 60")
]


class PlasticUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    plastic_id: Id
    usage_cg: int = Field(ge=1, description="Витрата в сотих грама; 120 г → 12000")


class QuoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    plastics: list[PlasticUsage] = Field(min_length=1)
    print_time_s: PrintTime

    @field_validator("plastics")
    @classmethod
    def _each_plastic_once(cls, plastics: list[PlasticUsage]) -> list[PlasticUsage]:
        seen: set[str] = set()
        for index, usage in enumerate(plastics):
            if usage.plastic_id in seen:
                detail = InitErrorDetails(
                    type=PydanticCustomError("value_error", "plastic is listed twice"),
                    loc=(index, "plastic_id"),
                    input=usage.plastic_id,
                )
                raise ValidationError.from_exception_data(cls.__name__, [detail])
            seen.add(usage.plastic_id)
        return plastics


class CostBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plastic_kop: int = Field(ge=0)
    electricity_kop: int = Field(ge=0)
    wear_kop: int = Field(ge=0)
    scrap_kop: int = Field(ge=0)


class Quote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_donation_kop: int = Field(ge=0)
    breakdown: CostBreakdown


class SettingsMissingProblem(Problem):
    missing: list[Literal["plastics", "price_settings"]] = Field(
        min_length=1, json_schema_extra={"uniqueItems": True}
    )
