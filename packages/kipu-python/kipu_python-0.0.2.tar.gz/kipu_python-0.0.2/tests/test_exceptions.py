"""
Tests for exceptions module
"""

from kipu.exceptions import (
    KipuAPIError,
    KipuAuthenticationError,
    KipuForbiddenError,
    KipuNotFoundError,
    KipuServerError,
    KipuValidationError,
)


class TestKipuExceptions:
    def test_base_exception(self):
        """Test base KipuAPIError"""
        error = KipuAPIError("Test error", 500, {"error": "test"})

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.response_data == {"error": "test"}

    def test_base_exception_minimal(self):
        """Test base exception with minimal arguments"""
        error = KipuAPIError("Simple error")

        assert str(error) == "Simple error"
        assert error.message == "Simple error"
        assert error.status_code is None
        assert error.response_data == {}

    def test_authentication_error(self):
        """Test authentication error"""
        error = KipuAuthenticationError("Auth failed", 401)

        assert isinstance(error, KipuAPIError)
        assert str(error) == "Auth failed"
        assert error.status_code == 401

    def test_validation_error(self):
        """Test validation error"""
        error = KipuValidationError("Invalid data", 400, {"field": "error"})

        assert isinstance(error, KipuAPIError)
        assert str(error) == "Invalid data"
        assert error.status_code == 400
        assert error.response_data == {"field": "error"}

    def test_not_found_error(self):
        """Test not found error"""
        error = KipuNotFoundError("Resource not found", 404)

        assert isinstance(error, KipuAPIError)
        assert str(error) == "Resource not found"
        assert error.status_code == 404

    def test_server_error(self):
        """Test server error"""
        error = KipuServerError("Internal error", 500)

        assert isinstance(error, KipuAPIError)
        assert str(error) == "Internal error"
        assert error.status_code == 500

    def test_forbidden_error(self):
        """Test forbidden error"""
        error = KipuForbiddenError("Access denied", 403)

        assert isinstance(error, KipuAPIError)
        assert str(error) == "Access denied"
        assert error.status_code == 403

    def test_exception_inheritance(self):
        """Test exception inheritance hierarchy"""
        # All custom exceptions should inherit from KipuAPIError
        assert issubclass(KipuAuthenticationError, KipuAPIError)
        assert issubclass(KipuValidationError, KipuAPIError)
        assert issubclass(KipuNotFoundError, KipuAPIError)
        assert issubclass(KipuServerError, KipuAPIError)
        assert issubclass(KipuForbiddenError, KipuAPIError)

        # And KipuAPIError should inherit from Exception
        assert issubclass(KipuAPIError, Exception)
