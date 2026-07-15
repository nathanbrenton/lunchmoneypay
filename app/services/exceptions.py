"""Domain exceptions raised by LunchMoneyPay services."""


class MerchantAlreadyExistsError(Exception):
    """Raised when a merchant name is already registered."""
