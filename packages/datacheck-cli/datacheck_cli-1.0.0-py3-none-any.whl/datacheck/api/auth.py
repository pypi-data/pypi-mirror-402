"""Authentication and authorization for DataCheck API.

Provides API key-based authentication for securing API endpoints.
"""

import os
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API key header name
API_KEY_HEADER_NAME = "X-API-Key"

# API key security scheme
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def load_api_keys() -> set[str]:
    """Load valid API keys from environment.

    Returns:
        Set of valid API keys

    Environment Variables:
        DATACHECK_API_KEYS: Comma-separated list of valid API keys
        DATACHECK_API_KEY: Single API key (legacy support)
    """
    api_keys = set()

    # Load from DATACHECK_API_KEYS (comma-separated)
    keys_env = os.getenv("DATACHECK_API_KEYS", "")
    if keys_env:
        api_keys.update(key.strip() for key in keys_env.split(",") if key.strip())

    # Load from DATACHECK_API_KEY (single key, for backward compatibility)
    single_key = os.getenv("DATACHECK_API_KEY", "")
    if single_key:
        api_keys.add(single_key.strip())

    return api_keys


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    """Verify API key from request header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The valid API key

    Raises:
        HTTPException: If API key is missing or invalid (403 Forbidden)
    """
    # Load valid API keys
    valid_keys = load_api_keys()

    # If no API keys configured, deny access (fail-safe)
    if not valid_keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication not configured. Set DATACHECK_API_KEYS environment variable.",
        )

    # Check if API key provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API key. Provide X-API-Key header.",
        )

    # Validate API key
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key


# Type annotation for dependency injection
APIKeyDep = Annotated[str, Depends(verify_api_key)]


def is_authentication_enabled() -> bool:
    """Check if API authentication is enabled.

    Authentication is enabled if at least one API key is configured.

    Returns:
        True if authentication is enabled
    """
    return bool(load_api_keys())


def get_optional_api_key(
    api_key: str = Security(api_key_header),
) -> str | None:
    """Get API key if provided, but don't enforce.

    Used for endpoints that support both authenticated and unauthenticated access.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        API key if valid, None otherwise
    """
    if not api_key:
        return None

    valid_keys = load_api_keys()
    if api_key in valid_keys:
        return api_key

    return None


__all__ = [
    "verify_api_key",
    "APIKeyDep",
    "is_authentication_enabled",
    "get_optional_api_key",
]
