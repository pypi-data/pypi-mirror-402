"""OpenSearch field mapping extraction utilities.

This module provides utilities to extract field mappings from OpenSearch indices
and convert them to the format expected by TQL for intelligent field selection.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_field_mappings_from_opensearch(
    opensearch_client: Any, index_pattern: str, tql_query: str, tql_instance: Optional[Any] = None
) -> Dict[str, Dict[str, Any]]:
    """Extract field mappings from OpenSearch for fields used in a TQL query.

    This function extracts field mappings from OpenSearch indices and converts them
    to the format expected by TQL. The output format is designed to work seamlessly
    with TQL's field mapping system and intelligent field selection.

    Args:
        opensearch_client: OpenSearch client instance
        index_pattern: Index pattern to query (e.g., 'logs-*', 'my-index')
        tql_query: TQL query string to extract field names from
        tql_instance: Optional TQL instance for field extraction (will create one if not provided)

    Returns:
        Dictionary of field mappings in TQL format. For example:
        {
            "message": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "lowercase": {"type": "text", "analyzer": "lowercase"}
                }
            },
            "level": {
                "type": "keyword"
            }
        }

    Raises:
        Exception: If OpenSearch query fails or mappings cannot be retrieved
    """
    # Import TQL here to avoid circular imports
    if tql_instance is None:
        from .core import TQL

        tql_instance = TQL()

    try:
        # Extract field names from the TQL query
        field_names = tql_instance.extract_fields(tql_query)
        logger.debug(f"Extracted {len(field_names)} fields from TQL query: {field_names}")

        if not field_names:
            logger.warning("No fields found in TQL query")
            return {}

        # Get mappings from OpenSearch
        try:
            mapping_response = opensearch_client.indices.get_mapping(index=index_pattern)
        except Exception as e:
            logger.error(f"Failed to get mappings from OpenSearch: {e}")
            raise RuntimeError(f"Failed to retrieve mappings from OpenSearch: {e}")

        # Extract and convert mappings to TQL format
        tql_mappings = _convert_opensearch_mappings_to_tql_format(mapping_response, field_names)

        logger.debug(f"Successfully converted mappings for {len(tql_mappings)} fields")
        return tql_mappings

    except Exception as e:
        logger.error(f"Error extracting field mappings: {e}")
        raise


def _convert_opensearch_mappings_to_tql_format(
    opensearch_mappings: Dict[str, Any], field_names: List[str]
) -> Dict[str, Dict[str, Any]]:
    """Convert OpenSearch mapping response to TQL's expected format.

    This function converts OpenSearch mappings to the format TQL expects,
    which is the same as the OpenSearch format but ensures proper structure.

    Args:
        opensearch_mappings: Raw OpenSearch mapping response
        field_names: List of field names to extract mappings for

    Returns:
        Dictionary of TQL-format field mappings
    """
    tql_mappings = {}

    # Collect all field mappings from all indices
    all_field_mappings: Dict[str, Any] = {}

    for _index_name, index_info in opensearch_mappings.items():
        if "mappings" in index_info and "properties" in index_info["mappings"]:
            properties = index_info["mappings"]["properties"]
            _extract_field_mappings_recursive(properties, all_field_mappings)

    # Convert requested fields to TQL format
    for field_name in field_names:
        if field_name in all_field_mappings:
            # Convert the OpenSearch mapping to TQL format
            opensearch_mapping = all_field_mappings[field_name]
            tql_mapping = _convert_opensearch_field_to_tql_format(opensearch_mapping)
            tql_mappings[field_name] = tql_mapping
        else:
            # Field not found in mappings - create a default keyword mapping
            logger.warning(f"Field '{field_name}' not found in OpenSearch mappings, using default keyword type")
            tql_mappings[field_name] = {"type": "keyword"}

    return tql_mappings


def _convert_opensearch_mappings_to_tql(
    opensearch_mappings: Dict[str, Any], field_names: List[str]
) -> Dict[str, Dict[str, Any]]:
    """Convert OpenSearch mapping response to TQL format.

    DEPRECATED: Use _convert_opensearch_mappings_to_tql_format instead.

    Args:
        opensearch_mappings: Raw OpenSearch mapping response
        field_names: List of field names to extract mappings for

    Returns:
        Dictionary of TQL-format field mappings
    """
    return _convert_opensearch_mappings_to_tql_format(opensearch_mappings, field_names)


def _extract_field_mappings_recursive(
    properties: Dict[str, Any], all_mappings: Dict[str, Any], prefix: str = ""
) -> None:
    """Recursively extract field mappings from OpenSearch properties.

    Args:
        properties: OpenSearch properties dictionary
        all_mappings: Dictionary to store extracted mappings
        prefix: Field name prefix for nested fields
    """
    for field_name, field_config in properties.items():
        full_field_name = f"{prefix}.{field_name}" if prefix else field_name

        if isinstance(field_config, dict):
            all_mappings[full_field_name] = field_config

            # Recursively process nested properties
            if "properties" in field_config:
                _extract_field_mappings_recursive(field_config["properties"], all_mappings, full_field_name)


def _convert_opensearch_field_to_tql_format(opensearch_mapping: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
    """Convert a single OpenSearch field mapping to TQL's expected format.

    This function ensures the mapping is in the exact format TQL expects.
    TQL expects the same structure as OpenSearch mappings but with clean formatting.

    Args:
        opensearch_mapping: OpenSearch mapping for the field

    Returns:
        TQL-format field mapping
    """
    # Create a clean TQL mapping structure
    tql_mapping = {}

    # Copy the type (required)
    if "type" in opensearch_mapping:
        tql_mapping["type"] = opensearch_mapping["type"]
    else:
        # Default to keyword if no type specified
        tql_mapping["type"] = "keyword"

    # Copy analyzer if present
    if "analyzer" in opensearch_mapping:
        tql_mapping["analyzer"] = opensearch_mapping["analyzer"]

    # Convert subfields (fields property)
    if "fields" in opensearch_mapping and isinstance(opensearch_mapping["fields"], dict):
        tql_mapping["fields"] = {}

        for subfield_name, subfield_config in opensearch_mapping["fields"].items():
            if isinstance(subfield_config, dict):
                # Create clean subfield mapping
                clean_subfield = {}

                # Type is required for subfields
                if "type" in subfield_config:
                    clean_subfield["type"] = subfield_config["type"]
                else:
                    clean_subfield["type"] = "keyword"  # Default

                # Copy analyzer if present
                if "analyzer" in subfield_config:
                    clean_subfield["analyzer"] = subfield_config["analyzer"]

                # Copy other relevant properties
                for prop in ["normalizer", "search_analyzer", "index", "store", "format"]:
                    if prop in subfield_config:
                        clean_subfield[prop] = subfield_config[prop]

                tql_mapping["fields"][subfield_name] = clean_subfield

    # Copy other relevant top-level properties
    for prop in ["normalizer", "search_analyzer", "index", "store", "format"]:
        if prop in opensearch_mapping:
            tql_mapping[prop] = opensearch_mapping[prop]

    return tql_mapping


def _convert_field_mapping_to_tql(field_name: str, opensearch_mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single OpenSearch field mapping to TQL format.

    DEPRECATED: Use _convert_opensearch_field_to_tql_format instead.

    Args:
        field_name: Name of the field
        opensearch_mapping: OpenSearch mapping for the field

    Returns:
        TQL-format field mapping
    """
    return _convert_opensearch_field_to_tql_format(opensearch_mapping)


def discover_field_mappings_for_query(
    opensearch_client: Any, index_pattern: str, tql_query: str, include_common_analyzers: bool = True
) -> Dict[str, Dict[str, Any]]:
    """Discover and enhance field mappings for a TQL query.

    This function not only extracts existing mappings but also suggests common
    analyzer variants that might be useful for TQL queries.

    Args:
        opensearch_client: OpenSearch client instance
        index_pattern: Index pattern to query
        tql_query: TQL query string
        include_common_analyzers: Whether to add common analyzer suggestions

    Returns:
        Enhanced field mappings with common analyzer variants
    """
    # Get base mappings
    base_mappings = extract_field_mappings_from_opensearch(opensearch_client, index_pattern, tql_query)

    if not include_common_analyzers:
        return base_mappings

    # Enhance text fields with common analyzers
    enhanced_mappings = {}

    for field_name, mapping in base_mappings.items():
        enhanced_mapping = mapping.copy()

        # For text fields, suggest common analyzer variants
        if mapping.get("type") == "text":
            if "fields" not in enhanced_mapping:
                enhanced_mapping["fields"] = {}

            # Add keyword field if not present
            if "keyword" not in enhanced_mapping["fields"]:
                enhanced_mapping["fields"]["keyword"] = {"type": "keyword"}

            # Add common text analyzers if not present
            common_analyzers = {
                "lowercase": {"type": "text", "analyzer": "lowercase"},
                "standard": {"type": "text", "analyzer": "standard"},
                "english": {"type": "text", "analyzer": "english"},
                "whitespace": {"type": "text", "analyzer": "whitespace"},
            }

            for analyzer_name, analyzer_config in common_analyzers.items():
                if analyzer_name not in enhanced_mapping["fields"]:
                    enhanced_mapping["fields"][analyzer_name] = analyzer_config

        enhanced_mappings[field_name] = enhanced_mapping

    return enhanced_mappings


def get_sample_data_from_index(opensearch_client: Any, index_pattern: str, size: int = 10) -> List[Dict[str, Any]]:
    """Get sample data from an OpenSearch index for testing TQL queries.

    Args:
        opensearch_client: OpenSearch client instance
        index_pattern: Index pattern to query
        size: Number of sample documents to retrieve

    Returns:
        List of sample documents
    """
    try:
        response = opensearch_client.search(index=index_pattern, body={"size": size, "query": {"match_all": {}}})

        documents = []
        for hit in response.get("hits", {}).get("hits", []):
            documents.append(hit.get("_source", {}))

        return documents

    except Exception as e:
        logger.error(f"Failed to get sample data: {e}")
        return []
