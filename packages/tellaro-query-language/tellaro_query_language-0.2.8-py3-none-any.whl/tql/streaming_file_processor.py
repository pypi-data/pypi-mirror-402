"""Streaming file processor for efficient line-by-line data processing.

This module provides generator-based file processing to handle large files
with minimal memory footprint, supporting JSON, JSONL, and CSV formats.
"""

import csv
import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Generator, List, Optional, Tuple

from .exceptions import TQLExecutionError
from .field_type_inference import FieldTypeInferencer


class StreamingFileProcessor:
    """Processes files in a streaming fashion with minimal memory usage."""

    def __init__(
        self,
        sample_size: int = 100,
        csv_delimiter: str = ",",
        field_types: Optional[Dict[str, str]] = None,
        csv_headers: Optional[List[str]] = None,
        no_header: bool = False,
    ):
        """Initialize the streaming processor.

        Args:
            sample_size: Number of records to sample for type inference
            csv_delimiter: CSV delimiter character
            field_types: Manual field type mappings
            csv_headers: Manual CSV header names
            no_header: Force CSV to be treated as having no header row
        """
        self.sample_size = sample_size
        self.csv_delimiter = csv_delimiter
        self.field_types = field_types or {}
        self.csv_headers = csv_headers
        self.no_header = no_header
        self.type_inferencer = FieldTypeInferencer(sample_size=sample_size)

    def process_file(self, file_path: str, input_format: str = "auto") -> Generator[Dict[str, Any], None, None]:
        """Process a single file in streaming mode.

        Args:
            file_path: Path to file
            input_format: File format ('json', 'jsonl', 'csv', 'auto')

        Yields:
            Parsed records as dictionaries

        Raises:
            TQLExecutionError: If file processing fails
        """
        if not os.path.exists(file_path):
            raise TQLExecutionError(f"File not found: {file_path}")

        # Auto-detect format if needed
        if input_format == "auto":
            input_format = self._detect_format(file_path)

        # Route to appropriate processor
        if input_format == "json":
            yield from self._process_json_stream(file_path)
        elif input_format == "jsonl":
            yield from self._process_jsonl_stream(file_path)
        elif input_format == "csv":
            yield from self._process_csv_stream(file_path)
        else:
            raise TQLExecutionError(f"Unsupported format: {input_format}")

    def process_folder(
        self,
        folder_path: str,
        pattern: str = "*",
        input_format: str = "auto",
        recursive: bool = False,
        parallel: int = 1,
    ) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """Process multiple files in a folder.

        Args:
            folder_path: Path to folder
            pattern: Glob pattern for file matching
            input_format: File format
            recursive: Process subdirectories recursively
            parallel: Number of parallel workers (1 = sequential)

        Yields:
            Tuples of (file_path, record)

        Raises:
            TQLExecutionError: If folder processing fails
        """
        if not os.path.exists(folder_path):
            raise TQLExecutionError(f"Folder not found: {folder_path}")

        if not os.path.isdir(folder_path):
            raise TQLExecutionError(f"Not a directory: {folder_path}")

        # Build glob pattern
        if recursive:
            glob_pattern = os.path.join(folder_path, "**", pattern)
        else:
            glob_pattern = os.path.join(folder_path, pattern)

        # Get matching files
        matching_files = glob.glob(glob_pattern, recursive=recursive)
        matching_files = [f for f in matching_files if os.path.isfile(f)]

        if not matching_files:
            raise TQLExecutionError(f"No files found matching pattern: {glob_pattern}")

        if parallel <= 1:
            # Sequential processing
            for file_path in matching_files:
                for record in self.process_file(file_path, input_format):
                    yield (file_path, record)
        else:
            # Parallel processing
            yield from self._process_files_parallel(matching_files, input_format, parallel)

    def _process_files_parallel(
        self, file_paths: List[str], input_format: str, parallel: int
    ) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """Process files in parallel using ThreadPoolExecutor.

        Args:
            file_paths: List of file paths
            input_format: File format
            parallel: Number of workers

        Yields:
            Tuples of (file_path, record)
        """

        def process_single_file(file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
            """Process a single file and return results."""
            records = list(self.process_file(file_path, input_format))
            return (file_path, records)

        with ThreadPoolExecutor(max_workers=parallel) as executor:
            # Submit all files
            futures = {executor.submit(process_single_file, fp): fp for fp in file_paths}

            # Yield results as they complete
            for future in as_completed(futures):
                file_path, records = future.result()
                for record in records:
                    yield (file_path, record)

    def _detect_format(self, file_path: str) -> str:
        """Detect file format from extension.

        Args:
            file_path: Path to file

        Returns:
            Detected format ('json', 'jsonl', or 'csv')
        """
        _, ext = os.path.splitext(file_path.lower())

        if ext == ".json":
            return "json"
        elif ext in [".jsonl", ".ndjson"]:
            return "jsonl"
        elif ext == ".csv":
            return "csv"
        else:
            # Default to JSONL for unknown extensions
            return "jsonl"

    def _process_json_stream(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """Process JSON file (array format) in streaming mode.

        For large JSON arrays, this attempts to parse incrementally.
        Falls back to full load for small files.

        Args:
            file_path: Path to JSON file

        Yields:
            Parsed records
        """
        try:
            # For JSON arrays, we need to load the full file
            # TODO: Implement true streaming JSON array parser using ijson library
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                yield data
            elif isinstance(data, list):
                for record in data:
                    if isinstance(record, dict):
                        yield record
            else:
                raise TQLExecutionError(f"Invalid JSON structure in {file_path}")

        except json.JSONDecodeError as e:
            raise TQLExecutionError(f"JSON parsing error in {file_path}: {e}")
        except Exception as e:
            raise TQLExecutionError(f"Error reading {file_path}: {e}")

    def _process_jsonl_stream(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """Process JSONL file (one JSON object per line) in streaming mode.

        Args:
            file_path: Path to JSONL file

        Yields:
            Parsed records
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue  # Skip empty lines

                    try:
                        record = json.loads(line)
                        if isinstance(record, dict):
                            yield record
                    except json.JSONDecodeError as e:
                        # Log warning but continue processing
                        print(f"Warning: Invalid JSON on line {line_num} in {file_path}: {e}")
                        continue

        except Exception as e:
            raise TQLExecutionError(f"Error reading {file_path}: {e}")

    def _process_csv_stream(self, file_path: str) -> Generator[Dict[str, Any], None, None]:  # noqa: C901
        """Process CSV file in streaming mode with type inference.

        Args:
            file_path: Path to CSV file

        Yields:
            Parsed records with typed values
        """
        try:
            # First pass: determine headers and infer types
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=self.csv_delimiter)

                # Get first row
                try:
                    first_row = next(reader)
                except StopIteration:
                    return  # Empty file

                # Determine headers
                has_headers = False
                headers = None

                if self.csv_headers:
                    # Manual headers provided - first row is data
                    headers = self.csv_headers
                    has_headers = False
                elif self.no_header:
                    # No headers, generate column names
                    headers = [f"column{i + 1}" for i in range(len(first_row))]
                    has_headers = False
                else:
                    # Auto-detect headers
                    try:
                        second_row = next(reader)
                        has_headers = self.type_inferencer.detect_csv_headers(first_row, second_row)

                        if has_headers:
                            headers = first_row
                        else:
                            headers = [f"column{i + 1}" for i in range(len(first_row))]
                    except StopIteration:
                        # Only one row, treat as headers
                        headers = first_row
                        return

                # Sample data for type inference if no manual types provided
                inferred_types = self.field_types or {}
                if not self.field_types:
                    # Rewind and collect sample
                    f.seek(0)
                    reader = csv.reader(f, delimiter=self.csv_delimiter)

                    # Skip header row only if file has headers (not manual)
                    if has_headers:
                        try:
                            next(reader)
                        except StopIteration:
                            return  # Empty file with only headers

                    # Collect sample
                    sample_records = []
                    for i, row in enumerate(reader):
                        if i >= self.sample_size:
                            break
                        if len(row) == len(headers):
                            record = dict(zip(headers, row))
                            sample_records.append(record)

                    # Infer types from sample
                    if sample_records:
                        inferred_types = self.type_inferencer.infer_from_records(sample_records)

            # Second pass: process all rows with type conversion
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=self.csv_delimiter)

                # Skip header row only if file has headers (not manual)
                if has_headers:
                    try:
                        next(reader)
                    except StopIteration:
                        return  # Empty file with only headers

                # Process all rows
                for row in reader:
                    if len(row) != len(headers):
                        continue  # Skip malformed rows

                    # Convert row to dict with type conversion
                    record = {}
                    for header, value in zip(headers, row):
                        field_type = inferred_types.get(header, "string")
                        record[header] = self.type_inferencer.convert_value(value, field_type)

                    yield record

        except Exception as e:
            raise TQLExecutionError(f"Error reading CSV file {file_path}: {e}")
