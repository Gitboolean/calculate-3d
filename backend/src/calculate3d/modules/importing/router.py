from typing import Annotated

from fastapi import APIRouter, Depends, Request

from calculate3d.core.db import ConnectionDep
from calculate3d.core.problems import GUARD_RESPONSES, Problem, problem_response
from calculate3d.modules.importing import service
from calculate3d.modules.importing.schemas import (
    ImportRejectedProblem,
    ImportSettingsMissingProblem,
    SlicerFile,
)

router = APIRouter(prefix="/api/importing", tags=["importing"], responses=GUARD_RESPONSES)

# 100 MB in decimal bytes, as Finder shows a file size (ADR 0002, PRD §6).
MAX_BODY_BYTES = 100_000_000

OCTET_STREAM_BODY = {
    "requestBody": {
        "required": True,
        "description": "Байти файлу слайсера, ≤ 100 000 000 (ADR 0002); тип — за вмістом",
        "content": {
            "application/octet-stream": {
                "schema": {"type": "string", "format": "binary", "maxLength": MAX_BODY_BYTES}
            }
        },
    }
}


async def read_body(request: Request) -> bytes:
    """The raw body in memory, never on disk; reading stops at the first byte over the limit."""
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        raise service.FileTooLarge
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > MAX_BODY_BYTES:
            raise service.FileTooLarge
    return bytes(body)


@router.post(
    "/parse",
    operation_id="parseSlicerFile",
    openapi_extra=OCTET_STREAM_BODY,
    responses={
        409: problem_response(
            ImportSettingsMissingProblem, "Бракує пластиків або налаштувань цін (AC-04)"
        ),
        413: problem_response(Problem, "Тіло понад 100 000 000 байт (AC-13, ADR 0002)"),
        415: problem_response(Problem, "Тіло не application/octet-stream (AC-15, ADR 0002)"),
        422: problem_response(
            ImportRejectedProblem, "Файл непридатний — код називає причину (AC-12…AC-14)"
        ),
    },
)
def parse_slicer_file(
    body: Annotated[bytes, Depends(read_body)], conn: ConnectionDep
) -> SlicerFile:
    return service.parse_slicer_file(conn, body)
