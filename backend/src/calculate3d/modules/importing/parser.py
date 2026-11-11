"""Slicer-file parser — pure `bytes →` result or `ParseError`, no I/O (SAD §8; ADR 0001).

Standard library only (SAD §2). Only the 4 service parts are ever inflated, by exact name and under
the archive read limits; G-code and attachments are never decompressed and archive paths are never
used as file-system paths. Expat ≥ 2.4 refuses exponential entity expansion and ElementTree never
loads external entities, so a hostile XML part only fails to parse.
"""

import io
import json
import struct
import zipfile
import zlib
from collections.abc import Buffer
from dataclasses import dataclass, replace
from typing import Any
from xml.etree import ElementTree as ET

from calculate3d.modules.importing import normalize

MODEL = "3D/3dmodel.model"
MODEL_SETTINGS = "Metadata/model_settings.config"
SLICE_INFO = "Metadata/slice_info.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
SERVICE_PARTS = (MODEL, MODEL_SETTINGS, SLICE_INFO, PROJECT_SETTINGS)

MAX_ENTRIES = 10_000
MAX_PART_BYTES = 8_000_000
BAMBU_APPLICATION_PREFIX = "BambuStudio-"
MAX_PRINT_TIME_S = 360_000_000  # 100 000 h, as for manual input (AC-14)
MAX_FILAMENTS = 32  # one mapping key per row, up to 32 rows (data-model)

# Rejection codes — the `code` of ImportRejectedProblem (contracts/openapi.yaml).
NOT_SLICER_PROJECT = "importing.not_slicer_project"
NOT_SLICED = "importing.not_sliced"
MULTIPLE_SLICED_PLATES = "importing.multiple_sliced_plates"
CORRUPTED_FILE = "importing.corrupted_file"
PRINT_TIME_OUT_OF_RANGE = "importing.print_time_out_of_range"
NO_FILAMENT_USAGE = "importing.no_filament_usage"

_SUPPORTED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
_ZIP_SIGNATURE = b"PK"


class ParseError(Exception):
    """The file is rejected; `code` names the reason (one per step of the SAD §8 chain)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Plate:
    index: int
    name: str


@dataclass(frozen=True)
class SlicedPlate:
    """The single sliced plate: its slicing results and the project's filament presets."""

    plate: Plate
    results: ET.Element
    project_settings: dict[str, Any]


@dataclass(frozen=True)
class ParsedFilament:
    """A used slicer filament, keyed by (name, color) after normalization (AC-09)."""

    name: str
    type: str
    color: str
    usage_mg: int


@dataclass(frozen=True)
class ParsedFile:
    plate: Plate
    print_time_s: int
    filaments: tuple[ParsedFilament, ...]


def parse(body: Buffer) -> ParsedFile:
    """The whole SAD §8 chain: steps 0–3, then integrity (4) and the file bounds (5)."""
    sliced = read_sliced_plate(body)
    print_time_s = normalize.print_time_s(_metadata(sliced.results).get("prediction", ""))
    if print_time_s is None:
        raise ParseError(CORRUPTED_FILE)
    filaments = _used_filaments(sliced)
    if not 0 < print_time_s <= MAX_PRINT_TIME_S:
        raise ParseError(PRINT_TIME_OUT_OF_RANGE)
    if not filaments:
        raise ParseError(NO_FILAMENT_USAGE)
    return ParsedFile(sliced.plate, print_time_s, filaments)


def read_sliced_plate(body: Buffer) -> SlicedPlate:
    """Steps 0–3: archive limits → Bambu Studio project → sliced → exactly one sliced plate."""
    parts = _read_service_parts(body)
    if not _is_bambu_project(parts):
        raise ParseError(NOT_SLICER_PROJECT)
    project_settings = _json_object(parts[PROJECT_SETTINGS])
    if MODEL_SETTINGS not in parts or SLICE_INFO not in parts:
        raise ParseError(CORRUPTED_FILE)
    gcode_plates = _plates_with_gcode(_xml(parts[MODEL_SETTINGS]))
    results = _slice_results(_xml(parts[SLICE_INFO]))
    sliced = [(index, name) for index, name in gcode_plates.items() if index in results]
    if not sliced:
        raise ParseError(NOT_SLICED)
    if len(sliced) > 1:
        raise ParseError(MULTIPLE_SLICED_PLATES)
    ((index, name),) = sliced
    return SlicedPlate(Plate(index, name), results[index], project_settings)


def _read_service_parts(buffer: Buffer) -> dict[str, bytes]:
    """Step 0 — open the ZIP and inflate only the service parts under the read limits."""
    body = memoryview(buffer)
    _check_central_directory(body)
    try:
        archive = zipfile.ZipFile(_BufferReader(body))
    except (zipfile.BadZipFile, ValueError, EOFError, NotImplementedError) as e:
        # Something ZIP-like that will not open is damaged; anything else is a foreign format.
        damaged = not body or bytes(body[:2]) == _ZIP_SIGNATURE
        raise ParseError(CORRUPTED_FILE if damaged else NOT_SLICER_PROJECT) from e
    with archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(entries) > MAX_ENTRIES or len(set(names)) != len(names):
            raise ParseError(CORRUPTED_FILE)
        if any(_is_unsafe_path(name) for name in names):
            raise ParseError(CORRUPTED_FILE)
        return {
            entry.filename: _inflate(archive, entry)
            for entry in entries
            if entry.filename in SERVICE_PARTS
        }


class _BufferReader(io.RawIOBase):
    """Read-only seekable view over a buffer — `io.BytesIO(buffer)` would copy the body."""

    def __init__(self, data: memoryview) -> None:
        self._data = data
        self._pos = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = (0, self._pos, len(self._data))[whence]
        self._pos = max(0, base + offset)
        return self._pos

    def readinto(self, buffer: Buffer) -> int:
        out = memoryview(buffer).cast("B")
        chunk = self._data[self._pos : self._pos + len(out)]
        out[: len(chunk)] = chunk
        self._pos += len(chunk)
        return len(chunk)


def _check_central_directory(body: memoryview) -> None:
    """Reject an over-limit entry count before `zipfile` builds its entry list (SAD §8).

    Mirrors zipfile's EOCD / Zip64 lookup so the count is taken from where zipfile reads the
    directory; a missing or malformed EOCD is left to `zipfile` to report.
    """
    if bytes(body[-22:-18]) == b"PK\x05\x06" and not any(body[-2:]):
        eocd = len(body) - 22  # no archive comment: the EOCD is the last 22 bytes
    else:
        tail_start = max(0, len(body) - (22 + 65_535))
        eocd = bytes(body[tail_start:]).rfind(b"PK\x05\x06")
        if eocd < 0:
            return
        eocd += tail_start
        if eocd + 22 > len(body):
            return
    _, _, _, _, count, size, _, _ = struct.unpack("<4s4H2LH", body[eocd : eocd + 22])
    location = eocd  # where the central directory ends: the EOCD or the Zip64 record
    if eocd >= 20 and bytes(body[eocd - 20 : eocd - 16]) == b"PK\x06\x07":
        reloff = struct.unpack("<Q", body[eocd - 12 : eocd - 4])[0]
        location = eocd - 20 - 56
        if location < 0 or reloff > location:
            return
        if bytes(body[reloff : reloff + 4]) == b"PK\x06\x06":
            location = reloff  # otherwise zipfile falls back to the record right before the locator
        if bytes(body[location : location + 4]) != b"PK\x06\x06":
            return
        count, size = struct.unpack("<QQ", body[location + 32 : location + 48])
    if count > MAX_ENTRIES:
        raise ParseError(CORRUPTED_FILE)
    _count_records(body, location - size, location)


def _count_records(body: memoryview, pos: int, end: int) -> None:
    """Walk the central-directory headers `zipfile` will parse (it reads by byte size, not by the
    declared count) and reject more than MAX_ENTRIES; a directory the walk can't follow is left to
    `zipfile` to report."""
    if pos < 0:
        return
    records = 0
    while pos < end:
        if pos + 46 > len(body) or bytes(body[pos : pos + 4]) != b"PK\x01\x02":
            return
        records += 1
        if records > MAX_ENTRIES:
            raise ParseError(CORRUPTED_FILE)
        name, extra, comment = struct.unpack("<3H", body[pos + 28 : pos + 34])
        pos += 46 + name + extra + comment


def _is_unsafe_path(name: str) -> bool:
    return name.startswith(("/", "\\")) or ".." in name.replace("\\", "/").split("/")


def _inflate(archive: zipfile.ZipFile, entry: zipfile.ZipInfo) -> bytes:
    encrypted = entry.flag_bits & 0x1
    if encrypted or entry.compress_type not in _SUPPORTED_COMPRESSION:
        raise ParseError(CORRUPTED_FILE)
    if entry.file_size > MAX_PART_BYTES:
        raise ParseError(CORRUPTED_FILE)
    try:
        with archive.open(entry) as part:
            # The header may lie about the size: never read more than the limit + 1 byte.
            data = part.read(MAX_PART_BYTES + 1)
    except (zipfile.BadZipFile, zlib.error, EOFError, OSError, RuntimeError, ValueError) as e:
        raise ParseError(CORRUPTED_FILE) from e
    if len(data) > MAX_PART_BYTES:
        raise ParseError(CORRUPTED_FILE)
    return data


def _xml(data: bytes) -> ET.Element:
    try:
        return ET.fromstring(data)
    except (ET.ParseError, LookupError, ValueError) as e:
        # LookupError: the XML declaration names an encoding Python does not know.
        raise ParseError(CORRUPTED_FILE) from e


def _json_object(data: bytes) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except (ValueError, RecursionError) as e:
        raise ParseError(CORRUPTED_FILE) from e
    if not isinstance(value, dict):
        raise ParseError(CORRUPTED_FILE)
    return value


def _local_name(tag: str) -> str:
    return tag.rpartition("}")[2]


def _is_bambu_project(parts: dict[str, bytes]) -> bool:
    """Step 1 — Bambu Studio wrote `Application`, and the project settings are present."""
    if MODEL not in parts:
        return False
    application = next(
        (
            element.text or ""
            for element in _xml(parts[MODEL])
            if _local_name(element.tag) == "metadata" and element.get("name") == "Application"
        ),
        "",
    )
    return application.startswith(BAMBU_APPLICATION_PREFIX) and PROJECT_SETTINGS in parts


def _metadata(element: ET.Element) -> dict[str, str]:
    return {item.get("key", ""): item.get("value", "") for item in element.findall("metadata")}


_MAX_ID_DIGITS = 9  # plate index / filament id are tiny; also keeps int() under the digit limit


def _positive_int(value: str | None) -> int:
    if (
        value is None
        or not value.isascii()
        or not value.isdigit()
        or len(value) > _MAX_ID_DIGITS
        or int(value) < 1
    ):
        raise ParseError(CORRUPTED_FILE)
    return int(value)


def _plates_with_gcode(model_settings: ET.Element) -> dict[int, str]:
    """Plates of `model_settings.config` that have a G-code file → their name (`plater_name`)."""
    plates: dict[int, str] = {}
    for plate in model_settings.findall("plate"):
        meta = _metadata(plate)
        if meta.get("gcode_file"):
            index = _positive_int(meta.get("plater_id"))
            if index in plates:
                raise ParseError(CORRUPTED_FILE)
            plates[index] = meta.get("plater_name", "")
    return plates


def _slice_results(slice_info: ET.Element) -> dict[int, ET.Element]:
    """Plates of `slice_info.config` that carry slicing results, by plate index."""
    results: dict[int, ET.Element] = {}
    for plate in slice_info.findall("plate"):
        index = _positive_int(_metadata(plate).get("index"))
        if index in results:
            raise ParseError(CORRUPTED_FILE)
        results[index] = plate
    return results


def _used_filaments(sliced: SlicedPlate) -> tuple[ParsedFilament, ...]:
    """Filaments with usage > 0; identical (name, color) slots merge with the exact sum (AC-10)."""
    presets = sliced.project_settings.get("filament_settings_id")
    if not isinstance(presets, list):
        raise ParseError(CORRUPTED_FILE)
    merged: dict[tuple[str, str], ParsedFilament] = {}
    for row in sliced.results.findall("filament"):
        filament = _filament(row, presets)
        if filament.usage_mg == 0:
            continue
        key = (filament.name, filament.color)
        if (same := merged.get(key)) is not None:
            filament = replace(same, usage_mg=same.usage_mg + filament.usage_mg)
        if filament.usage_mg > normalize.MAX_SAFE_INTEGER:
            raise ParseError(CORRUPTED_FILE)
        merged[key] = filament
    if len(merged) > MAX_FILAMENTS:
        raise ParseError(CORRUPTED_FILE)
    return tuple(merged.values())


def _filament(row: ET.Element, presets: list[Any]) -> ParsedFilament:
    """`<filament id type color used_g>`; its name is the preset `filament_settings_id[id-1]`."""
    index = _positive_int(row.get("id"))
    preset = presets[index - 1] if index <= len(presets) else None
    name = normalize.filament_name(preset) if isinstance(preset, str) else None
    color = normalize.filament_color(row.get("color", ""))
    usage_mg = normalize.usage_mg(row.get("used_g", ""))
    filament_type = row.get("type", "").strip()
    if name is None or color is None or usage_mg is None or not filament_type:
        raise ParseError(CORRUPTED_FILE)
    return ParsedFilament(name, filament_type, color, usage_mg)
