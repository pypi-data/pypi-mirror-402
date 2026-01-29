import pytest
import tempfile
import os
import csv
import json
from unittest.mock import patch, mock_open
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subscriptions_to_csv import fetch_exchange_rate, parse_subscription_data, write_csv_file
from subscriptions_to_csv.cli import parse_arguments


class TestParseArguments:
    """Test argument parsing functionality."""

    def test_default_arguments(self):
        """Test parsing with default arguments."""
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()
            assert args.input == 'subscriptions.txt'
            assert args.output == 'subscriptions.csv'

    def test_positional_arguments(self):
        """Test parsing with positional arguments."""
        with patch('sys.argv', ['main.py', 'input.txt', 'output.csv']):
            args = parse_arguments()
            assert args.input == 'input.txt'
            assert args.output == 'output.csv'

    def test_optional_arguments(self):
        """Test parsing with optional arguments."""
        with patch('sys.argv', ['main.py', '--input', 'custom.txt', '--output', 'result.csv']):
            args = parse_arguments()
            assert args.input == 'custom.txt'
            assert args.output == 'result.csv'


class TestFetchExchangeRate:
    """Test exchange rate fetching functionality."""

    @patch('urllib.request.urlopen')
    def test_successful_fetch(self, mock_urlopen):
        """Test successful exchange rate fetch."""
        mock_response = {
            'rates': {'EUR': 0.85}
        }

        # Mock the context manager properly
        mock_cm = mock_urlopen.return_value.__enter__.return_value
        with patch('json.load', return_value=mock_response):
            rate = fetch_exchange_rate()
            assert rate == 0.85

    @patch('urllib.request.urlopen')
    def test_fetch_failure_fallback(self, mock_urlopen):
        """Test fallback when exchange rate fetch fails."""
        mock_urlopen.side_effect = Exception("Network error")

        rate = fetch_exchange_rate()
        assert rate == 1.0


class TestParseSubscriptionData:
    """Test subscription data parsing functionality."""

    def test_parse_basic_eur_subscription(self):
        """Test parsing EUR subscription."""
        content = 'Spotify\n12.99 €'
        rate = 0.85
        subscriptions = parse_subscription_data(content, rate)

        assert len(subscriptions) == 1
        assert subscriptions[0]['Service'] == 'Spotify'
        assert subscriptions[0]['Price'] == '12.99'
        assert subscriptions[0]['Currency'] == 'EUR'
        assert subscriptions[0]['PriceEUR'] == '12.99'

    def test_parse_usd_subscription(self):
        """Test parsing USD subscription with conversion."""
        content = 'Service\n10.00 USD'
        rate = 0.85
        subscriptions = parse_subscription_data(content, rate)

        assert len(subscriptions) == 1
        assert subscriptions[0]['Service'] == 'Service'
        assert subscriptions[0]['Price'] == '10.00'
        assert subscriptions[0]['Currency'] == 'USD'
        assert subscriptions[0]['PriceEUR'] == '8.50'

    def test_parse_subscription_without_currency(self):
        """Test parsing subscription without explicit currency (defaults to EUR)."""
        content = 'Netflix\n19.99'
        rate = 0.85
        subscriptions = parse_subscription_data(content, rate)

        assert len(subscriptions) == 1
        assert subscriptions[0]['Currency'] == 'EUR'

    def test_parse_multiple_subscriptions(self):
        """Test parsing multiple subscriptions."""
        content = '''Spotify
12.99 €
Netflix
19.99 USD
Amazon
15.00'''
        rate = 0.85
        subscriptions = parse_subscription_data(content, rate)

        assert len(subscriptions) == 3
        assert subscriptions[0]['Service'] == 'Spotify'
        assert subscriptions[1]['Service'] == 'Netflix'
        assert subscriptions[2]['Service'] == 'Amazon'

    def test_skip_invalid_price(self):
        """Test skipping subscriptions with invalid prices."""
        content = '''Valid Service
10.99 €
Invalid Service
invalid_price €'''
        rate = 0.85
        subscriptions = parse_subscription_data(content, rate)

        assert len(subscriptions) == 1
        assert subscriptions[0]['Service'] == 'Valid Service'

    def test_skip_empty_lines(self):
        """Test handling of empty or malformed lines."""
        content = '''Service1
10.99 €

Service2
15.00 USD'''
        rate = 0.85
        subscriptions = parse_subscription_data(content, rate)

        assert len(subscriptions) == 2


class TestWriteCsvFile:
    """Test CSV file writing functionality."""

    def test_write_csv_and_calculate_total(self):
        """Test writing CSV file and calculating total."""
        subscriptions = [
            {'Service': 'Spotify', 'Price': '12.99', 'Currency': '€', 'PriceEUR': '12.99'},
            {'Service': 'Netflix', 'Price': '19.99', 'Currency': 'USD', 'PriceEUR': '16.99'}
        ]

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            temp_filename = temp_file.name

        try:
            total_eur = write_csv_file(subscriptions, temp_filename)

            # Check total calculation (12.99 + 16.99 = 29.98)
            assert abs(total_eur - 29.98) < 0.01

            # Check CSV content
            with open(temp_filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)

                assert len(rows) == 2
                assert rows[0]['Service'] == 'Spotify'
                assert rows[0]['PriceEUR'] == '12.99'
                assert rows[1]['Service'] == 'Netflix'
                assert rows[1]['PriceEUR'] == '16.99'

                # Check header
                assert reader.fieldnames == ['Service', 'Price', 'Currency', 'PriceEUR']

        finally:
            os.unlink(temp_filename)

    def test_empty_subscriptions(self):
        """Test writing CSV with no subscriptions."""
        subscriptions = []

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            temp_filename = temp_file.name

        try:
            total_eur = write_csv_file(subscriptions, temp_filename)
            assert total_eur == 0.0

            # Check CSV has only header
            with open(temp_filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                assert len(rows) == 0

        finally:
            os.unlink(temp_filename)


# Integration test
def test_full_workflow():
    """Integration test for the full workflow."""
    # Create temporary input file
    input_content = """Spotify
12.99 €
Netflix
19.99 USD
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as input_file:
        input_file.write(input_content)
        input_filename = input_file.name

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as output_file:
        output_filename = output_file.name

    try:
        # Mock the exchange rate
        with patch('subscriptions_to_csv.fetch_exchange_rate', return_value=0.85):
            # Read input
            with open(input_filename, 'r') as f:
                content = f.read()

            rate = 0.85
            subscriptions = parse_subscription_data(content, rate)
            total_eur = write_csv_file(subscriptions, output_filename)

            assert len(subscriptions) == 2
            assert abs(total_eur - 29.98) < 0.01  # 12.99 + (19.99 * 0.85)

    finally:
        os.unlink(input_filename)
        os.unlink(output_filename)