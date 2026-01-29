"""Tests for HelloLedger client."""

import pytest
from helloledger import HelloLedger
from helloledger.exceptions import AuthenticationError, APIError


def test_client_initialization():
    """Test client initialization with credentials."""
    client = HelloLedger(
        client_id="hl_test_abc123",
        secret_token="sk_test_xyz789",
        api_base="https://test.example.com",
    )
    assert client.client_id == "hl_test_abc123"
    assert client.secret_token == "sk_test_xyz789"
    assert client.api_base == "https://test.example.com"
    assert client.companies is not None
    assert client.transactions is not None
    client.close()


def test_client_context_manager():
    """Test client as context manager."""
    with HelloLedger(client_id="hl_test_abc123", secret_token="sk_test_xyz789") as client:
        assert client is not None
        assert hasattr(client, "companies")


# Note: Integration tests would require a test API server
# These would test actual API calls with mock or real endpoints
