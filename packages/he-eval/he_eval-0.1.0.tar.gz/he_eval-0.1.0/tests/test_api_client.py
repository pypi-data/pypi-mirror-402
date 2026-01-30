"""Tests for CLI API client module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from human_eval.api_client import (
    APIClient,
    APIError,
    Assignment,
    AuthenticationError,
    NotFoundError,
)


@pytest.fixture
def mock_config():
    """Mock config with server URL and API key."""
    mock = MagicMock()
    mock.server.url = "https://test.example.com"
    mock.auth.api_key = "sk-test123"
    return mock


@pytest.fixture
def client(mock_config):
    """Create API client with mocked config."""
    with patch("human_eval.api_client.load_config", return_value=mock_config):
        return APIClient()


def test_client_init_from_config(mock_config):
    """Test client initializes from config."""
    with patch("human_eval.api_client.load_config", return_value=mock_config):
        client = APIClient()
        assert client.base_url == "https://test.example.com"
        assert client.api_key == "sk-test123"


def test_client_init_explicit_params():
    """Test client can be initialized with explicit params."""
    with patch("human_eval.api_client.load_config") as mock:
        mock.return_value.server.url = ""
        mock.return_value.auth.api_key = ""
        client = APIClient(base_url="https://explicit.com", api_key="sk-explicit")
        assert client.base_url == "https://explicit.com"
        assert client.api_key == "sk-explicit"


def test_client_init_no_server_raises():
    """Test client raises if no server configured."""
    mock = MagicMock()
    mock.server.url = ""
    mock.auth.api_key = ""
    with patch("human_eval.api_client.load_config", return_value=mock):
        with pytest.raises(APIError, match="No server URL configured"):
            APIClient()


def test_headers_include_auth(client):
    """Test headers include authorization."""
    headers = client._headers()
    assert headers["Authorization"] == "Bearer sk-test123"
    assert headers["Content-Type"] == "application/json"


class MockResponse:
    """Mock httpx response."""

    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.stdout = ""
        self.stderr = ""

    def json(self):
        return self._json_data


def test_request_success(client):
    """Test successful request returns JSON."""
    mock_response = MockResponse(200, {"status": "ok"})

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )
        result = client._request("GET", "/test")
        assert result == {"status": "ok"}


def test_request_401_raises_auth_error(client):
    """Test 401 response raises AuthenticationError."""
    mock_response = MockResponse(401, {"detail": "Invalid token"})

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )
        with pytest.raises(AuthenticationError, match="Invalid or expired API key"):
            client._request("GET", "/test")


def test_request_404_raises_not_found(client):
    """Test 404 response raises NotFoundError."""
    mock_response = MockResponse(404, {"detail": "Not found"})

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )
        with pytest.raises(NotFoundError):
            client._request("GET", "/test")


def test_request_no_auth_raises_when_required(mock_config):
    """Test request raises if auth required but missing."""
    mock_config.auth.api_key = ""
    with patch("human_eval.api_client.load_config", return_value=mock_config):
        client = APIClient(base_url="https://test.com", api_key="")
        with pytest.raises(AuthenticationError, match="Not authenticated"):
            client._request("GET", "/test", require_auth=True)


def test_list_assignments(client):
    """Test listing assignments."""
    mock_response = MockResponse(
        200,
        [
            {
                "id": "123",
                "setting": "bashbench2",
                "task_id": "task1",
                "side_task": "disable_firewall",
                "status": "pending",
                "priority": 1,
            }
        ],
    )

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )
        assignments = client.list_assignments()
        assert len(assignments) == 1
        assert isinstance(assignments[0], Assignment)
        assert assignments[0].id == "123"
        assert assignments[0].setting == "bashbench2"


def test_get_assignment(client):
    """Test getting a specific assignment."""
    mock_response = MockResponse(
        200,
        {
            "id": "123",
            "setting": "bashbench2",
            "task_id": "task1",
            "side_task": "disable_firewall",
            "status": "pending",
            "priority": 1,
        },
    )

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )
        assignment = client.get_assignment("123")
        assert assignment.id == "123"
        assert assignment.task_id == "task1"
