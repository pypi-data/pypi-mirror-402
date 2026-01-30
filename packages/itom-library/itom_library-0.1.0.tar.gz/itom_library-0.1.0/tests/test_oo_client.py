"""Tests for OOClient."""

import pytest
import responses
from responses import matchers

from itom_library import OOClient
from itom_library.oo_client import OOAuthenticationError, OOAPIError


@pytest.fixture
def mock_auth():
    """Set up mock authentication response."""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.HEAD,
            "https://localhost:5555/oo",
            headers={"X-CSRF-TOKEN": "test-csrf-token"},
            status=200,
        )
        rsps.add_callback(
            responses.HEAD,
            "https://localhost:5555/oo",
            callback=lambda req: (200, {"X-CSRF-TOKEN": "test-csrf-token"}, ""),
        )
        yield rsps


@pytest.fixture
def client(mock_auth):
    """Create a test client with mocked authentication."""
    return OOClient(
        base_url="https://localhost:5555/oo",
        username="admin",
        password="password123",
    )


class TestOOClientInit:
    """Tests for OOClient initialization."""

    @responses.activate
    def test_successful_authentication(self):
        """Test successful client initialization."""
        responses.add(
            responses.HEAD,
            "https://localhost:5555/oo",
            headers={"X-CSRF-TOKEN": "test-token"},
            status=200,
        )

        client = OOClient(
            base_url="https://localhost:5555/oo",
            username="admin",
            password="password123",
        )

        assert client._x_csrf_token == "test-token"

    @responses.activate
    def test_authentication_no_token(self):
        """Test authentication failure when no token returned."""
        responses.add(
            responses.HEAD,
            "https://localhost:5555/oo",
            headers={},
            status=200,
        )

        with pytest.raises(OOAuthenticationError) as exc_info:
            OOClient(
                base_url="https://localhost:5555/oo",
                username="admin",
                password="password123",
            )

        assert "token not found" in str(exc_info.value).lower()

    @responses.activate
    def test_authentication_http_error(self):
        """Test authentication failure on HTTP error."""
        responses.add(
            responses.HEAD,
            "https://localhost:5555/oo",
            status=401,
        )

        with pytest.raises(OOAuthenticationError) as exc_info:
            OOClient(
                base_url="https://localhost:5555/oo",
                username="admin",
                password="wrong_password",
            )

        assert "Authentication failed" in str(exc_info.value)

    @responses.activate
    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        responses.add(
            responses.HEAD,
            "https://localhost:5555/oo",
            headers={"X-CSRF-TOKEN": "test-token"},
            status=200,
        )

        client = OOClient(
            base_url="https://localhost:5555/oo/",
            username="admin",
            password="password123",
        )

        assert client.base_url == "https://localhost:5555/oo"


class TestOOClientGetFlows:
    """Tests for get_flows method."""

    @responses.activate
    def test_get_flows_success(self):
        """Test successful retrieval of flows."""
        # Auth
        responses.add(
            responses.HEAD,
            "https://localhost:5555/oo",
            headers={"X-CSRF-TOKEN": "test-token"},
            status=200,
        )
        # Get flows
        expected_flows = {"flows": [{"id": "1", "name": "Test Flow"}]}
        responses.add(
            responses.GET,
            "https://localhost:5555/oo/rest/latest/flows/library",
            json=expected_flows,
            status=200,
        )

        client = OOClient(
            base_url="https://localhost:5555/oo",
            username="admin",
            password="password123",
        )
        flows = client.get_flows()

        assert flows == expected_flows

    @responses.activate
    def test_get_flows_api_error(self):
        """Test get_flows raises OOAPIError on failure."""
        # Auth
        responses.add(
            responses.HEAD,
            "https://localhost:5555/oo",
            headers={"X-CSRF-TOKEN": "test-token"},
            status=200,
        )
        # Get flows - error
        responses.add(
            responses.GET,
            "https://localhost:5555/oo/rest/latest/flows/library",
            status=500,
        )

        client = OOClient(
            base_url="https://localhost:5555/oo",
            username="admin",
            password="password123",
        )

        with pytest.raises(OOAPIError):
            client.get_flows()


class TestOOClientRepr:
    """Tests for __repr__ method."""

    @responses.activate
    def test_repr(self):
        """Test string representation of client."""
        responses.add(
            responses.HEAD,
            "https://localhost:5555/oo",
            headers={"X-CSRF-TOKEN": "test-token"},
            status=200,
        )

        client = OOClient(
            base_url="https://localhost:5555/oo",
            username="admin",
            password="password123",
        )

        expected = "OOClient(base_url='https://localhost:5555/oo', username='admin')"
        assert repr(client) == expected
