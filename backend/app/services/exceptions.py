"""Domain-level errors raised by services (mapped to HTTP in API layer)."""


class ServiceError(Exception):
    """Base class for service-layer failures."""


class UserConflictError(ServiceError):
    """Email or username already registered."""


class InvalidCredentialsError(ServiceError):
    """Wrong password, unknown user, or inactive account."""


class EmailNotVerifiedError(ServiceError):
    """Login blocked until the email address is verified."""


class InvalidTokenError(ServiceError):
    """Verification, reset, or refresh token invalid or expired."""
