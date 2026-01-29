"""
Custom exceptions for the Kipu API library
"""


class KipuAPIError(Exception):
    """Base exception for all Kipu API errors"""

    def __init__(
        self, message: str, status_code: int = None, response_data: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)


class KipuAuthenticationError(KipuAPIError):
    """Raised when authentication fails (401)"""

    pass


class KipuValidationError(KipuAPIError):
    """Raised when request validation fails (400, 422)"""

    pass


class KipuNotFoundError(KipuAPIError):
    """Raised when resource is not found (404)"""

    pass


class KipuServerError(KipuAPIError):
    """Raised when server error occurs (500, 502, 503, 504)"""

    pass


class KipuForbiddenError(KipuAPIError):
    """Raised when access is forbidden (403)"""

    pass
