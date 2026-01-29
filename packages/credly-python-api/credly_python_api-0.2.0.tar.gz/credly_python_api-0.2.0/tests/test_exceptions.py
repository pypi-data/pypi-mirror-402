"""Tests for custom exceptions."""

import pytest

from credly.exceptions import (
    CredlyAPIError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_base_exception(self):
        """Test CredlyAPIError base exception."""
        error = CredlyAPIError("Test error", status_code=500)
        assert str(error) == "Test error"
        assert error.status_code == 500
        assert error.message == "Test error"
        assert error.response is None

    def test_base_exception_with_response(self):
        """Test CredlyAPIError with response data."""
        response_data = {"error": "Something went wrong"}
        error = CredlyAPIError("Test error", status_code=500, response=response_data)
        assert error.response == response_data

    def test_unauthorized_error_inherits_from_base(self):
        """Test UnauthorizedError inherits from CredlyAPIError."""
        error = UnauthorizedError("Unauthorized", status_code=401)
        assert isinstance(error, CredlyAPIError)
        assert error.status_code == 401

    def test_forbidden_error_inherits_from_base(self):
        """Test ForbiddenError inherits from CredlyAPIError."""
        error = ForbiddenError("Forbidden", status_code=403)
        assert isinstance(error, CredlyAPIError)
        assert error.status_code == 403

    def test_not_found_error_inherits_from_base(self):
        """Test NotFoundError inherits from CredlyAPIError."""
        error = NotFoundError("Not found", status_code=404)
        assert isinstance(error, CredlyAPIError)
        assert error.status_code == 404

    def test_validation_error_inherits_from_base(self):
        """Test ValidationError inherits from CredlyAPIError."""
        error = ValidationError("Validation failed", status_code=422)
        assert isinstance(error, CredlyAPIError)
        assert error.status_code == 422

    def test_rate_limit_error_inherits_from_base(self):
        """Test RateLimitError inherits from CredlyAPIError."""
        error = RateLimitError("Rate limit exceeded", status_code=429)
        assert isinstance(error, CredlyAPIError)
        assert error.status_code == 429


class TestExceptionCatching:
    """Test exception catching behavior."""

    def test_catch_specific_exception(self):
        """Test catching specific exception type."""
        with pytest.raises(NotFoundError):
            raise NotFoundError("Resource not found", status_code=404)

    def test_catch_base_exception(self):
        """Test catching base exception catches all derived exceptions."""
        with pytest.raises(CredlyAPIError):
            raise UnauthorizedError("Unauthorized", status_code=401)

    def test_exception_message_accessible(self):
        """Test exception message is accessible."""
        try:
            raise ValidationError("Invalid data", status_code=422)
        except ValidationError as e:
            assert e.message == "Invalid data"
            assert str(e) == "Invalid data"
