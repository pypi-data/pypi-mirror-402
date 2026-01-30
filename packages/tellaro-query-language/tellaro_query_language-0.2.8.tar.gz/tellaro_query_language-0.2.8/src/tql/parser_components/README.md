# Parser Components

This package contains the modular components that make up the TQL parser.

## Overview

The parser components package splits the TQL parser functionality into focused, maintainable modules:

### Components

#### `grammar.py` - Grammar Definitions
Contains all pyparsing grammar definitions for TQL syntax, including:
- Basic tokens (identifiers, strings, numbers)
- Operators (comparison, logical, collection)
- Field specifications with type hints and mutators
- Value specifications with mutators
- Special expressions (geo, nslookup)
- Statistics expressions
- Complete TQL expression grammar

#### `ast_builder.py` - AST Construction
Handles building Abstract Syntax Tree nodes from parsed tokens:
- `extract_field_info()` - Extracts field name, type hints, and mutators
- `extract_value_info()` - Extracts values and value mutators
- Processes complex nested structures
- Handles mutator parameter parsing

#### `error_analyzer.py` - Error Analysis
Provides detailed error analysis for parse failures:
- `analyze_parse_error()` - Main error analysis entry point
- Generates helpful error messages with context
- Suggests corrections for common mistakes
- Shows error location in the original query

#### `field_extractor.py` - Field Extraction
Extracts field references from parsed AST:
- `extract_fields()` - Recursively finds all field references
- Handles all node types including special expressions
- Returns unique sorted list of fields
- Used for validation and analysis

## Usage

These components are used internally by the main `TQLParser` class. They should not be imported directly in application code.

```python
# Don't do this:
from tql.parser_components.grammar import TQLGrammar

# Do this instead:
from tql import TQL
tql = TQL()
ast = tql.parse("field = 'value'")
```

## Architecture

The parser follows a modular architecture:

```
TQLParser (main class)
    ├── TQLGrammar (grammar definitions)
    ├── ASTBuilder (AST construction)
    ├── ErrorAnalyzer (error handling)
    └── FieldExtractor (field analysis)
```

This separation allows for:
- Easier testing of individual components
- Better code organization
- Clearer separation of concerns
- Easier maintenance and updates