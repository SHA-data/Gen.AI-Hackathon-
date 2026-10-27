"""Core error handling and standard HTTP error envelopes (Part A2)."""
from typing import Any, Dict, Optional
from uuid import uuid4
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from packages.contracts.envelope import ErrorDetail, ErrorEnvelope


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("NOT_FOUND", message, status.HTTP_404_NOT_FOUND, details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__("UNAUTHORIZED", message, status.HTTP_401_UNAUTHORIZED, details)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__("FORBIDDEN", message, status.HTTP_403_FORBIDDEN, details)


class ConflictError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("CONFLICT", message, status.HTTP_409_CONFLICT, details)


class ValidationError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("VALIDATION_ERROR", message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id,
            }
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": {},
                "request_id": request_id,
            }
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message=str(exc) if getattr(request.app.state, "debug", False) else "An unexpected error occurred",
            details={},
            request_id=request_id,
        )
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=envelope.model_dump())
