"""Stripe billing utilities.

Requires the 'billing' optional dependency: pip install lightwave-core[billing]
"""

import decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from djstripe.models import Coupon, Price


def get_stripe_module():
    """
    Get the Stripe API module with the API key properly populated.

    Returns:
        The stripe module configured with the secret key from djstripe settings.
    """
    import stripe
    from djstripe.settings import djstripe_settings

    stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY
    return stripe


def create_stripe_api_keys_if_necessary() -> bool:
    """
    Create Stripe API keys in djstripe if they don't exist.

    Returns:
        True if keys were created, False if they already existed.
    """
    from djstripe.models import APIKey
    from djstripe.settings import djstripe_settings

    key, created = APIKey.objects.get_or_create_by_api_key(djstripe_settings.STRIPE_SECRET_KEY)
    return created


def get_discounted_price(amount: decimal.Decimal, coupon: "Coupon") -> decimal.Decimal:
    """
    Calculate the discounted price after applying a coupon.

    Args:
        amount: The original price in cents
        coupon: A djstripe Coupon object

    Returns:
        The discounted price in cents
    """
    if coupon.amount_off:
        return max(amount - (100 * coupon.amount_off), decimal.Decimal(0))
    elif coupon.percent_off:
        return amount * (1 - (coupon.percent_off / 100))
    return amount


def get_friendly_currency_amount(price: "Price", currency: str = None) -> str:
    """
    Get a formatted price string with currency symbol.

    Args:
        price: A djstripe Price object
        currency: Optional currency code (defaults to price's currency)

    Returns:
        Formatted price string like "$9.99" or "9.99 EUR"
    """
    if not currency:
        currency = price.currency
    if currency != price.currency:
        amount = get_price_for_secondary_currency(price, currency)
    elif price.unit_amount_decimal is None:
        return "Unknown"
    else:
        amount = price.unit_amount_decimal
    return get_price_display_with_currency(amount / 100, currency)


def get_price_for_secondary_currency(price: "Price", currency: str) -> int:
    """
    Get the price amount for a secondary currency via Stripe API.

    Note: This hits the Stripe API because djstripe doesn't store currency options.

    Args:
        price: A djstripe Price object
        currency: The currency code to get the price for

    Returns:
        The price amount in the smallest currency unit (cents)
    """
    stripe_price = get_stripe_module().Price.retrieve(price.id, expand=["currency_options"])
    unit_amount_decimal = stripe_price.currency_options[currency]["unit_amount_decimal"]
    return int(float(unit_amount_decimal))


def get_price_display_with_currency(amount: float, currency: str) -> str:
    """
    Format a price amount with its currency symbol or code.

    Args:
        amount: The price amount (not in cents)
        currency: The currency code

    Returns:
        Formatted string like "$9.99" or "9.99 EUR"
    """
    from djstripe.utils import CURRENCY_SIGILS

    currency = currency.upper()
    sigil = CURRENCY_SIGILS.get(currency, "")
    if sigil:
        return f"{sigil}{amount:.2f}"
    return f"{amount:.2f} {currency}"
