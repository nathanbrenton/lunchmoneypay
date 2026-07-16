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


class PaymentMethodNotFoundError(Exception):
    """Raised when a payment method cannot be found for a merchant."""


class PaymentIntentAlreadyExistsError(Exception):
    """Raised when a merchant reuses a payment-intent reference."""

    def __init__(self, external_reference: str) -> None:
        """Store the conflicting merchant-side reference."""

        self.external_reference = external_reference

        super().__init__(
            "A payment intent with this external reference "
            "already exists for this merchant."
        )


class PaymentIntentNotFoundError(Exception):
    """Raised when a payment intent cannot be found for a merchant."""


class PaymentIntentInvalidStateError(Exception):
    """Raised when a payment intent cannot perform the requested transition."""

    def __init__(
        self,
        operation: str,
        current_status: str,
    ) -> None:
        """Store the operation and state that blocked the transition."""

        self.operation = operation
        self.current_status = current_status

        super().__init__(
            f"Payment intent cannot be {operation} from status: {current_status}."
        )


class PaymentMethodCustomerMismatchError(Exception):
    """Raised when a payment method belongs to a different customer."""


class PaymentMethodInactiveError(Exception):
    """Raised when an inactive payment method cannot be used."""


class PaymentMethodRequiredError(Exception):
    """Raised when confirmation requires an attached payment method."""
