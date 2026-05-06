"""Domain-level errors raised by services (mapped to HTTP in API layer)."""


class ServiceError(Exception):
    """Base class for service-layer failures."""


class UserConflictError(ServiceError):
    """Email or username already registered."""
