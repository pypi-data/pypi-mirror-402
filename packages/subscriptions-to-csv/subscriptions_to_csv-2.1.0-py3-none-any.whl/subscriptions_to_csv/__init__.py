"""Convert subscription lists to CSV with EUR conversion.

This package provides both a command-line tool and a Python library
for converting subscription data to CSV format with EUR conversion.
"""

from .converter import (
    convert_subscriptions,
    fetch_exchange_rate,
    parse_subscription_data,
    write_csv_file,
    SubscriptionConverter,
    SubscriptionParseError,
    ExchangeRateError,
)

__version__ = "2.1.0"
__all__ = [
    "convert_subscriptions",
    "fetch_exchange_rate",
    "parse_subscription_data",
    "write_csv_file",
    "SubscriptionConverter",
    "SubscriptionParseError",
    "ExchangeRateError",
]