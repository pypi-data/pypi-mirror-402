class CubeSDKError(Exception):
    """Base SDK exception."""

class AuthenticationError(CubeSDKError):
    """Invalid or expired service token."""

class AuthorizationError(CubeSDKError):
    """Token does not have required permission or env access."""

class SecretNotFoundError(CubeSDKError):
    """Secret does not exist in the given environment."""

class APIError(CubeSDKError):
    """Unexpected API error."""
