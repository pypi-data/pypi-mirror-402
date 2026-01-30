"""File operations for TQL.

This module handles loading data from files and saving enrichments back to files.
"""

import csv
import json
import os
from typing import Any, Dict, List

from ..exceptions import TQLExecutionError


class FileOperations:
    """Handles file-based operations for TQL."""

    def load_file(self, file_path: str) -> List[Dict[str, Any]]:  # noqa: C901
        """Load data from a file (JSON or CSV).

        Args:
            file_path: Path to the file to load

        Returns:
            List of dictionaries representing the data

        Raises:
            TQLExecutionError: If file loading fails
        """
        if not os.path.exists(file_path):
            raise TQLExecutionError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path.lower())

        try:
            if ext == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Single object, wrap in list
                        return [data]
                    elif isinstance(data, list):
                        return data
                    else:
                        raise TQLExecutionError(f"Invalid JSON format in {file_path}")
            elif ext == ".csv":
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            elif ext == ".jsonl":
                # JSON Lines format - one JSON object per line
                records = []
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:  # Skip empty lines
                            records.append(json.loads(line))
                return records
            else:
                raise TQLExecutionError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise TQLExecutionError(f"Error loading file {file_path}: {str(e)}")

    def save_enrichments_to_json(self, file_path: str, records: List[Dict[str, Any]]) -> None:
        """Save enriched records back to JSON file.

        Args:
            file_path: Path to save the file
            records: List of records to save
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    def bulk_update_opensearch(
        self, client: Any, index: str, records: List[Dict[str, Any]], id_field: str = "_id", batch_size: int = 100
    ) -> Dict[str, int]:
        """Bulk update records in OpenSearch.

        Args:
            client: OpenSearch client instance
            index: Index name
            records: Records to update
            id_field: Field containing document ID
            batch_size: Number of documents per bulk request

        Returns:
            Dictionary with update statistics
        """
        from opensearchpy.helpers import bulk as opensearch_bulk

        updated = 0
        failed = 0

        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            actions = []

            for record in batch:
                if id_field in record:
                    action = {
                        "_op_type": "update",
                        "_index": index,
                        "_id": record[id_field],
                        "doc": {k: v for k, v in record.items() if k != id_field},
                    }
                    actions.append(action)

            if actions:
                success, failures = opensearch_bulk(client, actions, raise_on_error=False)
                updated += success
                failed += len(failures)

        return {"updated": updated, "failed": failed}
