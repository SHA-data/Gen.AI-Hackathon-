from uuid import UUID
from fastapi import FastAPI, Depends, status
from pydantic import BaseModel, Field

from packages.contracts.envelope import ErrorEnvelope
from services.api.app.core.auth import (
    AuthContext,
    create_access_token,
    get_auth_context,
)
from services.api.app.core.config import settings
from services.api.app.core.errors import (
    AppError,
    ForbiddenError,
    app_error_handler,
    global_exception_handler,
)
from services.api.app.core.middleware import RequestIdMiddleware

app = FastAPI(
    title="NeuralCFO API",
    version=settings.ENGINE_VERSION,
    description="Unified Backend for NeuralCFO, Moonshot Mode, and Chatbot Gateway",
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Middleware
app.add_middleware(RequestIdMiddleware)


class DevTokenRequest(BaseModel):
    user_id: UUID
    org_id: UUID
    role: str = Field(default="member", description="owner | admin | member | viewer")


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    org_id: UUID
    user_id: UUID
    role: str


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "engine_version": settings.ENGINE_VERSION,
        "env": settings.ENV,
    }


@app.post(
    "/v1/dev/token",
    response_model=DevTokenResponse,
    tags=["Auth"],
    responses={
        403: {"model": ErrorEnvelope, "description": "Forbidden if not dev environment"}
    },
)
async def create_dev_token(payload: DevTokenRequest):
    """Mints authentication tokens for seeded demo users in two demo orgs.

    Disabled unless ENV=dev.
    """
    if settings.ENV != "dev":
        raise ForbiddenError("Dev token endpoint is only active when ENV=dev")

    token = create_access_token(
        user_id=payload.user_id,
        org_id=payload.org_id,
        role=payload.role,
    )
    return DevTokenResponse(
        access_token=token,
        token_type="bearer",
        org_id=payload.org_id,
        user_id=payload.user_id,
        role=payload.role,
    )


@app.get("/v1/me", tags=["Auth"])
async def get_current_user(auth: AuthContext = Depends(get_auth_context)):
    return {
        "user_id": str(auth.user_id),
        "org_id": str(auth.org_id),
        "role": auth.role,
    }
