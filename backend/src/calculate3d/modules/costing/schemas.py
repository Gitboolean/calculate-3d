from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError

from calculate3d.core.problems import Problem
from calculate3d.core.schemas import Id

# Upper bounds (T24, S2-1): far beyond any real print (AC-07: no practical limit), but the worst
# case — every input at its cap, printer_lifetime_h=1, MAX_PLASTICS plastics — must keep
# min_donation_kop <= 2**53-1 (JS safe integer) and every stored value inside SQLite INTEGER.
# Worst case: wear (1e10+1e8)*1e5 h = 1.01e15, electricity 1e9*1e5 = 1e14, plastics
# 32*(1e9*1e8/1e5) = 3.2e13; sum ~1.14e15, x2 with 100 % scrap ~ 2.3e15 < 9.007e15.
MAX_PRINT_TIME_S = 360_000_000  # 100 000 h
MAX_USAGE_CG = 100_000_000  # 1000 kg
MAX_PLASTICS = 32

# Whole hours and minutes (AC-07): 3 год 30 хв → 12600.
PrintTime = Annotated[
    int,
    Field(
        ge=60,
        le=MAX_PRINT_TIME_S,
        multiple_of=60,
        description="Час друку в секундах, кратний 60, до 360 000 000 (100 000 год)",
    ),
]


class PlasticUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    plastic_id: Id
    usage_cg: int = Field(
        ge=1, le=MAX_USAGE_CG, description="Витрата в сотих грама; 120 г → 12000; до 100 000 000"
    )


class QuoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    plastics: list[PlasticUsage] = Field(min_length=1, max_length=MAX_PLASTICS)
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
