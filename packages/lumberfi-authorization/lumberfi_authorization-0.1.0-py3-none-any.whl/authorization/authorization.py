import re
from typing import Tuple, Optional, Protocol, Mapping
from .descope_client import validate_session
from .exceptions import NotAuthorized, PermissionDenied, SDKError
import logging
AUTHORIZATION_HEADER_NAME = "Authorization"
BEARER_RE = re.compile(r"^[Bb]earer (.+)$")


class RequestLike(Protocol):
    headers: Mapping[str, str]


class TokenValidator:
    """Token validator that only authorizes tokens by validating with Descope.

    Methods return the validated session dict (from Descope) and the raw token.
    """

    def parse_bearer(self, request: RequestLike) -> Optional[str]:
        headers = getattr(request, "headers", {}) or {}
        if isinstance(headers, dict):
            auth_header_value = headers.get(AUTHORIZATION_HEADER_NAME) or headers.get(AUTHORIZATION_HEADER_NAME.lower())
        else:
            try:
                auth_header_value = headers.get(AUTHORIZATION_HEADER_NAME)
            except Exception:
                auth_header_value = None
        if not auth_header_value:
            return None
        match = BEARER_RE.match(auth_header_value)
        if not match:
            return None
        return match.group(1)

    def validate_optional(self, request: RequestLike) -> Tuple[Optional[dict], Optional[str]]:
        token = self.parse_bearer(request)
        if not token:
            return (None, None)
        try:
            session = validate_session(token)
            return (session, token)
        except SDKError:
            # For optional validation, silently return None on any SDK error
            return (None, None)
        except Exception as e:
            # Catch any unexpected errors and return None
            logging.debug(f"Unexpected error during optional token validation: {e}")
            return (None, None)

    def validate_required(self, request: RequestLike) -> Tuple[dict, str]:
        token = self.parse_bearer(request)
        if not token:
            raise NotAuthorized(f'Request does not contain "{AUTHORIZATION_HEADER_NAME}" header')
        try:
            logging.debug("Validating token with Descope")
            session = validate_session(token)
            return (session, token)
        except SDKError:
            # Re-raise SDK errors as-is (ClientNotConfigured, etc.)
            raise
        except Exception as error:
            # Wrap unexpected errors in PermissionDenied for invalid tokens
            raise PermissionDenied(f"Token validation failed: {str(error)}")


# Convenience functions
def validate_token_optional(request: RequestLike) -> Tuple[Optional[dict], Optional[str]]:
    return TokenValidator().validate_optional(request)


def validate_token_required(request: RequestLike) -> Tuple[dict, str]:
    return TokenValidator().validate_required(request)
