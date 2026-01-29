"""Companies resource for HelloLedger API."""

from typing import List, Dict, Any, Optional


class Companies:
    """Companies resource for managing company data."""

    def __init__(self, client):
        """Initialize Companies resource.

        Args:
            client: HelloLedger client instance
        """
        self._client = client

    def list(self) -> List[Dict[str, Any]]:
        """
        List all companies accessible by the API key.

        Returns:
            List of company dictionaries

        Raises:
            AuthenticationError: If authentication fails
            APIError: If the request fails
        """
        response = self._client._request("GET", "/companies")
        # Handle different response formats
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and "data" in response:
            return response["data"]
        elif isinstance(response, dict) and "companies" in response:
            return response["companies"]
        else:
            return []

    def get(self, company_id: int) -> Dict[str, Any]:
        """
        Get a specific company by ID.

        Args:
            company_id: Company ID

        Returns:
            Company dictionary

        Raises:
            NotFoundError: If company not found or not accessible
            AuthenticationError: If authentication fails
            PermissionError: If API key doesn't have access to this company
            APIError: If the request fails
        """
        response = self._client._request("GET", f"/companies/{company_id}")
        return response
