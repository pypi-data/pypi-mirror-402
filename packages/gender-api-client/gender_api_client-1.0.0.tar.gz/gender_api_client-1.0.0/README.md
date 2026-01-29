# Gender-API.com Python Client

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/markus-perl/gender-api-client-python/actions/workflows/tests.yml/badge.svg)](https://github.com/markus-perl/gender-api-client-python/actions/workflows/tests.yml)

A modern, type-safe Python client for the [Gender-API.com](https://gender-api.com) service. Determine gender from first names, full names, or email addresses with high accuracy across 200+ countries.

## ✨ Features

- 🔍 **Name Gender Detection** - Detect gender from first names with 99%+ accuracy
- 🌍 **Country Localization** - Improve accuracy with country-specific results
- 📧 **Email Analysis** - Extract and analyze names from email addresses
- 🗺️ **Country of Origin** - Discover name origins and geographic distribution
- 📊 **Batch Processing** - Query multiple names in a single API call
- 🔒 **Type-Safe** - Full Python type hinting support with Pydantic models
- ⚡ **Modern** - Built on `requests` and `pydantic`

## 📦 Installation

Install via pip:

```bash
pip install gender-api-client
```

## 🔑 API Key

Get your free API key at: **[gender-api.com/account](https://gender-api.com/en/account)**

## 🚀 Quick Start

```python
from gender_api import Client

client = Client(api_key="your_api_key")

# Simple gender lookup
result = client.get_by_first_name("Elisabeth")

if result.result_found:
    print(result.gender)    # "female"
    print(result.accuracy)  # 99
```

## 📖 Usage Examples

### First Name with Country

For names that vary by country (e.g., "Andrea" is male in Italy, female in Germany):

```python
# In Italy, Andrea is typically male
result = client.get_by_first_name("Andrea", country="IT")
print(result.gender) # "male"

# In Germany, Andrea is typically female
result = client.get_by_first_name("Andrea", country="DE")
print(result.gender) # "female"
```

### First Name with Localization

Detect country from IP address or browser locale:

```python
# Localize by IP address
result = client.get_by_first_name("Jan", ip_address="178.27.52.144")

# Localize by browser locale
result = client.get_by_first_name("Jan", locale="de_DE")
```

### Full Name (First + Last Name Split)

The API automatically splits full names and identifies the first name:

```python
result = client.get_by_full_name("Sandra Miller")

print(result.first_name) # "Sandra"
print(result.last_name)  # "Miller"
print(result.gender)     # "female"
```

With country:

```python
result = client.get_by_full_name("Maria Garcia", country="ES")
```

### Email Address

Extract and analyze names from email addresses:

```python
result = client.get_by_email("elisabeth.smith@company.com")

print(result.gender)       # "female"
print(result.first_name)   # "Elisabeth" (extracted)
print(result.last_name)    # "Smith"
```

### Multiple Names (Batch)

Query multiple names in a single API call for efficiency:

```python
names = ["Michael", "Sarah", "Kim", "Jordan"]
results = client.get_by_multiple_names(names)

for result in results:
    print(f"{result.first_name}: {result.gender} ({result.accuracy}% confidence)")

# Output:
# Michael: male (99% confidence)
# Sarah: female (99% confidence)
# Kim: female (72% confidence)
# Jordan: male (68% confidence)
```

With country filter:

```python
results = client.get_by_multiple_names(["Andrea", "Nicola"], country="IT")
```

### Country of Origin

Discover where a name originates from:

```python
result = client.get_country_of_origin("Giuseppe")

print(result.gender) # "male"

for country in result.country_of_origin:
    print(f"{country.country_name} ({country.country}): {country.probability * 100:.0f}%")

# Output:
# Italy (IT): 89%
# Argentina (AR): 4%
# United States (US): 3%

# Get interactive map URL
print(result.country_of_origin_map_url)
```

### Account Statistics

Monitor your API usage:

```python
stats = client.get_stats()

print(stats.remaining_credits) # 4523
print(stats.is_limit_reached)  # False
```

## ⚙️ Configuration

### Custom API URL

For enterprise or on-premise installations:

```python
client = Client(api_key="your-key", api_url="https://custom-api.example.com/")
```

## 🧪 Development

### Requirements

- Python 3.7 or higher

### Setup

```bash
# Clone the repository
git clone https://github.com/gender-api/gender-api-client-python.git
cd gender-api-client-python

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
pytest
```

## 🔍 API Response Properties

### SingleNameResult

| Property | Type | Description |
|----------|------|-------------|
| `first_name` | `str` | The queried name |
| `probability` | `float` | Probability (e.g. 0.99) |
| `gender` | `str` | `"male"`, `"female"`, or `"unknown"` |
| `accuracy` | `int` | Confidence percentage (0-100) |
| `samples` | `int` | Number of data samples |
| `country` | `Optional[str]` | ISO 3166-1 country code |
| `result_found` | `bool` | Whether a gender was determined |

### StatsResult

| Property | Type | Description |
|----------|------|-------------|
| `remaining_credits` | `int` | API credits remaining |
| `is_limit_reached` | `bool` | Whether quota is exhausted |

## 🛠️ Error Handling

```python
from gender_api import Client, GenderApiError, InvalidArgumentError, ApiError

try:
    result = client.get_by_first_name("Elisabeth")
except InvalidArgumentError as e:
    # Invalid input parameters
    print(f"Invalid input: {e}")
except ApiError as e:
    # API returned an error (e.g., invalid key, limit exceeded)
    print(f"API Error {e.http_status}: {e}")
except GenderApiError as e:
    # Other library errors (e.g. network)
    print(f"Error: {e}")
```

## 📚 Resources

- **Homepage**: [gender-api.com](https://gender-api.com)
- **API Documentation**: [gender-api.com/api-docs](https://gender-api.com/en/api-docs)
- **FAQ**: [gender-api.com/faq](https://gender-api.com/en/frequently-asked-questions)
- **Error Codes**: [gender-api.com/error-codes](https://gender-api.com/en/api-docs/error-codes)
- **Support**: [gender-api.com/contact](https://gender-api.com/en/contact)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
