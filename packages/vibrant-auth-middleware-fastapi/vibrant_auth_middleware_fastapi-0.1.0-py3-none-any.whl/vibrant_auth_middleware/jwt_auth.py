"""
JWT Authentication Service.

Provides JWT token verification supporting both HS256 (symmetric) and RS256 (asymmetric) algorithms.
Automatically detects the algorithm from the JWT header and uses the appropriate verification method:
- HS256: Uses secret from Azure Key Vault or environment variable
- RS256: Uses public key from Azure App Configuration or environment variable
"""

import logging
import os
import time
from typing import Any, Dict, Optional

from azure.appconfiguration import AzureAppConfigurationClient
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential, WorkloadIdentityCredential
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from .config import jwt_config

logger = logging.getLogger(__name__)

# Cache for keys and configuration
_jwt_secret_cache: Optional[str] = None
_jwt_public_key_cache: Optional[str] = None
_cache_timestamp: float = 0
CACHE_TTL = 300  # 5 minutes cache


def _get_azure_credential():
    """
    Get the appropriate Azure credential based on the environment.

    Returns:
        WorkloadIdentityCredential for production (Kubernetes/AKS),
        DefaultAzureCredential for other environments (staging, dev).

    Environment Variables:
        APP_ENV: "production" uses WorkloadIdentityCredential,
                 "staging" or "dev" uses DefaultAzureCredential (default: "dev")
    """
    app_env = os.getenv("APP_ENV", "dev").lower()

    if app_env == "production":
        logger.debug(
            f"Using WorkloadIdentityCredential for Azure authentication (APP_ENV={app_env})"
        )
        return WorkloadIdentityCredential()
    else:
        logger.debug(
            f"Using DefaultAzureCredential for Azure authentication (APP_ENV={app_env})"
        )
        return DefaultAzureCredential()


def _get_azure_app_config_client() -> Optional[AzureAppConfigurationClient]:
    """Create and return an Azure App Configuration client."""
    connection_string = jwt_config.azure_app_config_connection_string
    endpoint = jwt_config.azure_app_config_endpoint

    if connection_string:
        return AzureAppConfigurationClient.from_connection_string(connection_string)
    elif endpoint:
        credential = _get_azure_credential()
        return AzureAppConfigurationClient(base_url=endpoint, credential=credential)

    return None


def _get_hs256_secret() -> str:
    """
    Get HS256 secret key from Azure Key Vault or environment.

    Returns:
        The secret key for HS256 verification.

    Raises:
        HTTPException: If secret cannot be retrieved.
    """
    global _jwt_secret_cache, _cache_timestamp

    current_time = time.time()
    # Return cached secret if still valid
    if _jwt_secret_cache and (current_time - _cache_timestamp) < CACHE_TTL:
        logger.debug("Using cached HS256 secret")
        return _jwt_secret_cache

    # Try environment variable first
    if jwt_config.jwt_secret_key:
        logger.debug("Using HS256 secret from environment variable")
        _jwt_secret_cache = jwt_config.jwt_secret_key
        _cache_timestamp = current_time
        return _jwt_secret_cache

    # Try Azure Key Vault
    if jwt_config.azure_key_vault_uri:
        try:
            from azure.keyvault.secrets import SecretClient

            credential = _get_azure_credential()
            client = SecretClient(
                vault_url=jwt_config.azure_key_vault_uri, credential=credential
            )

            logger.debug(
                f"Fetching HS256 secret from Azure Key Vault: {jwt_config.azure_key_vault_secret_name}"
            )
            secret = client.get_secret(jwt_config.azure_key_vault_secret_name)
            _jwt_secret_cache = secret.value
            _cache_timestamp = current_time
            logger.info("Successfully retrieved HS256 secret from Azure Key Vault")
            return _jwt_secret_cache

        except Exception as e:
            logger.error(f"Failed to retrieve secret from Azure Key Vault: {e}")

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="JWT secret not configured. Please set JWT_SECRET_KEY or configure Azure Key Vault.",
    )


def _get_rs256_public_key() -> str:
    """
    Get RS256 public key from Azure App Configuration or environment.

    Returns:
        The public key for RS256 verification.

    Raises:
        HTTPException: If public key cannot be retrieved.
    """
    global _jwt_public_key_cache, _cache_timestamp

    current_time = time.time()
    # Return cached public key if still valid
    if _jwt_public_key_cache and (current_time - _cache_timestamp) < CACHE_TTL:
        logger.debug("Using cached RS256 public key")
        return _jwt_public_key_cache

    # Try environment variable first
    if jwt_config.jwt_public_key:
        logger.debug("Using RS256 public key from environment variable")
        _jwt_public_key_cache = jwt_config.jwt_public_key
        _cache_timestamp = current_time
        return _jwt_public_key_cache

    # Try Azure App Configuration
    client = _get_azure_app_config_client()
    if client:
        try:
            logger.debug(
                f"Fetching RS256 public key from Azure App Configuration: {jwt_config.azure_app_config_jwt_key}"
            )
            item = client.get_configuration_setting(
                key=jwt_config.azure_app_config_jwt_key
            )

            # Handle Key Vault references
            if (
                item.content_type
                == "application/vnd.microsoft.appconfig.keyvaultref+json;charset=utf-8"
            ):
                logger.warning(
                    f"Key Vault reference found for {item.key}. Attempting to resolve..."
                )
                if item.value:
                    _jwt_public_key_cache = item.value
                    _cache_timestamp = current_time
                    logger.info(
                        "Successfully retrieved RS256 public key from Key Vault reference"
                    )
                    return _jwt_public_key_cache
            elif item.value:
                _jwt_public_key_cache = item.value
                _cache_timestamp = current_time
                logger.info(
                    "Successfully retrieved RS256 public key from Azure App Configuration"
                )
                return _jwt_public_key_cache

        except ResourceNotFoundError:
            logger.debug(
                f"Public key not found in Azure App Configuration: {jwt_config.azure_app_config_jwt_key}"
            )
        except Exception as e:
            logger.error(
                f"Failed to retrieve public key from Azure App Configuration: {e}"
            )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="JWT public key not configured. Please set JWT_PUBLIC_KEY or configure Azure App Configuration.",
    )


def _decode_key_with_pem_header(key: str, key_type: str) -> str:
    """
    Ensure the key has the proper PEM header/footer.

    Args:
        key: The key string.
        key_type: Either 'PUBLIC' or 'PRIVATE'.

    Returns:
        The key with proper PEM formatting.
    """
    key = key.strip()
    prefix = "-----BEGIN PUBLIC KEY-----"
    suffix = "-----END PUBLIC KEY-----"

    if key_type == "PUBLIC":
        if not key.startswith("-----BEGIN"):
            if "\\n" in key:
                key = key.replace("\\n", "\n")
            return f"{prefix}\n{key}\n{suffix}"
        return key

    return key


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify a JWT token and return its payload.

    Automatically detects the algorithm (HS256 or RS256) from the token header
    and uses the appropriate verification method.

    Args:
        token: The JWT token string (without 'Bearer ' prefix).

    Returns:
        The decoded token payload as a dictionary.

    Raises:
        HTTPException: If token is invalid, expired, or verification fails.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
        )

    try:
        # Get the header to determine the algorithm
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg", "HS256")

        logger.debug(f"Verifying JWT token with algorithm: {algorithm}")

        # Prepare decode options
        decode_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "leeway": jwt_config.jwt_leeway,
        }

        # Verify based on algorithm
        if algorithm == "HS256":
            secret = _get_hs256_secret()
            payload = jwt.decode(
                token,
                secret,
                algorithms=[algorithm],
                options=decode_options,
                audience=jwt_config.jwt_audience,
                issuer=jwt_config.jwt_issuer,
            )
        elif algorithm == "RS256":
            public_key = _get_rs256_public_key()
            public_key = _decode_key_with_pem_header(public_key, "PUBLIC")
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[algorithm],
                options=decode_options,
                audience=jwt_config.jwt_audience,
                issuer=jwt_config.jwt_issuer,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported algorithm: {algorithm}",
            )

        logger.debug("JWT token verified successfully")
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed",
        )


def get_user_id_from_token(token: str) -> str:
    """
    Extract user_id from a verified JWT token.

    Checks multiple possible fields in the token payload:
    - user_id (string or number)
    - userId (number, alternative field)
    - internal_user_id (fallback field)

    Args:
        token: The JWT token string (without 'Bearer ' prefix).

    Returns:
        The user_id as a string.

    Raises:
        HTTPException: If token is invalid or user_id cannot be extracted.
    """
    payload = verify_jwt_token(token)

    # Try different fields for user_id based on ClinicUserPayload interface
    user_id = (
        payload.get("user_id")
        or payload.get("userId")
        or payload.get("internal_user_id")
    )

    if not user_id:
        logger.warning("Token verified but no user_id found in payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain user_id",
        )

    return str(user_id)


def get_token_payload(token: str) -> Dict[str, Any]:
    """
    Get the full verified token payload.

    Args:
        token: The JWT token string (without 'Bearer ' prefix).

    Returns:
        The complete token payload as a dictionary.

    Raises:
        HTTPException: If token is invalid.
    """
    return verify_jwt_token(token)
