"""Command-line interface for TQL.

This module provides the CLI entry point for executing TQL queries against files
and folders with streaming support and smart output formatting.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from .core import TQL
from .exceptions import TQLError


def detect_output_format(output_path: Optional[str], explicit_format: Optional[str]) -> str:
    """Detect output format based on file extension or explicit flag.

    Args:
        output_path: Path to output file (None for stdout)
        explicit_format: Explicitly specified format

    Returns:
        Detected format ('json', 'jsonl', or 'table')
    """
    if explicit_format:
        return explicit_format

    if output_path is None:  # stdout
        return "table"

    ext = os.path.splitext(output_path)[1].lower()
    if ext == ".json":
        return "json"
    elif ext in [".jsonl", ".ndjson"]:
        return "jsonl"
    else:
        return "table"  # Default for unknown extensions


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten nested dictionary into dot-notation keys.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # For lists, convert to string representation
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def format_table(records: List[Dict[str, Any]], limit: Optional[int] = None) -> str:
    """Format records as a simple table.

    Args:
        records: List of records to format
        limit: Maximum number of records to display

    Returns:
        Formatted table string
    """
    if not records:
        return "No records found."

    # Apply limit if specified
    if limit:
        records = records[:limit]
        limited = True
    else:
        limited = False

    # Flatten all records (convert nested dicts to dot-notation)
    flattened_records = []
    for record in records:
        flattened_records.append(flatten_dict(record))

    # Get all unique keys across flattened records
    all_keys: set[str] = set()
    for record in flattened_records:
        all_keys.update(record.keys())

    # Sort keys for consistent display
    keys = sorted(all_keys)

    # Calculate column widths
    col_widths = {key: len(key) for key in keys}
    for record in flattened_records:
        for key in keys:
            value_str = str(record.get(key, ""))
            col_widths[key] = max(col_widths[key], len(value_str))

    # Build table
    lines = []

    # Header
    header = " | ".join(key.ljust(col_widths[key]) for key in keys)
    lines.append(header)
    lines.append("-" * len(header))

    # Rows
    for record in flattened_records:
        row = " | ".join(str(record.get(key, "")).ljust(col_widths[key]) for key in keys)
        lines.append(row)

    result = "\n".join(lines)

    if limited:
        result += f"\n\n... (showing {limit} of {len(records)} records)"

    return result


def format_stats(stats: Dict[str, Any]) -> str:
    """Format stats results for table output.

    Args:
        stats: Stats dictionary

    Returns:
        Formatted stats string
    """
    lines = []
    lines.append("Statistics:")
    lines.append("-" * 50)

    stats_type = stats.get("type")

    if stats_type == "simple_aggregation":
        lines.append(f"{stats['function']}({stats['field']}): {stats['value']}")

    elif stats_type == "multiple_aggregations":
        for key, value in stats["results"].items():
            lines.append(f"{key}: {value}")

    elif stats_type == "grouped_aggregation":
        group_by = stats.get("group_by", [])
        lines.append(f"Grouped by: {', '.join(group_by)}")
        lines.append("")

        for bucket in stats["results"]:
            key_str = ", ".join(f"{k}={v}" for k, v in bucket["key"].items())
            lines.append(f"  [{key_str}] (count: {bucket.get('doc_count', 0)})")

            if "aggregations" in bucket:
                for agg_key, agg_value in bucket["aggregations"].items():
                    lines.append(f"    {agg_key}: {agg_value}")
            else:
                # Single aggregation result
                for key, value in bucket.items():
                    if key not in ["key", "doc_count"]:
                        lines.append(f"    {key}: {value}")

    return "\n".join(lines)


def write_output(records: List[Dict[str, Any]], output_format: str, output_path: Optional[str], limit: Optional[int]):
    """Write records to output in specified format.

    Args:
        records: Records to write
        output_format: Format ('json', 'jsonl', 'table')
        output_path: Output file path (None for stdout)
        limit: Maximum records to output
    """
    # Apply limit if specified
    if limit and len(records) > limit:
        records = records[:limit]

    if output_format == "json":
        output = json.dumps(records, indent=2, ensure_ascii=False)
    elif output_format == "jsonl":
        output = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    else:  # table
        output = format_table(records, limit)

    # Write to file or stdout
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {output_path}")
    else:
        print(output)


def main():  # noqa: C901
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TQL - Tellaro Query Language CLI for querying structured data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query a JSON file
  tql 'status = "active"' data.json

  # Query with stats
  tql 'status = "active" | stats count() by type' data.jsonl

  # CSV with auto-detected headers
  tql 'age > 25' users.csv

  # Output to JSON file (auto-detects format from extension)
  tql 'status = 200' logs.jsonl --output results.json

  # Process folder with pattern
  tql '| stats count() by status' logs/ --pattern "*.jsonl" --recursive

  # Stdin to stdout
  cat data.jsonl | tql 'score > 90'
        """,
    )

    # Positional arguments
    parser.add_argument("query", help="TQL query string")
    parser.add_argument(
        "file_or_folder",
        nargs="?",
        help="Path to file or folder (defaults to stdin if not provided)",
    )

    # File options
    file_group = parser.add_argument_group("File Options")
    file_group.add_argument(
        "--format",
        choices=["json", "jsonl", "csv", "auto"],
        default="auto",
        help="Input file format (default: auto-detect from extension)",
    )
    file_group.add_argument(
        "--csv-delimiter",
        default=",",
        help="CSV delimiter character (default: ,)",
    )
    file_group.add_argument(
        "--csv-headers",
        help="Comma-separated CSV header names (overrides auto-detection)",
    )
    file_group.add_argument(
        "--no-header",
        action="store_true",
        help="CSV has no header row (generates column1, column2, etc.)",
    )
    file_group.add_argument(
        "--field-types",
        help='JSON string mapping field names to types (e.g., \'{"age":"integer"}\')',
    )
    file_group.add_argument(
        "--recursive",
        action="store_true",
        help="Process folders recursively",
    )
    file_group.add_argument(
        "--pattern",
        default="*",
        help="File pattern for folder processing (default: *)",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout). Format auto-detected from extension.",
    )
    output_group.add_argument(
        "--output-format",
        choices=["json", "jsonl", "table"],
        help="Output format (default: smart - table for console, matches extension for files)",
    )
    output_group.add_argument(
        "--limit",
        "-n",
        type=int,
        help="Maximum number of records to output",
    )
    output_group.add_argument(
        "--stats-only",
        action="store_true",
        help="Only output statistics, no records",
    )

    # Performance options
    perf_group = parser.add_argument_group("Performance Options")
    perf_group.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="Number of parallel workers for folder processing (default: 4)",
    )
    perf_group.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of records to sample for type inference (default: 100)",
    )

    # Misc options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with progress information",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress informational messages",
    )

    args = parser.parse_args()

    # Parse field types if provided
    field_types = None
    if args.field_types:
        try:
            field_types = json.loads(args.field_types)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON for --field-types: {e}", file=sys.stderr)
            sys.exit(1)

    # Parse CSV headers if provided
    csv_headers = None
    if args.csv_headers:
        csv_headers = [h.strip() for h in args.csv_headers.split(",")]

    # Detect output format
    output_format = detect_output_format(args.output, args.output_format)

    # Initialize TQL
    try:
        tql = TQL()

        # Determine input source
        is_folder = args.file_or_folder and os.path.isdir(args.file_or_folder)
        is_file = args.file_or_folder and os.path.isfile(args.file_or_folder)
        is_stdin = not args.file_or_folder

        if is_stdin:
            # Read from stdin
            if not args.quiet:
                print("Reading from stdin...", file=sys.stderr)

            # Read all lines from stdin and parse as JSONL
            records = []
            for line in sys.stdin:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        if not args.quiet:
                            print("Warning: Skipping invalid JSON line", file=sys.stderr)

            # Execute query
            result = tql.query(records, args.query)

            # Handle output
            if "stats" in result:
                if output_format == "table":
                    print(format_stats(result["stats"]))
                else:
                    write_output([result["stats"]], output_format, args.output, args.limit)
            elif "results" in result:
                write_output(result["results"], output_format, args.output, args.limit)
            else:
                write_output([], output_format, args.output, args.limit)

        elif is_folder:
            # Process folder
            if args.verbose:
                print(f"Processing folder: {args.file_or_folder}", file=sys.stderr)

            result = tql.query_folder(
                args.file_or_folder,
                args.query,
                pattern=args.pattern,
                input_format=args.format,
                recursive=args.recursive,
                parallel=args.parallel,
                csv_delimiter=args.csv_delimiter,
                csv_headers=csv_headers,
                no_header=args.no_header,
                field_types=field_types,
                sample_size=args.sample_size,
            )

            if args.verbose and "files_processed" in result:
                print(f"Files processed: {result['files_processed']}", file=sys.stderr)

            # Handle output
            if "stats" in result:
                if output_format == "table":
                    print(format_stats(result["stats"]))
                else:
                    write_output([result["stats"]], output_format, args.output, args.limit)
            elif "results" in result:
                if not args.stats_only:
                    write_output(result["results"], output_format, args.output, args.limit)

        elif is_file:
            # Check if query contains stats
            ast = tql.parse(args.query)
            has_stats = ast.get("type") in ["stats_expr", "query_with_stats"]

            if has_stats:
                # Use stats method
                if args.verbose:
                    print(f"Processing file with stats: {args.file_or_folder}", file=sys.stderr)

                result = tql.query_file_stats(
                    args.file_or_folder,
                    args.query,
                    input_format=args.format,
                    csv_delimiter=args.csv_delimiter,
                    csv_headers=csv_headers,
                    no_header=args.no_header,
                    field_types=field_types,
                    sample_size=args.sample_size,
                )

                # Format and output stats
                if output_format == "table":
                    print(format_stats(result))
                else:
                    write_output([result], output_format, args.output, args.limit)

            else:
                # Use streaming method for filter queries
                if args.verbose:
                    print(f"Processing file: {args.file_or_folder}", file=sys.stderr)

                records = list(
                    tql.query_file_streaming(
                        args.file_or_folder,
                        args.query,
                        input_format=args.format,
                        csv_delimiter=args.csv_delimiter,
                        csv_headers=csv_headers,
                        no_header=args.no_header,
                        field_types=field_types,
                        sample_size=args.sample_size,
                    )
                )

                if args.verbose:
                    print(f"Matched {len(records)} records", file=sys.stderr)

                write_output(records, output_format, args.output, args.limit)

        else:
            print(f"Error: {args.file_or_folder} is not a valid file or folder", file=sys.stderr)
            sys.exit(1)

    except TQLError as e:
        print(f"TQL Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
