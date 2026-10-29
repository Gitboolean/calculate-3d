from typing import Annotated

from fastapi import APIRouter, Query

from calculate3d.core.db import ConnectionDep
from calculate3d.core.problems import (
    GUARD_RESPONSES,
    UNSUPPORTED_MEDIA_TYPE,
    VALIDATION_ERROR,
    FieldProblem,
    Problem,
    ValidationProblem,
    problem_response,
)
from calculate3d.modules.catalog import service
from calculate3d.modules.catalog.schemas import Item, ItemDetail, ItemInput, ItemList
from calculate3d.modules.costing.service import SettingsMissingProblem

router = APIRouter(prefix="/api/catalog", tags=["catalog"], responses=GUARD_RESPONSES)

NOT_FOUND = problem_response(Problem, "Виробу з таким id немає")
SETTINGS_MISSING = problem_response(SettingsMissingProblem, "Бракує налаштувань цін (AC-09)")
NAME_TAKEN_OR_SETTINGS_MISSING = {
    "model": FieldProblem | SettingsMissingProblem,
    "description": (
        "Назва вже є в каталозі (AC-11, AC-14c) або бракує налаштувань цін — "
        "виріб без мінімального донату не зберегти (AC-10)"
    ),
}
ITEM_INVALID = {
    "model": ValidationProblem | FieldProblem,
    "description": "Хибні параметри виробу (AC-07, AC-14c) або пластика з таким id немає",
}


@router.get(
    "/items",
    operation_id="listItems",
    responses={409: SETTINGS_MISSING, 422: VALIDATION_ERROR},
)
def list_items(
    conn: ConnectionDep,
    q: Annotated[str | None, Query(max_length=100, description="Частина назви виробу")] = None,
) -> ItemList:
    return ItemList(items=service.list_items(conn, q))


@router.post(
    "/items",
    status_code=201,
    operation_id="createItem",
    responses={409: NAME_TAKEN_OR_SETTINGS_MISSING, 415: UNSUPPORTED_MEDIA_TYPE, 422: ITEM_INVALID},
)
def create_item(data: ItemInput, conn: ConnectionDep) -> Item:
    return service.create_item(conn, data)


@router.get(
    "/items/{item_id}",
    operation_id="getItem",
    responses={404: NOT_FOUND, 409: SETTINGS_MISSING},
)
def get_item(item_id: str, conn: ConnectionDep) -> ItemDetail:
    return service.get_item(conn, item_id)


@router.put(
    "/items/{item_id}",
    operation_id="updateItem",
    responses={
        404: NOT_FOUND,
        409: NAME_TAKEN_OR_SETTINGS_MISSING,
        415: UNSUPPORTED_MEDIA_TYPE,
        422: ITEM_INVALID,
    },
)
def update_item(item_id: str, data: ItemInput, conn: ConnectionDep) -> Item:
    return service.update_item(conn, item_id, data)


@router.delete(
    "/items/{item_id}",
    status_code=204,
    operation_id="deleteItem",
    responses={404: NOT_FOUND, 415: UNSUPPORTED_MEDIA_TYPE},
)
def delete_item(item_id: str, conn: ConnectionDep) -> None:
    service.delete_item(conn, item_id)
