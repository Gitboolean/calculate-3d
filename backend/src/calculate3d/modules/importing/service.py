"""importing — slicer-file parsing and filament mappings. No FastAPI/SQL imports; `catalog` calls
`remember_mappings` inside its item-save transaction, never `repo`/`tables` (ADR 0003, ADR 0005).
"""

from collections.abc import Callable, Sequence

from calculate3d.core.errors import AppError
from calculate3d.modules.importing import parser, repo
from calculate3d.modules.importing.schemas import (
    FilamentMappingInput,
    SlicedPlate,
    SlicerFilament,
    SlicerFile,
    each_filament_once,
)
from calculate3d.modules.pricing import service as pricing_service

__all__ = [
    "FilamentMappingInput",
    "FileTooLarge",
    "ImportPlasticNotFound",
    "ImportSettingsMissing",
    "each_filament_once",
    "parse_slicer_file",
    "remember_mappings",
]

# Messages are Ukrainian (SAD §10 «Локалізація»); the web words its hints from `code`.


class ImportSettingsMissing(AppError):
    def __init__(self, missing: list[str]) -> None:
        super().__init__(
            "importing.settings_missing",
            "Для імпорту бракує пластиків або налаштувань цін",
            409,
            missing=missing,
        )


class FileTooLarge(AppError):
    def __init__(self) -> None:
        super().__init__("importing.file_too_large", "Файл слайсера більший за 100 МБ", 413)


class ImportPlasticNotFound(AppError):
    def __init__(self, index: int) -> None:
        super().__init__(
            "importing.plastic_not_found",
            "Пластик зіставлення не знайдено",
            422,
            field=f"filament_mappings.{index}.plastic_id",
        )


class NotSlicerProject(AppError):
    def __init__(self) -> None:
        super().__init__(parser.NOT_SLICER_PROJECT, "Це не файл проєкту Bambu Studio", 422)


class NotSliced(AppError):
    def __init__(self) -> None:
        super().__init__(
            parser.NOT_SLICED, "Файл не нарізаний: у ньому немає витрати й часу друку", 422
        )


class MultipleSlicedPlates(AppError):
    def __init__(self) -> None:
        super().__init__(
            parser.MULTIPLE_SLICED_PLATES,
            "Імпортується лише файл з однією нарізаною пластиною",
            422,
        )


class CorruptedFile(AppError):
    def __init__(self) -> None:
        super().__init__(parser.CORRUPTED_FILE, "Файл слайсера пошкоджений", 422)


class PrintTimeOutOfRange(AppError):
    def __init__(self) -> None:
        super().__init__(
            parser.PRINT_TIME_OUT_OF_RANGE,
            "Час друку у файлі нульовий або понад 100 000 год",
            422,
        )


class NoFilamentUsage(AppError):
    def __init__(self) -> None:
        super().__init__(parser.NO_FILAMENT_USAGE, "У файлі немає витрати пластику", 422)


_REJECTIONS: dict[str, Callable[[], AppError]] = {
    parser.NOT_SLICER_PROJECT: NotSlicerProject,
    parser.NOT_SLICED: NotSliced,
    parser.MULTIPLE_SLICED_PLATES: MultipleSlicedPlates,
    parser.CORRUPTED_FILE: CorruptedFile,
    parser.PRINT_TIME_OUT_OF_RANGE: PrintTimeOutOfRange,
    parser.NO_FILAMENT_USAGE: NoFilamentUsage,
}


def parse_slicer_file(conn: repo.DbConnection, body: bytes) -> SlicerFile:
    """Settings readiness (AC-04) → parse (SAD §8) → remembered plastics. Writes nothing."""
    missing = [] if pricing_service.plastics_exist(conn) else ["plastics"]
    if pricing_service.get_settings(conn) is None:
        missing.append("price_settings")
    if missing:
        raise ImportSettingsMissing(missing)
    try:
        parsed = parser.parse(body)
    except parser.ParseError as exc:
        raise _REJECTIONS[exc.code]() from exc
    plastics = repo.find_mappings(conn, [(f.name, f.color) for f in parsed.filaments])
    return SlicerFile(
        plate=SlicedPlate(index=parsed.plate.index, name=parsed.plate.name),
        print_time_s=parsed.print_time_s,
        filaments=[
            SlicerFilament(
                filament_name=f.name,
                filament_type=f.type,
                filament_color=f.color,
                usage_mg=f.usage_mg,
                plastic_id=plastics.get((f.name, f.color)),
            )
            for f in parsed.filaments
        ],
    )


def _first_unknown(conn: repo.DbConnection, mappings: Sequence[FilamentMappingInput]) -> int | None:
    ids = {m.plastic_id for m in mappings}
    known = {p.id for p in pricing_service.list_plastics_by_ids(conn, ids)}
    return next((i for i, m in enumerate(mappings) if m.plastic_id not in known), None)


def remember_mappings(conn: repo.DbConnection, mappings: Sequence[FilamentMappingInput]) -> None:
    """Upsert on the caller's Connection — no transaction of its own (ADR 0003)."""
    if not mappings:
        return
    if (index := _first_unknown(conn, mappings)) is not None:
        raise ImportPlasticNotFound(index)
    records = [
        repo.MappingRecord(m.filament_name, m.filament_color, m.plastic_id) for m in mappings
    ]
    try:
        repo.upsert_mappings(conn, records)
    except repo.MappingPlasticMissing as exc:
        # A plastic vanished after the pre-check; point at the first one that is gone now.
        raise ImportPlasticNotFound(_first_unknown(conn, mappings) or 0) from exc
