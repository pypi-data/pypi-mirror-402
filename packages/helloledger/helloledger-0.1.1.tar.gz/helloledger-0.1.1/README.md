# HelloLedger Python SDK

Official Python SDK for the HelloLedger API. This SDK enables developers to integrate HelloLedger programmatically using API keys.

## Installation

```bash
pip install helloledger
```

## Quick Start

```python
from helloledger import HelloLedger

# Production (default)
client = HelloLedger(
    client_id="hl_live_abc123",
    secret_token="sk_live_xyz789",
    api_base="https://api.helloledger.ai"  # Optional, defaults to production
)

# Sandbox/Development
client = HelloLedger(
    client_id="hl_test_abc123",
    secret_token="sk_test_xyz789",
    api_base="https://devhlapi.azurewebsites.net"  # Use for testing
)

# List all companies accessible by your API key
companies = client.companies.list()

# Get a specific company
company = client.companies.get(company_id=123)

# List transactions for a company
transactions = client.transactions.list(company_id=123)

# Optional: Filter transactions by date
transactions = client.transactions.list(
    company_id=123,
    start_date="2025-01-01",
    end_date="2025-12-31"
)
```

## Authentication

The SDK uses HTTP Basic Authentication with your API key credentials. You need to:

1. Sign up for a HelloLedger account
2. Generate an API key (client_id + secret_token)
3. Initialize the client with your credentials

**Important**: Keep your `secret_token` secure and never commit it to version control.

## API Environments

The SDK supports two environments:

- **Production**: `https://api.helloledger.ai` (default)
  - Use for live/production applications
  - Requires production API keys

- **Sandbox**: `https://devhlapi.azurewebsites.net`
  - Use for testing and development
  - Requires sandbox/test API keys

Example:

```python
# Production
client = HelloLedger(
    client_id="hl_live_abc123",
    secret_token="sk_live_xyz789"
    # api_base defaults to https://api.helloledger.ai
)

# Sandbox
client = HelloLedger(
    client_id="hl_test_abc123",
    secret_token="sk_test_xyz789",
    api_base="https://devhlapi.azurewebsites.net"
)
```

## Error Handling

The SDK raises custom exceptions for different error scenarios:

```python
from helloledger import HelloLedger
from helloledger.exceptions import (
    AuthenticationError,
    PermissionError,
    NotFoundError,
    APIError
)

client = HelloLedger(client_id="...", secret_token="...")

try:
    company = client.companies.get(company_id=123)
except NotFoundError:
    print("Company not found or not accessible")
except PermissionError:
    print("Your API key doesn't have access to this company")
except AuthenticationError:
    print("Invalid API credentials")
except APIError as e:
    print(f"API error: {e.message} (Status: {e.status_code})")
```

## Available Methods (Phase 1 - MVP)

### Companies

- `client.companies.list()` - List all accessible companies
- `client.companies.get(company_id)` - Get a specific company

### Transactions

- `client.transactions.list(company_id, **kwargs)` - List transactions for a company
  - Optional parameters: `start_date`, `end_date`, `limit`, `offset`

## Context Manager

You can use the client as a context manager to ensure proper cleanup:

```python
with HelloLedger(client_id="...", secret_token="...") as client:
    companies = client.companies.list()
    # Client is automatically closed when exiting the context
```

## Requirements

- Python 3.8+
- httpx >= 0.24.0

## License

MIT

## Support

For issues, questions, or feature requests:
- **PyPI Project Page**: https://pypi.org/project/helloledger/
- **GitHub Repository**: https://github.com/helloledger/helloledger-python
- **GitHub Issues**: https://github.com/helloledger/helloledger-python/issues
