from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select

from calculate3d.modules.catalog.tables import item_plastics
from calculate3d.modules.catalog.tables import items as items_table
from tests.factories import make_item, make_plastic, make_price_settings


@pytest.fixture
def ids(engine: Engine) -> dict[str, str]:
    with engine.begin() as conn:
        make_price_settings(conn)
        return {
            "petg": make_plastic(conn, name="PETG чорний", price_per_kg_kop=65000),
            "pla": make_plastic(conn, name="PLA білий", price_per_kg_kop=40000),
        }


def body(name: str, *usages: tuple[str, int], print_time_s: int = 12600) -> dict[str, Any]:
    return {
        "name": name,
        "plastics": [{"plastic_id": pid, "usage_cg": cg} for pid, cg in usages],
        "print_time_s": print_time_s,
    }


def create(client: TestClient, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post("/api/catalog/items", json=payload)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def problem(response: Any, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    assert response.headers["content-type"] == "application/problem+json"
    payload: dict[str, Any] = response.json()
    assert payload["code"] == code
    return payload


def test_saved_item_stores_parameters_without_a_price(
    client: TestClient, ids: dict[str, str]
) -> None:
    payload = body("Брелок-тризуб", (ids["petg"], 12000))

    created = create(client, payload)

    assert created == {"id": created["id"], **payload}
    assert client.get("/api/catalog/items").json() == {
        "items": [{"id": created["id"], "name": "Брелок-тризуб", "min_donation_kop": 11525}]
    }


@pytest.mark.parametrize("name", ["брелок-тризуб", " Брелок-тризуб "])
def test_duplicate_item_name_is_a_409(client: TestClient, ids: dict[str, str], name: str) -> None:
    create(client, body("Брелок-тризуб", (ids["petg"], 12000)))

    response = client.post("/api/catalog/items", json=body(name, (ids["pla"], 100)))

    assert problem(response, 409, "catalog.name_taken")["field"] == "name"


@pytest.mark.parametrize(
    "payload_factory",
    [
        lambda ids: body("   ", (ids["petg"], 100)),
        lambda ids: body("X"),
        lambda ids: body("X", (ids["petg"], 0)),
        lambda ids: body("X", (ids["petg"], 100), (ids["petg"], 50)),
        lambda ids: body("X", (ids["petg"], 100), print_time_s=0),
    ],
    ids=["blank-name", "no-plastic", "zero-usage", "duplicate-plastic", "zero-time"],
)
def test_invalid_item_is_a_422(
    client: TestClient, ids: dict[str, str], payload_factory: Any
) -> None:
    response = client.post("/api/catalog/items", json=payload_factory(ids))

    problem(response, 422, "validation_error")
    assert client.get("/api/catalog/items").json() == {"items": []}


def test_unknown_plastic_is_a_422_on_its_row(client: TestClient, ids: dict[str, str]) -> None:
    response = client.post("/api/catalog/items", json=body("X", ("01900000-dead", 100)))

    assert problem(response, 422, "catalog.plastic_not_found")["field"] == "plastics.0.plastic_id"


def test_catalog_search_filters_and_sorts(client: TestClient, ids: dict[str, str]) -> None:
    for name in ["Ялинка-тризуб", "гачок", "Брелок-тризуб", "Benchy тризуб"]:
        create(client, body(name, (ids["petg"], 12000)))

    response = client.get("/api/catalog/items", params={"q": "ТРИЗУБ"})

    assert response.status_code == 200
    assert [i["name"] for i in response.json()["items"]] == [
        "Benchy тризуб",
        "Брелок-тризуб",
        "Ялинка-тризуб",
    ]


def test_too_long_search_is_a_422(client: TestClient) -> None:
    problem(client.get("/api/catalog/items", params={"q": "x" * 101}), 422, "validation_error")


def test_catalog_price_follows_a_plastic_price_change(
    client: TestClient, ids: dict[str, str]
) -> None:
    create(client, body("Брелок-тризуб", (ids["petg"], 12000)))

    client.put(
        f"/api/pricing/plastics/{ids['petg']}",
        json={"name": "PETG чорний", "price_per_kg_kop": 80000},
    )

    assert client.get("/api/catalog/items").json()["items"][0]["min_donation_kop"] == 13505


def test_opened_item_shows_parameters_and_breakdown(
    client: TestClient, ids: dict[str, str]
) -> None:
    payload = body("Підставка", (ids["petg"], 12000))
    created = create(client, payload)

    response = client.get(f"/api/catalog/items/{created['id']}")

    assert response.status_code == 200
    assert response.json() == {
        "id": created["id"],
        **payload,
        "quote": {
            "min_donation_kop": 11525,
            "breakdown": {
                "plastic_kop": 7800,
                "electricity_kop": 227,
                "wear_kop": 2450,
                "scrap_kop": 1048,
            },
        },
    }


def test_edited_item_shows_new_parameters_and_price(
    client: TestClient, ids: dict[str, str]
) -> None:
    created = create(client, body("Підставка", (ids["petg"], 12000)))
    changed = body("Підставка XL", (ids["pla"], 8000), (ids["petg"], 4000), print_time_s=7200)

    response = client.put(f"/api/catalog/items/{created['id']}", json=changed)

    assert response.status_code == 200
    detail = client.get(f"/api/catalog/items/{created['id']}").json()
    assert detail["name"] == "Підставка XL"
    assert sorted(p["plastic_id"] for p in detail["plastics"]) == sorted([ids["pla"], ids["petg"]])
    assert detail["quote"]["min_donation_kop"] == 8063


@pytest.mark.parametrize(
    ("payload_factory", "status", "code"),
    [
        (lambda ids: body("Органайзер", (ids["pla"], 100)), 409, "catalog.name_taken"),
        (
            lambda ids: body("Підставка", (ids["pla"], 100), ("gone", 1)),
            422,
            "catalog.plastic_not_found",
        ),
        (lambda ids: body("Підставка"), 422, "validation_error"),
        (lambda ids: body("   ", (ids["petg"], 12000)), 422, "validation_error"),
    ],
    ids=["name-taken", "unknown-plastic", "no-plastic", "blank-name"],
)
def test_rejected_edit_leaves_the_item_unchanged(
    client: TestClient, ids: dict[str, str], payload_factory: Any, status: int, code: str
) -> None:
    created = create(client, body("Підставка", (ids["petg"], 12000)))
    create(client, body("Органайзер", (ids["pla"], 100)))
    before = client.get(f"/api/catalog/items/{created['id']}").json()

    response = client.put(f"/api/catalog/items/{created['id']}", json=payload_factory(ids))

    problem(response, status, code)
    assert client.get(f"/api/catalog/items/{created['id']}").json() == before


def test_deleted_item_is_gone(client: TestClient, ids: dict[str, str]) -> None:
    created = create(client, body("Підставка", (ids["petg"], 12000)))

    response = client.delete(f"/api/catalog/items/{created['id']}")

    assert response.status_code == 204
    problem(client.get(f"/api/catalog/items/{created['id']}"), 404, "catalog.item_not_found")
    problem(client.delete(f"/api/catalog/items/{created['id']}"), 404, "catalog.item_not_found")


def test_plastic_used_by_items_cannot_be_deleted_until_they_are(
    client: TestClient, ids: dict[str, str]
) -> None:
    stand = create(client, body("Підставка", (ids["pla"], 100)))
    organizer = create(client, body("Органайзер", (ids["pla"], 200), (ids["petg"], 50)))

    refused = client.delete(f"/api/pricing/plastics/{ids['pla']}")

    assert problem(refused, 409, "pricing.plastic_in_use")["items"] == ["Органайзер", "Підставка"]
    assert any(p["id"] == ids["pla"] for p in client.get("/api/pricing/plastics").json()["items"])

    client.delete(f"/api/catalog/items/{stand['id']}")
    client.put(f"/api/catalog/items/{organizer['id']}", json=body("Органайзер", (ids["petg"], 50)))

    assert client.delete(f"/api/pricing/plastics/{ids['pla']}").status_code == 204


def test_catalog_without_settings_is_a_409(client: TestClient, engine: Engine) -> None:
    with engine.begin() as conn:
        from tests.factories import make_item

        make_item(conn, usage={make_plastic(conn): 100})

    response = client.get("/api/catalog/items")

    assert problem(response, 409, "costing.settings_missing")["missing"] == ["price_settings"]


CATALOG_OPERATIONS = {
    ("get", "/api/catalog/items"): ("listItems", {"409", "422"}),
    ("post", "/api/catalog/items"): ("createItem", {"409", "415", "422"}),
    ("get", "/api/catalog/items/{item_id}"): ("getItem", {"404", "409"}),
    ("put", "/api/catalog/items/{item_id}"): ("updateItem", {"404", "409", "415", "422"}),
    ("delete", "/api/catalog/items/{item_id}"): ("deleteItem", {"404", "415"}),
}


@pytest.mark.parametrize(("method", "path"), list(CATALOG_OPERATIONS))
def test_openapi_declares_catalog_operations(client: TestClient, method: str, path: str) -> None:
    operation = client.get("/openapi.json").json()["paths"][path][method]
    operation_id, own_errors = CATALOG_OPERATIONS[(method, path)]

    assert operation["operationId"] == operation_id
    assert {s for s in operation["responses"] if s[0] in "45"} == own_errors | {"400", "403", "500"}


def test_duplicate_plastic_is_a_422_on_the_second_occurrence(
    client: TestClient, ids: dict[str, str]
) -> None:
    pid = ids["petg"]
    response = client.post("/api/catalog/items", json=body("Дубль", (pid, 100), (pid, 200)))

    payload = problem(response, 422, "validation_error")
    assert payload["errors"][0]["loc"] == ["body", "plastics", 1, "plastic_id"]
    assert client.get("/api/catalog/items").json() == {"items": []}


def test_create_without_price_settings_is_a_409_and_saves_nothing(
    client: TestClient, engine: Engine
) -> None:
    with engine.begin() as conn:
        petg = make_plastic(conn)

    response = client.post("/api/catalog/items", json=body("Брелок-тризуб", (petg, 12000)))

    assert problem(response, 409, "costing.settings_missing")["missing"] == ["price_settings"]
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(items_table)).scalar_one() == 0
        assert conn.execute(select(func.count()).select_from(item_plastics)).scalar_one() == 0


def test_update_without_price_settings_is_a_409_and_leaves_the_item_unchanged(
    client: TestClient, engine: Engine
) -> None:
    with engine.begin() as conn:
        petg = make_plastic(conn)
        pla = make_plastic(conn, name="PLA білий", price_per_kg_kop=40000)
        item_id = make_item(conn, name="Підставка", usage={petg: 12000})

    response = client.put(
        f"/api/catalog/items/{item_id}", json=body("Підставка XL", (pla, 50), print_time_s=60)
    )

    assert problem(response, 409, "costing.settings_missing")["missing"] == ["price_settings"]
    with engine.connect() as conn:
        row = conn.execute(select(items_table).where(items_table.c.id == item_id)).one()
        usage = conn.execute(select(item_plastics.c.plastic_id, item_plastics.c.usage_cg)).all()
    assert (row.name, row.print_time_s) == ("Підставка", 12600)
    assert [tuple(u) for u in usage] == [(petg, 12000)]


@pytest.mark.parametrize(
    ("method", "path"),
    [("post", "/api/catalog/items"), ("put", "/api/catalog/items/{item_id}")],
)
def test_openapi_declares_409_on_create_and_update(
    client: TestClient, method: str, path: str
) -> None:
    operation = client.get("/openapi.json").json()["paths"][path][method]

    assert "409" in operation["responses"]
    schema = operation["responses"]["409"]["content"]["application/problem+json"]["schema"]
    refs = {variant["$ref"].rsplit("/", 1)[-1] for variant in schema.get("anyOf", [schema])}
    assert {"FieldProblem", "SettingsMissingProblem"} <= refs
