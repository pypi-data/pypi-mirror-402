"""
Mutators package for TQL.

This module maintains backward compatibility while organizing mutators into logical groups.
"""

import builtins
from typing import Any, Dict, List, Optional

# Import cache infrastructure
from ..cache import CacheManager, LocalCacheManager, RedisCacheManager

# Import all mutator classes
from .base import BaseMutator, append_to_result
from .dns import NSLookupMutator
from .encoding import Base64DecodeMutator, Base64EncodeMutator, URLDecodeMutator
from .geo import GeoIPLookupMutator, GeoIPResolver
from .list import (
    AllMutator,
    AnyMutator,
    AverageMutator,
    AvgMutator,
    MaxMutator,
    MinMutator,
    SumMutator,
)
from .network import IsGlobalMutator, IsPrivateMutator
from .security import DefangMutator, RefangMutator
from .string import LengthMutator, LowercaseMutator, ReplaceMutator, SplitMutator, TrimMutator, UppercaseMutator

# Maintain backward compatibility
__all__ = [
    # Base
    "BaseMutator",
    "append_to_result",
    # String mutators
    "LowercaseMutator",
    "UppercaseMutator",
    "TrimMutator",
    "SplitMutator",
    "LengthMutator",
    "ReplaceMutator",
    # Encoding mutators
    "Base64EncodeMutator",
    "Base64DecodeMutator",
    "URLDecodeMutator",
    # Security mutators
    "RefangMutator",
    "DefangMutator",
    # Network mutators
    "IsPrivateMutator",
    "IsGlobalMutator",
    # DNS mutator
    "NSLookupMutator",
    # GeoIP mutator
    "GeoIPLookupMutator",
    "GeoIPResolver",
    # List mutators
    "AnyMutator",
    "AllMutator",
    "AvgMutator",
    "AverageMutator",
    "SumMutator",
    "MaxMutator",
    "MinMutator",
    # Cache
    "CacheManager",
    "LocalCacheManager",
    "RedisCacheManager",
    # Factory functions
    "create_mutator",
    "apply_mutators",
    # Constants
    "ALLOWED_MUTATORS",
    "ENRICHMENT_MUTATORS",
]

# Allowed mutators dictionary (backward compatibility)
ALLOWED_MUTATORS: Dict[str, Optional[Dict[str, type]]] = {
    # String transform mutators
    "lowercase": None,
    "uppercase": None,
    "trim": None,
    "split": {"delimiter": str, "field": str},
    "length": {"field": str},
    "replace": {"find": str, "replace": str, "field": str},
    # URL and security transform mutators
    "refang": {"field": str},
    "defang": {"field": str},
    # Encoding/decoding mutators (enrichment)
    "b64encode": {"field": str},
    "b64decode": {"field": str},
    "urldecode": {"field": str},
    # List evaluation mutators
    "any": None,
    "all": None,
    "avg": None,
    "average": None,  # Alias for avg
    "max": None,
    "min": None,
    "sum": None,
    # Network mutators
    "is_private": None,
    "is_global": None,
    # Existing mutators
    "nslookup": {"servers": List, "append_field": str, "force": bool, "save": bool, "types": List, "field": str},
    "geoip_lookup": {"db_path": str, "cache": bool, "cache_ttl": int, "force": bool, "save": bool, "field": str},
    "geo": {
        "db_path": str,
        "cache": bool,
        "cache_ttl": int,
        "force": bool,
        "save": bool,
        "field": str,
    },  # Alias for geoip_lookup
}

# Define which mutators are enrichment mutators (they add data to records)
ENRICHMENT_MUTATORS = {
    "nslookup",
    "geoip_lookup",
    "geo",
    # Encoding/decoding mutators are enrichment
    "b64encode",
    "b64decode",
    "urldecode",
}


def create_mutator(name: str, params: Optional[List[List[Any]]] = None) -> BaseMutator:  # noqa: C901
    """
    Factory function to create a mutator instance.

    Args:
        name: The mutator name (case-insensitive).
        params: Optional parameters as a list of [key, value] pairs, e.g.
                [['servers', ['1.1.1.1', '1.0.0.1']], ['append_field', 'dns.answers']].

    Returns:
        An instance of the appropriate mutator.

    Raises:
        ValueError: If the mutator is not allowed or if parameters are invalid.
    """
    key = name.lower()
    if key not in ALLOWED_MUTATORS:
        raise ValueError(f"Mutator '{name}' is not allowed.")
    expected = ALLOWED_MUTATORS[key]
    params_dict = {}
    if params:
        for pair in params:
            if isinstance(pair, builtins.list) and len(pair) == 2:
                param_key, param_value = pair
                if expected is not None and param_key.lower() not in expected:
                    raise ValueError(f"Parameter '{param_key}' is not allowed for mutator '{name}'.")
                params_dict[param_key.lower()] = param_value
            else:
                raise ValueError("Parameters must be a list of [key, value] pairs.")

    # Create the appropriate mutator instance
    if key == "lowercase":
        return LowercaseMutator(params_dict)
    elif key == "uppercase":
        return UppercaseMutator(params_dict)
    elif key == "trim":
        return TrimMutator(params_dict)
    elif key == "split":
        return SplitMutator(params_dict)
    elif key == "length":
        return LengthMutator(params_dict)
    elif key == "replace":
        return ReplaceMutator(params_dict)
    elif key == "refang":
        return RefangMutator(params_dict)
    elif key == "defang":
        return DefangMutator(params_dict)
    elif key == "b64encode":
        return Base64EncodeMutator(params_dict)
    elif key == "b64decode":
        return Base64DecodeMutator(params_dict)
    elif key == "urldecode":
        return URLDecodeMutator(params_dict)
    elif key == "is_private":
        return IsPrivateMutator(params_dict)
    elif key == "is_global":
        return IsGlobalMutator(params_dict)
    elif key == "nslookup":
        return NSLookupMutator(params_dict)
    elif key in ["geoip_lookup", "geo"]:
        return GeoIPLookupMutator(params_dict)
    elif key == "any":
        return AnyMutator(params_dict)
    elif key == "all":
        return AllMutator(params_dict)
    elif key in ["avg", "average"]:
        return AvgMutator(params_dict)
    elif key == "sum":
        return SumMutator(params_dict)
    elif key == "max":
        return MaxMutator(params_dict)
    elif key == "min":
        return MinMutator(params_dict)
    else:
        # For now, return a base mutator for unimplemented mutators
        # This will be replaced as we implement more mutators
        return BaseMutator(params_dict)


def apply_mutators(value: Any, mutators: List[Dict[str, Any]], field_name: str, record: Dict[str, Any]) -> Any:
    """
    Apply a sequence of mutators to a value.

    Args:
        value: The original value.
        mutators: A list of mutator dictionaries, each with keys "name" and optional "params".
        field_name: The name of the field being processed.
        record: The entire record (for enrichment mutators).

    Returns:
        The final mutated value.
    """
    result = value
    for m in mutators:
        mut = create_mutator(m["name"], m.get("params"))
        result = mut.apply(field_name, record, result)
    return result
