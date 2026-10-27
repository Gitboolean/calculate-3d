import uuid

from calculate3d.core.ids import new_id


def test_new_id_is_canonical_uuid_v7_text() -> None:
    value = new_id()

    assert len(value) == 36
    assert uuid.UUID(value).version == 7


def test_new_ids_are_time_ordered() -> None:
    first, second = new_id(), new_id()

    assert first < second
