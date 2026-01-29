"""HelloLedger API Client."""

import base64
import json
from typing import Optional, Dict, Any
import httpx


class HelloLedger:
    """Main client class for HelloLedger API."""

    def __init__(
        self,
        client_id: str,
        secret_token: str,
        api_base: str = "https://api.helloledger.ai",
        timeout: int = 30,
    ):
        """
        Initialize HelloLedger client.

        Args:
            client_id: API client ID (e.g., "hl_live_abc123")
            secret_token: API secret token (e.g., "sk_live_xyz789")
            api_base: Base URL for the API
                - Production (default): "https://api.helloledger.ai"
                - Sandbox: "https://devhlapi.azurewebsites.net"
            timeout: Request timeout in seconds (default: 30)
        """
        self.client_id = client_id
        self.secret_token = secret_token
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

        # Create Basic Auth header: base64(client_id:secret_token)
        credentials = f"{client_id}:{secret_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"

        # Initialize HTTP client
        self._client = httpx.Client(
            base_url=self.api_base,
            timeout=self.timeout,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        # Initialize resources
        from helloledger.resources.companies import Companies
        from helloledger.resources.transactions import Transactions

        self.companies = Companies(self)
        self.transactions = Transactions(self)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path (e.g., "/companies")
            params: Query parameters
            json_data: JSON request body

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If authentication fails (401)
            PermissionError: If permission denied (403)
            NotFoundError: If resource not found (404)
            APIError: For other API errors
        """
        from helloledger.exceptions import (
            AuthenticationError,
            PermissionError,
            NotFoundError,
            APIError,
        )

        try:
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
            )

            # Parse response body
            try:
                response_data = response.json() if response.content else {}
            except json.JSONDecodeError:
                response_data = {
                    "message": response.text} if response.text else {}

            # Handle HTTP errors
            if response.status_code == 401:
                raise AuthenticationError(
                    message=response_data.get(
                        "detail", "Authentication failed"),
                    status_code=401,
                    response_body=response_data,
                )
            elif response.status_code == 403:
                raise PermissionError(
                    message=response_data.get("detail", "Permission denied"),
                    status_code=403,
                    response_body=response_data,
                )
            elif response.status_code == 404:
                raise NotFoundError(
                    message=response_data.get("detail", "Resource not found"),
                    status_code=404,
                    response_body=response_data,
                )
            elif not response.is_success:
                raise APIError(
                    message=response_data.get(
                        "detail", f"API error: {response.status_code}"),
                    status_code=response.status_code,
                    response_body=response_data,
                )

            return response_data

        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            # This should not happen since we check status_code manually,
            # but handle it just in case
            raise APIError(f"HTTP error: {str(e)}",
                           status_code=e.response.status_code)
        except (
            AuthenticationError,
            PermissionError,
            NotFoundError,
            APIError,
        ):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}")

    def close(self):
        """Close the HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
