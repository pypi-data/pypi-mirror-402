# Evaluator Components

This package contains the modular components for in-memory query evaluation.

## Overview

The evaluator components package provides the building blocks for evaluating TQL queries against Python dictionaries (records).

### Components

#### `field_access.py` - Field Access Utilities
Handles accessing values from nested dictionary structures:
- Dot-notation field paths (e.g., `user.profile.name`)
- Array indexing support (e.g., `items.0.price`)
- Field mapping resolution
- Type hint application
- Missing field handling

**Key Classes:**
- `FieldAccessor` - Field value extraction

**Key Methods:**
- `get_field_value()` - Extract value from nested path
- `apply_field_mapping()` - Resolve field name mappings
- `apply_type_hint()` - Convert values based on type hints

#### `value_comparison.py` - Value Comparison Operations
Implements all TQL comparison operators:
- Equality and inequality operators
- Range comparisons (>, <, >=, <=, between)
- String operations (contains, startswith, endswith)
- Pattern matching (regexp)
- List operations (in, not_in)
- Array operators (any, all, not_any, not_all)
- Network operations (cidr)
- Null handling (is, is_not)

**Key Classes:**
- `ValueComparator` - Comparison operations

**Key Methods:**
- `compare_values()` - Main comparison entry point
- `_convert_numeric()` - Smart type conversion
- `_check_cidr()` - CIDR range matching

#### `special_expressions.py` - Special Expression Evaluators
Handles geo() and nslookup() expressions:
- GeoIP lookups with enrichment
- DNS lookups and resolution
- Conditional evaluation on enriched data
- Caching of enrichment results

**Key Classes:**
- `SpecialExpressionEvaluator` - Special expression handler

**Key Methods:**
- `evaluate_geo_expr()` - Evaluate geo() expressions
- `evaluate_nslookup_expr()` - Evaluate nslookup() expressions

## Value Comparison Behavior

### Missing Fields
- Most operators return `False` for missing fields
- `not_exists` returns `True` for missing fields
- Negated string operators return `True` for missing fields

### Null Values
- `exists` returns `True` (field exists even if null)
- `is null` returns `True`
- Other operators return `False`

### Type Conversion
- Numeric strings are converted for comparison
- Boolean strings ("true"/"false") are converted
- CIDR operations validate IP addresses

### Array Handling
- `contains` checks if value is in array
- `any` checks if any element matches
- `all` checks if all elements match
- Single values are treated as one-element arrays for collection operators

## Architecture

```
TQLEvaluator (main class)
    ├── FieldAccessor (field extraction)
    ├── ValueComparator (comparisons)
    └── SpecialExpressionEvaluator (geo/nslookup)
```

## Special Features

### Sentinel Value
The evaluator uses a sentinel value `_MISSING_FIELD` to distinguish between:
- Fields that don't exist in the record
- Fields that exist but have `None` value

This distinction is important for operators like `exists` and `is null`.

### Type Hints
Support for explicit type conversion:
```
ip_field:ip cidr "10.0.0.0/8"
count:integer > 100
active:boolean = true
```

### Mutator Support
Field and value mutators are applied during evaluation:
- Field mutators transform the field value before comparison
- Value mutators transform the expected value
- Special mutators (geo, nslookup) enrich data

## Usage

Used internally by `TQLEvaluator`:

```python
from tql import TQL

tql = TQL()
data = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"}
]

# Evaluation happens internally
results = tql.query(data, "age > 27 AND city = 'NYC'")
# Returns: [{"name": "Alice", "age": 30, "city": "NYC"}]
```