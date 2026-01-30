"""Tests for the RelworxClient."""

import pytest
import requests_mock
from relworx import RelworxClient
from relworx.exceptions import ValidationError, AuthenticationError, APIError


class TestClientInitialization:
    """Test client initialization."""

    def test_init_with_valid_api_key(self):
        """Test initialization with valid API key."""
        client = RelworxClient(api_key="valid-key")
        assert client.api_key == "valid-key"
        assert client.timeout == 30

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        client = RelworxClient(api_key="valid-key", timeout=60)
        assert client.timeout == 60

    def test_init_with_empty_api_key(self):
        """Test initialization with empty API key raises error."""
        with pytest.raises(ValidationError):
            RelworxClient(api_key="")

    def test_init_with_none_api_key(self):
        """Test initialization with None API key raises error."""
        with pytest.raises(ValidationError):
            RelworxClient(api_key=None)

    def test_context_manager(self):
        """Test client works as context manager."""
        with RelworxClient(api_key="valid-key") as client:
            assert client.api_key == "valid-key"


class TestRequestValidation:
    """Test request validation."""

    def test_validate_request_payment_invalid_phone(self):
        """Test validation with invalid phone number."""
        client = RelworxClient(api_key="test-key")
        with pytest.raises(ValidationError):
            client._validate_request_payment("", 1000, "UGX", "ref123")

    def test_validate_request_payment_invalid_amount(self):
        """Test validation with invalid amount."""
        client = RelworxClient(api_key="test-key")
        with pytest.raises(ValidationError):
            client._validate_request_payment("256701234567", -100, "UGX", "ref123")

    def test_validate_request_payment_invalid_currency(self):
        """Test validation with invalid currency."""
        client = RelworxClient(api_key="test-key")
        with pytest.raises(ValidationError):
            client._validate_request_payment("256701234567", 1000, "", "ref123")

    def test_validate_request_payment_invalid_reference(self):
        """Test validation with invalid reference."""
        client = RelworxClient(api_key="test-key")
        with pytest.raises(ValidationError):
            client._validate_request_payment("256701234567", 1000, "UGX", "")

    def test_validate_request_payment_valid(self):
        """Test validation with valid parameters."""
        client = RelworxClient(api_key="test-key")
        # Should not raise
        client._validate_request_payment("256701234567", 1000, "UGX", "ref123")


class TestRequestPayment:
    """Test request payment functionality."""

    def test_request_payment_with_valid_params(self, client):
        """Test requesting payment with valid parameters."""
        expected_response = {
            "status": "success",
            "transaction_id": "txn_123",
            "reference": "ORDER123",
        }

        with requests_mock.Mocker() as m:
            m.post(
                "https://payments.relworx.com/api/request_payment",
                json=expected_response,
                status_code=201,
            )

            response = client.request_payment(
                phone_number="256701234567",
                amount=10000,
                currency="UGX",
                reference="ORDER123",
            )

        assert response["status"] == "success"

    def test_request_payment_with_description(self, client):
        """Test requesting payment with description."""
        expected_response = {
            "status": "success",
            "transaction_id": "txn_123",
        }

        with requests_mock.Mocker() as m:
            m.post(
                "https://payments.relworx.com/api/request_payment",
                json=expected_response,
                status_code=201,
            )

            response = client.request_payment(
                phone_number="256701234567",
                amount=10000,
                currency="UGX",
                reference="ORDER123",
                description="Payment for Order #123",
            )

        assert response["status"] == "success"


class TestSendMoney:
    """Test send money functionality."""

    def test_send_money_with_valid_params(self, client):
        """Test sending money with valid parameters."""
        expected_response = {
            "status": "success",
            "transaction_id": "txn_456",
            "reference": "SEND456",
        }

        with requests_mock.Mocker() as m:
            m.post(
                "https://payments.relworx.com/api/send_money",
                json=expected_response,
                status_code=201,
            )

            response = client.send_money(
                phone_number="256701234567",
                amount=5000,
                currency="UGX",
                reference="SEND456",
            )

        assert response["status"] == "success"


class TestExceptionHandling:
    """Test exception handling."""

    def test_authentication_error_on_401(self, client):
        """Test authentication error on 401 response."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://payments.relworx.com/api/request_payment",
                json={"message": "Unauthorized"},
                status_code=401,
            )

            with pytest.raises(AuthenticationError):
                client.request_payment(
                    phone_number="256701234567",
                    amount=10000,
                    currency="UGX",
                    reference="ORDER123",
                )

    def test_validation_error_on_400(self, client):
        """Test validation error on 400 response."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://payments.relworx.com/api/request_payment",
                json={"message": "Invalid amount"},
                status_code=400,
            )

            with pytest.raises(ValidationError):
                client.request_payment(
                    phone_number="256701234567",
                    amount=10000,
                    currency="UGX",
                    reference="ORDER123",
                )

    def test_api_error_on_500(self, client):
        """Test API error on 500 response."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://payments.relworx.com/api/request_payment",
                json={"message": "Internal server error"},
                status_code=500,
            )

            with pytest.raises(APIError):
                client.request_payment(
                    phone_number="256701234567",
                    amount=10000,
                    currency="UGX",
                    reference="ORDER123",
                )
