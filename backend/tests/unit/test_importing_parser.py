import time

import pytest

from calculate3d.modules.importing.parser import ParseError, Plate, read_sliced_plate
from tests.fixtures.slicer import LITTLE_TREES, VTULKA_PROJECT, VTULKA_SLICED
from tests.fixtures.slicer.bad_files import BAD_FILES, BadFile

# Steps 0–3 of the SAD §8 check chain: archive limits, Bambu project, sliced, one plate.
ARCHIVE_AND_PLATE_CASES = {
    "not_zip",
    "truncated_zip",
    "empty_body",
    "too_many_entries",
    "oversized_part",
    "lying_size_header",
    "duplicate_part_names",
    "path_traversal",
    "billion_laughs",
    "xxe",
    "gcode_zip_bomb",
    "cad_3mf",
    "orca_slicer",
    "unsliced_project",
    "two_sliced_plates",
    "missing_slice_info",
}


def _cases(names: set[str]) -> list[BadFile]:
    cases = [case for case in BAD_FILES if case.name in names]
    assert {case.name for case in cases} == names
    return cases


def test_sliced_plate_export_is_plate_1_without_a_name() -> None:
    assert read_sliced_plate(VTULKA_SLICED.read_bytes()).plate == Plate(index=1, name="")


def test_multi_plate_project_imports_its_only_sliced_plate() -> None:
    plate = read_sliced_plate(LITTLE_TREES.read_bytes()).plate
    assert plate == Plate(index=1, name="mini christmas tree")


def test_project_saved_without_slicing_is_not_sliced() -> None:
    with pytest.raises(ParseError) as err:
        read_sliced_plate(VTULKA_PROJECT.read_bytes())
    assert err.value.code == "importing.not_sliced"


@pytest.mark.parametrize("case", _cases(ARCHIVE_AND_PLATE_CASES), ids=lambda c: c.name)
def test_archive_and_plate_chain_rejects_with_its_code(case: BadFile) -> None:
    with pytest.raises(ParseError) as err:
        read_sliced_plate(case.body)
    assert err.value.code == case.expected_code


@pytest.mark.parametrize("name", ["billion_laughs", "xxe"])
def test_xml_entities_are_never_expanded(name: str) -> None:
    (case,) = _cases({name})
    started = time.perf_counter()
    with pytest.raises(ParseError) as err:
        read_sliced_plate(case.body)
    assert err.value.code == "importing.corrupted_file"
    assert "root:" not in str(err.value)  # nothing of /etc/passwd leaks
    assert time.perf_counter() - started < 1


def test_gcode_bomb_is_never_inflated() -> None:
    (case,) = _cases({"gcode_zip_bomb"})
    started = time.perf_counter()
    with pytest.raises(ParseError):
        read_sliced_plate(case.body)
    assert time.perf_counter() - started < 1
