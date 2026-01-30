# Relworx Python SDK

A Python library for integrating with the [Relworx Payments API](https://payments.relworx.com/). Send and request payments through mobile money providers across East Africa (MTN, Airtel, M-Pesa, and more).

## Features

- 🌍 **Multi-Country Support**: Uganda (UGX), Kenya (KES), Tanzania (TZS), Rwanda (RWF)
- 💳 **Multiple Providers**: MTN, Airtel, Safaricom M-Pesa, Vodacom, Tigo, Halopesa
- 📱 **Mobile Money & Cards**: Support for both mobile money and VISA payments
- ⚡ **Easy Integration**: Simple, Pythonic API
- 🔒 **Secure**: Built-in authentication and error handling
- 📊 **Transaction Tracking**: Check payment status and transaction history
- 🧪 **Type Hints**: Full type annotation support
- 📚 **Well Documented**: Comprehensive documentation and examples

## Installation

```bash
pip install relworx
```

### Requirements

- Python 3.7+
- requests >= 2.25.0

## Quick Start

```python
from relworx import RelworxClient

# Initialize the client
client = RelworxClient(api_key="your-api-key")

# Request a payment from a customer
response = client.request_payment(
    phone_number="256701234567",
    amount=10000,
    currency="UGX",
    reference="ORDER123",
    description="Payment for Order #123"
)

print(response)
# {
#     "status": "success",
#     "transaction_id": "txn_123",
#     "reference": "ORDER123",
#     ...
# }
```

## Usage Examples

### Request Payment

Request money from a customer's mobile money account:

```python
from relworx import RelworxClient

client = RelworxClient(api_key="your-api-key")

# Basic request
response = client.request_payment(
    phone_number="256701234567",  # Customer's phone number
    amount=50000,                  # Amount in UGX
    currency="UGX",               # Currency code
    reference="ORDER-2024-001"    # Unique transaction reference
)
```

### Send Money

Send money to a customer:

```python
# Send money to customer
response = client.send_money(
    phone_number="256701234567",
    amount=25000,
    currency="UGX",
    reference="REFUND-001",
    reason="Refund for cancelled order"
)
```

### Check Transaction Status

```python
# Get transaction status
status = client.get_transaction_status(reference="ORDER-2024-001")
print(status["status"])  # "pending", "completed", "failed", etc.
```

### Validate Payment Details

```python
# Validate phone number and currency before making a payment
validation = client.validate_payment_details(
    phone_number="256701234567",
    currency="UGX"
)
print(validation["valid"])     # True or False
print(validation["operator"])  # "MTN", "Airtel", etc.
```

### Get Exchange Rates

```python
# Get current exchange rates
rates = client.get_exchange_rates()
print(rates)
```

### Using Context Manager

```python
# Automatically close the client session
with RelworxClient(api_key="your-api-key") as client:
    response = client.request_payment(
        phone_number="256701234567",
        amount=10000,
        currency="UGX",
        reference="ORDER123"
    )
```

## Supported Countries and Currencies

| Country | Currency | Providers | Min Amount | Max Amount |
|---------|----------|-----------|-----------|-----------|
| Uganda | UGX | MTN, Airtel | 500 | 5,000,000 |
| Kenya | KES | Safaricom, Airtel | 10 | 70,000 |
| Tanzania | TZS | Airtel, Tigo, Vodacom, Halotel | 500 | 5,000,000 |
| Rwanda | RWF | MTN, Airtel | 100 | 5,000,000 |
| Global | USD | VISA (limited) | 12 | 5,000 |

## Error Handling

The SDK provides specific exceptions for different error scenarios:

```python
from relworx import RelworxClient
from relworx.exceptions import ValidationError, AuthenticationError, APIError

client = RelworxClient(api_key="your-api-key")

try:
    response = client.request_payment(
        phone_number="256701234567",
        amount=10000,
        currency="UGX",
        reference="ORDER123"
    )
except ValidationError as e:
    # Handle validation errors (invalid parameters)
    print(f"Validation error: {e}")
except AuthenticationError as e:
    # Handle authentication errors (invalid API key)
    print(f"Authentication error: {e}")
except APIError as e:
    # Handle API errors
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
```

## Configuration

### Custom Timeout

```python
# Set custom request timeout (in seconds)
client = RelworxClient(api_key="your-api-key", timeout=60)
```

### Environment Variables

Store your API key securely using environment variables:

```python
import os
from relworx import RelworxClient

api_key = os.getenv("RELWORX_API_KEY")
client = RelworxClient(api_key=api_key)
```

## Webhooks

For production use, configure webhooks in your Relworx dashboard to receive real-time payment status updates. Provide a callback URL when making requests:

```python
response = client.request_payment(
    phone_number="256701234567",
    amount=10000,
    currency="UGX",
    reference="ORDER123",
    callback_url="https://your-domain.com/webhooks/relworx"
)
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/relworx-python.git
cd relworx-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,test]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/relworx --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run tests with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 src/relworx tests

# Type checking
mypy src/relworx
```

## Building and Publishing

### Build Distribution

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Check distribution
twine check dist/*
```

### Upload to PyPI

```bash
# Upload to PyPI (requires credentials)
twine upload dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*
```

## API Reference

### RelworxClient

Main client class for interacting with the Relworx API.

#### Methods

- **request_payment()** - Request payment from customer
- **send_money()** - Send money to customer
- **get_transaction_status()** - Get transaction status
- **validate_payment_details()** - Validate phone and currency
- **get_exchange_rates()** - Get current exchange rates
- **close()** - Close client session

## Exceptions

- **RelworxError** - Base exception for all SDK errors
- **AuthenticationError** - Authentication failed
- **ValidationError** - Request validation failed
- **APIError** - API returned an error

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [API Documentation](https://payments.relworx.com/docs/)
- 🐛 [Report Issues](https://github.com/yourusername/relworx-python/issues)
- 💬 [Discussions](https://github.com/yourusername/relworx-python/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

## Disclaimer

This is an unofficial library. For official support, please visit [Relworx Payments](https://payments.relworx.com/).
