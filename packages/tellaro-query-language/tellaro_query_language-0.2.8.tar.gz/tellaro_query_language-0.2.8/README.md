# Tellaro Query Language (TQL)

[![PyPI version](https://badge.fury.io/py/tellaro-query-language.svg)](https://badge.fury.io/py/tellaro-query-language)
[![Tests Status](./badges/test-badge.svg?dummy=8484744)](./reports/pytest/junit.xml)
[![Coverage Status](./badges/coverage-badge.svg?dummy=8484744)](./reports/coverage/index.html)
[![Flake8 Status](./badges/flake8-badge.svg?dummy=8484744)](./reports/flake8/index.html)
[![Python 3.11-3.13](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: Source Available](https://img.shields.io/badge/License-Source%20Available-blue.svg)](LICENSE)

**A flexible, human-friendly query language for searching and filtering structured data across files, databases, and search engines.**

TQL provides a unified, readable syntax for expressing complex queries that works seamlessly with:
- **Files**: Query JSON, JSONL, CSV files directly with CLI or Python API
- **OpenSearch/Elasticsearch**: Convert TQL to DSL queries automatically
- **In-Memory Data**: Filter Python dictionaries and lists
- **Statistical Analysis**: Built-in aggregations and grouping

```python
# Query JSON files directly
results = tql.query("logs.jsonl", "status = 200 AND response_time > 500")

# Query OpenSearch with automatic DSL translation
results = tql.execute_opensearch(client, "events-*",
    "user.role = 'admin' AND timestamp > '2024-01-01'")

# Aggregate data with stats
results = tql.query("sales.json", "region = 'west' | stats sum(revenue) by product")
```

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (Python package)
pip install tellaro-query-language

# Install with OpenSearch support
pip install tellaro-query-language[opensearch]

# Or install Rust CLI (300x faster for large files)
cargo install tellaro-query-language
```

### Query Files with CLI

TQL includes a blazing-fast command-line interface for querying files:

```bash
# Query JSON/JSONL files
tql 'status = "active"' users.json
tql 'age > 25 AND city = "NYC"' data.jsonl

# Query CSV files (auto-detects headers)
tql 'price > 100 AND category = "electronics"' products.csv

# Statistical aggregations
tql '| stats count() by status' events.jsonl
tql 'status = 200 | stats average(response_time) by endpoint' logs.jsonl

# Process folders recursively
tql 'level = "ERROR"' logs/ --pattern "*.jsonl" --recursive

# Pipe data from stdin
cat data.jsonl | tql 'score > 90'
```

**Performance**: The Rust CLI processes 50MB files in milliseconds vs. seconds for Python implementations.

### Query Files with Python API

```python
from tql import TQL

tql = TQL()

# Query JSON files directly
results = tql.query("data.json", "user.role = 'admin' AND status = 'active'")

# Query with field transformations
results = tql.query("logs.jsonl", "email | lowercase contains '@example.com'")

# Statistical analysis
results = tql.query("sales.json", "| stats sum(revenue), avg(price) by category")
```

### Query In-Memory Data

```python
from tql import TQL

tql = TQL()
data = [
    {'name': 'Alice', 'age': 30, 'city': 'NYC'},
    {'name': 'Bob', 'age': 25, 'city': 'LA'},
    {'name': 'Charlie', 'age': 35, 'city': 'NYC'}
]

# Simple queries
results = tql.query(data, 'age > 27')
# Returns: [{'name': 'Alice', 'age': 30, 'city': 'NYC'},
#           {'name': 'Charlie', 'age': 35, 'city': 'NYC'}]

# Logical operators
results = tql.query(data, 'age >= 30 AND city = "NYC"')
# Returns: [{'name': 'Alice', ...}, {'name': 'Charlie', ...}]

# Field transformations
results = tql.query(data, 'name | lowercase = "alice"')
```

### Query OpenSearch

```python
from opensearchpy import OpenSearch
from tql import TQL

# Initialize OpenSearch client
client = OpenSearch(
    hosts=['localhost:9200'],
    http_auth=('admin', 'admin'),
    use_ssl=True,
    verify_certs=False
)

# Initialize TQL with field mappings
mappings = {
    'user.name': {'type': 'keyword'},
    'user.email': {'type': 'text'},
    'timestamp': {'type': 'date'}
}
tql = TQL(mappings)

# Execute queries with automatic DSL translation
results = tql.execute_opensearch(
    opensearch_client=client,
    index='users-*',
    query='user.name = "admin" AND status = "active"'
)

# Complex queries with mutators and post-processing
results = tql.execute_opensearch(
    opensearch_client=client,
    index='logs-*',
    query='email | lowercase contains "@example.com" AND level = "ERROR"'
)
# TQL automatically applies post-processing for mutators
```

---

## 🎯 Core Features

### 🔍 **Unified Query Syntax**
Write one query, run it anywhere - files, OpenSearch, in-memory data:

```python
# Same query works everywhere
query = 'status = "active" AND age > 25'

# Query files
tql.query("users.json", query)

# Query OpenSearch
tql.execute_opensearch(client, "users-*", query)

# Query Python data
tql.query(python_list, query)
```

### 📁 **First-Class File Support**
Query files as easily as databases:

```python
# JSON/JSONL files
tql.query("logs.jsonl", "level = 'ERROR'")

# CSV files with automatic header detection
tql.query("products.csv", "price > 100 AND stock < 10")

# Folders with glob patterns
tql.query("logs/2024/*.jsonl", "status = 500", recursive=True)

# Streaming for large files (CLI)
$ tql 'status = 200' large-file.jsonl  # Processes without loading to memory
```

### 🔄 **25+ Field Mutators**
Transform data inline before comparison:

```python
# String transformations
'email | lowercase | trim = "admin@example.com"'
'name | uppercase = "JOHN DOE"'

# Encoding/decoding
'data | b64decode | lowercase = "secret"'
'password | md5 = "5f4dcc3b5aa765d61d8327deb882cf99"'

# Network operations
'ip | is_private = true'           # Check if IP is RFC 1918
'domain | defang = "hxxp://evil[.]com"'  # Security analysis

# DNS lookups
'hostname | nslookup contains "8.8.8.8"'

# GeoIP enrichment
'ip | geoip.country_name = "United States"'

# List operations
'scores | avg > 80'
'prices | sum between [100, 500]'
```

### 📊 **Statistical Aggregations**
Analyze data with built-in stats functions:

```python
# Simple aggregations
tql.query(data, '| stats count(), sum(revenue), avg(price)')

# Grouped analysis
tql.query(data, '| stats count() by status, region')

# Top N analysis
tql.query(data, '| stats sum(sales, top 10) by product')

# Combined filtering and stats
tql.query(data, 'region = "west" | stats avg(revenue) by category')
```

### 🔧 **OpenSearch Integration**
Seamless OpenSearch/Elasticsearch integration:

- **Automatic DSL Translation**: TQL queries → OpenSearch Query DSL
- **Smart Field Mapping**: Handles keyword vs text fields automatically
- **Post-Processing**: Apply mutators that OpenSearch can't handle
- **Pagination Support**: Handle large result sets efficiently

```python
# TQL handles field mapping automatically
mappings = {'user.email': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}}}
tql = TQL(mappings)

# Exact match uses .keyword automatically
query = 'user.email = "admin@example.com"'  # Uses user.email.keyword

# Mutators trigger post-processing when needed
query = 'user.email | lowercase contains "admin"'  # Post-processes results
```

---

## 📖 Syntax Guide

### Comparison Operators

```python
# Equality
'status = "active"'           # Exact match (alias: eq)
'status != "inactive"'        # Not equal (alias: ne)

# Numeric comparisons
'age > 25'                    # Greater than
'age >= 18'                   # Greater or equal
'age < 65'                    # Less than
'age <= 100'                  # Less or equal

# String operations
'email contains "@example.com"'      # Substring
'name startswith "John"'            # Prefix
'filename endswith ".pdf"'          # Suffix
'email regexp "^\\w+@\\w+\\.\\w+$"'  # Regex

# Range and membership
'age between [18, 65]'              # Inclusive range
'status in ["active", "pending"]'   # Value in list
'priority range [1, 5]'             # Alias for between

# Existence checks
'field exists'                      # Field is present
'field not exists'                  # Field is missing
'field is null'                     # Field is null
'field is not null'                 # Field is not null

# Network operations
'ip cidr "192.168.0.0/16"'          # IP in CIDR range
```

### Logical Operators

```python
# AND (all conditions must be true)
'age > 25 AND city = "NYC"'
'status = "active" AND role in ["admin", "moderator"]'

# OR (any condition must be true)
'city = "NYC" OR city = "LA"'
'status = "admin" OR role = "superuser"'

# NOT (negates condition)
'NOT (age < 18)'
'NOT status = "deleted"'

# Complex expressions with parentheses
'(age > 25 AND city = "NYC") OR (status = "vip" AND score > 90)'
```

### Collection Operators

```python
# ANY - at least one array element matches
'ANY tags = "premium"'
'ANY user.roles = "admin"'

# ALL - every array element matches
'ALL scores >= 80'
'ALL status = "active"'

# NONE - no array elements match
'NONE flags = "spam"'
'NONE violations.severity = "critical"'
```

### Nested Field Access

```python
# Dot notation for nested objects
'user.profile.email contains "@example.com"'
'metadata.tags.priority = "high"'

# Array indexing
'tags[0] = "urgent"'
'history[5].status = "completed"'
```

### Field Mutators Reference

#### **String Mutators**
- `lowercase`, `uppercase` - Case conversion
- `trim` - Remove whitespace
- `split(delimiter)` - Split string into array
- `length` - Get string length
- `replace(old, new)` - Replace substring

#### **Encoding Mutators**
- `b64encode`, `b64decode` - Base64 encoding/decoding
- `urldecode` - URL decode
- `hexencode`, `hexdecode` - Hex encoding/decoding
- `md5`, `sha256` - Cryptographic hashing

#### **Network/Security Mutators**
- `refang` - Convert defanged indicators (hxxp → http)
- `defang` - Defang URLs for safe display
- `is_private` - Check if IP is private (RFC 1918)
- `is_global` - Check if IP is globally routable

#### **DNS Mutators**
- `nslookup` - Resolve hostname to IP addresses

#### **GeoIP Mutators**
- `geoip` - Enrich IP with geolocation data
- Returns: `geo.country_name`, `geo.city_name`, `geo.location`, `geo.continent_code`, etc.

#### **List Mutators**
- `any`, `all` - Boolean aggregations
- `avg`, `average` - Calculate mean
- `sum` - Calculate sum
- `min`, `max` - Find min/max values

---

## 📊 Statistical Aggregations

TQL includes a powerful stats engine for data analysis:

### Available Functions

```python
# Counting
'| stats count()'              # Count all records
'| stats count(field)'         # Count non-null values
'| stats unique_count(field)'  # Count distinct values

# Numeric aggregations
'| stats sum(revenue)'         # Calculate sum
'| stats avg(price)'           # Calculate average (aliases: average, mean)
'| stats min(age), max(age)'   # Find min/max values
'| stats median(score)'        # Calculate median

# Statistical measures
'| stats std(values)'          # Standard deviation (aliases: stdev)
'| stats percentile(score, 95)' # Calculate percentile

# Value extraction
'| stats values(category)'     # Get unique values
```

### Grouping and Top N

```python
# Group by single field
'| stats count() by status'

# Group by multiple fields
'| stats sum(revenue) by region, category'

# Top N analysis
'| stats sum(sales, top 10) by product'

# Multiple aggregations
'| stats count(), sum(revenue), avg(price) by status'
```

### Combined Filtering and Stats

```python
# Filter then aggregate
'status = "success" AND region = "west" | stats avg(revenue) by category'

# Complex analytics
'timestamp > "2024-01-01" | stats count(), sum(bytes), avg(response_time) by endpoint'
```

---

## 🔌 OpenSearch Integration Guide

### Setup

```python
from opensearchpy import OpenSearch
from tql import TQL

# Create OpenSearch client
client = OpenSearch(
    hosts=['localhost:9200'],
    http_auth=('admin', 'admin'),
    use_ssl=True,
    verify_certs=False
)

# Get index mappings
response = client.indices.get_mapping(index='users-*')
mappings = response['users-2024']['mappings']['properties']

# Initialize TQL with mappings
tql = TQL(mappings)
```

### Query Translation

TQL automatically translates queries to OpenSearch DSL:

```python
# TQL Query
query = 'age > 25 AND status = "active"'

# Translates to OpenSearch DSL:
{
    "query": {
        "bool": {
            "must": [
                {"range": {"age": {"gt": 25}}},
                {"term": {"status.keyword": "active"}}
            ]
        }
    }
}

# Execute seamlessly
results = tql.execute_opensearch(client, 'users-*', query)
```

### Field Mapping Intelligence

TQL automatically handles field types:

```python
# Text field with keyword subfield
mappings = {
    'email': {
        'type': 'text',
        'fields': {
            'keyword': {'type': 'keyword'}
        }
    }
}

# Exact match - uses .keyword automatically
'email = "admin@example.com"'  # → term query on email.keyword

# Full-text search - uses text field
'email contains "example"'      # → match query on email

# Case-insensitive - triggers post-processing
'email | lowercase = "admin@example.com"'  # → fetch + filter
```

### Post-Processing

When OpenSearch can't handle operations, TQL applies post-processing:

```python
# Mutators that require post-processing
'email | lowercase contains "admin"'    # Post-process: case conversion
'data | b64decode contains "secret"'    # Post-process: decode
'ip | geoip.country = "US"'            # Post-process: GeoIP lookup

# TQL automatically:
# 1. Executes base query in OpenSearch
# 2. Fetches results
# 3. Applies mutators in Python
# 4. Filters results
# 5. Returns final matches
```

### Query Analysis

Analyze queries before execution to understand performance implications:

```python
# Analyze query health
analysis = tql.analyze_query('email | lowercase contains "admin"', context='opensearch')

print(f"Health: {analysis['health']['status']}")  # 'fair' (post-processing)
print(f"Score: {analysis['health']['score']}")    # 85
print(f"Post-processing: {analysis['mutator_health']['requires_post_processing']}")  # True

# Recommendations for optimization
for issue in analysis['health']['issues']:
    print(f"Issue: {issue['message']}")
    print(f"Fix: {issue['recommendation']}")
```

---

## 📚 Documentation

Comprehensive documentation is available in the [docs/](./docs/) directory:

- **[Getting Started](./docs/user-guide/getting-started.md)** - Quick introduction and basic concepts
- **[Query Basics](./docs/user-guide/query-basics.md)** - Syntax fundamentals
- **[Operators Reference](./docs/user-guide/operators-reference.md)** - Complete operator guide
- **[Mutators Reference](./docs/user-guide/mutators-reference.md)** - All 25+ mutator functions
- **[OpenSearch Integration](./docs/opensearch/index.md)** - Complete OpenSearch guide
- **[Stats & Aggregations](./docs/stats/index.md)** - Statistical analysis guide
- **[API Reference](./docs/api-reference/index.md)** - Python API documentation
- **[Examples](./docs/cookbook/index.md)** - Real-world query examples

---

## ⚡ Performance

### Benchmarks

**Python Implementation:**
- In-memory queries: ~10,000 records/sec
- File parsing (JSON): ~5MB/sec
- OpenSearch queries: Limited by network latency

**Rust CLI (300x faster):**
- In-memory queries: ~3,000,000 records/sec
- File parsing (JSON): ~150MB/sec
- Large file streaming: Process 50MB in ~200ms

### Optimization Tips

```python
# Use CLI for large files (300x faster)
$ tql 'status = 200' 50MB-file.jsonl  # ✓ Fast (Rust)
$ python -m tql 'status = 200' 50MB-file.jsonl  # ✗ Slow (Python)

# Pre-compile queries for reuse
ast = tql.parse('age > 25 AND status = "active"')
results1 = tql.evaluate(ast, dataset1)
results2 = tql.evaluate(ast, dataset2)

# Use OpenSearch for large datasets
tql.execute_opensearch(client, 'huge-index-*', query)  # Leverages OpenSearch's speed

# Minimize post-processing
'email.keyword = "admin@example.com"'  # ✓ Fast (OpenSearch only)
'email | lowercase = "admin@example.com"'  # ✗ Slower (post-processing)
```

---

## 🛠️ Development

### Installation

```bash
# Clone repository
git clone https://github.com/tellaro/tellaro-query-language.git
cd tellaro-query-language

# Install with Poetry (recommended)
poetry install

# Or with pip
pip install -e .
```

### Testing

```bash
# Run all tests
poetry run tests

# Run specific test file
poetry run pytest tests/test_parser.py -v

# Run with coverage
poetry run cov

# Run integration tests (requires OpenSearch)
cp .env.example .env  # Configure OpenSearch connection
poetry run pytest tests/test_opensearch_integration.py -v
```

### Code Quality

```bash
# Format code
poetry run black .

# Type checking
poetry run mypy src

# Linting
poetry run pylint src
poetry run flake8 src

# Security checks
poetry run bandit -r src/
```

---

## 🗺️ Roadmap

### ✅ Implemented Features
- ✅ Core query engine with all operators
- ✅ 25+ field mutators (string, encoding, network, DNS, GeoIP, list)
- ✅ Statistical aggregations with grouping
- ✅ File support (JSON, JSONL, CSV)
- ✅ OpenSearch/Elasticsearch backend
- ✅ Intelligent post-processing
- ✅ Rust CLI for performance
- ✅ Mutator caching for GeoIP/DNS
- ✅ Query health analysis

### 🚧 In Progress
- 🚧 OpenSearch stats aggregation translation
- 🚧 Additional hash functions (SHA1, SHA512)
- 🚧 JSON parsing mutator
- 🚧 Timestamp conversion mutators

### 📋 Planned Features
- 📋 ElasticSearch backend support
- 📋 PostgreSQL/MySQL backends
- 📋 Query optimization engine
- 📋 Custom mutator plugins
- 📋 GraphQL-style field selection
- 📋 Parallel record evaluation
- 📋 Incremental file processing

### 🔮 Future Considerations
- 🔮 Time-series specific operators
- 🔮 Machine learning integration
- 🔮 Distributed query execution
- 🔮 Query caching layer

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./docs/developer/contributing.md) for guidelines.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`poetry run tests`)
5. Run linters (`poetry run lint`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📄 License

**Tellaro Query Language (TQL)** is **source-available** software with specific usage terms:

✅ **Permitted Uses:**
- Personal use (individual, non-commercial)
- Organizational use (within your company/organization)
- Integration into your applications and services
- Internal tools and automation

❌ **Restricted Uses:**
- Creating derivative query language products
- Commercial redistribution or resale
- Offering TQL-based commercial services to third parties
- Using source code to build competing products

For commercial licensing inquiries, contact: **support@tellaro.io**

See [LICENSE](LICENSE) for complete terms and conditions.

---

## 🔗 Related Projects

- **[TQL Rust](https://crates.io/crates/tellaro-query-language)** - High-performance Rust implementation
- **[Tellaro Platform](https://github.com/tellaro)** - Security operations platform using TQL

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/tellaro/tellaro-query-language/issues)
- **Documentation**: [Full Documentation](./docs/)
- **Examples**: [Cookbook](./docs/cookbook/)
- **Email**: support@tellaro.io

---

## 🌟 Quick Examples

### Security Log Analysis

```python
# Find high-severity events from private IPs
query = '''
    source_ip | is_private = true AND
    severity in ["high", "critical"] AND
    (ANY tags = "malware" OR url | defang contains "suspicious")
'''
results = tql.query("security-logs.jsonl", query)
```

### E-commerce Analytics

```python
# Analyze sales by region for premium products
query = '''
    product_tier = "premium" AND
    order_date > "2024-01-01" |
    stats sum(revenue), avg(order_value), count() by region
'''
results = tql.query("sales.json", query)
```

### System Monitoring

```python
# Find servers with high resource usage
query = '''
    hostname | nslookup exists AND
    (cpu_usage > 80 OR memory_usage > 90) AND
    status = "production"
'''
results = tql.execute_opensearch(client, "metrics-*", query)
```

---

**Made with ❤️ by the Tellaro Team**
