from fastapi import APIRouter

from calculate3d.core.db import ConnectionDep
from calculate3d.core.problems import (
    GUARD_RESPONSES,
    UNSUPPORTED_MEDIA_TYPE,
    FieldProblem,
    ValidationProblem,
    problem_response,
)
from calculate3d.modules.costing import service
from calculate3d.modules.costing.schemas import Quote, QuoteInput, SettingsMissingProblem

router = APIRouter(prefix="/api/costing", tags=["costing"], responses=GUARD_RESPONSES)


@router.post(
    "/quote",
    operation_id="quoteCost",
    responses={
        409: problem_response(SettingsMissingProblem, "Бракує налаштувань цін (AC-09)"),
        415: UNSUPPORTED_MEDIA_TYPE,
        422: {
            "model": ValidationProblem | FieldProblem,
            "description": (
                "Хибний вхід (AC-07: порожньо, нуль, зайва точність, понад межу, понад 32"
                " пластики, повтор пластику) або пластика з таким id немає"
            ),
        },
    },
)
def quote_cost(data: QuoteInput, conn: ConnectionDep) -> Quote:
    """Мінімальний донат і розбивка з поточних налаштувань цін; нічого не зберігає."""
    return service.quote(conn, data)
