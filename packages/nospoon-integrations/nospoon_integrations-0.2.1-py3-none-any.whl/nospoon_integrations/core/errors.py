"""Custom error classes for the NoSpoon Integrations SDK."""

from typing import Optional


class IntegrationError(Exception):
    """Base error class for all integration errors."""

    def __init__(self, message: str, provider: Optional[str] = None):
        self.provider = provider
        formatted_message = f"[{provider}] {message}" if provider else message
        super().__init__(formatted_message)


class OAuthError(IntegrationError):
    """OAuth-related error (authorization, token exchange, etc.)."""

    def __init__(self, provider: str, message: str, original_error: Optional[str] = None):
        self.original_error = original_error
        super().__init__(message, provider)


class TokenNotFoundError(IntegrationError):
    """No tokens found for user."""

    def __init__(self, provider: str, user_id: Optional[str] = None):
        self.user_id = user_id
        message = f"No tokens found for user {user_id}" if user_id else "No tokens found"
        super().__init__(message, provider)


class TokenExpiredError(IntegrationError):
    """Token expired and cannot be refreshed."""

    def __init__(self, provider: str, user_id: Optional[str] = None, reason: str = ""):
        self.user_id = user_id
        self.reason = reason
        if user_id:
            message = f"Token expired for user {user_id}"
        else:
            message = f"Token expired: {reason}" if reason else "Token expired"
        super().__init__(message, provider)


class TokenRefreshError(IntegrationError):
    """Token refresh failed."""

    def __init__(self, provider: str, message: str):
        super().__init__(message, provider)


class ProviderAPIError(IntegrationError):
    """Error from provider API."""

    def __init__(
        self,
        provider: str,
        status_code: int,
        message: str,
        response_body: Optional[str] = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"API error ({status_code}): {message}", provider)


class ConfigurationError(IntegrationError):
    """Configuration error (missing credentials, invalid config, etc.)."""

    pass


class InsufficientScopeError(ProviderAPIError):
    """
    Insufficient OAuth scopes for the requested operation.

    This error is thrown when an API call fails due to missing permissions.
    The user needs to reconnect their account with the required scopes.
    """

    def __init__(
        self,
        provider: str,
        required_scopes: list[str],
        granted_scopes: Optional[list[str]] = None,
        response_body: Optional[str] = None,
    ):
        self.required_scopes = required_scopes
        self.granted_scopes = granted_scopes
        scope_list = ", ".join(required_scopes)
        self.hint = (
            f"User needs to disconnect and reconnect their {provider} account "
            f"to grant the required scopes: {scope_list}"
        )
        super().__init__(
            provider,
            403,
            f"Insufficient scopes. Required: {scope_list}",
            response_body,
        )

    @classmethod
    def from_response(
        cls,
        provider: str,
        status_code: int,
        www_authenticate: Optional[str],
        required_scopes: list[str],
        response_body: Optional[str] = None,
    ) -> Optional["InsufficientScopeError"]:
        """
        Create an InsufficientScopeError from an API response.

        Args:
            provider: Provider name
            status_code: HTTP status code
            www_authenticate: WWW-Authenticate header value
            required_scopes: Scopes required for the operation
            response_body: Response body (optional)

        Returns:
            InsufficientScopeError if the response indicates insufficient scopes, None otherwise
        """
        if status_code != 403:
            return None

        # Check for insufficient_scope in www-authenticate header
        if www_authenticate and "insufficient_scope" in www_authenticate:
            return cls(provider, required_scopes, None, response_body)

        return None
