import io
import zipfile

import pytest

from tests.fixtures.slicer import LITTLE_TREES, REFERENCE_FILES, VTULKA_PROJECT, VTULKA_SLICED
from tests.fixtures.slicer.bad_files import BAD_FILES, BadFile, zip_bomb

# ImportRejectedProblem.code enum of openapi.yaml (FileTooLarge is built by T10, not here).
CONTRACT_REJECTION_CODES = {
    "importing.not_slicer_project",
    "importing.not_sliced",
    "importing.multiple_sliced_plates",
    "importing.corrupted_file",
    "importing.print_time_out_of_range",
    "importing.no_filament_usage",
}

# SAD §10 QG-2 + T2: every reason has its own case.
REQUIRED_CASES = {
    "not_zip",
    "truncated_zip",
    "empty_body",
    "too_many_entries",
    "oversized_part",
    "lying_size_header",
    "gcode_zip_bomb",
    "billion_laughs",
    "xxe",
    "cad_3mf",
    "orca_slicer",
    "unsliced_project",
    "two_sliced_plates",
    "duplicate_part_names",
    "path_traversal",
    "missing_slice_info",
    "missing_prediction",
    "nan_grams",
    "infinite_grams",
    "exponent_grams",
    "negative_grams",
    "too_precise_grams",
    "zero_print_time",
    "too_long_print_time",
    "no_filament_usage",
    "filament_without_name",
    "too_long_filament_name",
    "non_canonical_color",
    "too_many_filament_pairs",
    "usage_mg_over_safe_integer",
}


def test_reference_files_are_the_three_slicer_references() -> None:
    assert {p.name for p in REFERENCE_FILES} == {
        "vtulka_A.3mf",
        "vtulka_A.gcode.3mf",
        "LITTLE_TREES_-_multicolor.gcode.3mf",
    }
    for path in (VTULKA_PROJECT, VTULKA_SLICED, LITTLE_TREES):
        assert zipfile.is_zipfile(path)


def test_every_required_bad_case_is_present_once() -> None:
    names = [case.name for case in BAD_FILES]
    assert len(names) == len(set(names))
    assert set(names) >= REQUIRED_CASES


@pytest.mark.parametrize("case", BAD_FILES, ids=lambda c: c.name)
def test_each_bad_case_builds_with_a_contract_code(case: BadFile) -> None:
    assert isinstance(case.body, bytes)
    assert case.expected_code in CONTRACT_REJECTION_CODES


def test_empty_body_is_really_empty() -> None:
    (case,) = [c for c in BAD_FILES if c.name == "empty_body"]
    assert case.body == b""


def test_zip_bomb_is_small_but_inflates_to_gigabytes() -> None:
    body = zip_bomb()
    assert len(body) < 1_000_000
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        gcode = zf.getinfo("Metadata/plate_1.gcode")
    assert gcode.file_size >= 1_000_000_000


def test_too_many_entries_has_10001_entries() -> None:
    (case,) = [c for c in BAD_FILES if c.name == "too_many_entries"]
    with zipfile.ZipFile(io.BytesIO(case.body)) as zf:
        assert len(zf.infolist()) == 10_001
