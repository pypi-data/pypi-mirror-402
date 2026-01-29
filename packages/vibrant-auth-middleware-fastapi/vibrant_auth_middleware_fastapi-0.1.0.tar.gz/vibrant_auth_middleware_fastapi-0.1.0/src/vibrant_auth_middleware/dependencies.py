"""
FastAPI dependencies for authentication.

Provides injectable dependencies for use with FastAPI's Depends system.
"""

from typing import Any, Dict, Optional, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param

from .jwt_auth import get_token_payload, get_user_id_from_token


class OAuth2PasswordToken(OAuth2):
    """OAuth2 scheme for extracting Bearer token from Authorization header."""

    def __init__(
        self,
        tokenUrl: str = "/auth/token",
        scheme_name: Optional[str] = None,
        scopes: Optional[dict] = None,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=False)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            return None
        return cast(str, param)


OAUTH2_SCHEME = OAuth2PasswordToken(tokenUrl="/auth/token")


def _get_token_from_cookie(request: Request) -> Optional[str]:
    """
    Extract JWT token from cookies using access_token and token_type pair.

    Looks for 'access_token' and 'token_type' cookies. If both are present
    and token_type is 'Bearer', returns the access_token.

    Args:
        request: The incoming HTTP request.

    Returns:
        The access_token if valid cookie pair exists, None otherwise.
    """
    access_token = request.cookies.get("access_token")
    token_type = request.cookies.get("token_type")

    if access_token and token_type and token_type.lower() == "bearer":
        return access_token

    return None


async def get_user_id_from_cookie(request: Request) -> str:
    """
    Extract user_id from JWT token stored in cookies.

    This dependency:
    1. Extracts access_token and token_type from cookies
    2. Validates that token_type is 'Bearer'
    3. Verifies the token signature using HS256 or RS256 (auto-detected)
    4. Extracts user_id from the verified token payload

    Args:
        request: The incoming HTTP request.

    Returns:
        The user_id as a string.

    Raises:
        HTTPException: If cookies are missing, invalid, or token lacks user_id.

    Usage:
        ```python
        from fastapi import FastAPI, Depends
        from vibrant_auth_middleware import get_user_id_from_cookie

        app = FastAPI()

        @app.get("/protected")
        def protected_route(user_id: str = Depends(get_user_id_from_cookie)):
            return {"user_id": user_id}
        ```
    """
    token = _get_token_from_cookie(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: missing or invalid cookie credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return get_user_id_from_token(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_id(
    request: Request,
    token: Optional[str] = Depends(OAUTH2_SCHEME),
) -> str:
    """
    Extract user_id from verified JWT token in Authorization header or cookies.

    This dependency:
    1. First tries to extract the Bearer token from the Authorization header
    2. Falls back to cookies (access_token + token_type pair) if header is missing
    3. Verifies the token signature using HS256 or RS256 (auto-detected)
    4. Extracts user_id from the verified token payload

    Supports multiple user_id fields from ClinicUserPayload:
    - user_id (string or number)
    - userId (number, alternative field)
    - internal_user_id (fallback field)

    Args:
        request: The incoming HTTP request.
        token: Bearer token extracted from Authorization header (injected by Depends)

    Returns:
        The user_id as a string.

    Raises:
        HTTPException: If token is missing, invalid, or lacks user_id.

    Usage:
        ```python
        from fastapi import FastAPI, Depends
        from vibrant_auth_middleware import get_user_id

        app = FastAPI()

        @app.get("/protected")
        def protected_route(user_id: str = Depends(get_user_id)):
            return {"user_id": user_id}
        ```
    """
    # Try Authorization header first, then fall back to cookies
    if not token:
        token = _get_token_from_cookie(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return get_user_id_from_token(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user(
    request: Request,
    token: Optional[str] = Depends(OAUTH2_SCHEME),
) -> Dict[str, Any]:
    """
    Extract full payload from verified JWT token in Authorization header or cookies.

    This dependency:
    1. First tries to extract the Bearer token from the Authorization header
    2. Falls back to cookies (access_token + token_type pair) if header is missing
    3. Verifies the token signature using HS256 or RS256 (auto-detected)
    4. Returns the verified token payload

    Args:
        request: The incoming HTTP request.
        token: Bearer token extracted from Authorization header (injected by Depends)

    Returns:
        The verified token payload as a dictionary.

    Raises:
        HTTPException: If token is missing or invalid.

    Usage:
        ```python
        from fastapi import FastAPI, Depends
        from vibrant_auth_middleware import get_user

        app = FastAPI()

        @app.get("/protected")
        def protected_route(user: dict = Depends(get_user)):
            return {"user": user}
        ```
    """
    # Try Authorization header first, then fall back to cookies
    if not token:
        token = _get_token_from_cookie(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return get_token_payload(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
