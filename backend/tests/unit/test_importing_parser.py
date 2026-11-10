import json
import re
import time
import zipfile
from collections.abc import Callable

import pytest

from calculate3d.modules.importing.parser import (
    ParsedFilament,
    ParsedFile,
    ParseError,
    Plate,
    parse,
    read_sliced_plate,
)
from tests.fixtures.slicer import LITTLE_TREES, VTULKA_PROJECT, VTULKA_SLICED
from tests.fixtures.slicer.bad_files import (
    BAD_FILES,
    PROJECT_SETTINGS,
    SERVICE_PARTS,
    SLICE_INFO,
    BadFile,
    build_zip,
)

PLA = "Bambu PLA Basic @BBL A1M"

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


def _vtulka(
    slice_info: Callable[[str], str] = lambda t: t,
    presets: list[str] | None = None,
) -> bytes:
    """vtulka_A.gcode.3mf with its slice_info / filament presets rewritten in memory."""
    with zipfile.ZipFile(VTULKA_SLICED) as zf:
        parts = {name: zf.read(name) for name in SERVICE_PARTS}
    parts[SLICE_INFO] = slice_info(parts[SLICE_INFO].decode()).encode()
    if presets is not None:
        settings = json.loads(parts[PROJECT_SETTINGS])
        settings["filament_settings_id"] = presets
        parts[PROJECT_SETTINGS] = json.dumps(settings).encode()
    return build_zip(parts.items())


def _set(attr: str, value: str) -> Callable[[str], str]:
    return lambda text: re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', text, count=1)


def _prediction(value: str) -> Callable[[str], str]:
    return lambda t: re.sub(r'key="prediction" value="\d+"', f'key="prediction" value="{value}"', t)


def _filaments(*lines: tuple[int, str, str]) -> Callable[[str], str]:
    """Replace the filament rows by (id, color, used_g) rows."""
    rows = "".join(
        f'    <filament id="{i}" type="PLA" color="{color}" used_m="1" used_g="{grams}"/>\n'
        for i, color, grams in lines
    )
    return lambda text: re.sub(r"    <filament [^\n]*\n", "", text).replace(
        "    <warning", rows + "    <warning", 1
    )


def test_vtulka_parses_to_one_white_pla_and_time_rounded_up_to_a_minute() -> None:
    assert parse(VTULKA_SLICED.read_bytes()) == ParsedFile(
        plate=Plate(index=1, name=""),
        print_time_s=5880,  # 5 828 s → 1 h 38 min (AC-01, AC-03)
        filaments=(ParsedFilament(PLA, "PLA", "#FFFFFF", 11_540),),
    )


def test_little_trees_has_three_used_filaments_with_purge_and_no_brown() -> None:
    parsed = parse(LITTLE_TREES.read_bytes())

    assert parsed.plate == Plate(index=1, name="mini christmas tree")
    assert parsed.print_time_s == 5460  # 5 401 s → 1 h 31 min (AC-02)
    assert [(f.color, f.usage_mg) for f in parsed.filaments] == [
        ("#3F8E43", 15_490),
        ("#000000", 2_230),
        ("#FEC600", 2_360),
    ]
    assert {f.name for f in parsed.filaments} == {PLA}
    assert "#6F5034" not in {f.color for f in parsed.filaments}


def test_whole_minute_time_is_kept_and_extra_precision_grams_stay_exact() -> None:
    parsed = parse(_vtulka(lambda t: _set("used_g", "11.543")(_prediction("5820")(t))))

    assert parsed.print_time_s == 5820
    assert parsed.filaments[0].usage_mg == 11_543


@pytest.mark.parametrize("color", ["#ffffff", "#FFFFFFFF", "#ffffff80"])
def test_color_is_normalized_to_upper_rrggbb_without_alpha(color: str) -> None:
    assert parse(_vtulka(_set("color", color))).filaments[0].color == "#FFFFFF"


def test_name_is_only_trimmed_and_keeps_its_case() -> None:
    padded = parse(_vtulka(presets=[f"  {PLA} "])).filaments[0]
    lower = parse(_vtulka(presets=[PLA.lower()])).filaments[0]

    assert padded.name == PLA
    assert lower.name == "bambu pla basic @bbl a1m"


def test_200_code_point_name_is_accepted() -> None:
    assert parse(_vtulka(presets=["я" * 200])).filaments[0].name == "я" * 200


def test_identical_slots_merge_into_one_filament_with_the_exact_sum() -> None:
    parsed = parse(
        _vtulka(_filaments((1, "#FFFFFF", "2.001"), (2, "#ffffff", "2.001")), presets=[PLA, PLA])
    )

    assert parsed.filaments == (ParsedFilament(PLA, "PLA", "#FFFFFF", 4_002),)


def test_same_preset_in_another_color_stays_a_separate_filament() -> None:
    parsed = parse(
        _vtulka(_filaments((1, "#FFFFFF", "1.00"), (2, "#000000", "2.00")), presets=[PLA, PLA])
    )

    assert [(f.color, f.usage_mg) for f in parsed.filaments] == [
        ("#FFFFFF", 1_000),
        ("#000000", 2_000),
    ]


def test_unused_filament_is_skipped() -> None:
    parsed = parse(
        _vtulka(_filaments((1, "#FFFFFF", "11.54"), (2, "#000000", "0.00")), presets=[PLA, PLA])
    )

    assert [f.color for f in parsed.filaments] == ["#FFFFFF"]


def test_32_distinct_pairs_are_accepted() -> None:
    rows = [(n, f"#0000{n:02X}", "1.00") for n in range(1, 33)]
    assert len(parse(_vtulka(_filaments(*rows), presets=[PLA] * 32)).filaments) == 32


def test_largest_safe_integer_usage_is_accepted_but_merging_past_it_is_corrupted() -> None:
    assert parse(_vtulka(_set("used_g", "9007199254740.991"))).filaments[0].usage_mg == (2**53 - 1)
    with pytest.raises(ParseError) as err:
        parse(
            _vtulka(
                _filaments((1, "#FFFFFF", "9007199254740.991"), (2, "#FFFFFF", "0.001")),
                presets=[PLA, PLA],
            )
        )
    assert err.value.code == "importing.corrupted_file"


@pytest.mark.parametrize("prediction", ["359999999", "360000000"])
def test_time_up_to_100_000_hours_is_accepted(prediction: str) -> None:
    assert parse(_vtulka(_prediction(prediction))).print_time_s == 360_000_000


@pytest.mark.parametrize("case", BAD_FILES, ids=lambda c: c.name)
def test_every_bad_file_is_rejected_with_its_code(case: BadFile) -> None:
    with pytest.raises(ParseError) as err:
        parse(case.body)
    assert err.value.code == case.expected_code
