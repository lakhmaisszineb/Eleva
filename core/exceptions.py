"""
Custom exceptions for Eleva.

Using specific exceptions makes error handling clearer and more maintainable.
"""


class ElevaError(Exception):
    """Base exception for all Eleva-related errors."""
    pass


class DataNotFoundError(ElevaError):
    """Raised when required company data cannot be found."""
    pass


class InvalidCompanyError(ElevaError):
    """Raised when the provided company_id is invalid or not found."""
    pass


class ObservationError(ElevaError):
    """Raised when the observation step fails."""
    pass


class ReasoningError(ElevaError):
    """Raised when the reasoning / decision step fails."""
    pass