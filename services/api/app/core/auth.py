import time
from typing import Optional
from uuid import UUID
import jwt
from fastapi import Header
from pydantic import BaseModel

from services.api.app.core.config import settings
from services.api.app.core.errors import ForbiddenError, UnauthorizedError

ROLE_HIERARCHY = {
    "viewer": 1,
    "member": 2,
    "admin": 3,
    "owner": 4,
}


class AuthContext(BaseModel):
    user_id: UUID
    org_id: UUID
    role: str

    def can_perform(self, required_role: str) -> bool:
        user_level = ROLE_HIERARCHY.get(self.role.lower(), 0)
        required_level = ROLE_HIERARCHY.get(required_role.lower(), 99)
        return user_level >= required_level


def create_access_token(
    user_id: UUID,
    org_id: UUID,
    role: str,
    expires_in_minutes: Optional[int] = None,
) -> str:
    exp_minutes = expires_in_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "role": role.lower(),
        "iat": now,
        "exp": now + (exp_minutes * 60),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> AuthContext:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = UUID(str(payload.get("sub")))
        org_id = UUID(str(payload.get("org_id")))
        role = str(payload.get("role", "viewer")).lower()

        if role not in ROLE_HIERARCHY:
            raise UnauthorizedError("Invalid token role")

        return AuthContext(user_id=user_id, org_id=org_id, role=role)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise UnauthorizedError(f"Invalid authentication token: {str(exc)}")


async def get_auth_context(authorization: Optional[str] = Header(None)) -> AuthContext:
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header format; expected Bearer <token>")
    return decode_access_token(parts[1])


def require_role(min_role: str):
    async def role_checker(auth: AuthContext = Header(None)) -> AuthContext:
        # Note: in fastapi dependency injection, get_auth_context will be called
        pass
    return role_checker


class RoleChecker:
    def __init__(self, min_role: str):
        self.min_role = min_role

    def __call__(self, auth: AuthContext) -> AuthContext:
        if not auth.can_perform(self.min_role):
            raise ForbiddenError(f"Operation requires minimum role '{self.min_role}'")
        return auth
