"""
Configuration for JWT authentication.

Loads settings from environment variables for JWT verification,
supporting both HS256 (symmetric) and RS256 (asymmetric) algorithms.
"""

import os
from typing import Optional


class JWTConfig:
    """JWT configuration settings loaded from environment variables."""

    def __init__(self):
        # HS256 Secret Key (from Azure Key Vault or env var)
        self.jwt_secret_key: Optional[str] = os.getenv("JWT_SECRET_KEY")
        self.azure_key_vault_secret_name: str = os.getenv(
            "AZURE_KEY_VAULT_JWT_SECRET", "jwt-secret-key"
        )
        self.azure_key_vault_uri: Optional[str] = os.getenv("AZURE_KEY_VAULT_URI")

        # RS256 Public Key (from Azure App Configuration or env var)
        self.jwt_public_key: Optional[str] = os.getenv("JWT_PUBLIC_KEY")
        self.azure_app_config_jwt_key: str = os.getenv(
            "AZURE_APP_CONFIG_JWT_KEY", "jwt-public-key"
        )
        self.azure_app_config_endpoint: Optional[str] = os.getenv(
            "AZURE_APP_CONFIG_ENDPOINT"
        )
        self.azure_app_config_connection_string: Optional[str] = os.getenv(
            "AZURE_APP_CONFIG_CONNECTION_STRING"
        )

        # JWT verification options
        self.jwt_audience: Optional[str] = os.getenv("JWT_AUDIENCE")
        self.jwt_issuer: Optional[str] = os.getenv("JWT_ISSUER")
        self.jwt_leeway: int = int(os.getenv("JWT_LEEWAY", "0"))


jwt_config = JWTConfig()
