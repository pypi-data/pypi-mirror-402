# TOON Converter

**Token Optimized Object Notation** — A Python library for reducing LLM token usage by 40-60% when sending structured data.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## The Problem

When you send JSON arrays to LLMs, you repeat attribute names for every single record:

```json
[
  {"customerId": "C12345", "firstName": "John", "status": "active"},
  {"customerId": "C12346", "firstName": "Jane", "status": "active"},
  {"customerId": "C12347", "firstName": "Bob", "status": "inactive"}
]
```

The strings `"customerId"`, `"firstName"`, and `"status"` appear three times each. Every occurrence costs tokens. At enterprise scale with thousands of records, this redundancy becomes expensive.

## The Solution

TOON separates the schema from the data, declaring attribute names once:

```
@schema:customerId,firstName,status
C12345|John|active
C12346|Jane|active
C12347|Bob|inactive
```

**Result: 40-60% fewer tokens** for the same data.

## Installation

```bash
# Clone the repository
git clone https://github.com/prashantdudami/toon-converter.git
cd toon-converter

# Install in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## Quick Start

### Convert JSON to TOON

```python
from toon_converter import json_to_toon

data = [
    {"name": "John", "age": 30, "city": "NYC"},
    {"name": "Jane", "age": 25, "city": "LA"},
    {"name": "Bob", "age": 35, "city": "Chicago"},
]

toon = json_to_toon(data)
print(toon)
```

Output:
```
@schema:name,age,city
John|30|NYC
Jane|25|LA
Bob|35|Chicago
```

### Convert TOON back to JSON

```python
from toon_converter import toon_to_json

toon_string = """@schema:name,age,city
John|30|NYC
Jane|25|LA"""

data = toon_to_json(toon_string)
print(data)
# [{'name': 'John', 'age': '30', 'city': 'NYC'}, {'name': 'Jane', 'age': '25', 'city': 'LA'}]
```

## Features

### Nested Object Flattening

Nested objects are automatically flattened using dot notation:

```python
data = [{"customer": {"name": "John", "address": {"city": "NYC"}}}]
toon = json_to_toon(data)
```

Output:
```
@schema:customer.name,customer.address.city
John|NYC
```

### Array Serialization

Arrays of simple values are serialized as comma-separated strings:

```python
data = [{"tags": ["premium", "active", "verified"]}]
toon = json_to_toon(data)
```

Output:
```
@schema:tags
premium,active,verified
```

### Special Character Handling

Pipe characters in values are automatically escaped:

```python
data = [{"description": "A|B|C", "id": "1"}]
toon = json_to_toon(data)
# Values with pipes are escaped as \|
```

### Null and Empty Values

Missing or null values become empty strings:

```python
data = [
    {"name": "John", "email": "john@test.com"},
    {"name": "Jane", "email": None},
]
toon = json_to_toon(data)
```

Output:
```
@schema:name,email
John|john@test.com
Jane|
```

## Advanced Usage

### Using the TOONConverter Class

For more control, use the `TOONConverter` class directly:

```python
from toon_converter import TOONConverter

# Create converter with custom options
converter = TOONConverter(
    flatten_nested=True,    # Flatten nested objects with dot notation
    serialize_arrays=True,  # Serialize arrays as comma-separated values
)

data = [{"user": {"name": "John"}, "tags": ["a", "b"]}]
toon = converter.json_to_toon(data)
```

### Disabling Flattening

If you need to preserve nested structure as JSON strings:

```python
converter = TOONConverter(flatten_nested=False)
data = [{"user": {"name": "John", "role": "admin"}}]
toon = converter.json_to_toon(data)
# Nested object is serialized as JSON string
```

## Using TOON with LLMs

### Example: OpenAI API

```python
import openai
from toon_converter import json_to_toon

# Your data
customers = [
    {"id": "C001", "name": "Acme Corp", "status": "active", "tier": "premium"},
    {"id": "C002", "name": "TechStart", "status": "active", "tier": "basic"},
    # ... hundreds more records
]

# Convert to TOON
toon_data = json_to_toon(customers)

# Use in prompt
prompt = f"""Analyze these customer records and identify upsell opportunities.

Data format: TOON (schema on first line, pipe-delimited values)
{toon_data}

Provide your analysis:"""

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)
```

### Example: Anthropic Claude

```python
import anthropic
from toon_converter import json_to_toon

client = anthropic.Anthropic()

# Convert data to TOON
toon_data = json_to_toon(your_data)

message = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"""The following data is in TOON format (Token Optimized Object Notation).
The first line defines the schema, subsequent lines are pipe-delimited values.

{toon_data}

Summarize this data."""
    }]
)
```

## TOON Format Specification

| Element | Description |
|---------|-------------|
| `@schema:` | Schema line prefix (required) |
| `,` | Attribute separator in schema line |
| `\|` | Value delimiter in data rows |
| `\\|` | Escaped pipe character in values |
| `.` | Nested key separator (e.g., `user.name`) |
| Empty between `\|\|` | Null or empty value |

### Example

```
@schema:id,user.name,user.email,tags,status
C001|John Doe|john@example.com|premium,active|active
C002|Jane Smith||basic|pending
```

## Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=toon_converter --cov-report=term-missing
```

## Token Savings Analysis

| Records | JSON Tokens | TOON Tokens | Savings |
|---------|-------------|-------------|---------|
| 10 | ~850 | ~340 | 60% |
| 100 | ~8,500 | ~3,200 | 62% |
| 1,000 | ~85,000 | ~31,000 | 64% |

*Based on typical customer records with 8-10 attributes each.*

## When to Use TOON

✅ **Use TOON when:**
- Processing hundreds or thousands of records
- All records share the same schema
- Token costs are a significant concern
- Batch/analytical workloads (not real-time chat)
- RAG context injection

⚠️ **Consider alternatives when:**
- Under 10 records (schema overhead not justified)
- Objects have varying schemas
- Users see raw prompts/responses
- You need the model to return structured JSON

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Prashant Dudami**

- LinkedIn: [linkedin.com/in/prashantdudami](https://linkedin.com/in/prashantdudami)
- GitHub: [github.com/prashantdudami](https://github.com/prashantdudami)

---

*TOON was developed as part of research into token-efficient data representation for enterprise LLM systems.*
