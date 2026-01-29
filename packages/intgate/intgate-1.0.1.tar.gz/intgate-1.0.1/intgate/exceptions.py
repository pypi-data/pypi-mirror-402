"""
Exception classes for the IntGate API client.
"""


class IntGateError(Exception):
    """Base exception for all IntGate errors."""
    pass


class IntGateAPIError(IntGateError):
    """Exception raised when the API returns an error response."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class IntGateValidationError(IntGateError):
    """Exception raised when input validation fails."""
    pass
