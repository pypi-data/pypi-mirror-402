"""
Authentication and authorization utilities for Agentic Fabric SDK.
"""

from .oauth import (
    api_key_required,
    mtls_required,
    no_auth_required,
    oauth_required,
    ScopeValidator,
    TokenValidator,
)
from .token_cache import TokenManager, VaultClient
from .applications import (
    get_application_client,
    exchange_okta_for_af_token,
    load_application_config,
    list_applications,
    ApplicationNotFoundError,
    AuthenticationError,
)
from .credentials import (
    load_stored_credentials,
    exchange_keycloak_for_af_token,
    get_valid_token_sync,
    StoredCredentials,
    AFTokenResponse,
)

__all__ = [
    "oauth_required",
    "api_key_required",
    "mtls_required",
    "no_auth_required",
    "ScopeValidator",
    "TokenValidator",
    "TokenManager",
    "VaultClient",
    # Application helpers (read-only)
    "get_application_client",
    "exchange_okta_for_af_token",
    "load_application_config",
    "list_applications",
    "ApplicationNotFoundError",
    "AuthenticationError",
    # Non-IdP authentication
    "load_stored_credentials",
    "exchange_keycloak_for_af_token",
    "get_valid_token_sync",
    "StoredCredentials",
    "AFTokenResponse",
]
