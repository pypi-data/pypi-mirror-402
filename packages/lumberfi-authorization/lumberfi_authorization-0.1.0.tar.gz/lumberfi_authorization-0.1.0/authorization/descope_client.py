import os
from typing import Optional, Any
from .exceptions import ClientNotConfigured, ValidationError

try:
    from descope import DescopeClient
except ImportError:
    DescopeClient = None

# internally stored client instance
_descope_client: Optional[Any] = None


def init_client(
    project_id: Optional[str] = None,
    management_key: Optional[str] = None,
    client: Optional[Any] = None
) -> Any:
    """Initialize the descope client for SDK use.

    You can either pass an existing `client` instance or provide `project_id` and
    `management_key` to construct one. If the Descope SDK isn't installed, attempting
    to build a client will raise ImportError.

    Args:
        project_id: Descope project ID. If not provided, will try to use
                   DESCOPE_PROJECT_ID environment variable.
        management_key: Descope management key. If not provided, will try to use
                       DESCOPE_MANAGEMENT_KEY environment variable.
        client: Optional existing DescopeClient instance to use instead of creating one.

    Returns:
        The configured DescopeClient instance.

    Raises:
        ImportError: If descope package is not available and client is not provided.
        RuntimeError: If project_id and management_key are not provided and client is None.
    """
    global _descope_client

    if client is not None:
        _descope_client = client
        return _descope_client

    if DescopeClient is None:
        raise ImportError("descope package is not available. Install it with: pip install descope")

    pid = project_id or os.getenv("DESCOPE_PROJECT_ID")
    mkey = management_key or os.getenv("DESCOPE_MANAGEMENT_KEY")

    if not pid or not mkey:
        raise RuntimeError(
            "project_id and management_key are required to create DescopeClient. "
            "Either pass them as arguments or set DESCOPE_PROJECT_ID and "
            "DESCOPE_MANAGEMENT_KEY environment variables."
        )

    _descope_client = DescopeClient(project_id=pid, management_key=mkey)
    return _descope_client


def validate_session(session_token: str) -> dict:
    """Validate a session token using the configured Descope client.

    Args:
        session_token: The session token to validate.

    Returns:
        The validated session dictionary from Descope.

    Raises:
        ClientNotConfigured: If the client is not configured. Call init_client(...) first.
        ValidationError: If token validation fails due to an unexpected error.
    """
    global _descope_client

    if _descope_client is None:
        # Try to auto-initialize from environment variables
        try:
            init_client()
        except (ImportError, RuntimeError):
            raise ClientNotConfigured(
                "Descope client not configured. Call init_client(...) to configure the SDK"
            )

    try:
        return _descope_client.validate_session(session_token=session_token)
    except Exception as e:
        # Wrap Descope client errors in ValidationError for better error handling
        if isinstance(e, ClientNotConfigured):
            raise
        raise ValidationError(f"Token validation failed: {str(e)}") from e