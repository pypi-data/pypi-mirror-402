"""Exceptions for dataset operations."""


class DatasetError(Exception):
    """Base exception for dataset operations."""
    pass


class DatasetNotFoundError(DatasetError):
    """Raised when a dataset is not found."""
    pass


class DatasetAPIError(DatasetError):
    """Raised when an API request fails."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

