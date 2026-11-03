import pytest
from sqlalchemy import Engine, func, select

from calculate3d.modules.pricing.tables import plastics
from tests.factories import make_plastic


@pytest.mark.parametrize("step", ["first", "second"])
def test_each_test_gets_its_own_database_file(engine: Engine, step: str) -> None:
    with engine.begin() as conn:
        make_plastic(conn, name=f"Canary {step}")
        count = conn.execute(select(func.count()).select_from(plastics)).scalar()

    assert count == 1
