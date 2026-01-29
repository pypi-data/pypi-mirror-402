"""Custom exceptions for flo_integrations package."""


class FloIntegrationError(Exception):
    """Base exception for all flo_integrations errors."""
    pass


class AuthenticationError(FloIntegrationError):
    """Raised when authentication fails."""
    pass


class APIError(FloIntegrationError):
    """Raised when an API request fails."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class QuickBooksError(FloIntegrationError):
    """Raised when a QuickBooks-specific error occurs."""
    pass


class DataSourceNotFoundError(FloIntegrationError):
    """Raised when a required data source is not found in __data_sources__."""
    pass


class JobberError(FloIntegrationError):
    """Raised when a Jobber-specific error occurs."""
    pass


class PlaidError(FloIntegrationError):
    """Raised when a Plaid-specific error occurs."""
    pass


class BuildiumError(FloIntegrationError):
    """Raised when a Buildium-specific error occurs."""
    pass


class RentManagerError(FloIntegrationError):
    """Raised when a Rent Manager-specific error occurs."""
    pass


class HostawayError(FloIntegrationError):
    """Raised when a Hostaway-specific error occurs."""
    pass


class MergeError(FloIntegrationError):
    """Raised when a Merge file storage-specific error occurs."""
    pass
