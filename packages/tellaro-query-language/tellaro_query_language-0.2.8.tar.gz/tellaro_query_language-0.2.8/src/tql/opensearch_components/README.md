# OpenSearch Components

This package contains the modular components for OpenSearch backend integration.

## Overview

The OpenSearch components package provides intelligent query conversion from TQL to OpenSearch Query DSL with field-aware optimizations.

### Components

#### `field_mapping.py` - Field Mapping Logic
Manages intelligent field selection based on field types and operators:
- Supports multiple mapping formats (simple, intelligent, OpenSearch-style)
- Automatic field variant selection (keyword vs text fields)
- Operator compatibility validation
- Analyzer-aware field selection

**Key Classes:**
- `FieldMapping` - Represents field mapping configuration

**Key Methods:**
- `get_field_for_operator()` - Select optimal field variant for operator
- `validate_operator_for_field_type()` - Check operator/field compatibility
- `needs_wildcard_conversion()` - Determine if wildcard conversion needed

#### `query_converter.py` - Query Conversion
Converts TQL AST to OpenSearch Query DSL:
- Handles all TQL operators and expressions
- Intelligent query generation based on field types
- Post-processing detection for complex operations
- Special handling for array operators (ANY, ALL)

**Key Classes:**
- `QueryConverter` - Main conversion engine

**Key Methods:**
- `convert_node()` - Convert AST node to OpenSearch query
- `_convert_comparison()` - Handle comparison operations
- `_convert_logical_op()` - Handle AND/OR operations
- `_convert_geo_expr()` - Handle geo expressions

#### `lucene_converter.py` - Lucene Query Conversion
Converts TQL AST to Lucene query strings:
- Alternative query format for Lucene-based systems
- Proper escaping of special characters
- Support for all TQL operators
- Field name resolution

**Key Classes:**
- `LuceneConverter` - Lucene string converter

**Key Methods:**
- `convert_lucene()` - Convert AST to Lucene query string
- `_escape_lucene_value()` - Escape special characters

## Field Mapping Formats

### Simple Mapping
```python
field_mappings = {
    "src_ip": "source.ip",  # Simple rename
    "status": "event.status"
}
```

### Type Specification
```python
field_mappings = {
    "ip_address": "ip",      # Field type
    "user_id": "keyword",
    "score": "float"
}
```

### Intelligent Mapping
```python
field_mappings = {
    "message": {
        "message": "keyword",
        "message.text": {"type": "text", "analyzer": "standard"},
        "message.english": {"type": "text", "analyzer": "english"}
    }
}
```

### OpenSearch-Style Mapping
```python
field_mappings = {
    "title": {
        "type": "text",
        "fields": {
            "keyword": {"type": "keyword"},
            "autocomplete": {"type": "text", "analyzer": "autocomplete"}
        }
    }
}
```

## Operator Field Selection

The system automatically selects the appropriate field variant based on the operator:

| Operator Type | Preferred Field | Example |
|--------------|-----------------|---------|
| Exact match (=, !=) | keyword | `title.keyword` |
| Text search (contains) | text | `title` or `title.text` |
| Wildcard (startswith) | keyword | `title.keyword` |
| Range (>, <) | numeric/keyword | `price` or `timestamp` |
| CIDR | ip/keyword | `source.ip` |

## Usage

Used internally by `OpenSearchBackend`:

```python
from tql import TQL

tql = TQL(field_mappings={
    "message": {
        "message": "keyword",
        "message.text": "text"
    }
})

# Automatically uses message.text for text search
query = tql.to_opensearch("message contains 'error'")

# Automatically uses message (keyword) for exact match
query = tql.to_opensearch("message = 'ERROR: Failed'")
```