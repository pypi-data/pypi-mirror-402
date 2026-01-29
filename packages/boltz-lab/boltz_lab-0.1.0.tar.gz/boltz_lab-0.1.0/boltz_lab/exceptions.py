"""Exception classes for Boltz Lab API client."""


class BoltzAPIError(Exception):
    """Base exception for all Boltz API errors."""

    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class BoltzAuthenticationError(BoltzAPIError):
    """Raised when API authentication fails."""

    pass


class BoltzNotFoundError(BoltzAPIError):
    """Raised when a requested resource is not found."""

    pass


class BoltzTimeoutError(BoltzAPIError):
    """Raised when a request times out."""

    pass


class BoltzValidationError(BoltzAPIError):
    """Raised when request validation fails."""

    pass


class BoltzConnectionError(BoltzAPIError):
    """Raised when connection to the API server fails."""

    pass
