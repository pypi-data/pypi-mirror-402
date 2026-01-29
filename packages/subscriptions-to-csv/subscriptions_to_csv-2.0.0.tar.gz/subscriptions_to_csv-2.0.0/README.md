# Subscriptions to CSV

A Python package built as a Nix flake utility that provides both CLI and library functionality to convert subscription lists into CSV files with EUR conversions and totals. Includes comprehensive type hints, error handling, and a full test suite.

## Description

This tool processes subscription data (from files or strings) containing service names and prices, generates CSV output with columns for Service, Price, Currency, and Price in EUR (with automatic USD to EUR conversion), and calculates total sums in EUR.

Available as both:
- **Command-line tool**: Process files directly from the terminal
- **Python library**: Import and use programmatically in your applications

The project includes comprehensive unit tests covering all major functionality and supports PyPI distribution.

## Installation

### Option 1: PyPI (Library + CLI)

```bash
pip install subscriptions-to-csv
```

This installs both the command-line tool and Python library.

### Option 2: Nix Flake (Development/Direct Usage)

Ensure you have Nix installed with flakes enabled.

#### Clone the Repository

```bash
git clone https://github.com/MBanucu/subscriptions-to-csv.git
cd subscriptions-to-csv

# Allow direnv to load the .envrc file (one-time setup)
direnv allow
```

The project uses [direnv](https://direnv.net/) for automatic development environment loading. After running `direnv allow`, the Nix devShell will be automatically activated whenever you enter the directory.

#### Direct from GitHub

You can also use this flake directly from GitHub without cloning:

```bash
# Run with default files
nix run github:MBanucu/subscriptions-to-csv#subscriptions-to-csv

# Specify input and output files
nix run github:MBanucu/subscriptions-to-csv#subscriptions-to-csv path/to/input.txt path/to/output.csv

# Show help
nix run github:MBanucu/subscriptions-to-csv#subscriptions-to-csv -- --help
```

This approach allows you to use the tool immediately without downloading the source code.

**Note**: When using `nix run` directly from GitHub, use positional arguments for input/output files or the `--` separator before option flags. Both approaches work the same way. Options work normally when running locally after cloning.

## Usage

### CLI Usage

#### Basic Usage

```bash
# Enter the development shell (or use direnv for automatic loading)
nix develop

# Run the converter
subscriptions-to-csv
```

This will read `subscriptions.txt` and output `subscriptions.csv`.

**Note**: If you have direnv installed, the development shell will be automatically activated when you enter the directory, making the `nix develop` step unnecessary.

### Custom Files

```bash
# Specify input and output files (positional)
nix run .#subscriptions-to-csv path/to/input.txt path/to/output.csv

# Or using options
nix run .#subscriptions-to-csv --input path/to/input.txt --output path/to/output.csv
```

### Direct Run

```bash
nix run .#subscriptions-to-csv
```

### Help

```bash
# Show usage information
nix run .#subscriptions-to-csv -- --help
```

Note: The `--` separates nix arguments from application arguments.

## Library Usage

When installed via pip, you can use the package as a Python library:

### Basic Usage

```python
from subscriptions_to_csv import convert_subscriptions

# Convert from string data
data = """Netflix
$15.99 USD
Spotify
€9.99"""

subscriptions, total = convert_subscriptions(data)
print(f"Total: €{total:.2f}")
for sub in subscriptions:
    print(f"{sub['Service']}: {sub['Price']} {sub['Currency']} = €{sub['PriceEUR']}")
```

### Advanced Usage

```python
from subscriptions_to_csv import SubscriptionConverter, fetch_exchange_rate

# Manual control over exchange rates
converter = SubscriptionConverter()
converter.set_exchange_rate(0.85)  # Set custom rate

# Convert and get data
subscriptions = converter.convert("Netflix\n$15.99 USD")
total, count = converter.convert_with_total("Netflix\n$15.99 USD")

# Write to CSV file
converter.convert_to_csv("Netflix\n$15.99 USD", "output.csv")

# Individual functions
rate = fetch_exchange_rate()
```

## Input Format

The input file should contain subscription data in the following format:

```
Service Name
	Price Currency
Service Name
	Price Currency
```

Example:

```
Spotify
	12.99 €
Netflix
	19.99 €
GutHub Copilot Pro
	$10.00 USD
```

Supported currencies: € (Euro), USD (automatically converted to EUR).

## Output

The output CSV contains:

- **Service**: The subscription name
- **Price**: The original price
- **Currency**: The original currency
- **PriceEUR**: The price in EUR (converted if necessary)

Plus a total sum in EUR printed to the console.

Example output:

```
Service,Price,Currency,PriceEUR
Spotify,12.99,€,12.99
Netflix,19.99,€,19.99
GutHub Copilot Pro,10.00,USD,8.62
Total in EUR: 41.60
```

## Configuration

- **Input file**: Default `subscriptions.txt`, can be overridden with `--input` or positional argument
- **Output file**: Default `subscriptions.csv`, can be overridden with `--output` or positional argument
- **Exchange rate**: Automatically fetched from exchangerate-api.com
- **Fallback**: If API fails, uses rate 1.0

## Test Coverage

The project includes comprehensive unit tests covering:
- Command-line argument parsing (default, positional, optional)
- Exchange rate API fetching with fallback behavior
- Subscription data parsing and currency conversion
- CSV file generation and total calculations
- Integration testing of the full workflow

## Requirements

### CLI Usage
- Nix with flakes support (for nix-based installation)
- Internet connection for exchange rate fetching

### Library Usage
- Python 3.6+ (3.13 recommended)
- pip for installation
- Internet connection for exchange rate fetching

## Development

### Project Structure

The project is structured as a proper Python package:

- `flake.nix`: Nix flake configuration for multi-platform builds
- `flake.lock`: Nix flake lock file
- `.envrc`: Direnv configuration for automatic devShell loading
- `pyproject.toml`: Python package configuration and build system
- `subscriptions_to_csv/`: Main Python package
  - `__init__.py`: Package initialization and exports
  - `converter.py`: Core conversion functions and classes
  - `cli.py`: Command-line interface
- `tests/test_main.py`: Comprehensive unit test suite

### Building

Build the Python package:

```bash
nix build
```

This creates a proper Python package using `buildPythonPackage` that can be installed and distributed.

### Testing

Run the comprehensive test suite including CLI integration tests:

```bash
# Run unit tests (direnv automatically loads environment)
pytest

# Or manually enter devShell and run tests
nix develop --command pytest

# Run flake checks (includes CLI functionality tests)
nix flake check

# Run specific flake checks
nix build .#checks.x86_64-linux.help-test
nix build .#checks.x86_64-linux.basic-test
nix build .#checks.x86_64-linux.named-args-test
```

The flake checks verify that:
- The `--help` command works correctly
- Basic functionality with sample data works
- Positional and named arguments function properly

### Testing

```bash
# Run the test suite (environment loads automatically with direnv)
pytest

# Or enter devShell manually
nix develop
pytest

# Run specific tests
pytest tests/test_main.py
pytest -k "parse"  # Run tests matching pattern

# Manual testing - Run with defaults
nix run .#subscriptions-to-csv

# Test CLI options
nix run .#subscriptions-to-csv -- --help

# Check the output CSV and total
```

### Release Process

The project uses automated semantic versioning with cutting-edge tooling. When you push commits to the `main` branch:

1. **Conventional commits** trigger automatic version analysis
2. **Semantic-release v25.0.2** determines version bumps and generates changelogs
3. **GitHub Actions v6.0.0** handles the complete release pipeline
4. **Version files** are automatically updated and committed
5. **PyPI publishing** via trusted publisher authentication

**Example workflow**:
```bash
# Make changes
git add .
git commit -m "feat: add new export format"

# Push to main - triggers automated release (13-16 seconds)
git push origin main
```

**Tools Used**:
- **semantic-release**: v25.0.2 (latest stable)
- **GitHub Action**: cycjimmy/semantic-release-action v6.0.0
- **Node.js**: 24+ compatible
- **Plugins**: changelog, git (optimized for Python projects)

### Code Style

See AGENTS.md for detailed coding guidelines.

## Releases

This project uses automated semantic versioning and publishing with **semantic-release v25.0.2** and **cycjimmy/semantic-release-action v6.0.0**:

🎉 **Fully automated release system now active!**

### Automated Releases
- **Trigger**: Push to `main` branch with conventional commits
- **Versioning**: Automatic based on commit types (`feat:`, `fix:`, etc.)
- **Publishing**: Automatic PyPI publishing via trusted publisher
- **Changelog**: Automatically generated from commit messages
- **Performance**: 13-16 second release cycles
- **Compatibility**: Latest Node.js 24 and plugin ecosystem support

### Commit Types & Releases

| Commit Type | Release Type | Version Bump | Example |
|-------------|--------------|--------------|---------|
| `fix:` | Patch | 0.0.1 | `fix: handle empty files` |
| `feat:` | Minor | 0.1.0 | `feat: add export formats` |
| `feat!:` or `BREAKING CHANGE:` | Major | 1.0.0 | `feat!: redesign API` |
| `docs:`, `refactor:`, `test:`, `chore:` | No release | - | `docs: update README` |

### Manual Releases
For special cases, create releases manually:
```bash
gh release create v1.2.3 --generate-notes
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Run tests: `pytest` (direnv automatically loads the environment)
5. Test CLI: `nix run .#subscriptions-to-csv -- --help`
6. Test library: `python3 -c "from subscriptions_to_csv import convert_subscriptions; print('Library works')"`
7. Submit a pull request

## License

This project is open source. Please check the license file if present.