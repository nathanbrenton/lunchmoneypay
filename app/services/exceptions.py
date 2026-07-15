"""Domain exceptions raised by LunchMoneyPay services."""


class MerchantAlreadyExistsError(Exception):
    """Raised when a merchant name is already registered."""


class MerchantNotFoundError(Exception):
    """Raised when a merchant cannot be found."""
