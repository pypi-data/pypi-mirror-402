class GenderApiError(Exception):
    """Base exception for all Gender API errors."""
    pass


class InvalidArgumentError(GenderApiError):
    """Raised when an invalid argument is provided to a client method."""
    pass


class ApiError(GenderApiError):
    """Raised when the API returns an error response."""
    def __init__(self, message: str, error_code: int = None, http_status: int = None):
        super().__init__(message)
        self.error_code = error_code
        self.http_status = http_status
