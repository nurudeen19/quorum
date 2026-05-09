"""Shared application exceptions."""


class StartupConfigurationError(RuntimeError):
    """Raised when startup cannot complete (configuration or critical dependency)."""
