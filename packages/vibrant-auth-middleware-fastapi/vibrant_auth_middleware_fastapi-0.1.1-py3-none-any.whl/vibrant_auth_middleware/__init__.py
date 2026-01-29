"""
Vibrant Auth Middleware for FastAPI.

A library for JWT authentication with Azure integration, supporting both
HS256 (symmetric) and RS256 (asymmetric) algorithms.

Usage:
    ```python
    from fastapi import FastAPI, Depends
    from vibrant_auth_middleware import get_user_id

    app = FastAPI()

    @app.get("/protected")
    def protected_route(user_id: str = Depends(get_user_id)):
        return {"user_id": user_id}
    ```

Environment Variables:
    JWT_SECRET_KEY: HS256 secret key (or use Azure Key Vault)
    JWT_PUBLIC_KEY: RS256 public key (or use Azure App Configuration)
    AZURE_KEY_VAULT_URI: Azure Key Vault URI for HS256 secret
    AZURE_KEY_VAULT_JWT_SECRET: Secret name in Key Vault (default: "jwt-secret-key")
    AZURE_APP_CONFIG_ENDPOINT: Azure App Configuration endpoint for RS256 public key
    AZURE_APP_CONFIG_CONNECTION_STRING: App Configuration connection string
    AZURE_APP_CONFIG_JWT_KEY: Key name in App Configuration (default: "jwt-public-key")
    JWT_AUDIENCE: Optional audience claim for token verification
    JWT_ISSUER: Optional issuer claim for token verification
    JWT_LEEWAY: Leeway in seconds for time validation (default: 0)
    APP_ENV: "production" for WorkloadIdentityCredential, else DefaultAzureCredential
"""

from .config import JWTConfig, jwt_config
from .dependencies import (
    OAUTH2_SCHEME,
    OAuth2PasswordToken,
    get_user,
    get_user_id,
    get_user_id_from_cookie,
)
from .jwt_auth import (
    get_token_payload,
    get_user_id_from_token,
    verify_jwt_token,
)

__all__ = [
    # Configuration
    "JWTConfig",
    "jwt_config",
    # FastAPI dependencies
    "get_user",
    "get_user_id",
    "get_user_id_from_cookie",
    "OAUTH2_SCHEME",
    "OAuth2PasswordToken",
    # Core functions
    "verify_jwt_token",
    "get_user_id_from_token",
    "get_token_payload",
]

__version__ = "0.1.0"
