# Py Currency Converter

A simple Python library to convert currencies using the live exchange rates from the Frankfurter API.

## Installation

```bash
pip install cashy
```

## Usage

```python
from cashy import CurrencyConverter

converter = CurrencyConverter()

# Convert 100 USD to INR
result = converter.convert(100, 'USD', 'INR')
print(f"100 USD is {result} INR")

# Get exchange rate
rate = converter.get_exchange_rate('USD', 'INR')
print(f"Current rate from USD to INR: {rate}")
```

## Features

- Real-time exchange rates
- No API key required (uses Frankfurter API)
- Simple and easy to use
