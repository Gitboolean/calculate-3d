"""T19 (review Q1, Q2): the archive entry limit is enforced before ZipFile builds its entry list,
and the request body is held in memory once (SAD §7 peak, §8 archive read limits)."""

import asyncio
import tracemalloc
import zipfile
from collections.abc import AsyncIterator
from typing import Any

import pytest

from calculate3d.modules.importing import parser
from calculate3d.modules.importing.router import read_body
from tests.fixtures.slicer.bad_files import BAD_FILES, CORRUPTED_FILE

OVER_LIMIT_CASES = (
    "too_many_entries",
    "forged_eocd_entry_count",
    "forged_zip64_entry_count",
    "cd_flood_small_declared_count",
    "cd_flood_eocd_offset_field_has_signature",
    "cd_flood_zip64_locator_unflagged",
    "cd_flood_zip64_record_at_locator_minus_56",
    "cd_flood_zip64_extensible_data",
    "cd_fat_records",
    "cd_oversized_within_entry_limit",
)


@pytest.mark.parametrize("name", OVER_LIMIT_CASES)
def test_entry_count_over_the_limit_is_rejected_before_zipfile_is_constructed(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    (case,) = [c for c in BAD_FILES if c.name == name]

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("zipfile.ZipFile was constructed for an over-limit central directory")

    monkeypatch.setattr(parser.zipfile, "ZipFile", forbidden)

    with pytest.raises(parser.ParseError) as raised:
        parser.read_sliced_plate(case.body)

    assert raised.value.code == CORRUPTED_FILE


def test_zipfile_spy_is_effective_for_a_valid_archive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard: the patched name is the one the parser really uses to open archives."""
    calls: list[int] = []
    real = zipfile.ZipFile

    def spy(*args: Any, **kwargs: Any) -> zipfile.ZipFile:
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(parser.zipfile, "ZipFile", spy)
    (case,) = [c for c in BAD_FILES if c.name == "unsliced_project"]
    with pytest.raises(parser.ParseError):
        parser.parse(case.body)  # rejected later by the chain, after the archive was opened
    assert calls


class _FakeRequest:
    """Just what `read_body` touches: headers and a lazily produced stream of chunks."""

    def __init__(self, size: int, chunk: int = 65_536) -> None:
        self.headers: dict[str, str] = {}
        self._size = size
        self._chunk = chunk

    async def stream(self) -> AsyncIterator[bytes]:
        sent = 0
        while sent < self._size:
            piece = min(self._chunk, self._size - sent)
            yield bytes(piece)
            sent += piece


def test_read_body_holds_one_copy_of_the_body() -> None:
    size = 24_000_000
    request: Any = _FakeRequest(size)

    tracemalloc.start()
    try:
        body = asyncio.run(read_body(request))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert len(body) == size
    assert peak < 1.5 * size, f"peak {peak / size:.2f}x the body: a second copy is alive"
