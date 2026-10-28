from fastapi import APIRouter

from calculate3d.core.db import ConnectionDep
from calculate3d.core.problems import (
    GUARD_RESPONSES,
    UNSUPPORTED_MEDIA_TYPE,
    VALIDATION_ERROR,
    FieldProblem,
    Problem,
    problem_response,
)
from calculate3d.modules.catalog import service as catalog_service
from calculate3d.modules.pricing import service
from calculate3d.modules.pricing.schemas import (
    Plastic,
    PlasticInput,
    PlasticInUseProblem,
    PlasticList,
    PriceSettings,
    PriceSettingsInput,
)

router = APIRouter(prefix="/api/pricing", tags=["pricing"], responses=GUARD_RESPONSES)

NAME_TAKEN = problem_response(FieldProblem, "Назва вже є серед пластиків (AC-02)")
NOT_FOUND = problem_response(Problem, "Пластика з таким id немає")
IN_USE = problem_response(PlasticInUseProblem, "Пластик використовують вироби (AC-03)")


@router.get("/plastics", operation_id="listPlastics")
def list_plastics(conn: ConnectionDep) -> PlasticList:
    return PlasticList(items=service.list_plastics(conn))


@router.post(
    "/plastics",
    status_code=201,
    operation_id="createPlastic",
    responses={409: NAME_TAKEN, 415: UNSUPPORTED_MEDIA_TYPE, 422: VALIDATION_ERROR},
)
def create_plastic(data: PlasticInput, conn: ConnectionDep) -> Plastic:
    return service.create_plastic(conn, data)


@router.put(
    "/plastics/{plastic_id}",
    operation_id="updatePlastic",
    responses={
        404: NOT_FOUND,
        409: NAME_TAKEN,
        415: UNSUPPORTED_MEDIA_TYPE,
        422: VALIDATION_ERROR,
    },
)
def update_plastic(plastic_id: str, data: PlasticInput, conn: ConnectionDep) -> Plastic:
    return service.update_plastic(conn, plastic_id, data)


@router.delete(
    "/plastics/{plastic_id}",
    status_code=204,
    operation_id="deletePlastic",
    responses={404: NOT_FOUND, 409: IN_USE},
)
def delete_plastic(plastic_id: str, conn: ConnectionDep) -> None:
    # The only pricing → catalog edge, and only here in the router (ADR 0005).
    service.delete_plastic(
        conn,
        plastic_id,
        item_names_using=lambda pid: catalog_service.item_names_using_plastic(conn, pid),
    )


@router.get("/settings", operation_id="getPriceSettings")
def get_settings(conn: ConnectionDep) -> PriceSettings | None:
    return service.get_settings(conn)


@router.put(
    "/settings",
    operation_id="replacePriceSettings",
    responses={415: UNSUPPORTED_MEDIA_TYPE, 422: VALIDATION_ERROR},
)
def replace_settings(data: PriceSettingsInput, conn: ConnectionDep) -> PriceSettings:
    return service.replace_settings(conn, data)
