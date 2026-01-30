# Core Components

This package contains the modular components that implement TQL's core functionality.

## Overview

The core components package splits the TQL core functionality into specialized modules:

### Components

#### `opensearch_operations.py` - OpenSearch Operations
Handles all OpenSearch-specific functionality:
- Query conversion to OpenSearch DSL
- Query execution against OpenSearch clusters
- Mutator analysis and optimization
- Phase 1/Phase 2 query splitting for optimal performance
- Result post-processing

**Key Methods:**
- `to_opensearch()` - Convert TQL to OpenSearch query
- `execute_opensearch()` - Execute query and return results
- `analyze_opensearch_query()` - Analyze query optimization opportunities (internal use)

#### `file_operations.py` - File I/O Operations
Manages file loading and saving:
- JSON file support with pretty printing
- CSV file support (read-only)
- Enrichment saving back to source files
- Automatic file type detection

**Key Methods:**
- `load_file()` - Load data from JSON/CSV files
- `save_enrichments_to_json()` - Save enriched data back to JSON

#### `stats_operations.py` - Statistics Operations
Implements statistical aggregations:
- Aggregation functions (count, sum, avg, min, max, etc.)
- Group-by operations
- Combined filter and stats queries
- Stats query analysis

**Key Methods:**
- `stats()` - Execute stats-only queries
- `query_stats()` - Execute combined filter + stats queries
- `analyze_stats_query()` - Analyze stats query for issues

#### `validation_operations.py` - Query Validation
Provides comprehensive query validation:
- Syntax validation via parsing
- Field name validation against mappings
- Type compatibility checking
- Performance issue detection
- Query complexity analysis

**Key Methods:**
- `validate()` - Validate query syntax and fields
- `check_type_compatibility()` - Verify operator/field type compatibility
- `check_performance_issues()` - Identify potential performance problems

## Usage

These components are used internally by the main `TQL` class. They should not be imported directly:

```python
# Don't do this:
from tql.core_components.opensearch_operations import OpenSearchOperations

# Do this instead:
from tql import TQL
tql = TQL()
results = tql.execute_opensearch("status = 'active'", index="logs")
```

## Architecture

The core follows a modular architecture:

```
TQL (main class)
    ├── OpenSearchOperations (OpenSearch integration)
    ├── FileOperations (file I/O)
    ├── StatsOperations (aggregations)
    └── ValidationOperations (validation)
```

## Design Principles

1. **Separation of Concerns**: Each component handles a specific domain
2. **Dependency Injection**: Components receive dependencies via constructor
3. **Stateless Operations**: Methods are mostly stateless for better testability
4. **Error Propagation**: Components raise specific TQL exceptions
5. **Type Safety**: Full type hints for better IDE support