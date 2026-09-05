"""ERROR_AND_AUTH.md error envelope and shared error type."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self, status: int, code: str, message: str, details: dict[str, object] | None = None
    ):
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


def error_body(
    code: str, message: str, request_id: str, details: dict[str, object]
) -> dict[str, object]:
    return {
        "error": {"code": code, "message": message, "request_id": request_id, "details": details}
    }


def install_error_handlers(app: FastAPI) -> None:
    def request_id(request: Request) -> str:
        return getattr(request.state, "request_id", "")

    @app.exception_handler(ApiError)
    def api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            error_body(exc.code, exc.message, request_id(request), exc.details),
            status_code=exc.status,
        )

    @app.exception_handler(RequestValidationError)
    def invalid(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = []
        for item in exc.errors():
            location = item.get("loc") or ()
            field = location[-1] if location else "body"
            fields.append({"field": str(field), "issue": str(item.get("type", "invalid"))})
        return JSONResponse(
            error_body(
                "VALIDATION_ERROR",
                "The request body is invalid.",
                request_id(request),
                {"fields": fields},
            ),
            status_code=422,
        )
