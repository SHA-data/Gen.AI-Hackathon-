"""Core foundation package for NeuralCFO FastAPI API."""
from services.api.app.core.config import settings
from services.api.app.core.auth import (
    AuthContext,
    create_access_token,
    decode_access_token,
    get_auth_context,
    require_role,
    DEMO_ORG_A,
    DEMO_ORG_B,
    DEMO_USER_A_MEMBER,
    DEMO_USER_A_ADMIN,
    DEMO_USER_A_VIEWER,
    DEMO_USER_B_MEMBER,
)
from services.api.app.core.audit import audit_logger, AuditLogEntry
from services.api.app.core.errors import AppError, app_error_handler, http_exception_handler
from services.api.app.core.evidence import evidence_registry
