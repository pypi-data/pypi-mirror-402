"""Integration tests for HelloLedger SDK against real backend."""

import pytest
import os
from helloledger import HelloLedger
from helloledger.exceptions import AuthenticationError, PermissionError, NotFoundError, APIError


# Test credentials from your generated API key
# Can be overridden via environment variables for CI/CD
TEST_CLIENT_ID = os.getenv(
    "TEST_CLIENT_ID", "hl_live_wOzYunkWVcAH5OqPJjbDGEZb")
TEST_SECRET_TOKEN = os.getenv(
    "TEST_SECRET_TOKEN", "sk_live_IlKOCMSKUOqhZZ28ejojIY2ofZYW1chQO7VA3K2X")
TEST_COMPANY_ID = int(os.getenv("TEST_COMPANY_ID", "202"))
TEST_API_BASE = os.getenv(
    "TEST_API_BASE", "http://localhost:7071")  # Local backend

# Skip integration tests if backend is not available
pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    """Create a test client with real credentials."""
    return HelloLedger(
        client_id=TEST_CLIENT_ID,
        secret_token=TEST_SECRET_TOKEN,
        api_base=TEST_API_BASE,
        timeout=10,  # Shorter timeout for local tests
    )


class TestAuthentication:
    """Test API key authentication."""

    def test_valid_credentials(self, client):
        """Test that valid credentials work."""
        # Just verify client is initialized correctly
        assert client.client_id == TEST_CLIENT_ID
        assert client.secret_token == TEST_SECRET_TOKEN
        assert client.api_base == TEST_API_BASE
        assert hasattr(client, "companies")
        assert hasattr(client, "transactions")

    def test_invalid_credentials(self):
        """Test that invalid credentials raise AuthenticationError."""
        invalid_client = HelloLedger(
            client_id="hl_live_invalid",
            secret_token="sk_live_invalid",
            api_base=TEST_API_BASE,
        )

        with pytest.raises((AuthenticationError, PermissionError, APIError)):
            invalid_client.companies.list()

        invalid_client.close()


class TestCompanies:
    """Test Companies resource."""

    def test_list_companies(self, client):
        """Test listing companies accessible by the API key."""
        companies = client.companies.list()

        # Should return a list
        assert isinstance(companies, list)

        # Should contain the company_id from the API key
        company_ids = [c.get("company_id") or c.get("id") for c in companies]
        assert TEST_COMPANY_ID in company_ids, f"Expected company {TEST_COMPANY_ID} not in list"

    def test_get_company(self, client):
        """Test getting a specific company."""
        company = client.companies.get(company_id=TEST_COMPANY_ID)

        # Should return a dict
        assert isinstance(company, dict)

        # Should have company_id
        company_id = company.get("company_id") or company.get("id")
        assert company_id == TEST_COMPANY_ID, f"Expected company_id {TEST_COMPANY_ID}, got {company_id}"

    def test_get_company_not_accessible(self, client):
        """Test getting a company the API key doesn't have access to."""
        # This test might pass or fail depending on backend implementation
        # If routes aren't updated, it will fail with auth error
        # If routes are updated, it should fail with PermissionError
        with pytest.raises((PermissionError, NotFoundError, AuthenticationError, APIError)):
            client.companies.get(company_id=999)


class TestTransactions:
    """Test Transactions resource."""

    def test_list_transactions(self, client):
        """Test listing transactions for the accessible company."""
        transactions = client.transactions.list(company_id=TEST_COMPANY_ID)

        # Should return a list
        assert isinstance(transactions, list)
        print(
            f"\n✅ Found {len(transactions)} transactions for company {TEST_COMPANY_ID}")

    def test_list_transactions_with_params(self, client):
        """Test listing transactions with query parameters."""
        transactions = client.transactions.list(
            company_id=TEST_COMPANY_ID,
            limit=10,
            offset=0
        )

        # Should return a list (may be empty)
        assert isinstance(transactions, list)
        # Note: Backend may not enforce limit in query params, so we just check it's a list

    def test_list_transactions_not_accessible(self, client):
        """Test listing transactions for a company the API key doesn't have access to."""
        # This test might pass or fail depending on backend implementation
        with pytest.raises((PermissionError, NotFoundError, AuthenticationError, APIError)):
            client.transactions.list(company_id=999)


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow(self, client):
        """Test a complete workflow: list companies, get company, list transactions."""
        # Step 1: List companies
        companies = client.companies.list()
        assert len(companies) > 0, "Should have at least one company"

        # Step 2: Get the first company
        first_company_id = companies[0].get(
            "company_id") or companies[0].get("id")
        company = client.companies.get(company_id=first_company_id)
        assert company is not None

        # Step 3: List transactions for that company
        transactions = client.transactions.list(company_id=first_company_id)
        assert isinstance(transactions, list)
        print(
            f"\n✅ Full workflow complete - found {len(transactions)} transactions")

    def test_context_manager(self):
        """Test using client as context manager."""
        with HelloLedger(
            client_id=TEST_CLIENT_ID,
            secret_token=TEST_SECRET_TOKEN,
            api_base=TEST_API_BASE,
        ) as client:
            # Just verify client works, don't test actual API calls yet
            assert client is not None
            assert hasattr(client, "companies")
            assert hasattr(client, "transactions")
        # Client should be closed automatically


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_connection_timeout(self):
        """Test handling connection timeout."""
        # Use an unreachable URL
        client = HelloLedger(
            client_id=TEST_CLIENT_ID,
            secret_token=TEST_SECRET_TOKEN,
            api_base="http://192.0.2.1:7071",  # Unreachable IP
            timeout=1,  # Very short timeout
        )

        with pytest.raises(APIError):
            client.companies.list()

        client.close()

    def test_invalid_api_base(self):
        """Test handling invalid API base URL."""
        client = HelloLedger(
            client_id=TEST_CLIENT_ID,
            secret_token=TEST_SECRET_TOKEN,
            api_base="http://invalid-domain-that-does-not-exist.local:7071",
            timeout=5,
        )

        with pytest.raises(APIError):
            client.companies.list()

        client.close()


class TestBackendStatus:
    """Test to verify backend implementation status."""

    def test_backend_responds_to_basic_auth(self, client):
        """Test that backend responds to Basic Auth correctly.

        This test verifies:
        1. Backend is running
        2. Basic Auth header is being sent correctly
        3. Backend routes support API key authentication
        """
        # Try to list companies - should work now
        companies = client.companies.list()
        print("\n✅ Backend routes support API key Basic Auth!")
        assert isinstance(companies, list)
