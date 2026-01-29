"""
Exception classes for SunEnergyXT API.
"""


class SunEnergyXTError(Exception):
    """Base exception for all SunEnergyXT errors."""
    pass


class SunEnergyXTConnectionError(SunEnergyXTError):
    """Raised when connection to device fails."""
    pass


class SunEnergyXTTimeoutError(SunEnergyXTError):
    """Raised when operation times out."""
    pass


class SunEnergyXTCommandError(SunEnergyXTError):
    """Raised when a command fails to execute."""

    def __init__(self, message: str, error_code: int = None):
        super().__init__(message)
        self.error_code = error_code


class SunEnergyXTValidationError(SunEnergyXTError):
    """Raised when parameter validation fails."""
    pass


class SunEnergyXTDiscoveryError(SunEnergyXTError):
    """Raised when device discovery fails."""
    pass
