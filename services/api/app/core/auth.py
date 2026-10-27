"""Authentication & Authorization Foundation (Part A4).
JWT-based authentication resolving AuthContext(user_id, org_id, role).
"""
from datetime import datetime, timedelta
from typing import Literal, NamedTuple, Optional
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from services.api.app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

RoleType = Literal["owner", "admin", "member", "viewer"]

class AuthContext(NamedTuple):
    user_id: UUID
    org_id: UUID
    role: RoleType

DEMO_ORG_A = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ORG_B = UUID("22222222-2222-2222-2222-222222222222")

DEMO_USER_A_MEMBER = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
DEMO_USER_A_ADMIN = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaad")
DEMO_USER_A_VIEWER = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaae")

DEMO_USER_B_MEMBER = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

def create_access_token(
    user_id: UUID,
    org_id: UUID,
    role: RoleType,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "role": role,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> AuthContext:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = UUID(payload["sub"])
        org_id = UUID(payload["org_id"])
        role = payload["role"]
        if role not in ("owner", "admin", "member", "viewer"):
            raise ValueError(f"Invalid role in token: {role}")
        return AuthContext(user_id=user_id, org_id=org_id, role=role)
    except (jwt.PyJWTError, KeyError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(err)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_auth_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> AuthContext:
    """FastAPI dependency to extract verified AuthContext.
    NEVER read org_id from request body or query parameter!
    """
    if credentials is None:
        # In dev mode, fallback to default demo user if no token is passed
        if settings.ENV == "dev":
            return AuthContext(user_id=DEMO_USER_A_MEMBER, org_id=DEMO_ORG_A, role="member")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)

def require_role(*allowed_roles: RoleType):
    """Dependency factory ensuring the caller has at least one of the allowed roles."""
    async def role_checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{ctx.role}' does not have sufficient permissions. Required one of: {allowed_roles}",
            )
        return ctx
    return role_checker
