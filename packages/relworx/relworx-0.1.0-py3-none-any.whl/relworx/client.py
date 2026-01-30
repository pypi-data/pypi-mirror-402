"""
Main Relworx API Client.
"""

import requests
from typing import Dict, Any, Optional

from .exceptions import AuthenticationError, ValidationError, APIError


class RelworxClient:
    """
    Relworx Payments API Client.

    Provides methods for requesting payments and sending money through
    mobile money providers in East Africa.

    Example:
        >>> client = RelworxClient(api_key="your-api-key")
        >>> response = client.request_payment(
        ...     phone_number="256701234567",
        ...     amount=10000,
        ...     currency="UGX",
        ...     reference="ORDER123"
        ... )
    """

    BASE_URL = "https://payments.relworx.com/api"

    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize the Relworx client.

        Args:
            api_key: Your Relworx API key
            timeout: Request timeout in seconds (default: 30)

        Raises:
            ValidationError: If API key is empty
        """
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("API key must be a non-empty string")

        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self) -> None:
        """Configure default headers for API requests."""
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def request_payment(
        self,
        phone_number: str,
        amount: float,
        currency: str,
        reference: str,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Request a payment from a customer.

        Args:
            phone_number: Customer's mobile money number (e.g., "256701234567")
            amount: Amount to request
            currency: Currency code (UGX, TZS, KES, RWF, USD)
            reference: Unique transaction reference
            description: Optional description of the payment
            callback_url: Optional URL for payment status callbacks
            metadata: Optional additional metadata

        Returns:
            API response with transaction details

        Raises:
            ValidationError: If validation fails
            APIError: If the API returns an error
        """
        self._validate_request_payment(phone_number, amount, currency, reference)

        payload = {
            "phone_number": phone_number,
            "amount": amount,
            "currency": currency,
            "reference": reference,
        }

        if description:
            payload["description"] = description
        if callback_url:
            payload["callback_url"] = callback_url
        if metadata:
            payload["metadata"] = metadata

        return self._post("request_payment", payload)

    def send_money(
        self,
        phone_number: str,
        amount: float,
        currency: str,
        reference: str,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send money to a customer's mobile money account.

        Args:
            phone_number: Recipient's mobile money number
            amount: Amount to send
            currency: Currency code (UGX, TZS, KES, RWF, USD)
            reference: Unique transaction reference
            reason: Optional reason for the transfer
            metadata: Optional additional metadata

        Returns:
            API response with transaction details

        Raises:
            ValidationError: If validation fails
            APIError: If the API returns an error
        """
        self._validate_send_money(phone_number, amount, currency, reference)

        payload = {
            "phone_number": phone_number,
            "amount": amount,
            "currency": currency,
            "reference": reference,
        }

        if reason:
            payload["reason"] = reason
        if metadata:
            payload["metadata"] = metadata

        return self._post("send_money", payload)

    def get_transaction_status(self, reference: str) -> Dict[str, Any]:
        """
        Get the status of a transaction.

        Args:
            reference: Transaction reference

        Returns:
            Transaction status details

        Raises:
            ValidationError: If reference is invalid
            APIError: If the API returns an error
        """
        if not reference or not isinstance(reference, str):
            raise ValidationError("Reference must be a non-empty string")

        return self._get(f"transaction/{reference}")

    def validate_payment_details(
        self,
        phone_number: str,
        currency: str,
    ) -> Dict[str, Any]:
        """
        Validate a phone number and currency combination.

        Args:
            phone_number: Phone number to validate
            currency: Currency code to validate

        Returns:
            Validation result with operator and supported status

        Raises:
            ValidationError: If inputs are invalid
            APIError: If the API returns an error
        """
        if not phone_number or not isinstance(phone_number, str):
            raise ValidationError("Phone number must be a non-empty string")
        if not currency or not isinstance(currency, str):
            raise ValidationError("Currency must be a non-empty string")

        return self._post("validate", {
            "phone_number": phone_number,
            "currency": currency,
        })

    def get_exchange_rates(self) -> Dict[str, Any]:
        """
        Get current exchange rates.

        Returns:
            Dictionary of exchange rates

        Raises:
            APIError: If the API returns an error
        """
        return self._get("rates")

    def _validate_request_payment(
        self, phone_number: str, amount: float, currency: str, reference: str
    ) -> None:
        """Validate request payment parameters."""
        if not phone_number or not isinstance(phone_number, str):
            raise ValidationError("Phone number must be a non-empty string")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValidationError("Amount must be a positive number")
        if not currency or not isinstance(currency, str):
            raise ValidationError("Currency must be a non-empty string")
        if not reference or not isinstance(reference, str):
            raise ValidationError("Reference must be a non-empty string")

    def _validate_send_money(
        self, phone_number: str, amount: float, currency: str, reference: str
    ) -> None:
        """Validate send money parameters."""
        self._validate_request_payment(phone_number, amount, currency, reference)

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the API."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            return self._handle_response(response)
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the API."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            return self._handle_response(response)
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        try:
            response_data = response.json()
        except ValueError:
            raise APIError(
                f"Invalid JSON response: {response.text}",
                status_code=response.status_code,
            )

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key or authentication failed")

        if response.status_code == 400:
            error_msg = response_data.get("message", "Bad request")
            raise ValidationError(error_msg)

        if 400 <= response.status_code < 500:
            error_msg = response_data.get("message", "Client error")
            raise APIError(error_msg, status_code=response.status_code, response_data=response_data)

        if response.status_code >= 500:
            error_msg = response_data.get("message", "Server error")
            raise APIError(error_msg, status_code=response.status_code, response_data=response_data)

        if response.status_code not in (200, 201, 202):
            raise APIError(
                f"Unexpected status code: {response.status_code}",
                status_code=response.status_code,
                response_data=response_data,
            )

        return response_data

    def close(self) -> None:
        """Close the client session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
