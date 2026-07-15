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
