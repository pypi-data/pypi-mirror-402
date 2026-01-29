"""Command-line interface for subscription-to-csv converter."""

import sys
import argparse
from pathlib import Path
from .converter import convert_subscriptions, ExchangeRateError, SubscriptionParseError


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Convert subscription list to CSV with EUR conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Input File Format:
Each subscription consists of 2 lines:
  Line 1: Service name (e.g., "Netflix")
  Line 2: Price with currency, optionally preceded by tabs/spaces (e.g., "$15.99 USD" or "€9.99")

Example input file format:
Netflix
\t12.99 €
Spotify
\t9.99 €

Supported currencies: USD ($), EUR (€)
All prices are converted to EUR in the output CSV.

Examples:
  subscriptions-to-csv subscriptions.txt output.csv
  subscriptions-to-csv --input subscriptions.txt --output output.csv
  subscriptions-to-csv  # uses default files
        """
    )
    parser.add_argument('input_pos', nargs='?', help='Input file containing subscriptions')
    parser.add_argument('output_pos', nargs='?', help='Output CSV file')
    parser.add_argument('--input', '-i', help='Input file containing subscriptions')
    parser.add_argument('--output', '-o', help='Output CSV file')
    args = parser.parse_args()

    # Use optional args if provided, otherwise positional, otherwise defaults
    args.input = args.input or args.input_pos or 'subscriptions.txt'
    args.output = args.output or args.output_pos or 'subscriptions.csv'

    return args


def print_summary(output_file: str, subscriptions: list, total_eur: float):
    """Print summary of the conversion."""
    print(f'Created {output_file}')
    print('First few lines:')

    # Show header and first few rows
    if subscriptions:
        print('Service,Price,Currency,PriceEUR')
        for sub in subscriptions[:3]:  # Show first 3 subscriptions
            print(f"{sub['Service']},{sub['Price']},{sub['Currency']},{sub['PriceEUR']}")
        if len(subscriptions) > 3:
            print('...')

    print(f'Total in EUR: {total_eur:.2f}')


def main():
    """Main function to run the subscription converter CLI."""
    args = parse_arguments()

    try:
        # Check if input file exists
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file '{args.input}' does not exist", file=sys.stderr)
            sys.exit(1)

        # Read input file
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()

        # Convert subscriptions
        subscriptions, total_eur = convert_subscriptions(content, args.output)

        # Print summary
        print_summary(args.output, subscriptions, total_eur)

    except ExchangeRateError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except SubscriptionParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()