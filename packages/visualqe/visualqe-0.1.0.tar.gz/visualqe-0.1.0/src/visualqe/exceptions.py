"""Custom exceptions for VisualQE."""


class VisualQEError(Exception):
    """Base exception for VisualQE."""

    pass


class CaptureError(VisualQEError):
    """Screenshot capture failed."""

    pass


class BaselineNotFoundError(VisualQEError):
    """Baseline image not found."""

    pass


class AnalysisError(VisualQEError):
    """VLM analysis failed."""

    pass


class ConfigurationError(VisualQEError):
    """Invalid configuration."""

    pass


class DiffError(VisualQEError):
    """Image comparison failed."""

    pass


class RateLimitError(CaptureError):
    """API rate limit exceeded."""

    pass


class AuthenticationError(VisualQEError):
    """API authentication failed."""

    pass
