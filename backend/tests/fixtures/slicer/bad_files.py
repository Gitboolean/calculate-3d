"""In-memory bad slicer files — SAD §10 QG-2 (one case per rejection reason).

Every case is derived from a reference file and rebuilt with `zipfile` in a `BytesIO`; nothing is
written to disk. The generator knows only the file format (SAD §8), never `parser.py`.
"""

import functools
import io
import json
import re
import struct
import warnings
import zipfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from tests.fixtures.slicer import VTULKA_PROJECT, VTULKA_SLICED

MODEL = "3D/3dmodel.model"
MODEL_SETTINGS = "Metadata/model_settings.config"
SLICE_INFO = "Metadata/slice_info.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
SERVICE_PARTS = (MODEL, MODEL_SETTINGS, SLICE_INFO, PROJECT_SETTINGS)
GCODE = "Metadata/plate_1.gcode"

PART_LIMIT = 8_000_000
ENTRY_LIMIT = 10_000

NOT_SLICER_PROJECT = "importing.not_slicer_project"
NOT_SLICED = "importing.not_sliced"
MULTIPLE_SLICED_PLATES = "importing.multiple_sliced_plates"
CORRUPTED_FILE = "importing.corrupted_file"
PRINT_TIME_OUT_OF_RANGE = "importing.print_time_out_of_range"
NO_FILAMENT_USAGE = "importing.no_filament_usage"


@dataclass(frozen=True)
class BadFile:
    name: str
    body: bytes
    expected_code: str


Parts = list[tuple[str, bytes]]


def _service_parts(path: Path = VTULKA_SLICED) -> Parts:
    """The 4 parts the parser reads, plus a tiny G-code stub (G-code is never inflated)."""
    with zipfile.ZipFile(path) as zf:
        parts = [(name, zf.read(name)) for name in SERVICE_PARTS if name in zf.namelist()]
    return [*parts, (GCODE, b"; G-code stub\n")]


def build_zip(parts: Iterable[tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with warnings.catch_warnings():
        # Duplicate names are a deliberate case; zipfile warns about them.
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in parts:
                zf.writestr(name, data)
    return buf.getvalue()


def _edit(name: str, change: Callable[[str], str], parts: Parts | None = None) -> Parts:
    parts = _service_parts() if parts is None else parts
    edited = [(n, change(d.decode()).encode() if n == name else d) for n, d in parts]
    if edited == parts:
        raise AssertionError(f"edit of {name} changed nothing")
    return edited


def _sub(pattern: str, repl: str) -> Callable[[str], str]:
    def change(text: str) -> str:
        new, count = re.subn(pattern, repl, text)
        if count == 0:
            raise AssertionError(f"pattern {pattern!r} not found")
        return new

    return change


def _used_g(value: str) -> bytes:
    return build_zip(_edit(SLICE_INFO, _sub(r'used_g="[^"]*"', f'used_g="{value}"')))


def _prediction(value: str) -> bytes:
    return build_zip(
        _edit(
            SLICE_INFO, _sub(r'key="prediction" value="[^"]*"', f'key="prediction" value="{value}"')
        )
    )


def _project_settings(change: Callable[[dict[str, object]], None]) -> Callable[[str], str]:
    def edit(text: str) -> str:
        settings = json.loads(text)
        change(settings)
        return json.dumps(settings, indent=4)

    return edit


def _without(name: str) -> bytes:
    return build_zip([(n, d) for n, d in _service_parts() if n != name])


def _too_many_entries() -> bytes:
    parts = _service_parts()
    filler = [(f"Auxiliaries/f{n}", b"") for n in range(ENTRY_LIMIT + 1 - len(parts))]
    return build_zip([*parts, *filler])


def _oversized_part() -> bytes:
    def pad(text: str) -> str:
        return text + " " * (PART_LIMIT + 1 - len(text.encode()))

    return build_zip(_edit(PROJECT_SETTINGS, pad))


def _lying_size_header() -> bytes:
    """slice_info inflates to > 8 MB, but both ZIP headers claim 1 000 bytes."""
    claimed = 1000
    body = bytearray(build_zip(_edit(SLICE_INFO, lambda t: t + "<!--" + "x" * PART_LIMIT + "-->")))
    name = SLICE_INFO.encode()
    # Local header: uncompressed size at +22; central directory header: at +24.
    for signature, offset in ((b"PK\x03\x04", 22), (b"PK\x01\x02", 24)):
        start = 0
        while (pos := body.find(signature, start)) != -1:
            name_len_at = 26 if signature == b"PK\x03\x04" else 28
            (name_len,) = struct.unpack_from("<H", body, pos + name_len_at)
            name_at = pos + (30 if signature == b"PK\x03\x04" else 46)
            if bytes(body[name_at : name_at + name_len]) == name:
                struct.pack_into("<I", body, pos + offset, claimed)
            start = pos + 4
    return bytes(body)


@functools.cache
def zip_bomb() -> bytes:
    """An unsliced project whose G-code inflates to ~1 GB from < 1 MB (G-code is never read)."""
    buf = io.BytesIO()
    chunk = bytes(1 << 20)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, data in _service_parts(VTULKA_PROJECT)[:-1]:
            zf.writestr(name, data)
        with zf.open(GCODE, "w", force_zip64=True) as gcode:
            for _ in range(954):  # 954 MiB > 10^9 bytes, still < 1 MB deflated
                gcode.write(chunk)
    return buf.getvalue()


BILLION_LAUGHS = b"""<?xml version="1.0"?>
<!DOCTYPE model [
 <!ENTITY lol "lol">
 <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
 <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
 <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
 <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
 <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
 <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
 <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
 <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
 <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
]>
<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <metadata name="Application">BambuStudio-&lol9;</metadata>
</model>
"""

XXE = b"""<?xml version="1.0"?>
<!DOCTYPE model [<!ENTITY app SYSTEM "file:///etc/passwd">]>
<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <metadata name="Application">BambuStudio-&app;</metadata>
</model>
"""

CAD_MODEL = b"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <metadata name="Application">Autodesk Fusion 360</metadata>
 <resources/>
 <build/>
</model>
"""


def _replace_model(model: bytes) -> bytes:
    return build_zip([(n, model if n == MODEL else d) for n, d in _service_parts()])


def _two_sliced_plates() -> bytes:
    def second_slice_plate(text: str) -> str:
        plate = re.search(r"  <plate>.*?</plate>\n", text, re.S)
        assert plate is not None
        twin = plate.group(0).replace('key="index" value="1"', 'key="index" value="2"')
        return text.replace("</config>", twin + "</config>")

    def second_model_plate(text: str) -> str:
        plate = re.search(r"  <plate>.*?</plate>\n", text, re.S)
        assert plate is not None
        twin = (
            plate.group(0)
            .replace('key="plater_id" value="1"', 'key="plater_id" value="2"')
            .replace("plate_1.gcode", "plate_2.gcode")
        )
        return text.replace("</config>", twin + "</config>")

    parts = _edit(MODEL_SETTINGS, second_model_plate, _edit(SLICE_INFO, second_slice_plate))
    return build_zip(parts)


def _filament_line(filament_id: int, color: str, used_g: str = "1.00") -> str:
    return (
        f'    <filament id="{filament_id}" tray_info_idx="GFA00" type="PLA" color="{color}"'
        f' used_m="0.33" used_g="{used_g}" group_id="0"/>\n'
    )


def _extra_filaments(count: int, names: int) -> bytes:
    """`count` filaments in slice_info with distinct colors; `names` presets in the project."""

    def filaments(text: str) -> str:
        lines = "".join(_filament_line(n, f"#0000{n:02X}") for n in range(2, count + 1))
        return _sub(r"(    <filament id=\"1\"[^\n]*\n)", r"\g<1>" + lines)(text)

    def presets(settings: dict[str, object]) -> None:
        settings["filament_settings_id"] = ["Bambu PLA Basic @BBL A1M"] * names

    parts = _edit(PROJECT_SETTINGS, _project_settings(presets), _edit(SLICE_INFO, filaments))
    return build_zip(parts)


def _name(value: str) -> bytes:
    def preset(settings: dict[str, object]) -> None:
        settings["filament_settings_id"] = [value]

    return build_zip(_edit(PROJECT_SETTINGS, _project_settings(preset)))


BAD_FILES: tuple[BadFile, ...] = (
    # Step 0 — not a ZIP, or a ZIP breaking the archive read limits (SAD §8).
    BadFile("not_zip", b"%PDF-1.7\nnot a slicer project\n", NOT_SLICER_PROJECT),
    BadFile("truncated_zip", build_zip(_service_parts())[:2000], CORRUPTED_FILE),
    BadFile("empty_body", b"", CORRUPTED_FILE),
    BadFile("too_many_entries", _too_many_entries(), CORRUPTED_FILE),
    BadFile("oversized_part", _oversized_part(), CORRUPTED_FILE),
    BadFile("lying_size_header", _lying_size_header(), CORRUPTED_FILE),
    BadFile(
        "duplicate_part_names",
        build_zip([*_service_parts(), (SLICE_INFO, b"<config/>")]),
        CORRUPTED_FILE,
    ),
    BadFile(
        "path_traversal", build_zip([*_service_parts(), ("../evil.txt", b"x")]), CORRUPTED_FILE
    ),
    BadFile("billion_laughs", _replace_model(BILLION_LAUGHS), CORRUPTED_FILE),
    BadFile("xxe", _replace_model(XXE), CORRUPTED_FILE),
    # The bomb sits in G-code, which is never inflated: only the 4 parts decide (not sliced).
    BadFile("gcode_zip_bomb", zip_bomb(), NOT_SLICED),
    # Step 1 — not a Bambu Studio project.
    BadFile("cad_3mf", build_zip([(MODEL, CAD_MODEL)]), NOT_SLICER_PROJECT),
    BadFile(
        "orca_slicer",
        build_zip(_edit(MODEL, _sub("BambuStudio-02.08.02.61", "OrcaSlicer-2.2.0"))),
        NOT_SLICER_PROJECT,
    ),
    # Step 2 — no sliced plate; step 3 — more than one.
    BadFile("unsliced_project", VTULKA_PROJECT.read_bytes(), NOT_SLICED),
    BadFile("two_sliced_plates", _two_sliced_plates(), MULTIPLE_SLICED_PLATES),
    # Step 4 — integrity, numbers, normalization.
    BadFile("missing_slice_info", _without(SLICE_INFO), CORRUPTED_FILE),
    BadFile(
        "missing_prediction",
        build_zip(_edit(SLICE_INFO, _sub(r'    <metadata key="prediction"[^\n]*\n', ""))),
        CORRUPTED_FILE,
    ),
    BadFile("nan_grams", _used_g("NaN"), CORRUPTED_FILE),
    BadFile("infinite_grams", _used_g("Infinity"), CORRUPTED_FILE),
    BadFile("exponent_grams", _used_g("1.154e1"), CORRUPTED_FILE),
    BadFile("negative_grams", _used_g("-11.54"), CORRUPTED_FILE),
    BadFile("too_precise_grams", _used_g("11.5431"), CORRUPTED_FILE),
    BadFile("usage_mg_over_safe_integer", _used_g("9007199254740.992"), CORRUPTED_FILE),
    BadFile("filament_without_name", _extra_filaments(count=2, names=1), CORRUPTED_FILE),
    BadFile("too_long_filament_name", _name("x" * 201), CORRUPTED_FILE),
    BadFile(
        "non_canonical_color",
        build_zip(_edit(SLICE_INFO, _sub(r'color="#FFFFFF"', 'color="#FFF"'))),
        CORRUPTED_FILE,
    ),
    BadFile("too_many_filament_pairs", _extra_filaments(count=33, names=33), CORRUPTED_FILE),
    # Step 5 — file bounds (AC-14).
    BadFile("zero_print_time", _prediction("0"), PRINT_TIME_OUT_OF_RANGE),
    BadFile("too_long_print_time", _prediction("360000001"), PRINT_TIME_OUT_OF_RANGE),
    BadFile("no_filament_usage", _used_g("0.00"), NO_FILAMENT_USAGE),
)


# ── Valid variants of the sliced reference (QG-1 AC-05, QG-4) ──


def vtulka_variant(*, used_g: str | None = None, prediction: str | None = None) -> bytes:
    """vtulka_A.gcode.3mf re-sliced in memory: another PLA-white usage and/or prediction."""
    parts = _service_parts()
    if used_g is not None:
        parts = _edit(SLICE_INFO, _sub(r'used_g="[^"]*"', f'used_g="{used_g}"'), parts)
    if prediction is not None:
        pattern, repl = r'key="prediction" value="[^"]*"', f'key="prediction" value="{prediction}"'
        parts = _edit(SLICE_INFO, _sub(pattern, repl), parts)
    return build_zip(parts)


def padded_to(size: int) -> bytes:
    """The sliced reference plus a stored (uncompressed) attachment, exactly `size` bytes."""
    with zipfile.ZipFile(VTULKA_SLICED) as zf:
        parts = [(info.filename, zf.read(info)) for info in zf.infolist()]
    name = "Auxiliaries/padding.bin"

    def build(padding: int) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for part, data in parts:
                zf.writestr(part, data)
            zf.writestr(name, bytes(padding), compress_type=zipfile.ZIP_STORED)
        return buf.getvalue()

    body = build(size - len(build(0)))
    assert len(body) == size
    return body
