# ZahlWort2num (v.0.4.3)

🇩🇪 🇩🇪 🇩🇪
A small but useful package (due to shortage of/low quality support for `lang_de`) for handy conversion of German numerals (incl. ordinal numbers) written as strings to numbers.

To put it differently: _It allows reverse text normalization for numbers_.

This package might be a good complementary lib to https://github.com/savoirfairelinux/num2words

# PyPI Project Page
https://pypi.org/project/zahlwort2num/

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features-)
- [Development](#development)
- [Roadmap / Known Issues](#roadmap--known-issues)
- [Acknowledgments](#acknowledgments-)

# Installation

```bash
pip install zahlwort2num
```

# Usage

### Basic Usage

```python
import zahlwort2num as w2n
```

### Examples

```python
# Basic cardinal numbers
w2n.convert('Zweihundertfünfundzwanzig')  # => 225

# Ordinal numbers (return as string with dot)
w2n.convert('neunte')  # => '9.'

# Negative numbers
w2n.convert('minus siebenhundert Millionen achtundsiebzig')  # => -700000078

# Complex large numbers
w2n.convert('sechshundertdreiundfünfzigtausendfünfhunderteinundzwanzig')  # => 653521

# Fractions
w2n.convert('ein und zwei')  # => 0.5
```

### Command Line Usage

Use quotes around parameters containing spaces:

```bash
zahlwort2num-convert 'eine Million siebenhunderteinundzwanzig'
```

# Development

### Setup

Install development dependencies:

```bash
python3 -m pip install -r requirements.txt
```

### Testing

Run the test suite:

```bash
python3 -m unittest
```

### Linting

Run the linter:

```bash
flake8 ./zahlwort2num/*.py --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

# Documentation

*More comprehensive documentation and examples coming soon.*

# Features ✨

- **Large Numbers**: Theoretically supports numbers from 0 up to 999 × 10^27
- **Command Line Interface**: Use from terminal with `zahlwort2num-convert`
- **Ordinal Numbers**: Supports ordinal numerals (e.g., "erste", "zweite") with inflections (suffixes like 'ste', 'ten', etc.)
  - Returns strings with dots for ordinals (e.g., '15.' instead of integer)
- **Case & Whitespace Handling**: Fault-tolerant with trailing whitespaces and case variations
- **Signed Numbers**: Handles negative numbers (e.g., 'minus zehn') and negative ordinals
- **Swiss German Support**: Includes Swiss variants (e.g., "dreissig" vs "dreißig")
- **Fault Tolerance**: Handles ß → ss conversion and other common variations
- **Fraction Support**: Basic fraction conversion (e.g., "ein und zwei" → 0.5)

# Roadmap / Known Issues

- [x] ~~Make POC, functional for all common cases~~
- [x] ~~Ordinal number support~~
- [x] ~~Handle exceptions and trailing whitespaces~~
- [x] ~~Create package structure and publish to PyPI~~
- [x] ~~Command line support~~
- [x] ~~Support both direct and indirect forms (einhundert/hundert)~~
- [x] ~~Simplify/refactor POC code and improve documentation~~
- [x] ~~Add "zwo" variant support~~
- [x] ~~Add linter and test suite~~
- [x] ~~Swiss German variants~~
- [x] ~~Fault tolerance (ß → ss conversion)~~
- [x] ~~Support for scales larger than 10^60~~
- [x] ~~Ordinal numbers with large scales (e.g., "Millionste")~~
- [x] ~~Performance improvements (tail recursion, etc.)~~
- [x] ~~Better error handling and validation~~
- [x] ~~Basic fraction support~~
- [ ] More comprehensive test cases
- [ ] Extended fraction support (e.g., "drei viertel" → 0.75)
- [ ] Decimal number support (e.g., "zwei komma fünf" → 2.5)
- [ ] Austrian German variants


# Acknowledgments 🙏

Special thanks to:
- [@warichet](https://github.com/warichet) for addressing issues
- [@spatialbitz](https://github.com/spatialbitz) for providing fixes
- [@psawa](https://github.com/psawa) for adding "zwo" variant support
- All contributors and users of this package!
