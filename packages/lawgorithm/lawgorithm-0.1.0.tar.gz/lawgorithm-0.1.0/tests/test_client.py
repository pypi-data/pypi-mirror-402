"""Tests for LawgorithmClient."""

import pytest
from pytest_httpx import HTTPXMock

from lawgorithm import LawgorithmClient
from lawgorithm.exceptions import AuthenticationError, NotFoundError


@pytest.fixture
def client() -> LawgorithmClient:
    """Create a test client."""
    return LawgorithmClient(
        api_url="https://api.test.lawgorithm.io",
        api_token="test-token"
    )


def test_client_headers(client: LawgorithmClient) -> None:
    """Test that client sets correct headers."""
    headers = client._headers()
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Content-Type"] == "application/json"


def test_list_systems(client: LawgorithmClient, httpx_mock: HTTPXMock) -> None:
    """Test listing systems."""
    httpx_mock.add_response(
        url="https://api.test.lawgorithm.io/systems?skip=0&limit=100",
        json=[
            {
                "id": "123",
                "name": "Test System",
                "risk_level": "high",
                "created_at": "2025-01-01T00:00:00Z"
            }
        ]
    )

    systems = client.list_systems()
    assert len(systems) == 1
    assert systems[0].name == "Test System"
    assert systems[0].risk_level.value == "high"


def test_get_system(client: LawgorithmClient, httpx_mock: HTTPXMock) -> None:
    """Test getting a single system."""
    httpx_mock.add_response(
        url="https://api.test.lawgorithm.io/systems/123",
        json={
            "id": "123",
            "name": "Test System",
            "risk_level": "high",
            "created_at": "2025-01-01T00:00:00Z"
        }
    )

    system = client.get_system("123")
    assert system.id == "123"
    assert system.name == "Test System"


def test_authentication_error(client: LawgorithmClient, httpx_mock: HTTPXMock) -> None:
    """Test that 401 raises AuthenticationError."""
    httpx_mock.add_response(
        url="https://api.test.lawgorithm.io/systems",
        status_code=401
    )

    with pytest.raises(AuthenticationError):
        client.list_systems()


def test_not_found_error(client: LawgorithmClient, httpx_mock: HTTPXMock) -> None:
    """Test that 404 raises NotFoundError."""
    httpx_mock.add_response(
        url="https://api.test.lawgorithm.io/systems/nonexistent",
        status_code=404
    )

    with pytest.raises(NotFoundError):
        client.get_system("nonexistent")


def test_context_manager() -> None:
    """Test client as context manager."""
    with LawgorithmClient(api_url="https://test.api") as client:
        assert client is not None
    # Client should be closed after exiting context


def test_check_compliance(client: LawgorithmClient, httpx_mock: HTTPXMock) -> None:
    """Test compliance check."""
    httpx_mock.add_response(
        url="https://api.test.lawgorithm.io/ci/check",
        json={
            "repo": "myorg/myrepo",
            "commit": "abc123",
            "branch": "main",
            "systems_analyzed": 1,
            "policies_evaluated": 10,
            "passed": 8,
            "failed": 2,
            "compliance_rate": 0.8,
            "has_failures": True,
            "blocked": False,
            "issues": [],
            "exit_code": 0
        }
    )

    result = client.check_compliance(
        repo="myorg/myrepo",
        commit="abc123",
        branch="main"
    )

    assert result.compliance_rate == 0.8
    assert result.passed == 8
    assert result.failed == 2
    assert not result.blocked
