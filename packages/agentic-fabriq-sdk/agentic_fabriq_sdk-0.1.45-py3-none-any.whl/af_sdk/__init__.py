"""
Agentic Fabric SDK

Official Python SDK for building connectors and interacting with Agentic Fabric.
"""

from .auth.oauth import oauth_required
from .connectors.base import AgentConnector, ConnectorContext, ToolConnector
from .exceptions import (
    AFError,
    AuthenticationError,
    AuthorizationError,
    ConnectorError,
    NotFoundError,
    ValidationError,
    MCPError,
    MCPConnectionError,
)
from .models.types import (
    ToolInvokeRequest,
    ToolInvokeResult,
)
from .mcp_client import MCPClient
from .auth import (
    get_application_client,
    exchange_okta_for_af_token,
    load_application_config,
    list_applications,
    ApplicationNotFoundError,
    # Non-IdP authentication
    load_stored_credentials,
    exchange_keycloak_for_af_token,
    get_valid_token_sync,
    StoredCredentials,
    AFTokenResponse,
)

__version__ = "1.0.0"

__all__ = [
    "oauth_required",
    "ToolConnector",
    "AgentConnector",
    "ConnectorContext",
    # Exceptions
    "AFError",
    "AuthenticationError",
    "AuthorizationError",
    "ConnectorError",
    "NotFoundError",
    "ValidationError",
    "MCPError",
    "MCPConnectionError",
    # Models
    "ToolInvokeRequest",
    "ToolInvokeResult",
    # Clients
    "MCPClient",
    # Application auth helpers (read-only)
    "get_application_client",
    "exchange_okta_for_af_token",
    "load_application_config",
    "list_applications",
    "ApplicationNotFoundError",
    # Non-IdP authentication
    "load_stored_credentials",
    "exchange_keycloak_for_af_token",
    "get_valid_token_sync",
    "StoredCredentials",
    "AFTokenResponse",
]
