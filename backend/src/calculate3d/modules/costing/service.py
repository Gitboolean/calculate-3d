"""costing — prices a print from the current pricing data; stores nothing (ADR 0002, 0005)."""

from collections.abc import Sequence

from calculate3d.core.errors import AppError
from calculate3d.modules.costing import domain
from calculate3d.modules.costing.schemas import CostBreakdown
from calculate3d.modules.costing.schemas import PlasticUsage as PlasticUsage
from calculate3d.modules.costing.schemas import Quote as Quote
from calculate3d.modules.costing.schemas import QuoteInput as QuoteInput
from calculate3d.modules.costing.schemas import SettingsMissingProblem as SettingsMissingProblem
from calculate3d.modules.pricing import service as pricing_service

DbConnection = pricing_service.DbConnection


class SettingsMissing(AppError):
    def __init__(self, missing: list[str]) -> None:
        super().__init__(
            "costing.settings_missing", "Price settings are not set", 409, missing=missing
        )


class PlasticNotFound(AppError):
    def __init__(self, index: int) -> None:
        super().__init__(
            "costing.plastic_not_found",
            "Plastic not found",
            422,
            field=f"plastics.{index}.plastic_id",
        )


def quote(conn: DbConnection, data: QuoteInput) -> Quote:
    return quote_many(conn, [data])[0]


def quote_many(conn: DbConnection, inputs: Sequence[QuoteInput]) -> list[Quote]:
    """Price many prints with one read of the pricing data (catalog, ADR 0003)."""
    if not inputs:
        return []
    settings = pricing_service.get_settings(conn)
    missing = [] if pricing_service.plastics_exist(conn) else ["plastics"]
    if settings is None:
        missing.append("price_settings")
    if missing or settings is None:
        raise SettingsMissing(missing)

    ids = {usage.plastic_id for data in inputs for usage in data.plastics}
    prices = {p.id: p.price_per_kg_kop for p in pricing_service.list_plastics_by_ids(conn, ids)}
    cost_settings = domain.CostSettings(**settings.model_dump(exclude={"wear_per_hour_kop"}))
    return [_quote_one(data, prices, cost_settings) for data in inputs]


def _quote_one(data: QuoteInput, prices: dict[str, int], settings: domain.CostSettings) -> Quote:
    usages = []
    for index, usage in enumerate(data.plastics):
        if usage.plastic_id not in prices:
            raise PlasticNotFound(index)
        usages.append(domain.PlasticUsage(prices[usage.plastic_id], usage.usage_cg))
    result = domain.compute_quote(usages, data.print_time_s, settings)
    b = result.breakdown
    return Quote(
        min_donation_kop=result.min_donation_kop,
        breakdown=CostBreakdown(
            plastic_kop=b.plastic_kop,
            electricity_kop=b.electricity_kop,
            wear_kop=b.wear_kop,
            scrap_kop=b.scrap_kop,
        ),
    )
