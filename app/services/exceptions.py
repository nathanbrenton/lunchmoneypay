"""Domain exceptions raised by LunchMoneyPay services."""


class MerchantAlreadyExistsError(Exception):
    """Raised when a merchant name is already registered."""


class MerchantNotFoundError(Exception):
    """Raised when a merchant cannot be found."""


class InvalidApiKeyError(Exception):
    """Raised when an API key is missing, malformed, or incorrect."""


class InactiveApiCredentialError(Exception):
    """Raised when an API credential is revoked or expired."""


class CustomerAlreadyExistsError(Exception):
    """Raised when a merchant reuses a customer external reference."""


class CustomerNotFoundError(Exception):
    """Raised when a customer cannot be found for a merchant."""


class PaymentIntentAlreadyExistsError(Exception):
    """Raised when a merchant reuses a payment-intent reference."""

    def __init__(self, external_reference: str) -> None:
        """Store the conflicting merchant-side reference."""

        self.external_reference = external_reference

        super().__init__(
            "A payment intent with this external reference "
            "already exists for this merchant."
        )
