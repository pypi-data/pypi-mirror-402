"""Convert subscription lists to CSV with EUR conversion."""

import json
import urllib.request
import csv
from typing import List, Dict, Union, Optional, Tuple


class SubscriptionParseError(Exception):
    """Exception raised when subscription data cannot be parsed."""
    pass


class ExchangeRateError(Exception):
    """Exception raised when exchange rate cannot be fetched."""
    pass


def fetch_exchange_rate() -> float:
    """Fetch USD to EUR exchange rate from API.

    Returns:
        Exchange rate as float

    Note:
        Falls back to 1.0 if the API request fails
    """
    try:
        with urllib.request.urlopen('https://api.exchangerate-api.com/v4/latest/USD') as f:
            data = json.load(f)
        return float(data['rates']['EUR'])
    except Exception:
        return 1.0  # fallback


def parse_subscription_data(content: Union[str, List[str]], rate: float) -> List[Dict[str, str]]:
    """Parse subscription data from string or list of lines into list of dictionaries.

    Args:
        content: Subscription data as string or list of lines
        rate: USD to EUR exchange rate

    Returns:
        List of subscription dictionaries with Service, Price, Currency, and PriceEUR keys

    Raises:
        SubscriptionParseError: If the content format is invalid
    """
    if isinstance(content, str):
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
    else:
        lines = [line.strip() for line in content if line.strip()]

    subscriptions = []
    for i in range(0, len(lines), 2):
        if i + 1 >= len(lines):
            break

        service = lines[i]
        price_line = lines[i + 1].lstrip('\t')
        parts = price_line.split()

        if not parts:
            continue

        price_str = parts[0].lstrip('$').lstrip('€')
        try:
            price = float(price_str)
        except ValueError:
            continue  # Skip invalid prices

        # Determine currency from the price string
        if parts[0].startswith('€') or (len(parts) > 1 and parts[1].upper() in ('EUR', '€')):
            currency = 'EUR'
        elif parts[0].startswith('$') or (len(parts) > 1 and parts[1].upper() == 'USD'):
            currency = 'USD'
        else:
            currency = parts[1] if len(parts) > 1 else 'EUR'

        if currency.upper() == 'USD':
            eur_price = price * rate
        elif currency.upper() in ('EUR', '€'):
            eur_price = price
        else:
            raise SubscriptionParseError(f"Unsupported currency '{currency}' for service '{service}'")

        subscriptions.append({
            'Service': service,
            'Price': f'{price:.2f}',
            'Currency': currency.upper(),
            'PriceEUR': f'{eur_price:.2f}'
        })

    return subscriptions


def write_csv_file(subscriptions: List[Dict[str, str]], output_file: str) -> float:
    """Write subscriptions to CSV file.

    Args:
        subscriptions: List of subscription dictionaries
        output_file: Path to output CSV file

    Returns:
        Total EUR amount
    """
    total_eur = sum(float(sub['PriceEUR']) for sub in subscriptions)
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['Service', 'Price', 'Currency', 'PriceEUR']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(subscriptions)
    return total_eur


def convert_subscriptions(
    content: Union[str, List[str]],
    output_file: Optional[str] = None,
    exchange_rate: Optional[float] = None
) -> Tuple[List[Dict[str, str]], float]:
    """Convert subscription data to CSV format with EUR conversion.

    This is the main library function for converting subscription data.

    Args:
        content: Subscription data as string or list of lines
        output_file: Optional path to write CSV file to
        exchange_rate: Optional exchange rate (will fetch if not provided)

    Returns:
        Tuple of (subscriptions_list, total_eur_amount)

    Raises:
        ExchangeRateError: If exchange rate cannot be fetched
        SubscriptionParseError: If subscription data is malformed
    """
    rate = exchange_rate if exchange_rate is not None else fetch_exchange_rate()
    subscriptions = parse_subscription_data(content, rate)

    if output_file:
        total_eur = write_csv_file(subscriptions, output_file)
    else:
        total_eur = sum(float(sub['PriceEUR']) for sub in subscriptions)

    return subscriptions, total_eur


class SubscriptionConverter:
    """Advanced converter class for subscription data processing.

    This class provides more control over the conversion process,
    allowing you to reuse exchange rates and customize behavior.
    """

    def __init__(self, exchange_rate: Optional[float] = None):
        """Initialize the converter.

        Args:
            exchange_rate: Optional exchange rate to use (will fetch if not provided)
        """
        self.exchange_rate = exchange_rate

    def set_exchange_rate(self, rate: float) -> None:
        """Set a custom exchange rate."""
        self.exchange_rate = rate

    def get_exchange_rate(self) -> float:
        """Get the current exchange rate, fetching if necessary."""
        if self.exchange_rate is None:
            self.exchange_rate = fetch_exchange_rate()
        return self.exchange_rate

    def convert(self, content: Union[str, List[str]]) -> List[Dict[str, str]]:
        """Convert subscription content to list of dictionaries.

        Args:
            content: Subscription data as string or list of lines

        Returns:
            List of subscription dictionaries
        """
        rate = self.get_exchange_rate()
        return parse_subscription_data(content, rate)

    def convert_to_csv(self, content: Union[str, List[str]], output_file: str) -> float:
        """Convert subscription content and write to CSV file.

        Args:
            content: Subscription data as string or list of lines
            output_file: Path to output CSV file

        Returns:
            Total EUR amount
        """
        subscriptions = self.convert(content)
        return write_csv_file(subscriptions, output_file)

    def convert_with_total(self, content: Union[str, List[str]]) -> Tuple[List[Dict[str, str]], float]:
        """Convert subscription content and return data with total.

        Args:
            content: Subscription data as string or list of lines

        Returns:
            Tuple of (subscriptions_list, total_eur_amount)
        """
        subscriptions = self.convert(content)
        total_eur = sum(float(sub['PriceEUR']) for sub in subscriptions)
        return subscriptions, total_eur