"""FastAPI Application Entrypoint."""
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from services.api.app.chat.api.router import v1_router
from services.api.app.core.errors import AppError, app_error_handler, http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

# Ensure tools are loaded and registered
import services.api.app.chat.tools

app = FastAPI(
    title="NeuralCFO + Moonshot Mode API Gateway",
    version="1.0.0",
    description="Modular monolith API gateway and conversational engine",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach request_id to request state
@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include v1 router
app.include_router(v1_router)

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "service": "neuralcfo-gateway"}
