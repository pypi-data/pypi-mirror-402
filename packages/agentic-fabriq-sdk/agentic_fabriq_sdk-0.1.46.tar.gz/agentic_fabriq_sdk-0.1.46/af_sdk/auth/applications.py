"""
Authentication helpers for Agentic Fabric SDK.

Provides utilities for loading application credentials and creating
authenticated clients.
"""

from pathlib import Path
import json
import httpx
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from ..mcp_client import MCPClient

logger = logging.getLogger(__name__)


class ApplicationNotFoundError(Exception):
    """Raised when an application configuration is not found."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


async def get_application_client(
    app_id: str,
    config_dir: Optional[Path] = None,
    gateway_url: Optional[str] = None,
) -> "MCPClient":
    """
    Get authenticated FabriqClient for an application.
    
    Automatically loads credentials from ~/.af/applications/{app_id}.json
    and exchanges them for a JWT token.
    
    Args:
        app_id: Application identifier (e.g., "my-slack-bot")
        config_dir: Optional custom config directory (default: ~/.af)
        gateway_url: Optional gateway URL override (default: from app config)
    
    Returns:
        Authenticated FabriqClient instance
    
    Raises:
        ApplicationNotFoundError: If application config doesn't exist
        AuthenticationError: If authentication fails
    
    Example:
        >>> client = await get_application_client("my-slack-bot")
        >>> result = await client.invoke_connection("my-slack", method="post_message", parameters={...})
    """
    # 1. Load application config
    try:
        app_config = load_application_config(app_id, config_dir)
    except FileNotFoundError as e:
        raise ApplicationNotFoundError(
            f"Application '{app_id}' not found. "
            f"Register it first with: afctl applications create --app-id {app_id} ..."
        ) from e
    
    # Use provided gateway_url or fall back to config
    base_url = gateway_url or app_config.get("gateway_url", "https://dashboard.agenticfabriq.com")
    
    # 2. Exchange credentials for JWT token
    # Use keycloak_client_id (full namespaced ID) if available, fallback to app_id
    effective_app_id = app_config.get("keycloak_client_id") or app_config["app_id"]
    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f"{base_url}/api/v1/applications/token",
                json={
                    "app_id": effective_app_id,
                    "secret_key": app_config["secret_key"]
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", response.text)
                except:
                    pass
                
                raise AuthenticationError(
                    f"Failed to authenticate application '{app_id}': {error_detail}"
                )
            
            token_data = response.json()
    except httpx.HTTPError as e:
        raise AuthenticationError(
            f"Network error while authenticating application '{app_id}': {e}"
        ) from e
    
    # 3. Create MCPClient - caller should use as context manager
    from ..mcp_client import MCPClient
    
    client = MCPClient(
        method="cli",
        app_id=effective_app_id,
        app_secret=app_config["secret_key"],
        gateway_url=base_url,
        mcp_url=f"{base_url}/mcp",
    )
    
    logger.info(
        f"Created MCPClient for application '{app_id}' "
        f"(user_id={token_data.get('user_id')}, tenant_id={token_data.get('tenant_id')})"
    )
    
    return client


# ============================================================================
# Internal functions used by CLI (not exported in public SDK API)
# ============================================================================

async def register_application(
    app_id: str,
    provider_scopes: Dict[str, List[str]],
    auth_token: str,
    gateway_url: str = "https://dashboard.agenticfabriq.com",
    display_name: Optional[str] = None,
) -> Tuple[str, Dict]:
    """
    Register a new application (Step 1 of 2).
    Internal function used by CLI.
    """
    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f"{gateway_url}/api/v1/applications/register",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "app_id": app_id,
                    "provider_scopes": provider_scopes,
                    "display_name": display_name,
                },
                timeout=30.0
            )
            
            if response.status_code != 201:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", response.text)
                except:
                    pass
                
                raise AuthenticationError(
                    f"Failed to register application '{app_id}': {error_detail}"
                )
            
            data = response.json()
            logger.info(f"Registered application '{app_id}', activation token expires: {data.get('expires_at')}")
            return data["activation_token"], data
            
    except httpx.HTTPError as e:
        raise AuthenticationError(
            f"Network error while registering application '{app_id}': {e}"
        ) from e


async def activate_application(
    activation_token: str,
    auth_token: str,
    gateway_url: str = "https://dashboard.agenticfabriq.com",
    config_dir: Optional[Path] = None,
    auto_save: bool = True,
    idp_client_id: Optional[str] = None,
    idp_client_secret: Optional[str] = None,
) -> Dict:
    """
    Activate an application (Step 2 of 2).
    Internal function used by CLI.
    """
    try:
        # Build request payload
        payload = {"activation_token": activation_token}
        if idp_client_id:
            payload["idp_client_id"] = idp_client_id
        if idp_client_secret:
            payload["idp_client_secret"] = idp_client_secret
        
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f"{gateway_url}/api/v1/applications/activate",
                headers={"Authorization": f"Bearer {auth_token}"},
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 404:
                raise AuthenticationError(
                    "Invalid or expired activation token. "
                    "The token may have expired (valid for 1 hour) or was already used."
                )
            elif response.status_code == 403:
                raise AuthenticationError("This activation token does not belong to you")
            elif response.status_code != 201:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", response.text)
                except:
                    pass
                
                raise AuthenticationError(f"Failed to activate application: {error_detail}")
            
            data = response.json()
            
            # Optionally save credentials locally
            if auto_save:
                app_config = {
                    "app_id": data["app_id"],
                    "secret_key": data["secret_key"],
                    "keycloak_client_id": data.get("keycloak_client_id"),
                    "user_id": data["user_id"],
                    "tenant_id": data["tenant_id"],
                    "organization_id": data.get("organization_id"),
                    "tool_connections": data.get("tool_connections", {}),
                    "created_at": data["created_at"],
                    "gateway_url": gateway_url
                }
                
                app_file = save_application_config(data["app_id"], app_config, config_dir)
                logger.info(f"Saved application credentials to {app_file}")
                data["_config_file"] = str(app_file)
            
            logger.info(f"Activated application '{data['app_id']}'")
            return data
            
    except httpx.HTTPError as e:
        raise AuthenticationError(
            f"Network error while activating application: {e}"
        ) from e


async def exchange_okta_for_af_token(
    okta_token: str,
    app_id: str,
    app_secret: str,
    keycloak_url: str = "https://auth.agenticfabriq.com",
    org_url: Optional[str] = None,
    gateway_url: str = "https://dashboard.agenticfabriq.com",
) -> str:
    """
    Exchange Okta SSO token for AF JWT token.
    """
    logger.debug(f"Exchanging Okta token via gateway for app: {app_id}, org_url: {org_url or 'auto-detect'}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            logger.info(f"Calling gateway okta-token-exchange for app: {app_id}")
            
            # Build request payload
            request_body = {
                "okta_token": okta_token,
                "app_id": app_id,
                "app_secret": app_secret,
            }
            # Only include org_url if explicitly provided
            if org_url:
                request_body["org_url"] = org_url
            
            response = await http.post(
                f"{gateway_url}/api/v1/auth/okta-token-exchange",
                json=request_body,
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Gateway okta-token-exchange failed: {error_detail}")
                raise AuthenticationError(
                    f"Okta token exchange failed (status {response.status_code}): {error_detail}"
                )
            
            result = response.json()
            af_token = result.get("access_token")
            
            if not af_token:
                raise AuthenticationError("Gateway response missing access_token")
            
            logger.info("Successfully obtained AF token via gateway okta-token-exchange")
            return af_token
            
    except httpx.RequestError as e:
        logger.error(f"Network error during token exchange: {e}")
        raise AuthenticationError(f"Token exchange network error: {str(e)}") from e
    except KeyError as e:
        logger.error(f"Invalid token response format: {e}")
        raise AuthenticationError(f"Invalid token response format: {str(e)}") from e


def load_application_config(
    app_id: str,
    config_dir: Optional[Path] = None
) -> Dict:
    """
    Load application config from disk.
    """
    if config_dir is None:
        config_dir = Path.home() / ".af"
    
    app_file = config_dir / "applications" / f"{app_id}.json"
    
    if not app_file.exists():
        raise FileNotFoundError(
            f"Application '{app_id}' not found at {app_file}. "
            f"Register it with: afctl applications create --app-id {app_id}"
        )
    
    with open(app_file, "r") as f:
        return json.load(f)


def save_application_config(
    app_id: str,
    config: Dict,
    config_dir: Optional[Path] = None
) -> Path:
    """
    Save application config to disk.
    Internal function used by CLI.
    """
    if config_dir is None:
        config_dir = Path.home() / ".af"
    
    # Create applications directory if it doesn't exist
    app_dir = config_dir / "applications"
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Write config file
    app_file = app_dir / f"{app_id}.json"
    with open(app_file, "w") as f:
        json.dump(config, f, indent=2)
    
    # Secure the file (user read/write only)
    app_file.chmod(0o600)
    
    logger.info(f"Saved application config to {app_file}")
    
    return app_file


def list_applications(
    config_dir: Optional[Path] = None
) -> List[Dict]:
    """
    List all registered applications.
    """
    if config_dir is None:
        config_dir = Path.home() / ".af"
    
    app_dir = config_dir / "applications"
    
    if not app_dir.exists():
        return []
    
    apps = []
    for app_file in sorted(app_dir.glob("*.json")):
        try:
            with open(app_file, "r") as f:
                app_config = json.load(f)
                apps.append(app_config)
        except Exception as e:
            logger.warning(f"Failed to load application config from {app_file}: {e}")
    
    return apps


def delete_application_config(
    app_id: str,
    config_dir: Optional[Path] = None
) -> bool:
    """
    Delete application config from disk.
    Internal function used by CLI.
    """
    if config_dir is None:
        config_dir = Path.home() / ".af"
    
    app_file = config_dir / "applications" / f"{app_id}.json"
    
    if not app_file.exists():
        return False
    
    app_file.unlink()
    logger.info(f"Deleted application config: {app_file}")
    
    return True
