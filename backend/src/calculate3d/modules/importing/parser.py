"""Slicer-file parser — pure `bytes →` result or `ParseError`, no I/O (SAD §8; ADR 0001).

Standard library only (SAD §2). Only the 4 service parts are ever inflated, by exact name and under
the archive read limits; G-code and attachments are never decompressed and archive paths are never
used as file-system paths. Expat ≥ 2.4 refuses exponential entity expansion and ElementTree never
loads external entities, so a hostile XML part only fails to parse.
"""

import io
import json
import zipfile
import zlib
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

MODEL = "3D/3dmodel.model"
MODEL_SETTINGS = "Metadata/model_settings.config"
SLICE_INFO = "Metadata/slice_info.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
SERVICE_PARTS = (MODEL, MODEL_SETTINGS, SLICE_INFO, PROJECT_SETTINGS)

MAX_ENTRIES = 10_000
MAX_PART_BYTES = 8_000_000
BAMBU_APPLICATION_PREFIX = "BambuStudio-"

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


def read_sliced_plate(body: bytes) -> SlicedPlate:
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


def _read_service_parts(body: bytes) -> dict[str, bytes]:
    """Step 0 — open the ZIP and inflate only the service parts under the read limits."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(body))
    except (zipfile.BadZipFile, ValueError, EOFError) as e:
        # Something ZIP-like that will not open is damaged; anything else is a foreign format.
        damaged = not body or body.startswith(_ZIP_SIGNATURE)
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
    except (zipfile.BadZipFile, zlib.error, EOFError, OSError, RuntimeError) as e:
        raise ParseError(CORRUPTED_FILE) from e
    if len(data) > MAX_PART_BYTES:
        raise ParseError(CORRUPTED_FILE)
    return data


def _xml(data: bytes) -> ET.Element:
    try:
        return ET.fromstring(data)
    except ET.ParseError as e:
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


def _plate_index(value: str | None) -> int:
    if value is None or not value.isascii() or not value.isdigit() or int(value) < 1:
        raise ParseError(CORRUPTED_FILE)
    return int(value)


def _plates_with_gcode(model_settings: ET.Element) -> dict[int, str]:
    """Plates of `model_settings.config` that have a G-code file → their name (`plater_name`)."""
    plates: dict[int, str] = {}
    for plate in model_settings.findall("plate"):
        meta = _metadata(plate)
        if meta.get("gcode_file"):
            index = _plate_index(meta.get("plater_id"))
            if index in plates:
                raise ParseError(CORRUPTED_FILE)
            plates[index] = meta.get("plater_name", "")
    return plates


def _slice_results(slice_info: ET.Element) -> dict[int, ET.Element]:
    """Plates of `slice_info.config` that carry slicing results, by plate index."""
    results: dict[int, ET.Element] = {}
    for plate in slice_info.findall("plate"):
        index = _plate_index(_metadata(plate).get("index"))
        if index in results:
            raise ParseError(CORRUPTED_FILE)
        results[index] = plate
    return results
