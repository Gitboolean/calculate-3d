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


def _forged_entry_count(zip64: bool = False) -> bytes:
    """A small valid archive whose end-of-central-directory record declares 20 000 entries."""
    body = bytearray(build_zip(_service_parts()))
    eocd = body.rfind(b"PK\x05\x06")
    declared = 2 * ENTRY_LIMIT
    if not zip64:
        struct.pack_into("<HH", body, eocd + 8, declared, declared)
        return bytes(body)
    cd_size, cd_offset = struct.unpack_from("<II", body, eocd + 12)
    # Zip64 EOCD record + locator go right before the classic EOCD, which then holds 0xFFFF.
    record = struct.pack(
        "<IQHHIIQQQQ", 0x06064B50, 44, 45, 45, 0, 0, declared, declared, cd_size, cd_offset
    )
    locator = struct.pack("<IIQI", 0x07064B50, 0, eocd, 1)
    struct.pack_into("<HH", body, eocd + 8, 0xFFFF, 0xFFFF)
    body[eocd:eocd] = record + locator
    return bytes(body)


def _cd_flood_small_declared_count() -> bytes:
    """A valid archive whose real central directory holds > ENTRY_LIMIT records, while the EOCD
    still declares a single entry: `zipfile` reads the directory by its byte size, not the count."""
    body = bytearray(build_zip(_service_parts()))
    eocd = body.rfind(b"PK\x05\x06")
    cd_size, cd_offset = struct.unpack_from("<II", body, eocd + 12)
    # Central directory header with an empty name, no extra field, no comment, stored, 0 bytes.
    record = struct.pack(
        "<4s6H3I5H2I", b"PK\x01\x02", 20, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    )
    flood = record * (ENTRY_LIMIT + 2_000)
    body[eocd:eocd] = flood
    eocd += len(flood)
    struct.pack_into("<HH", body, eocd + 8, 1, 1)
    struct.pack_into("<I", body, eocd + 12, cd_size + len(flood))
    assert struct.unpack_from("<I", body, eocd + 16) == (cd_offset,)
    return bytes(body)


_EMPTY_CD_RECORD = struct.pack("<4s6H3I5H2I", b"PK\x01\x02", 20, 20, *[0] * 12, 0, 0)
_FLOOD_RECORDS = ENTRY_LIMIT + 2_000


def _flooded_parts() -> tuple[bytes, int, int]:
    """A valid archive cut before its EOCD, with the flood appended to its central directory.

    Returns (body without EOCD, central-directory offset, central-directory size incl. flood).
    """
    body = build_zip(_service_parts())
    eocd = body.rfind(b"PK\x05\x06")
    cd_size, cd_offset = struct.unpack_from("<II", body, eocd + 12)
    flood = _EMPTY_CD_RECORD * _FLOOD_RECORDS
    return body[:eocd] + flood, cd_offset, cd_size + len(flood)


def _eocd(count: int, size: int, offset: int) -> bytes:
    return struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, count, count, size, offset, 0)


def _cd_flood_eocd_offset_field_has_signature() -> bytes:
    """Honest comment-less EOCD whose CD-offset field reads b"PK\\x05\\x06" (zipfile ignores it)."""
    head, _, cd_size = _flooded_parts()
    count = len(_service_parts()) + _FLOOD_RECORDS
    return head + _eocd(count, cd_size, struct.unpack("<I", b"PK\x05\x06")[0])


def _zip64_tail(record_at: int, reloff: int, diroffset: int, dirsize: int) -> bytes:
    record = struct.pack("<IQHHIIQQQQ", 0x06064B50, 44, 45, 45, 0, 0, 1, 1, dirsize, diroffset)
    locator = struct.pack("<IIQI", 0x07064B50, 0, reloff, 1)
    assert record_at >= 0
    return record + locator


def _cd_flood_zip64_locator_unflagged() -> bytes:
    """Classic EOCD says 1 entry / 46 bytes (nothing saturated); the Zip64 record has the truth."""
    head, cd_offset, cd_size = _flooded_parts()
    reloff = cd_offset + cd_size  # the Zip64 record directly follows the central directory
    tail = _zip64_tail(reloff, reloff, cd_offset, cd_size)
    assert len(head) == reloff
    return head + tail + _eocd(1, 46, cd_offset)


def _cd_flood_zip64_record_at_locator_minus_56() -> bytes:
    """The locator's offset is wrong (no PK\\x06\\x06 there); the record sits at locator - 56."""
    head, cd_offset, cd_size = _flooded_parts()
    record_at = cd_offset + cd_size
    reloff = record_at - len(_EMPTY_CD_RECORD)  # inside the CD: not a Zip64 record signature
    tail = _zip64_tail(record_at, reloff, reloff - cd_size, cd_size)
    assert len(head) == record_at
    return head + tail + _eocd(1, 46, cd_offset)


def _cd_record(
    name: bytes, extra: bytes = b"", comment: bytes = b"", header_offset: int = 0
) -> bytes:
    """A stored, empty central-directory record (all sizes 0) with the given variable fields."""
    header = struct.pack(
        "<4s6H3I5H2I",
        b"PK\x01\x02",
        20,
        20,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        len(name),
        len(extra),
        len(comment),
        0,
        0,
        0,
        header_offset,
    )
    return header + name + extra + comment


def _with_cd_records(records: list[bytes]) -> bytes:
    """A valid archive whose central directory also holds `records`, with an honest EOCD."""
    body = build_zip(_service_parts())
    eocd = body.rfind(b"PK\x05\x06")
    cd_size, cd_offset = struct.unpack_from("<II", body, eocd + 12)
    extra = b"".join(records)
    count = len(_service_parts()) + len(records)
    return body[:eocd] + extra + _eocd(count, cd_size + len(extra), cd_offset)


# A little over the 4 MB central-directory byte cap (real ones are 1-5 KB): a raised cap is caught.
_DISTINCT_OFFSET = 100_000_000  # past the real parts; each record gets its own, so none overlap
_FAT_RECORDS = 63  # 63 x 65 535-byte names = 4.13 MB central directory
_WITHIN_LIMIT_RECORDS = 810  # 810 x ~5 KB = 4.1 MB central directory, far below ENTRY_LIMIT


def cd_padded_to(cd_size: int) -> bytes:
    """A valid-looking archive whose central directory is exactly `cd_size` bytes: the real
    parts plus padding records (distinct header offsets, the slack carried in their comments)."""
    body = build_zip(_service_parts())
    real_size = struct.unpack_from("<I", body, body.rfind(b"PK\x05\x06") + 12)[0]
    slack = cd_size - real_size
    name_len = len(b"Auxiliaries/p00000")
    per_record = 46 + name_len + 65_535
    count = -(-slack // per_record)
    comments, extra = divmod(slack - count * (46 + name_len), count)
    records = [
        _cd_record(
            f"Auxiliaries/p{n:05d}".encode(),
            comment=b"c" * (comments + (1 if n < extra else 0)),
            header_offset=_DISTINCT_OFFSET + n,
        )
        for n in range(count)
    ]
    return _with_cd_records(records)


def _cd_fat_records() -> bytes:
    """Few records, but each carries a 65 535-byte name: the directory is megabytes."""
    return _with_cd_records(
        [
            _cd_record(f"{n:05d}".encode().ljust(65_535, b"n"), header_offset=_DISTINCT_OFFSET + n)
            for n in range(_FAT_RECORDS)
        ]
    )


def _cd_oversized_within_entry_limit() -> bytes:
    """Under ENTRY_LIMIT records (each with a 5 KB comment), yet the directory is > 4 MB."""
    return _with_cd_records(
        [
            _cd_record(
                f"Auxiliaries/f{n}".encode(),
                comment=b"c" * 5_000,
                header_offset=_DISTINCT_OFFSET + n,
            )
            for n in range(_WITHIN_LIMIT_RECORDS)
        ]
    )


def _cd_flood_zip64_extensible_data() -> bytes:
    """Zip64 record with 64 bytes of extensible data: the locator's offset (cd end) is the only
    place that finds it; classic EOCD says 1 entry / 46 bytes."""
    head, cd_offset, cd_size = _flooded_parts()
    ext = b"E" * 64
    reloff = cd_offset + cd_size
    record = struct.pack(
        "<IQHHIIQQQQ", 0x06064B50, 44 + len(ext), 45, 45, 0, 0, 1, 1, cd_size, cd_offset
    )
    locator = struct.pack("<IIQI", 0x07064B50, 0, reloff, 1)
    assert len(head) == reloff
    return head + record + ext + locator + _eocd(1, 46, cd_offset)


def _overlapped_entries() -> bytes:
    """Two central-directory records (the model part and an extra one) share one header offset."""
    body = build_zip(_service_parts())
    eocd = body.rfind(b"PK\x05\x06")
    cd_size, cd_offset = struct.unpack_from("<II", body, eocd + 12)
    (name_len,) = struct.unpack_from("<H", body, cd_offset + 28)
    assert body[cd_offset + 46 : cd_offset + 46 + name_len] == MODEL.encode()
    (shared,) = struct.unpack_from("<I", body, cd_offset + 42)
    twin = _cd_record(b"Auxiliaries/twin", header_offset=shared)
    return body[:eocd] + twin + _eocd(len(_service_parts()) + 1, cd_size + len(twin), cd_offset)


def _cd_extract_version_unsupported() -> bytes:
    """The first central-directory record needs version 6.4 to extract (zipfile supports 6.3)."""
    body = bytearray(build_zip(_service_parts()))
    cd = body.find(b"PK\x01\x02")
    struct.pack_into("<H", body, cd + 6, 64)
    return bytes(body)


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


HUGE_NUMBER = "9" * 4301  # > 4300 digits: int() refuses it (CPython limit)


def _huge_digits(name: str, pattern: str, repl: str) -> bytes:
    return build_zip(_edit(name, _sub(pattern, repl.replace("@", HUGE_NUMBER))))


def _unknown_xml_encoding() -> bytes:
    return build_zip(_edit(SLICE_INFO, _sub(r'encoding="UTF-8"', 'encoding="x-bogus"')))


def _local_name_not_utf8() -> bytes:
    """slice_info's LOCAL header sets the UTF-8 flag (0x800) and has a non-UTF-8 name byte."""
    body = bytearray(build_zip(_service_parts()))
    name = SLICE_INFO.encode()
    pos = body.find(b"PK\x03\x04")
    while pos != -1:
        (name_len,) = struct.unpack_from("<H", body, pos + 26)
        if bytes(body[pos + 30 : pos + 30 + name_len]) == name:
            (flags,) = struct.unpack_from("<H", body, pos + 6)
            struct.pack_into("<H", body, pos + 6, flags | 0x800)
            body[pos + 30 + name_len - 1] = 0xFF  # last name byte: invalid UTF-8
            return bytes(body)
        pos = body.find(b"PK\x03\x04", pos + 4)
    raise AssertionError("local header of slice_info not found")


BAD_FILES: tuple[BadFile, ...] = (
    # Step 0 — not a ZIP, or a ZIP breaking the archive read limits (SAD §8).
    BadFile("not_zip", b"%PDF-1.7\nnot a slicer project\n", NOT_SLICER_PROJECT),
    BadFile("truncated_zip", build_zip(_service_parts())[:2000], CORRUPTED_FILE),
    BadFile("empty_body", b"", CORRUPTED_FILE),
    BadFile("too_many_entries", _too_many_entries(), CORRUPTED_FILE),
    BadFile("forged_eocd_entry_count", _forged_entry_count(), CORRUPTED_FILE),
    BadFile("forged_zip64_entry_count", _forged_entry_count(zip64=True), CORRUPTED_FILE),
    BadFile("cd_flood_small_declared_count", _cd_flood_small_declared_count(), CORRUPTED_FILE),
    BadFile(
        "cd_flood_eocd_offset_field_has_signature",
        _cd_flood_eocd_offset_field_has_signature(),
        CORRUPTED_FILE,
    ),
    BadFile(
        "cd_flood_zip64_locator_unflagged", _cd_flood_zip64_locator_unflagged(), CORRUPTED_FILE
    ),
    BadFile(
        "cd_flood_zip64_record_at_locator_minus_56",
        _cd_flood_zip64_record_at_locator_minus_56(),
        CORRUPTED_FILE,
    ),
    BadFile("cd_fat_records", _cd_fat_records(), CORRUPTED_FILE),
    BadFile("cd_oversized_within_entry_limit", _cd_oversized_within_entry_limit(), CORRUPTED_FILE),
    BadFile("cd_flood_zip64_extensible_data", _cd_flood_zip64_extensible_data(), CORRUPTED_FILE),
    BadFile("overlapped_entries", _overlapped_entries(), CORRUPTED_FILE),
    BadFile("cd_extract_version_unsupported", _cd_extract_version_unsupported(), CORRUPTED_FILE),
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
    BadFile("non_ascii_digits_in_usage", _used_g("\u0663" + "11.54"), CORRUPTED_FILE),
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
    BadFile(
        "huge_plate_index",
        _huge_digits(SLICE_INFO, r'key="index" value="1"', 'key="index" value="@"'),
        CORRUPTED_FILE,
    ),
    BadFile(
        "huge_filament_id",
        _huge_digits(SLICE_INFO, r'<filament id="1"', '<filament id="@"'),
        CORRUPTED_FILE,
    ),
    BadFile(
        "huge_plater_id",
        _huge_digits(MODEL_SETTINGS, r'key="plater_id" value="1"', 'key="plater_id" value="@"'),
        CORRUPTED_FILE,
    ),
    BadFile("unknown_xml_encoding", _unknown_xml_encoding(), CORRUPTED_FILE),
    BadFile("local_header_name_not_utf8", _local_name_not_utf8(), CORRUPTED_FILE),
    # Step 5 — file bounds (AC-14).
    BadFile("non_ascii_digits_in_print_time", _prediction("\u0663" + "600"), CORRUPTED_FILE),
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
