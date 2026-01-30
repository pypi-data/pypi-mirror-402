"""Custom exceptions for the lumberfi-authorization SDK.

These exceptions are framework-agnostic and can be used in any Python environment
(Django, Flask, FastAPI, etc.). All exceptions inherit from SDKError for easy
exception handling.

Example:
    try:
        session, token = validate_token_required(request)
    except NotAuthenticated:
        # Handle missing or malformed token
        pass
    except PermissionDenied:
        # Handle invalid or expired token
        pass
    except SDKError:
        # Catch any SDK-related error
        pass
"""

from typing import List, Optional


class SDKError(Exception):
    """Base exception for all SDK-related errors.

    All exceptions in this module inherit from this class, making it easy to
    catch any SDK-related error with a single except clause.

    Attributes:
        message: Human-readable error message.
        error_code: Optional error code for programmatic error handling.

    Example:
        try:
            # SDK operations
            pass
        except SDKError as e:
            # Handle any SDK error
            print(f"SDK Error: {e}")
    """

    def __init__(self, message: str, error_code: Optional[str] = None):
        """Initialize SDKError.

        Args:
            message: Human-readable error message.
            error_code: Optional error code for programmatic handling.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ClientNotConfigured(SDKError):
    """Raised when the Descope client has not been initialized.

    This exception is raised when attempting to validate a token before
    initializing the SDK with init_client().

    Example:
        # Without calling init_client() first
        try:
            validate_session("token")
        except ClientNotConfigured:
            init_client(project_id="...", management_key="...")
    """

    def __init__(self, message: str = "Descope client not configured. Call init_client(...) to configure the SDK"):
        """Initialize ClientNotConfigured.

        Args:
            message: Custom error message. Defaults to a helpful message.
        """
        super().__init__(message, error_code="CLIENT_NOT_CONFIGURED")


class TokenMissing(SDKError):
    """Raised when a required token is missing from the request.

    This exception indicates that the Authorization header is completely
    missing from the request, or the header format is incorrect.

    Example:
        try:
            session, token = validate_token_required(request)
        except TokenMissing:
            # Request doesn't have Authorization header
            return {"error": "Authentication required"}, 401
    """

    def __init__(self, message: str = "Authorization token is missing from the request"):
        """Initialize TokenMissing.

        Args:
            message: Custom error message. Defaults to a helpful message.
        """
        super().__init__(message, error_code="TOKEN_MISSING")


class TokenInvalid(SDKError):
    """Raised when a token is invalid according to the authorization provider.

    This exception is raised when the token exists but is invalid, expired,
    or malformed according to Descope's validation.

    Attributes:
        token: The token that failed validation (if available).

    Example:
        try:
            session = validate_session("invalid_token")
        except TokenInvalid as e:
            # Token is invalid or expired
            print(f"Invalid token: {e}")
    """

    def __init__(self, message: str = "Token is invalid or expired", token: Optional[str] = None):
        """Initialize TokenInvalid.

        Args:
            message: Custom error message. Defaults to a helpful message.
            token: The invalid token (optional, for logging purposes).
        """
        super().__init__(message, error_code="TOKEN_INVALID")
        self.token = token


class PermissionDenied(SDKError):
    """Raised when an operation is not permitted due to authorization failure.

    This exception is raised when token validation fails, indicating that
    the user does not have permission to access the resource. This can
    happen due to invalid tokens, expired tokens, or insufficient permissions.

    Example:
        try:
            session, token = validate_token_required(request)
        except PermissionDenied:
            # Token validation failed
            return {"error": "Access denied"}, 403
    """

    def __init__(self, message: str = "Permission denied"):
        """Initialize PermissionDenied.

        Args:
            message: Custom error message. Defaults to a helpful message.
        """
        super().__init__(message, error_code="PERMISSION_DENIED")


class NotAuthorized(SDKError):
    """Raised when an authentication/authorization token is missing or malformed.

    This exception is raised when the Authorization header is missing,
    malformed, or doesn't contain a valid Bearer token format.

    Example:
        try:
            session, token = validate_token_required(request)
        except NotAuthorized:
            # Missing or malformed Authorization header
            return {"error": "Authentication required"}, 401
    """

    def __init__(self, message: str = "Authentication required"):
        """Initialize NotAuthorized.

        Args:
            message: Custom error message. Defaults to a helpful message.
        """
        super().__init__(message, error_code="NOT_AUTHENTICATED")


class ValidationError(SDKError):
    """Raised when token validation fails due to an unexpected error.

    This exception is raised when token validation encounters an unexpected
    error during the validation process (e.g., network issues, service
    unavailability).

    Example:
        try:
            session = validate_session(token)
        except ValidationError as e:
            # Unexpected error during validation
            logger.error(f"Validation error: {e}")
    """

    def __init__(self, message: str = "Token validation failed"):
        """Initialize ValidationError.

        Args:
            message: Custom error message. Defaults to a helpful message.
        """
        super().__init__(message, error_code="VALIDATION_ERROR")


__all__: List[str] = [
    "SDKError",
    "ClientNotConfigured",
    "TokenMissing",
    "TokenInvalid",
    "PermissionDenied",
    "NotAuthorized",
    "ValidationError",
]
