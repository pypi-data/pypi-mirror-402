"""Transactions resource for HelloLedger API."""

from typing import List, Dict, Any, Optional


class Transactions:
    """Transactions resource for managing transaction data."""

    def __init__(self, client):
        """Initialize Transactions resource.

        Args:
            client: HelloLedger client instance
        """
        self._client = client

    def list(self, company_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        List transactions for a specific company.

        Args:
            company_id: Company ID (required)
            **kwargs: Additional query parameters (e.g., start_date, end_date, limit, offset)

        Returns:
            List of transaction dictionaries

        Raises:
            NotFoundError: If company not found or not accessible
            AuthenticationError: If authentication fails
            PermissionError: If API key doesn't have access to this company
            APIError: If the request fails
        """
        params = {"company_id": company_id}
        params.update(kwargs)
        response = self._client._request("GET", "/transactions", params=params)
        # Handle different response formats
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and "data" in response:
            return response["data"]
        elif isinstance(response, dict) and "transactions" in response:
            return response["transactions"]
        else:
            return []
