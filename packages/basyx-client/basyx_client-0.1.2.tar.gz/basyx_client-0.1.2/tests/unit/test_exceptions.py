"""Unit tests for exception handling."""

import pytest

from basyx_client.exceptions import (
    AASClientError,
    BadRequestError,
    ConflictError,
    ConnectionError,
    ForbiddenError,
    ResourceNotFoundError,
    ServerError,
    TimeoutError,
    UnauthorizedError,
    map_status_to_exception,
)


class TestAASClientError:
    """Tests for base AASClientError."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = AASClientError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.status_code is None
        assert error.url is None
        assert error.details == {}

    def test_error_with_all_fields(self) -> None:
        """Test error with all fields populated."""
        error = AASClientError(
            message="Not found",
            status_code=404,
            url="http://localhost/shells/abc",
            details={"reason": "AAS does not exist"},
        )

        assert "Not found" in str(error)
        assert "[404]" in str(error)
        assert "http://localhost/shells/abc" in str(error)
        assert error.status_code == 404
        assert error.details == {"reason": "AAS does not exist"}

    def test_repr(self) -> None:
        """Test error representation."""
        error = AASClientError("Test error", 500, "http://test.com")

        repr_str = repr(error)
        assert "AASClientError" in repr_str
        assert "Test error" in repr_str
        assert "500" in repr_str


class TestSpecificExceptions:
    """Tests for specific exception types."""

    def test_resource_not_found_error(self) -> None:
        """Test ResourceNotFoundError."""
        error = ResourceNotFoundError("AAS not found", 404)

        assert isinstance(error, AASClientError)
        assert error.status_code == 404

    def test_bad_request_error(self) -> None:
        """Test BadRequestError."""
        error = BadRequestError("Invalid AAS data", 400)

        assert isinstance(error, AASClientError)
        assert error.status_code == 400

    def test_conflict_error(self) -> None:
        """Test ConflictError."""
        error = ConflictError("AAS already exists", 409)

        assert isinstance(error, AASClientError)
        assert error.status_code == 409

    def test_unauthorized_error(self) -> None:
        """Test UnauthorizedError."""
        error = UnauthorizedError("Invalid token", 401)

        assert isinstance(error, AASClientError)
        assert error.status_code == 401

    def test_forbidden_error(self) -> None:
        """Test ForbiddenError."""
        error = ForbiddenError("Access denied", 403)

        assert isinstance(error, AASClientError)
        assert error.status_code == 403

    def test_server_error(self) -> None:
        """Test ServerError."""
        error = ServerError("Internal server error", 500)

        assert isinstance(error, AASClientError)
        assert error.status_code == 500

    def test_connection_error(self) -> None:
        """Test ConnectionError."""
        error = ConnectionError("Could not connect")

        assert isinstance(error, AASClientError)

    def test_timeout_error(self) -> None:
        """Test TimeoutError."""
        error = TimeoutError("Request timed out")

        assert isinstance(error, AASClientError)


class TestMapStatusToException:
    """Tests for map_status_to_exception function."""

    def test_map_400(self) -> None:
        """Test mapping 400 status."""
        error = map_status_to_exception(400, "Bad request")

        assert isinstance(error, BadRequestError)
        assert error.status_code == 400

    def test_map_401(self) -> None:
        """Test mapping 401 status."""
        error = map_status_to_exception(401, "Unauthorized")

        assert isinstance(error, UnauthorizedError)
        assert error.status_code == 401

    def test_map_403(self) -> None:
        """Test mapping 403 status."""
        error = map_status_to_exception(403, "Forbidden")

        assert isinstance(error, ForbiddenError)
        assert error.status_code == 403

    def test_map_404(self) -> None:
        """Test mapping 404 status."""
        error = map_status_to_exception(404, "Not found")

        assert isinstance(error, ResourceNotFoundError)
        assert error.status_code == 404

    def test_map_409(self) -> None:
        """Test mapping 409 status."""
        error = map_status_to_exception(409, "Conflict")

        assert isinstance(error, ConflictError)
        assert error.status_code == 409

    def test_map_500(self) -> None:
        """Test mapping 500 status."""
        error = map_status_to_exception(500, "Server error")

        assert isinstance(error, ServerError)
        assert error.status_code == 500

    def test_map_502(self) -> None:
        """Test mapping 502 status (should be ServerError)."""
        error = map_status_to_exception(502, "Bad gateway")

        assert isinstance(error, ServerError)
        assert error.status_code == 502

    def test_map_503(self) -> None:
        """Test mapping 503 status (should be ServerError)."""
        error = map_status_to_exception(503, "Service unavailable")

        assert isinstance(error, ServerError)
        assert error.status_code == 503

    def test_map_unknown_client_error(self) -> None:
        """Test mapping unknown client error (418)."""
        error = map_status_to_exception(418, "I'm a teapot")

        assert isinstance(error, AASClientError)
        assert not isinstance(error, BadRequestError)
        assert error.status_code == 418

    def test_map_with_url_and_details(self) -> None:
        """Test mapping with URL and details."""
        error = map_status_to_exception(
            404,
            "Not found",
            url="http://localhost/shells/abc",
            details={"reason": "Does not exist"},
        )

        assert error.url == "http://localhost/shells/abc"
        assert error.details == {"reason": "Does not exist"}


class TestExceptionHierarchy:
    """Test exception hierarchy for proper except clause handling."""

    def test_catch_specific_with_base(self) -> None:
        """Test that specific exceptions can be caught with base."""
        error = ResourceNotFoundError("Not found", 404)

        # Should be catchable as base type
        try:
            raise error
        except AASClientError as e:
            assert e.status_code == 404

    def test_catch_all_http_errors(self) -> None:
        """Test catching all HTTP errors with base exception."""
        errors = [
            BadRequestError("Bad", 400),
            UnauthorizedError("Unauth", 401),
            ForbiddenError("Forbidden", 403),
            ResourceNotFoundError("Not found", 404),
            ConflictError("Conflict", 409),
            ServerError("Error", 500),
        ]

        for error in errors:
            try:
                raise error
            except AASClientError:
                pass  # All should be caught
            except Exception:
                pytest.fail(f"{type(error).__name__} not caught by AASClientError")
